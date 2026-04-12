from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.base import Base


class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    color = Column(String, nullable=False, default="#6366f1")

    __table_args__ = (UniqueConstraint("org_id", "name", name="uq_label_org_name"),)

    organization = relationship("Organization", back_populates="labels")
    issues = relationship("Issue", secondary="issue_labels", back_populates="labels")


class IssueLabel(Base):
    __tablename__ = "issue_labels"

    issue_id = Column(
        Integer, ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True
    )
    label_id = Column(
        Integer, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True
    )


class IssueAssignee(Base):
    __tablename__ = "issue_assignees"

    issue_id = Column(
        Integer, ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
