"""
Unit tests for API exception handling middleware.

Tests for custom exception classes, error response formatting,
and exception handler middleware integration.
Follows TDD cycle: RED -> GREEN -> REFACTOR
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestAppException:
    """Tests for the base AppException class."""

    def test_app_exception_has_default_status_code(self):
        """AppException should have 500 as default status code."""
        from src.api.exceptions import AppException

        exc = AppException(message="Something went wrong")

        assert exc.status_code == 500

    def test_app_exception_accepts_custom_status_code(self):
        """AppException should accept custom status code."""
        from src.api.exceptions import AppException

        exc = AppException(message="Not found", status_code=404)

        assert exc.status_code == 404

    def test_app_exception_stores_message(self):
        """AppException should store the error message."""
        from src.api.exceptions import AppException

        exc = AppException(message="Custom error message")

        assert exc.message == "Custom error message"

    def test_app_exception_accepts_error_code(self):
        """AppException should accept an error code."""
        from src.api.exceptions import AppException

        exc = AppException(message="Error", code="CUSTOM_ERROR")

        assert exc.code == "CUSTOM_ERROR"

    def test_app_exception_accepts_detail(self):
        """AppException should accept additional detail."""
        from src.api.exceptions import AppException

        detail = {"field": "email", "issue": "invalid format"}
        exc = AppException(message="Validation failed", detail=detail)

        assert exc.detail == detail


class TestBadRequestException:
    """Tests for BadRequestException (400)."""

    def test_bad_request_has_400_status_code(self):
        """BadRequestException should have 400 status code."""
        from src.api.exceptions import BadRequestException

        exc = BadRequestException(message="Invalid request")

        assert exc.status_code == 400

    def test_bad_request_has_default_code(self):
        """BadRequestException should have BAD_REQUEST as default code."""
        from src.api.exceptions import BadRequestException

        exc = BadRequestException(message="Invalid request")

        assert exc.code == "BAD_REQUEST"


class TestAuthenticationException:
    """Tests for AuthenticationException (401)."""

    def test_authentication_has_401_status_code(self):
        """AuthenticationException should have 401 status code."""
        from src.api.exceptions import AuthenticationException

        exc = AuthenticationException(message="Login required")

        assert exc.status_code == 401

    def test_authentication_has_default_code(self):
        """AuthenticationException should have AUTHENTICATION_FAILED as default code."""
        from src.api.exceptions import AuthenticationException

        exc = AuthenticationException(message="Login required")

        assert exc.code == "AUTHENTICATION_FAILED"


class TestAuthorizationException:
    """Tests for AuthorizationException (403)."""

    def test_authorization_has_403_status_code(self):
        """AuthorizationException should have 403 status code."""
        from src.api.exceptions import AuthorizationException

        exc = AuthorizationException(message="Access denied")

        assert exc.status_code == 403

    def test_authorization_has_default_code(self):
        """AuthorizationException should have AUTHORIZATION_FAILED as default code."""
        from src.api.exceptions import AuthorizationException

        exc = AuthorizationException(message="Access denied")

        assert exc.code == "AUTHORIZATION_FAILED"


class TestNotFoundException:
    """Tests for NotFoundException (404)."""

    def test_not_found_has_404_status_code(self):
        """NotFoundException should have 404 status code."""
        from src.api.exceptions import NotFoundException

        exc = NotFoundException(message="Resource not found")

        assert exc.status_code == 404

    def test_not_found_has_default_code(self):
        """NotFoundException should have NOT_FOUND as default code."""
        from src.api.exceptions import NotFoundException

        exc = NotFoundException(message="Resource not found")

        assert exc.code == "NOT_FOUND"


class TestConflictException:
    """Tests for ConflictException (409)."""

    def test_conflict_has_409_status_code(self):
        """ConflictException should have 409 status code."""
        from src.api.exceptions import ConflictException

        exc = ConflictException(message="Resource already exists")

        assert exc.status_code == 409

    def test_conflict_has_default_code(self):
        """ConflictException should have CONFLICT as default code."""
        from src.api.exceptions import ConflictException

        exc = ConflictException(message="Resource already exists")

        assert exc.code == "CONFLICT"


class TestValidationException:
    """Tests for ValidationException (422)."""

    def test_validation_has_422_status_code(self):
        """ValidationException should have 422 status code."""
        from src.api.exceptions import ValidationException

        exc = ValidationException(message="Validation failed")

        assert exc.status_code == 422

    def test_validation_has_default_code(self):
        """ValidationException should have VALIDATION_ERROR as default code."""
        from src.api.exceptions import ValidationException

        exc = ValidationException(message="Validation failed")

        assert exc.code == "VALIDATION_ERROR"

    def test_validation_accepts_errors_list(self):
        """ValidationException should accept list of validation errors."""
        from src.api.exceptions import ValidationException

        errors = [
            {"field": "email", "error": "Invalid email format"},
            {"field": "password", "error": "Password too short"},
        ]
        exc = ValidationException(message="Validation failed", errors=errors)

        assert exc.errors == errors
        assert len(exc.errors) == 2


class TestFormatErrorResponse:
    """Tests for format_error_response utility function."""

    def test_format_error_response_includes_error_message(self):
        """Formatted response should include error message."""
        from src.api.exceptions import format_error_response

        response = format_error_response(
            message="Something went wrong", code="INTERNAL_ERROR"
        )

        assert response["error"] == "Something went wrong"

    def test_format_error_response_includes_code(self):
        """Formatted response should include error code."""
        from src.api.exceptions import format_error_response

        response = format_error_response(message="Error", code="CUSTOM_CODE")

        assert response["code"] == "CUSTOM_CODE"

    def test_format_error_response_includes_detail_when_provided(self):
        """Formatted response should include detail when provided."""
        from src.api.exceptions import format_error_response

        detail = {"reason": "timeout"}
        response = format_error_response(message="Error", code="TIMEOUT", detail=detail)

        assert response["detail"] == detail

    def test_format_error_response_excludes_detail_when_none(self):
        """Formatted response should not include detail key when None."""
        from src.api.exceptions import format_error_response

        response = format_error_response(message="Error", code="ERROR")

        assert "detail" not in response


class TestExceptionHandlers:
    """Integration tests for exception handlers."""

    @pytest.fixture
    def test_app(self) -> FastAPI:
        """Create a test FastAPI app with exception handlers."""
        from src.api.exceptions import (
            AppException,
            AuthenticationException,
            NotFoundException,
            ValidationException,
            add_exception_handlers,
        )

        app = FastAPI()
        add_exception_handlers(app)

        @app.get("/app-exception")
        def raise_app_exception():
            raise AppException(message="Server error", code="SERVER_ERROR")

        @app.get("/auth-exception")
        def raise_auth_exception():
            raise AuthenticationException(message="Please login")

        @app.get("/not-found-exception")
        def raise_not_found():
            raise NotFoundException(message="Project not found")

        @app.get("/validation-exception")
        def raise_validation():
            raise ValidationException(
                message="Invalid input",
                errors=[{"field": "email", "error": "required"}],
            )

        @app.get("/generic-exception")
        def raise_generic():
            raise ValueError("Unexpected error")

        return app

    @pytest.fixture
    def client(self, test_app: FastAPI) -> TestClient:
        """Create test client."""
        return TestClient(test_app, raise_server_exceptions=False)

    def test_app_exception_returns_json_response(self, client: TestClient):
        """AppException should return JSON error response."""
        response = client.get("/app-exception")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Server error"
        assert data["code"] == "SERVER_ERROR"

    def test_auth_exception_returns_401(self, client: TestClient):
        """AuthenticationException should return 401 status."""
        response = client.get("/auth-exception")

        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "Please login"
        assert data["code"] == "AUTHENTICATION_FAILED"

    def test_not_found_exception_returns_404(self, client: TestClient):
        """NotFoundException should return 404 status."""
        response = client.get("/not-found-exception")

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Project not found"
        assert data["code"] == "NOT_FOUND"

    def test_validation_exception_includes_errors(self, client: TestClient):
        """ValidationException should include validation errors in response."""
        response = client.get("/validation-exception")

        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Invalid input"
        assert data["code"] == "VALIDATION_ERROR"
        assert "errors" in data["detail"]
        assert len(data["detail"]["errors"]) == 1

    def test_generic_exception_returns_500(self, client: TestClient):
        """Unhandled exceptions should return generic 500 error."""
        response = client.get("/generic-exception")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal server error"
        assert data["code"] == "INTERNAL_ERROR"


class TestAddExceptionHandlers:
    """Tests for the add_exception_handlers function."""

    def test_add_exception_handlers_registers_handlers(self):
        """add_exception_handlers should register handlers on the app."""
        from src.api.exceptions import add_exception_handlers

        app = FastAPI()
        add_exception_handlers(app)

        # Check that exception handlers are registered
        assert len(app.exception_handlers) > 0

    def test_add_exception_handlers_returns_none(self):
        """add_exception_handlers should return None."""
        from src.api.exceptions import add_exception_handlers

        app = FastAPI()
        result = add_exception_handlers(app)

        assert result is None
