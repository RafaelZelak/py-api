import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from core.exceptions import DomainException

_logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainException)
    async def handle_domain_exception(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        field_errors = {
            ".".join(str(part) for part in error["loc"][1:]): error["msg"]
            for error in exc.errors()
        }
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "REQUEST_VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": field_errors,
            },
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        _logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {},
            },
        )
