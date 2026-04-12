from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core import security
from app.core.security import require_org_role
from app.models.organization import OrganizationMember, RoleEnum
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/orgs/{org_id}/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    org_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.member)),
):
    return ProjectService.list(db, org_id)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    org_id: int,
    data: ProjectCreate,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    return ProjectService.create(db, org_id, data)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    org_id: int,
    project_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.member)),
):
    return ProjectService.get(db, org_id, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    org_id: int,
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.admin)),
):
    return ProjectService.update(db, org_id, project_id, data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    org_id: int,
    project_id: int,
    db: Session = Depends(security.get_db),
    _: OrganizationMember = Depends(require_org_role(RoleEnum.owner)),
):
    ProjectService.delete(db, org_id, project_id)
