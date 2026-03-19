from typing import Any


class DomainException(Exception):
    error_code: str = "DOMAIN_ERROR"
    http_status: int = 500

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ResourceNotFoundError(DomainException):
    error_code = "RESOURCE_NOT_FOUND"
    http_status = 404


class ResourceAlreadyExistsError(DomainException):
    error_code = "RESOURCE_ALREADY_EXISTS"
    http_status = 409


class BusinessRuleViolationError(DomainException):
    error_code = "BUSINESS_RULE_VIOLATION"
    http_status = 422


class ValidationError(DomainException):
    error_code = "DOMAIN_VALIDATION_ERROR"
    http_status = 422


class UnauthorizedError(DomainException):
    error_code = "UNAUTHORIZED"
    http_status = 401


class ForbiddenError(DomainException):
    error_code = "FORBIDDEN"
    http_status = 403


class InfrastructureError(DomainException):
    error_code = "INFRASTRUCTURE_ERROR"
    http_status = 500
