from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from transport.http.v1.schemas.user import CreateUserRequest, UserResponse
from application.create_user_use_case import CreateUserUseCase
from application.delete_user_use_case import DeleteUserUseCase
from infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from infrastructure.database import get_db

router = APIRouter()

@router.post("/users", response_model=UserResponse)
def create_user(request: CreateUserRequest, db: Session = Depends(get_db)):
    repository = SQLAlchemyUserRepository(db)
    use_case = CreateUserUseCase(repository)
    try:
        user = use_case.execute(request.name, request.email, request.password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    repository = SQLAlchemyUserRepository(db)
    use_case = DeleteUserUseCase(repository)
    try:
        user = use_case.execute(user_id)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
