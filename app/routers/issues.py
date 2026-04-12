from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core import security
from app.core.security import require_org_role
from app.models.user import User
from app.models.issue import StatusEnum, PriorityEnum
from app.models.organization import OrganizationMember, RoleEnum
from app.schemas.issue import (
    IssueCreate, IssueUpdate, IssueResponse, IssueDetailResponse, PaginatedIssues,
)
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.activity_log import ActivityLogResponse
from app.services.issue_service import IssueService
from app.services.comment_service import CommentService
from app.services.project_service import ProjectService

router = APIRouter(
    prefix="/orgs/{org_id}/projects/{project_id}/issues", tags=["issues"]
)


def _verify_project(org_id: int, project_id: int, db: Session = Depends(security.get_db)):
    return ProjectService.get(db, org_id, project_id)


# ── List (with filters + cursor pagination) ──────────────────────────────────

@router.get("/", response_model=PaginatedIssues, summary="List issues with filters and search")
def list_issues(
    org_id: int,
    project_id: int,
    status: StatusEnum | None = Query(None, description="Filter by status"),
    priority: PriorityEnum | None = Query(None, description="Filter by priority"),
    assignee_id: int | None = Query(None, description="Filter by assignee user ID"),
    label_id: int | None = Query(None, description="Filter by label ID"),
    q: str | None = Query(None, description="Full-text search on title and description"),
    sort: str = Query(
        default="-updated_at",
        pattern=r"^-?(updated_at|created_at|priority|status)$",
        description="Sort field. Prefix with `-` for descending.",
    ),
    cursor: str | None = Query(None, description="Pagination cursor from previous response"),
    limit: int = Query(default=20, ge=1, le=100, description="Page size"),
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.member)),
):
    _verify_project(org_id, project_id, db)
    return IssueService.list_paginated(
        db, project_id,
        status=status, priority=priority,
        assignee_id=assignee_id, label_id=label_id,
        search=q, sort=sort, cursor=cursor, limit=limit,
    )


# ── Single issue ──────────────────────────────────────────────────────────────

@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    org_id: int,
    project_id: int,
    data: IssueCreate,
    db: Session = Depends(security.get_db),
    membership: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    _verify_project(org_id, project_id, db)
    return IssueService.create(db, project_id, data, created_by=membership.user_id)


@router.get("/{issue_id}", response_model=IssueDetailResponse)
def get_issue(
    org_id: int,
    project_id: int,
    issue_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.member)),
):
    return IssueService.get(db, project_id, issue_id)


@router.patch("/{issue_id}", response_model=IssueResponse)
def update_issue(
    org_id: int,
    project_id: int,
    issue_id: int,
    data: IssueUpdate,
    db: Session = Depends(security.get_db),
    membership: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    return IssueService.update(db, project_id, issue_id, data, user_id=membership.user_id)


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(
    org_id: int,
    project_id: int,
    issue_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.owner)),
):
    IssueService.delete(db, project_id, issue_id)


# ── Assignees ─────────────────────────────────────────────────────────────────

@router.post(
    "/{issue_id}/assignees/{user_id}",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_assignee(
    org_id: int,
    project_id: int,
    issue_id: int,
    user_id: int,
    db: Session = Depends(security.get_db),
    membership: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    return IssueService.add_assignee(
        db, project_id, issue_id, user_id, actor_id=membership.user_id
    )


@router.delete(
    "/{issue_id}/assignees/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_assignee(
    org_id: int,
    project_id: int,
    issue_id: int,
    user_id: int,
    db: Session = Depends(security.get_db),
    membership: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    IssueService.remove_assignee(
        db, project_id, issue_id, user_id, actor_id=membership.user_id
    )


# ── Labels ────────────────────────────────────────────────────────────────────

@router.post(
    "/{issue_id}/labels/{label_id}",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_label(
    org_id: int,
    project_id: int,
    issue_id: int,
    label_id: int,
    db: Session = Depends(security.get_db),
    membership: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    return IssueService.add_label(
        db, project_id, issue_id, label_id, actor_id=membership.user_id
    )


@router.delete(
    "/{issue_id}/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_label(
    org_id: int,
    project_id: int,
    issue_id: int,
    label_id: int,
    db: Session = Depends(security.get_db),
    membership: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    IssueService.remove_label(
        db, project_id, issue_id, label_id, actor_id=membership.user_id
    )


# ── Comments ──────────────────────────────────────────────────────────────────

@router.get("/{issue_id}/comments", response_model=list[CommentResponse])
def list_comments(
    org_id: int,
    project_id: int,
    issue_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.member)),
):
    # Verify issue belongs to project
    IssueService.get(db, project_id, issue_id)
    return CommentService.list(db, issue_id)


@router.post(
    "/{issue_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    org_id: int,
    project_id: int,
    issue_id: int,
    data: CommentCreate,
    db: Session = Depends(security.get_db),
    membership: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    IssueService.get(db, project_id, issue_id)
    return CommentService.create(db, issue_id, data, user_id=membership.user_id)


@router.delete(
    "/{issue_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_comment(
    org_id: int,
    project_id: int,
    issue_id: int,
    comment_id: int,
    db: Session = Depends(security.get_db),
    membership: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    CommentService.delete(db, issue_id, comment_id, user_id=membership.user_id)


# ── Activity log ──────────────────────────────────────────────────────────────

@router.get("/{issue_id}/activity", response_model=list[ActivityLogResponse])
def get_activity(
    org_id: int,
    project_id: int,
    issue_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.member)),
):
    issue = IssueService.get(db, project_id, issue_id)
    return issue.activity_logs
