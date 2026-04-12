import base64
import json
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc, or_
from fastapi import HTTPException
from app.models.issue import Issue, StatusEnum, PriorityEnum
from app.models.activity_log import ActivityLog
from app.models.label import IssueLabel, IssueAssignee
from app.schemas.issue import IssueCreate, IssueUpdate, PaginatedIssues, IssueResponse
import app.database as _db_module

# ---------------------------------------------------------------------------
# Cursor helpers  (keyset by id — simple, DB-agnostic)
# ---------------------------------------------------------------------------

def _encode_cursor(issue_id: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"id": issue_id}).encode()).decode()


def _decode_cursor(cursor: str) -> int:
    try:
        return json.loads(base64.urlsafe_b64decode(cursor).decode())["id"]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid pagination cursor")


# ---------------------------------------------------------------------------
# Sort helpers
# ---------------------------------------------------------------------------

_SORT_COLUMNS = {
    "updated_at": Issue.updated_at,
    "created_at": Issue.created_at,
    "priority":   Issue.priority,
    "status":     Issue.status,
}


def _build_order(sort: str):
    descending = sort.startswith("-")
    col = _SORT_COLUMNS.get(sort.lstrip("-"), Issue.updated_at)
    return desc(col) if descending else asc(col)


# ---------------------------------------------------------------------------
# Activity log helper
# ---------------------------------------------------------------------------

def _log(db: Session, issue_id: int, user_id: int, action: str,
         field: str | None = None, old: str | None = None, new: str | None = None):
    db.add(ActivityLog(
        issue_id=issue_id, user_id=user_id,
        action=action, field=field, old_value=old, new_value=new,
    ))


# ---------------------------------------------------------------------------
# IssueService
# ---------------------------------------------------------------------------

class IssueService:

    @staticmethod
    def create(db: Session, project_id: int, data: IssueCreate, created_by: int) -> Issue:
        issue = Issue(
            project_id=project_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            created_by=created_by,
        )
        db.add(issue)
        db.flush()
        _log(db, issue.id, created_by, "created")
        db.commit()
        db.refresh(issue)
        return issue

    @staticmethod
    def list_paginated(
        db: Session,
        project_id: int,
        status: StatusEnum | None = None,
        priority: PriorityEnum | None = None,
        assignee_id: int | None = None,
        label_id: int | None = None,
        search: str | None = None,
        sort: str = "-updated_at",
        cursor: str | None = None,
        limit: int = 20,
    ) -> PaginatedIssues:
        q = (
            db.query(Issue)
            .options(joinedload(Issue.assignees), joinedload(Issue.labels))
            .filter(Issue.project_id == project_id)
        )

        if status:
            q = q.filter(Issue.status == status)
        if priority:
            q = q.filter(Issue.priority == priority)
        if assignee_id:
            q = q.filter(
                Issue.id.in_(
                    db.query(IssueAssignee.issue_id)
                    .filter(IssueAssignee.user_id == assignee_id)
                )
            )
        if label_id:
            q = q.filter(
                Issue.id.in_(
                    db.query(IssueLabel.issue_id)
                    .filter(IssueLabel.label_id == label_id)
                )
            )

        if search:
            dialect = _db_module.engine.dialect.name
            if dialect == "postgresql":
                from sqlalchemy import text as sa_text
                q = q.filter(
                    sa_text("issues.search_vector @@ plainto_tsquery('english', :q)")
                    .bindparams(q=search)
                )
            else:
                pattern = f"%{search}%"
                q = q.filter(
                    or_(Issue.title.ilike(pattern), Issue.description.ilike(pattern))
                )

        total = q.with_entities(Issue.id).distinct().count()

        descending = sort.startswith("-")
        primary_order = _build_order(sort)
        secondary_order = desc(Issue.id) if descending else asc(Issue.id)

        if cursor:
            cur_id = _decode_cursor(cursor)
            if descending:
                q = q.filter(Issue.id < cur_id)
            else:
                q = q.filter(Issue.id > cur_id)

        issues = (
            q.order_by(primary_order, secondary_order)
            .limit(limit + 1)
            .all()
        )

        next_cursor: str | None = None
        if len(issues) > limit:
            next_cursor = _encode_cursor(issues[limit - 1].id)
            issues = issues[:limit]

        return PaginatedIssues(
            items=[IssueResponse.model_validate(i) for i in issues],
            next_cursor=next_cursor,
            total=total,
        )

    @staticmethod
    def get(db: Session, project_id: int, issue_id: int) -> Issue:
        issue = (
            db.query(Issue)
            .options(
                joinedload(Issue.assignees),
                joinedload(Issue.labels),
                joinedload(Issue.comments),
                joinedload(Issue.activity_logs),
            )
            .filter(Issue.id == issue_id, Issue.project_id == project_id)
            .first()
        )
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        return issue

    @staticmethod
    def update(
        db: Session, project_id: int, issue_id: int, data: IssueUpdate, user_id: int
    ) -> Issue:
        issue = IssueService.get(db, project_id, issue_id)

        for field_name in ("title", "description", "status", "priority"):
            new_val = getattr(data, field_name)
            if new_val is None:
                continue
            old_val = getattr(issue, field_name)
            old_str = old_val.value if hasattr(old_val, "value") else str(old_val or "")
            new_str = new_val.value if hasattr(new_val, "value") else str(new_val)
            if old_val != new_val:
                setattr(issue, field_name, new_val)
                _log(db, issue.id, user_id, f"{field_name}_changed",
                     field=field_name, old=old_str, new=new_str)

        db.commit()
        db.refresh(issue)
        return issue

    @staticmethod
    def delete(db: Session, project_id: int, issue_id: int) -> None:
        issue = IssueService.get(db, project_id, issue_id)
        db.delete(issue)
        db.commit()

    # ── Assignees ────────────────────────────────────────────────────────────

    @staticmethod
    def add_assignee(
        db: Session, project_id: int, issue_id: int, user_id: int, actor_id: int
    ) -> Issue:
        issue = IssueService.get(db, project_id, issue_id)
        if any(u.id == user_id for u in issue.assignees):
            raise HTTPException(status_code=400, detail="User already assigned")
        db.add(IssueAssignee(issue_id=issue_id, user_id=user_id))
        _log(db, issue_id, actor_id, "assigned", new=str(user_id))
        db.commit()
        db.refresh(issue)
        return issue

    @staticmethod
    def remove_assignee(
        db: Session, project_id: int, issue_id: int, user_id: int, actor_id: int
    ) -> Issue:
        issue = IssueService.get(db, project_id, issue_id)
        row = db.query(IssueAssignee).filter(
            IssueAssignee.issue_id == issue_id, IssueAssignee.user_id == user_id
        ).first()
        if not row:
            raise HTTPException(status_code=404, detail="Assignee not found")
        db.delete(row)
        _log(db, issue_id, actor_id, "unassigned", old=str(user_id))
        db.commit()
        db.refresh(issue)
        return issue

    # ── Labels ────────────────────────────────────────────────────────────────

    @staticmethod
    def add_label(
        db: Session, project_id: int, issue_id: int, label_id: int, actor_id: int
    ) -> Issue:
        issue = IssueService.get(db, project_id, issue_id)
        if any(lb.id == label_id for lb in issue.labels):
            raise HTTPException(status_code=400, detail="Label already added")
        db.add(IssueLabel(issue_id=issue_id, label_id=label_id))
        _log(db, issue_id, actor_id, "labeled", new=str(label_id))
        db.commit()
        db.refresh(issue)
        return issue

    @staticmethod
    def remove_label(
        db: Session, project_id: int, issue_id: int, label_id: int, actor_id: int
    ) -> Issue:
        issue = IssueService.get(db, project_id, issue_id)
        row = db.query(IssueLabel).filter(
            IssueLabel.issue_id == issue_id, IssueLabel.label_id == label_id
        ).first()
        if not row:
            raise HTTPException(status_code=404, detail="Label not found on issue")
        db.delete(row)
        _log(db, issue_id, actor_id, "unlabeled", old=str(label_id))
        db.commit()
        db.refresh(issue)
        return issue
