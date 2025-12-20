"""API exception handling middleware and exception schemas.

This module provides:
- Custom exception classes for different error types
- Consistent error response formatting
- Exception handlers for FastAPI integration

All exceptions follow a consistent structure for easy frontend handling.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception class for all application errors.

    Provides consistent structure for all custom exceptions with:
    - HTTP status code
    - Error message
    - Error code (machine-readable identifier)
    - Optional detail (additional context)
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            status_code: HTTP status code (default: 500).
            code: Machine-readable error code.
            detail: Additional error details.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code or "INTERNAL_ERROR"
        self.detail = detail


class BadRequestException(AppException):
    """Exception for malformed or invalid requests (400)."""

    def __init__(
        self,
        message: str,
        code: str = "BAD_REQUEST",
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a bad request exception.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code (default: BAD_REQUEST).
            detail: Additional error details.
        """
        super().__init__(message=message, status_code=400, code=code, detail=detail)


class AuthenticationException(AppException):
    """Exception for authentication failures (401)."""

    def __init__(
        self,
        message: str,
        code: str = "AUTHENTICATION_FAILED",
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Initialize an authentication exception.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code (default: AUTHENTICATION_FAILED).
            detail: Additional error details.
        """
        super().__init__(message=message, status_code=401, code=code, detail=detail)


class AuthorizationException(AppException):
    """Exception for authorization failures (403)."""

    def __init__(
        self,
        message: str,
        code: str = "AUTHORIZATION_FAILED",
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Initialize an authorization exception.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code (default: AUTHORIZATION_FAILED).
            detail: Additional error details.
        """
        super().__init__(message=message, status_code=403, code=code, detail=detail)


class NotFoundException(AppException):
    """Exception for resource not found errors (404)."""

    def __init__(
        self,
        message: str,
        code: str = "NOT_FOUND",
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a not found exception.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code (default: NOT_FOUND).
            detail: Additional error details.
        """
        super().__init__(message=message, status_code=404, code=code, detail=detail)


class ConflictException(AppException):
    """Exception for resource conflicts (409)."""

    def __init__(
        self,
        message: str,
        code: str = "CONFLICT",
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a conflict exception.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code (default: CONFLICT).
            detail: Additional error details.
        """
        super().__init__(message=message, status_code=409, code=code, detail=detail)


class ValidationException(AppException):
    """Exception for validation errors (422).

    Supports a list of field-level validation errors.
    """

    def __init__(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        errors: list[dict[str, Any]] | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a validation exception.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code (default: VALIDATION_ERROR).
            errors: List of field-level validation errors.
            detail: Additional error details.
        """
        super().__init__(message=message, status_code=422, code=code, detail=detail)
        self.errors = errors or []


def format_error_response(
    message: str,
    code: str,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format an error response dictionary.

    Args:
        message: Human-readable error message.
        code: Machine-readable error code.
        detail: Optional additional error details.

    Returns:
        Dictionary with error, code, and optionally detail keys.
    """
    response: dict[str, Any] = {
        "error": message,
        "code": code,
    }
    if detail is not None:
        response["detail"] = detail
    return response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle AppException and its subclasses.

    Args:
        request: The incoming request.
        exc: The raised AppException.

    Returns:
        JSON response with error details.
    """
    # For ValidationException, include errors in detail
    detail = exc.detail
    if isinstance(exc, ValidationException) and exc.errors:
        detail = {"errors": exc.errors, **(detail or {})}

    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            message=exc.message,
            code=exc.code,
            detail=detail,
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions.

    Catches any exception not handled by specific handlers and returns
    a generic 500 error. Does not expose internal error details.

    Args:
        request: The incoming request.
        exc: The raised exception.

    Returns:
        JSON response with generic error message.
    """
    return JSONResponse(
        status_code=500,
        content=format_error_response(
            message="Internal server error",
            code="INTERNAL_ERROR",
        ),
    )


def add_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
