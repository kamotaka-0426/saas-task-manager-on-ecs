from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core import security
from app.core.security import require_org_role
from app.models.user import User
from app.models.organization import OrganizationMember, RoleEnum
from app.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    MemberInvite, MemberResponse,
)
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/orgs", tags=["organizations"])


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_org(
    data: OrganizationCreate,
    db: Session = Depends(security.get_db),
    current_user: User = Depends(security.get_current_user),
):
    return OrganizationService.create(db, data, owner_id=current_user.id)


@router.get("/", response_model=list[OrganizationResponse])
def list_orgs(
    db: Session = Depends(security.get_db),
    current_user: User = Depends(security.get_current_user),
):
    return OrganizationService.list_for_user(db, current_user.id)


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_org(
    org_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.member)),
):
    return OrganizationService.get(db, org_id)


@router.patch("/{org_id}", response_model=OrganizationResponse)
def update_org(
    org_id: int,
    data: OrganizationUpdate,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.owner)),
):
    return OrganizationService.update(db, org_id, data)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_org(
    org_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.owner)),
):
    OrganizationService.delete(db, org_id)


@router.get("/{org_id}/members", response_model=list[MemberResponse])
def list_members(
    org_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.member)),
):
    return OrganizationService.list_members(db, org_id)


@router.post(
    "/{org_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED
)
def add_member(
    org_id: int,
    data: MemberInvite,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    return OrganizationService.add_member(db, org_id, data)


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    org_id: int,
    user_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.owner)),
):
    OrganizationService.remove_member(db, org_id, user_id)
