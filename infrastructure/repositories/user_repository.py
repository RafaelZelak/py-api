from sqlalchemy.orm import Session
from typing import Optional
from domain.user import User
from domain.ports.user_repository import UserRepository
from infrastructure.models.user import UserModel

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    def save(self, user: User) -> User:
        user_model = UserModel(
            name=user.name,
            email=user.email,
            password_hash=user.password_hash,
            is_active=user.is_active
        )
        if user.id:
            # Update existing (simplified for MVP, ideally would fetch and update)
            user_model.id = user.id
            self.db.merge(user_model)
        else:
            self.db.add(user_model)
        
        self.db.commit()
        self.db.refresh(user_model)
        return User(
            id=user_model.id,
            name=user_model.name,
            email=user_model.email,
            password_hash=user_model.password_hash,
            is_active=user_model.is_active
        )

    def find_by_email(self, email: str) -> Optional[User]:
        user_model = self.db.query(UserModel).filter(UserModel.email == email).first()
        if user_model:
            return User(
                id=user_model.id,
                name=user_model.name,
                email=user_model.email,
                password_hash=user_model.password_hash,
                is_active=user_model.is_active
            )
        return None

    def find_by_id(self, user_id: int) -> Optional[User]:
        user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_model:
            return User(
                id=user_model.id,
                name=user_model.name,
                email=user_model.email,
                password_hash=user_model.password_hash,
                is_active=user_model.is_active
            )
        return None
