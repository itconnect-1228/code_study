"""Unit tests for the FastAPI application initialization.

Tests cover:
- Application creation and configuration
- CORS middleware setup
- Health check endpoint
- Root endpoint
- Lifespan events (startup/shutdown)
"""

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.src.main import app, create_app, get_app_settings


class TestAppSettings:
    """Tests for application settings loading."""

    def test_default_settings(self):
        """Test default settings when environment variables are not set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = get_app_settings()

            assert settings["app_name"] == "AI Code Learning Platform"
            assert settings["app_version"] == "1.0.0"
            assert settings["debug"] is False
            assert "http://localhost:3000" in settings["cors_origins"]
            assert "http://localhost:5173" in settings["cors_origins"]

    def test_custom_settings_from_env(self):
        """Test settings loaded from environment variables."""
        env_vars = {
            "APP_NAME": "Custom App",
            "APP_VERSION": "2.0.0",
            "DEBUG": "true",
            "CORS_ORIGINS": "http://example.com,http://test.com",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = get_app_settings()

            assert settings["app_name"] == "Custom App"
            assert settings["app_version"] == "2.0.0"
            assert settings["debug"] is True
            assert settings["cors_origins"] == ["http://example.com", "http://test.com"]

    def test_debug_variations(self):
        """Test various debug flag values."""
        for true_value in ["true", "True", "TRUE", "1", "yes", "YES"]:
            with patch.dict(os.environ, {"DEBUG": true_value}, clear=True):
                settings = get_app_settings()
                assert settings["debug"] is True, f"Failed for DEBUG={true_value}"

        for false_value in ["false", "False", "0", "no", ""]:
            with patch.dict(os.environ, {"DEBUG": false_value}, clear=True):
                settings = get_app_settings()
                assert settings["debug"] is False, f"Failed for DEBUG={false_value}"


class TestAppCreation:
    """Tests for FastAPI application creation."""

    def test_app_is_created(self):
        """Test that the app is created successfully."""
        assert app is not None
        assert app.title is not None

    def test_create_app_returns_fastapi_instance(self):
        """Test that create_app returns a FastAPI instance."""
        with patch.dict(os.environ, {}, clear=True):
            test_app = create_app()
            assert test_app is not None
            assert hasattr(test_app, "routes")

    def test_app_has_correct_title(self):
        """Test that app has the correct title from settings."""
        with patch.dict(os.environ, {"APP_NAME": "Test App"}, clear=True):
            test_app = create_app()
            assert test_app.title == "Test App"


class TestCorsMiddleware:
    """Tests for CORS middleware configuration."""

    def test_cors_middleware_is_configured(self):
        """Test that CORS middleware is added to the app."""
        # Check that the app has middleware
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    def test_cors_headers_in_response(self):
        """Test that CORS headers are included in responses."""
        client = TestClient(app)
        response = client.get("/", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_preflight_request(self):
        """Test CORS preflight (OPTIONS) request handling."""
        client = TestClient(app)
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self):
        """Test that /health returns 200 OK."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_returns_healthy_status(self):
        """Test that /health returns healthy status."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_includes_timestamp(self):
        """Test that /health includes a timestamp."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()

        assert "timestamp" in data
        # Verify it's a valid ISO format timestamp
        assert "T" in data["timestamp"]

    def test_health_includes_version(self):
        """Test that /health includes the version."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()

        assert "version" in data


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_200(self):
        """Test that / returns 200 OK."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200

    def test_root_returns_api_info(self):
        """Test that / returns API information."""
        client = TestClient(app)
        response = client.get("/")
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert data["docs"] == "/docs"


class TestLifespan:
    """Tests for application lifespan events."""

    def test_app_starts_without_db(self):
        """Test that app can start even without database connection."""
        # The app should handle database initialization failure gracefully
        with patch.dict(os.environ, {}, clear=True):
            test_app = create_app()
            client = TestClient(test_app)
            response = client.get("/health")
            assert response.status_code == 200
