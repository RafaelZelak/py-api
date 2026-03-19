import pytest
from core.exceptions import ResourceAlreadyExistsError
from application.users.create_user_use_case import CreateUserUseCase
from tests.fakes.fake_user_repository import FakeUserRepository
from domain.user import User
from infrastructure.security import Security


class TestCreateUserUseCase_Execute:
    def test_creates_user_successfully(self):
        # Arrange
        fake_repo = FakeUserRepository()
        use_case = CreateUserUseCase(fake_repo)

        # Act
        result = use_case.execute(name="Rafael", email="rafael@test.com", password="password123")

        # Assert
        assert result.id is not None
        assert result.name == "Rafael"
        assert result.email == "rafael@test.com"
        assert result.is_active is True
        # Verifica se criptografou a senha (não salva plaintext)
        assert result.password_hash != "password123"
        assert Security.verify_password("password123", result.password_hash) is True
        
        # Verifica estado da dependencia
        saved_user = fake_repo.find_by_email("rafael@test.com")
        assert saved_user is not None

    def test_email_already_registered_stops_execution_with_error(self):
        # Arrange
        fake_repo = FakeUserRepository([
            User(id=1, name="Existing", email="existing@test.com", password_hash="123")
        ])
        use_case = CreateUserUseCase(fake_repo)

        # Act & Assert
        with pytest.raises(ResourceAlreadyExistsError) as exc_info:
            use_case.execute(name="New Guy", email="existing@test.com", password="newpassword")

        # Assert
        assert exc_info.value.error_code == "RESOURCE_ALREADY_EXISTS"
        
        # Não devia ter salvo ninguem novo com o mesmo email (na verdade abortou antes)
        assert len(fake_repo.users) == 1
