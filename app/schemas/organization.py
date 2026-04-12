from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.organization import RoleEnum


class OrganizationCreate(BaseModel):
    name: str
    slug: str


class OrganizationUpdate(BaseModel):
    name: str | None = None


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    created_at: datetime


class MemberInvite(BaseModel):
    email: str
    role: RoleEnum = RoleEnum.member


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role: RoleEnum
