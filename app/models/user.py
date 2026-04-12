from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    org_memberships = relationship(
        "OrganizationMember", back_populates="user", cascade="all, delete-orphan"
    )
    created_issues = relationship("Issue", back_populates="creator")
