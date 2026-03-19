from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from transport.http.v1.schemas.user import CreateUserRequest, UserResponse
from application.users.create_user_use_case import CreateUserUseCase
from application.users.delete_user_use_case import DeleteUserUseCase
from infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from infrastructure.database import get_db

router = APIRouter()


@router.post("/users", response_model=UserResponse)
def create_user(request: CreateUserRequest, db: Session = Depends(get_db)):
    repository = SQLAlchemyUserRepository(db)
    use_case = CreateUserUseCase(repository)
    return use_case.execute(request.name, request.email, request.password)


@router.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    repository = SQLAlchemyUserRepository(db)
    use_case = DeleteUserUseCase(repository)
    return use_case.execute(user_id)
