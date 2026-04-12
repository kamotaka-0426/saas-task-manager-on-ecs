from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.label import Label
from app.schemas.label import LabelCreate


class LabelService:
    @staticmethod
    def list(db: Session, org_id: int) -> list[Label]:
        return db.query(Label).filter(Label.org_id == org_id).all()

    @staticmethod
    def create(db: Session, org_id: int, data: LabelCreate) -> Label:
        if db.query(Label).filter(Label.org_id == org_id, Label.name == data.name).first():
            raise HTTPException(status_code=400, detail="Label name already exists in this org")
        label = Label(org_id=org_id, name=data.name, color=data.color)
        db.add(label)
        db.commit()
        db.refresh(label)
        return label

    @staticmethod
    def get(db: Session, org_id: int, label_id: int) -> Label:
        label = db.query(Label).filter(
            Label.id == label_id, Label.org_id == org_id
        ).first()
        if not label:
            raise HTTPException(status_code=404, detail="Label not found")
        return label

    @staticmethod
    def delete(db: Session, org_id: int, label_id: int) -> None:
        label = LabelService.get(db, org_id, label_id)
        db.delete(label)
        db.commit()
