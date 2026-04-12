from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    @staticmethod
    def create(db: Session, org_id: int, data: ProjectCreate) -> Project:
        project = Project(org_id=org_id, name=data.name, description=data.description)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def list(db: Session, org_id: int) -> list[Project]:
        return db.query(Project).filter(Project.org_id == org_id).all()

    @staticmethod
    def get(db: Session, org_id: int, project_id: int) -> Project:
        project = (
            db.query(Project)
            .filter(Project.id == project_id, Project.org_id == org_id)
            .first()
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    @staticmethod
    def update(db: Session, org_id: int, project_id: int, data: ProjectUpdate) -> Project:
        project = ProjectService.get(db, org_id, project_id)
        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete(db: Session, org_id: int, project_id: int) -> None:
        project = ProjectService.get(db, org_id, project_id)
        db.delete(project)
        db.commit()
