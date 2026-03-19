import pytest
from fastapi.testclient import TestClient
from main import app
from infrastructure.database import get_db


# Mock do get_db genérico para não exigir banco de dados nos testes de transporte
def override_get_db():
    yield None

@pytest.fixture(scope="module")
def client() -> TestClient:
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
