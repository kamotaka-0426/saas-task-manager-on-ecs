import enum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.base import Base


class StatusEnum(str, enum.Enum):
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


class PriorityEnum(str, enum.Enum):
    none = "none"
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        SAEnum(StatusEnum, name="statusenum"), nullable=False, default=StatusEnum.backlog
    )
    priority = Column(
        SAEnum(PriorityEnum, name="priorityenum"), nullable=False, default=PriorityEnum.none
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project = relationship("Project", back_populates="issues")
    creator = relationship("User", back_populates="created_issues")
    comments = relationship("Comment", back_populates="issue", cascade="all, delete-orphan")
    activity_logs = relationship(
        "ActivityLog", back_populates="issue", cascade="all, delete-orphan",
        order_by="ActivityLog.created_at",
    )
    labels = relationship("Label", secondary="issue_labels", back_populates="issues")
    assignees = relationship("User", secondary="issue_assignees", foreign_keys="[IssueAssignee.issue_id, IssueAssignee.user_id]")
