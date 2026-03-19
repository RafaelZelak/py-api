from typing import Optional
from domain.user import User
from domain.ports.user_repository import UserRepository


class FakeUserRepository(UserRepository):
    def __init__(self, existing_users: list[User] | None = None):
        self.users: dict[int, User] = {}
        self.users_by_email: dict[str, User] = {}
        self._next_id = 1
        
        if existing_users:
            for user in existing_users:
                self.save(user)
    
    def save(self, user: User) -> User:
        if user.id is None:
            user.id = self._next_id
            self._next_id += 1
            
        self.users[user.id] = user
        self.users_by_email[user.email] = user
        return user

    def find_by_email(self, email: str) -> Optional[User]:
        return self.users_by_email.get(email)

    def find_by_id(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)
