from fastapi.testclient import TestClient


class TestEchoRoute_Post:
    def test_echo_returns_provided_message(self, client: TestClient):
        # Arrange
        payload = {"message": "Hello FastAPI"}

        # Act
        response = client.post("/api/v1/echo", json=payload)

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": "Hello FastAPI"}

    def test_empty_message_stops_on_pydantic_validation(self, client: TestClient):
        # Arrange (faltando message)
        payload = {}

        # Act
        response = client.post("/api/v1/echo", json=payload)

        # Assert (O Error Handler Global captura perfeitamente)
        assert response.status_code == 422
        body = response.json()
        assert body["error_code"] == "REQUEST_VALIDATION_ERROR"
        assert "message" in body["details"]
