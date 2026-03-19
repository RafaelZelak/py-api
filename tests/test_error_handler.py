import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleViolationError,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    InfrastructureError,
)
from transport.http.error_handler import register_exception_handlers


def _build_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/raise/not-found")
    def raise_not_found():
        raise ResourceNotFoundError("Product not found")

    @app.get("/raise/already-exists")
    def raise_already_exists():
        raise ResourceAlreadyExistsError("Email already registered")

    @app.get("/raise/business-rule")
    def raise_business_rule():
        raise BusinessRuleViolationError("Cannot cancel a shipped order")

    @app.get("/raise/domain-validation")
    def raise_domain_validation():
        raise ValidationError("Invalid CPF format")

    @app.get("/raise/unauthorized")
    def raise_unauthorized():
        raise UnauthorizedError("Missing credentials")

    @app.get("/raise/forbidden")
    def raise_forbidden():
        raise ForbiddenError("Insufficient permissions")

    @app.get("/raise/infrastructure")
    def raise_infrastructure():
        raise InfrastructureError("Database operation failed")

    @app.get("/raise/unhandled")
    def raise_unhandled():
        raise RuntimeError("something internal exploded")

    class _RequiredBody(BaseModel):
        name: str
        age: int

    @app.post("/raise/pydantic-validation")
    def raise_pydantic_validation(body: _RequiredBody):
        return body

    return app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(_build_test_app(), raise_server_exceptions=False)


def _assert_error_schema(body: dict) -> None:
    assert "error_code" in body, f"missing error_code in {body}"
    assert "message" in body, f"missing message in {body}"
    assert "details" in body, f"missing details in {body}"


class TestErrorHandler_DomainExceptions:
    def test_resource_not_found(self, client: TestClient):
        response = client.get("/raise/not-found")
        assert response.status_code == 404, f"expected 404, got {response.status_code}"
        body = response.json()
        _assert_error_schema(body)
        assert body["error_code"] == "RESOURCE_NOT_FOUND"
        assert body["message"] == "Product not found"

    def test_resource_already_exists(self, client: TestClient):
        response = client.get("/raise/already-exists")
        assert response.status_code == 409, f"expected 409, got {response.status_code}"
        body = response.json()
        _assert_error_schema(body)
        assert body["error_code"] == "RESOURCE_ALREADY_EXISTS"

    def test_business_rule_violation(self, client: TestClient):
        response = client.get("/raise/business-rule")
        assert response.status_code == 422, f"expected 422, got {response.status_code}"
        body = response.json()
        _assert_error_schema(body)
        assert body["error_code"] == "BUSINESS_RULE_VIOLATION"

    def test_domain_validation(self, client: TestClient):
        response = client.get("/raise/domain-validation")
        assert response.status_code == 422, f"expected 422, got {response.status_code}"
        body = response.json()
        _assert_error_schema(body)
        assert body["error_code"] == "DOMAIN_VALIDATION_ERROR"

    def test_unauthorized(self, client: TestClient):
        response = client.get("/raise/unauthorized")
        assert response.status_code == 401, f"expected 401, got {response.status_code}"
        body = response.json()
        _assert_error_schema(body)
        assert body["error_code"] == "UNAUTHORIZED"

    def test_forbidden(self, client: TestClient):
        response = client.get("/raise/forbidden")
        assert response.status_code == 403, f"expected 403, got {response.status_code}"
        body = response.json()
        _assert_error_schema(body)
        assert body["error_code"] == "FORBIDDEN"

    def test_infrastructure_error(self, client: TestClient):
        response = client.get("/raise/infrastructure")
        assert response.status_code == 500, f"expected 500, got {response.status_code}"
        body = response.json()
        _assert_error_schema(body)
        assert body["error_code"] == "INFRASTRUCTURE_ERROR"


class TestErrorHandler_PydanticValidation:
    def test_missing_fields_returns_422_with_details(self, client: TestClient):
        response = client.post("/raise/pydantic-validation", json={})
        assert response.status_code == 422, f"expected 422, got {response.status_code}"
        body = response.json()
        _assert_error_schema(body)
        assert body["error_code"] == "REQUEST_VALIDATION_ERROR"
        assert isinstance(body["details"], dict)
        assert len(body["details"]) > 0, "details must contain field-level errors"

    def test_details_map_field_to_message(self, client: TestClient):
        response = client.post("/raise/pydantic-validation", json={"name": "Alice"})
        assert response.status_code == 422, f"expected 422, got {response.status_code}"
        body = response.json()
        assert "age" in body["details"], f"expected 'age' in details, got {body['details']}"


class TestErrorHandler_UnhandledException:
    def test_returns_500_with_generic_message(self, client: TestClient):
        response = client.get("/raise/unhandled")
        assert response.status_code == 500, f"expected 500, got {response.status_code}"
        body = response.json()
        _assert_error_schema(body)
        assert body["error_code"] == "INTERNAL_SERVER_ERROR"

    def test_does_not_leak_internal_details(self, client: TestClient):
        response = client.get("/raise/unhandled")
        body_text = response.text
        assert "RuntimeError" not in body_text, "exception class must not appear in response"
        assert "exploded" not in body_text, "internal exception message must not appear in response"
        assert "Traceback" not in body_text, "traceback must not appear in response"
