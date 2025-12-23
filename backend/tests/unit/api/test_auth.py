"""Unit tests for authentication API endpoints.

This module tests the authentication API endpoints:
- POST /auth/register - User registration
- POST /auth/login - User login with JWT token generation
- POST /auth/logout - User logout with token revocation
- POST /auth/refresh - Refresh token rotation

All tests use the async test client and isolated database sessions.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth.user_service import UserService


class TestRegisterEndpoint:
    """Tests for POST /auth/register endpoint (T028)."""

    @pytest.mark.asyncio
    async def test_register_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful user registration."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == "newuser@example.com"
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test registration with duplicate email returns 409 Conflict."""
        # Create first user
        user_service = UserService(db_session)
        await user_service.register("existing@example.com", "Password123!")
        await db_session.commit()

        # Try to register with same email
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "existing@example.com",
                "password": "DifferentPass456!",
            },
        )

        assert response.status_code == 409
        data = response.json()
        assert "error" in data
        assert data["code"] == "EMAIL_ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_register_invalid_email(
        self,
        async_client: AsyncClient,
    ):
        """Test registration with invalid email format."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password(
        self,
        async_client: AsyncClient,
    ):
        """Test registration with weak password (less than 8 chars)."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "weak",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields(
        self,
        async_client: AsyncClient,
    ):
        """Test registration with missing required fields."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com"},
        )
        assert response.status_code == 422

        response = await async_client.post(
            "/api/v1/auth/register",
            json={"password": "SecurePass123!"},
        )
        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests for POST /auth/login endpoint (T029)."""

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful login returns tokens."""
        # Create user first
        user_service = UserService(db_session)
        await user_service.register("test@example.com", "Password123!")
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "Password123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"

        # Check refresh token cookie
        assert "refresh_token" in response.cookies

    @pytest.mark.asyncio
    async def test_login_invalid_email(
        self,
        async_client: AsyncClient,
    ):
        """Test login with non-existent email returns 401."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123!",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test login with wrong password returns 401."""
        # Create user
        user_service = UserService(db_session)
        await user_service.register("test@example.com", "Password123!")
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword!",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "INVALID_CREDENTIALS"


class TestLogoutEndpoint:
    """Tests for POST /auth/logout endpoint (T030)."""

    @pytest.mark.asyncio
    async def test_logout_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful logout clears cookies."""
        # Login first
        user_service = UserService(db_session)
        await user_service.register("test@example.com", "Password123!")
        await db_session.commit()

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "Password123!",
            },
        )
        access_token = login_response.json()["access_token"]

        # Logout
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_logout_without_auth(
        self,
        async_client: AsyncClient,
    ):
        """Test logout without authentication returns 401."""
        response = await async_client.post("/api/v1/auth/logout")

        assert response.status_code == 401


class TestRefreshEndpoint:
    """Tests for POST /auth/refresh endpoint (T031)."""

    @pytest.mark.asyncio
    async def test_refresh_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful token refresh."""
        # Login first
        user_service = UserService(db_session)
        await user_service.register("test@example.com", "Password123!")
        await db_session.commit()

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "Password123!",
            },
        )

        # Get refresh token from cookies
        refresh_token = login_response.cookies.get("refresh_token")

        # Refresh token
        response = await async_client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data

    @pytest.mark.asyncio
    async def test_refresh_without_token(
        self,
        async_client: AsyncClient,
    ):
        """Test refresh without token returns 401."""
        response = await async_client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "MISSING_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(
        self,
        async_client: AsyncClient,
    ):
        """Test refresh with invalid token returns 401."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401
