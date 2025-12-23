"""Unit tests for API dependencies.

Tests the authentication dependency functionality including:
- Extracting access token from cookies
- Verifying token and returning current user
- Handling missing or invalid tokens
- Handling expired tokens

TDD RED Phase: These tests are written before the implementation.
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.services.auth.token_service import TokenService
from src.utils.security import hash_password


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for dependency tests."""
        user = User(
            email="deptest@example.com",
            password_hash=hash_password("TestPassword123!"),
            skill_level="Complete Beginner",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Should return user when valid access token is provided in cookies."""
        from src.api.dependencies import get_current_user

        # Create a valid access token
        token_service = TokenService(db_session)
        access_token = await token_service.create_access_token(test_user.id)

        # Mock the request with the token in cookies
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"access_token": access_token}

        # Get the current user
        current_user = await get_current_user(mock_request, db_session)

        assert current_user is not None
        assert current_user.id == test_user.id
        assert current_user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_current_user_missing_token(
        self, db_session: AsyncSession
    ) -> None:
        """Should raise AuthenticationException when token is missing."""
        from src.api.dependencies import get_current_user
        from src.api.exceptions import AuthenticationException

        # Mock request without access_token cookie
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {}

        with pytest.raises(AuthenticationException) as exc_info:
            await get_current_user(mock_request, db_session)

        assert exc_info.value.status_code == 401
        assert (
            "token" in exc_info.value.message.lower()
            or "auth" in exc_info.value.message.lower()
        )

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self, db_session: AsyncSession
    ) -> None:
        """Should raise AuthenticationException when token is invalid."""
        from src.api.dependencies import get_current_user
        from src.api.exceptions import AuthenticationException

        # Mock request with invalid token
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"access_token": "invalid.token.here"}

        with pytest.raises(AuthenticationException) as exc_info:
            await get_current_user(mock_request, db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Should raise AuthenticationException when token is expired."""
        from datetime import timedelta

        from src.api.dependencies import get_current_user
        from src.api.exceptions import AuthenticationException

        # Create an expired token
        token_service = TokenService(db_session)
        expired_token = await token_service.create_access_token(
            test_user.id, expires_delta=timedelta(seconds=-1)
        )

        # Mock request with expired token
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"access_token": expired_token}

        with pytest.raises(AuthenticationException) as exc_info:
            await get_current_user(mock_request, db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(
        self, db_session: AsyncSession
    ) -> None:
        """Should raise AuthenticationException when user in token doesn't exist."""
        from src.api.dependencies import get_current_user
        from src.api.exceptions import AuthenticationException

        # Create a token for a non-existent user
        non_existent_user_id = uuid4()
        token_service = TokenService(db_session)
        access_token = await token_service.create_access_token(non_existent_user_id)

        # Mock request with valid token but non-existent user
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"access_token": access_token}

        with pytest.raises(AuthenticationException) as exc_info:
            await get_current_user(mock_request, db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_refresh_token_rejected(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Should reject refresh tokens (only access tokens allowed)."""
        from src.api.dependencies import get_current_user
        from src.api.exceptions import AuthenticationException

        # Create a refresh token
        token_service = TokenService(db_session)
        refresh_token = await token_service.create_refresh_token(test_user.id)

        # Mock request with refresh token instead of access token
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"access_token": refresh_token}

        with pytest.raises(AuthenticationException) as exc_info:
            await get_current_user(mock_request, db_session)

        assert exc_info.value.status_code == 401


class TestGetCurrentUserOptional:
    """Tests for get_current_user_optional dependency."""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for dependency tests."""
        user = User(
            email="optionaltest@example.com",
            password_hash=hash_password("TestPassword123!"),
            skill_level="Complete Beginner",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_valid_token(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Should return user when valid access token is provided."""
        from src.api.dependencies import get_current_user_optional

        # Create a valid access token
        token_service = TokenService(db_session)
        access_token = await token_service.create_access_token(test_user.id)

        # Mock request with valid token
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"access_token": access_token}

        current_user = await get_current_user_optional(mock_request, db_session)

        assert current_user is not None
        assert current_user.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_current_user_optional_without_token(
        self, db_session: AsyncSession
    ) -> None:
        """Should return None when no token is provided."""
        from src.api.dependencies import get_current_user_optional

        # Mock request without token
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {}

        current_user = await get_current_user_optional(mock_request, db_session)

        assert current_user is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_invalid_token(
        self, db_session: AsyncSession
    ) -> None:
        """Should return None when token is invalid."""
        from src.api.dependencies import get_current_user_optional

        # Mock request with invalid token
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"access_token": "invalid.token.here"}

        current_user = await get_current_user_optional(mock_request, db_session)

        assert current_user is None
