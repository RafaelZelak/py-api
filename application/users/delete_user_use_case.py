from domain.user import User
from domain.ports.user_repository import UserRepository
from core.exceptions import ResourceNotFoundError


class DeleteUserUseCase:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, user_id: int) -> User:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User not found")

        user.is_active = False
        return self.repository.save(user)
