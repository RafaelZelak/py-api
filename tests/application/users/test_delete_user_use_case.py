import pytest
from core.exceptions import ResourceNotFoundError
from application.users.delete_user_use_case import DeleteUserUseCase
from tests.fakes.fake_user_repository import FakeUserRepository
from domain.user import User


class TestDeleteUserUseCase_Execute:
    def test_deactivates_user_successfully(self):
        # Arrange
        existing_user = User(id=1, name="Rafael", email="rafa@test.com", password_hash="hash", is_active=True)
        fake_repo = FakeUserRepository([existing_user])
        use_case = DeleteUserUseCase(fake_repo)

        # Act
        result = use_case.execute(user_id=1)

        # Assert
        assert result.is_active is False
        assert result.id == 1
        
        # Garante que as mudanças refletiram no repositorio
        saved_user = fake_repo.find_by_id(1)
        assert saved_user.is_active is False

    def test_user_not_found_stops_execution_with_error(self):
        # Arrange
        fake_repo = FakeUserRepository()
        use_case = DeleteUserUseCase(fake_repo)

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            use_case.execute(user_id=999)

        # Assert
        assert exc_info.value.error_code == "RESOURCE_NOT_FOUND"
        assert "not found" in exc_info.value.message.lower()
