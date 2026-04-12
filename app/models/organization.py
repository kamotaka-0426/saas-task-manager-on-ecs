import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Enum as SAEnum, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.base import Base


class RoleEnum(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = relationship(
        "OrganizationMember", back_populates="organization", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Project", back_populates="organization", cascade="all, delete-orphan"
    )
    labels = relationship(
        "Label", back_populates="organization", cascade="all, delete-orphan"
    )


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(
        SAEnum(RoleEnum, name="roleenum"), nullable=False, default=RoleEnum.member
    )

    __table_args__ = (UniqueConstraint("org_id", "user_id", name="uq_org_member"),)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="org_memberships")
