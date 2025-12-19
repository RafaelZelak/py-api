from domain.user import User
from domain.ports.user_repository import UserRepository
from infrastructure.security import Security

class CreateUserUseCase:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, name: str, email: str, password: str) -> User:
        if self.repository.find_by_email(email):
            raise ValueError("Email already registered")

        password_hash = Security.get_password_hash(password)
        user = User(id=None, name=name, email=email, password_hash=password_hash)
        return self.repository.save(user)
