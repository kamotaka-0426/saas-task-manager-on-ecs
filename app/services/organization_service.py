from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.organization import Organization, OrganizationMember, RoleEnum
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationUpdate, MemberInvite


class OrganizationService:
    @staticmethod
    def create(db: Session, data: OrganizationCreate, owner_id: int) -> Organization:
        if db.query(Organization).filter(Organization.slug == data.slug).first():
            raise HTTPException(status_code=400, detail="Slug already taken")
        org = Organization(name=data.name, slug=data.slug)
        db.add(org)
        db.flush()  # get org.id before committing
        member = OrganizationMember(org_id=org.id, user_id=owner_id, role=RoleEnum.owner)
        db.add(member)
        db.commit()
        db.refresh(org)
        return org

    @staticmethod
    def get(db: Session, org_id: int) -> Organization:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org

    @staticmethod
    def list_for_user(db: Session, user_id: int) -> list[Organization]:
        return (
            db.query(Organization)
            .join(OrganizationMember)
            .filter(OrganizationMember.user_id == user_id)
            .all()
        )

    @staticmethod
    def update(db: Session, org_id: int, data: OrganizationUpdate) -> Organization:
        org = OrganizationService.get(db, org_id)
        if data.name is not None:
            org.name = data.name
        db.commit()
        db.refresh(org)
        return org

    @staticmethod
    def delete(db: Session, org_id: int) -> None:
        org = OrganizationService.get(db, org_id)
        db.delete(org)
        db.commit()

    @staticmethod
    def list_members(db: Session, org_id: int) -> list[OrganizationMember]:
        return (
            db.query(OrganizationMember)
            .filter(OrganizationMember.org_id == org_id)
            .all()
        )

    @staticmethod
    def add_member(db: Session, org_id: int, data: MemberInvite) -> OrganizationMember:
        user = db.query(User).filter(User.email == data.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        existing = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.org_id == org_id,
                OrganizationMember.user_id == user.id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="User is already a member")
        member = OrganizationMember(org_id=org_id, user_id=user.id, role=data.role)
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def remove_member(db: Session, org_id: int, user_id: int) -> None:
        member = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.org_id == org_id,
                OrganizationMember.user_id == user_id,
            )
            .first()
        )
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        if member.role == RoleEnum.owner:
            raise HTTPException(status_code=400, detail="Cannot remove the owner")
        db.delete(member)
        db.commit()
