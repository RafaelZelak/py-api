from fastapi.testclient import TestClient


class TestPingRoute_Get:
    def test_ping_returns_success(self, client: TestClient):
        # Act
        response = client.get("/api/v1/ping")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": "It's a live"}
