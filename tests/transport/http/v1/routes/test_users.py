import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from tests.fakes.fake_user_repository import FakeUserRepository
from domain.user import User


class TestUsersRoute_CreateUser:
    def test_creates_user_and_returns_valid_schema(self, client: TestClient):
        # Arrange
        fake_repo = FakeUserRepository()
        payload = {"name": "Test User", "email": "test@test.com", "password": "123"}

        # Act
        with patch("transport.http.v1.routes.users.SQLAlchemyUserRepository", return_value=fake_repo):
            response = client.post("/api/v1/users", json=payload)

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["id"] is not None
        assert body["name"] == "Test User"
        assert body["email"] == "test@test.com"
        assert body["is_active"] is True
        
        # Testando o contrato estrito (A API não deve exibir password_hash para fora, confira o Schema)
        assert "password_hash" not in body
        assert "password" not in body


class TestUsersRoute_DeleteUser:
    def test_deactivates_user_and_returns_updated_schema(self, client: TestClient):
        # Arrange
        existing_user = User(id=1, name="Old", email="old@test.com", password_hash="abc", is_active=True)
        fake_repo = FakeUserRepository([existing_user])

        # Act
        with patch("transport.http.v1.routes.users.SQLAlchemyUserRepository", return_value=fake_repo):
            response = client.delete("/api/v1/users/1")

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["is_active"] is False
        assert body["id"] == 1

    def test_non_existent_returns_404(self, client: TestClient):
        # Arrange
        fake_repo = FakeUserRepository()

        # Act
        with patch("transport.http.v1.routes.users.SQLAlchemyUserRepository", return_value=fake_repo):
            response = client.delete("/api/v1/users/999")

        # Assert
        assert response.status_code == 404
        body = response.json()
        assert body["error_code"] == "RESOURCE_NOT_FOUND"
