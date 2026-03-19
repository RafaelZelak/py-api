import pytest
from infrastructure.security import Security


class TestSecurity_GetPasswordHash:
    def test_generates_hash_different_from_plaintext(self):
        # Arrange
        plain_password = "mySecretPassword123"

        # Act
        hashed_password = Security.get_password_hash(plain_password)

        # Assert
        assert plain_password != hashed_password
        assert hashed_password.startswith("$2")  # Padrão bcrypt


class TestSecurity_VerifyPassword:
    def test_correct_password_returns_true(self):
        # Arrange
        plain_password = "mySecretPassword123"
        hashed = Security.get_password_hash(plain_password)

        # Act
        is_valid = Security.verify_password(plain_password, hashed)

        # Assert
        assert is_valid is True

    def test_wrong_password_returns_false(self):
        # Arrange
        plain_password = "mySecretPassword123"
        wrong_password = "WrongPassword456"
        hashed = Security.get_password_hash(plain_password)

        # Act
        is_valid = Security.verify_password(wrong_password, hashed)

        # Assert
        assert is_valid is False
