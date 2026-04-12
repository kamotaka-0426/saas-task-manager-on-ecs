from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.base import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(
        Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # e.g. "status_changed", "priority_changed", "assigned", "unassigned",
    #      "labeled", "unlabeled", "commented"
    action = Column(String, nullable=False)
    field = Column(String, nullable=True)      # field that changed
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("Issue", back_populates="activity_logs")
    user = relationship("User")
