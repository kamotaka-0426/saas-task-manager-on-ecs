from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core import security
from app.core.security import require_org_role
from app.models.organization import OrganizationMember, RoleEnum
from app.schemas.label import LabelCreate, LabelResponse
from app.services.label_service import LabelService

router = APIRouter(prefix="/orgs/{org_id}/labels", tags=["labels"])


@router.get("/", response_model=list[LabelResponse])
def list_labels(
    org_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.member)),
):
    return LabelService.list(db, org_id)


@router.post("/", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
def create_label(
    org_id: int,
    data: LabelCreate,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    return LabelService.create(db, org_id, data)


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(
    org_id: int,
    label_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.owner)),
):
    LabelService.delete(db, org_id, label_id)
