from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.schemas.auth import UserCreate
from app.models.user import User
from app.core import security


class UserService:
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        new_user = User(
            email=user.email,
            hashed_password=security.get_password_hash(user.password),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User | None:
        user = db.query(User).filter(User.email == email).first()
        if not user or not security.verify_password(password, user.hashed_password):
            return None
        return user
