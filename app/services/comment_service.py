from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.comment import Comment
from app.models.activity_log import ActivityLog
from app.schemas.comment import CommentCreate


class CommentService:
    @staticmethod
    def list(db: Session, issue_id: int) -> list[Comment]:
        return (
            db.query(Comment)
            .filter(Comment.issue_id == issue_id)
            .order_by(Comment.created_at)
            .all()
        )

    @staticmethod
    def create(
        db: Session, issue_id: int, data: CommentCreate, user_id: int
    ) -> Comment:
        comment = Comment(issue_id=issue_id, created_by=user_id, content=data.content)
        db.add(comment)
        # record activity
        log = ActivityLog(
            issue_id=issue_id, user_id=user_id, action="commented",
            new_value=data.content[:120],
        )
        db.add(log)
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def delete(db: Session, issue_id: int, comment_id: int, user_id: int) -> None:
        comment = (
            db.query(Comment)
            .filter(Comment.id == comment_id, Comment.issue_id == issue_id)
            .first()
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        if comment.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete another user's comment",
            )
        db.delete(comment)
        db.commit()
