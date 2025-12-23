"""Unit tests for TokenService.

Tests the token service functionality including:
- Access token creation and verification
- Refresh token creation, verification, and storage
- Token rotation (use and issue new)
- Token revocation (single and all user tokens)
- Expired token cleanup

TDD RED Phase: These tests are written before the implementation.
"""

import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_token import RefreshToken
from src.models.user import User
from src.services.auth.token_service import TokenService
from src.utils.security import hash_password


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for token tests."""
    user = User(
        email="tokentest@example.com",
        password_hash=hash_password("TestPassword123!"),
        skill_level="Complete Beginner",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def token_service(db_session: AsyncSession) -> TokenService:
    """Create a TokenService instance for testing."""
    return TokenService(db_session)


class TestCreateAccessToken:
    """Tests for access token creation."""

    async def test_create_access_token_returns_string(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Access token should be a non-empty string."""
        token = await token_service.create_access_token(test_user.id)
        assert isinstance(token, str)
        assert len(token) > 0

    async def test_create_access_token_contains_user_id(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Access token should contain the user ID."""
        token = await token_service.create_access_token(test_user.id)
        # Verify by decoding token
        user_id = await token_service.get_user_id_from_token(token)
        assert user_id == test_user.id

    async def test_create_access_token_with_custom_expiry(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Access token should support custom expiry time."""
        token = await token_service.create_access_token(
            test_user.id, expires_delta=timedelta(minutes=5)
        )
        assert isinstance(token, str)
        assert len(token) > 0


class TestCreateRefreshToken:
    """Tests for refresh token creation."""

    async def test_create_refresh_token_returns_string(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Refresh token should be a non-empty string."""
        token = await token_service.create_refresh_token(test_user.id)
        assert isinstance(token, str)
        assert len(token) > 0

    async def test_create_refresh_token_stored_in_database(
        self, token_service: TokenService, test_user: User, db_session: AsyncSession
    ) -> None:
        """Refresh token hash should be stored in the database."""
        token = await token_service.create_refresh_token(test_user.id)

        # Calculate expected hash
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Query database for the token
        from sqlalchemy import select

        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db_session.execute(stmt)
        db_token = result.scalar_one_or_none()

        assert db_token is not None
        assert db_token.user_id == test_user.id
        assert not db_token.revoked

    async def test_create_multiple_refresh_tokens_unique(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Multiple refresh tokens should be unique."""
        token1 = await token_service.create_refresh_token(test_user.id)
        token2 = await token_service.create_refresh_token(test_user.id)
        assert token1 != token2

    async def test_create_refresh_token_with_custom_expiry(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Refresh token should support custom expiry time."""
        token = await token_service.create_refresh_token(
            test_user.id, expires_delta=timedelta(days=1)
        )
        assert isinstance(token, str)


class TestVerifyAccessToken:
    """Tests for access token verification."""

    async def test_verify_valid_access_token(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Valid access token should be verified successfully."""
        token = await token_service.create_access_token(test_user.id)
        is_valid = await token_service.verify_access_token(token)
        assert is_valid is True

    async def test_verify_invalid_access_token(
        self, token_service: TokenService
    ) -> None:
        """Invalid access token should fail verification."""
        is_valid = await token_service.verify_access_token("invalid.token.here")
        assert is_valid is False

    async def test_verify_expired_access_token(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Expired access token should fail verification."""
        token = await token_service.create_access_token(
            test_user.id, expires_delta=timedelta(seconds=-1)
        )
        is_valid = await token_service.verify_access_token(token)
        assert is_valid is False


class TestVerifyRefreshToken:
    """Tests for refresh token verification."""

    async def test_verify_valid_refresh_token(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Valid refresh token should be verified successfully."""
        token = await token_service.create_refresh_token(test_user.id)
        is_valid = await token_service.verify_refresh_token(token)
        assert is_valid is True

    async def test_verify_invalid_refresh_token(
        self, token_service: TokenService
    ) -> None:
        """Invalid refresh token should fail verification."""
        is_valid = await token_service.verify_refresh_token("invalid.token.here")
        assert is_valid is False

    async def test_verify_revoked_refresh_token(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Revoked refresh token should fail verification."""
        token = await token_service.create_refresh_token(test_user.id)
        await token_service.revoke_refresh_token(token)
        is_valid = await token_service.verify_refresh_token(token)
        assert is_valid is False


class TestRotateRefreshToken:
    """Tests for refresh token rotation."""

    async def test_rotate_refresh_token_returns_new_token(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Rotation should return a new refresh token."""
        old_token = await token_service.create_refresh_token(test_user.id)
        new_token = await token_service.rotate_refresh_token(old_token)
        assert new_token != old_token
        assert isinstance(new_token, str)

    async def test_rotate_refresh_token_revokes_old_token(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Rotation should revoke the old token."""
        old_token = await token_service.create_refresh_token(test_user.id)
        await token_service.rotate_refresh_token(old_token)

        is_valid = await token_service.verify_refresh_token(old_token)
        assert is_valid is False

    async def test_rotate_refresh_token_new_token_valid(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """New token from rotation should be valid."""
        old_token = await token_service.create_refresh_token(test_user.id)
        new_token = await token_service.rotate_refresh_token(old_token)

        is_valid = await token_service.verify_refresh_token(new_token)
        assert is_valid is True

    async def test_rotate_invalid_token_raises_error(
        self, token_service: TokenService
    ) -> None:
        """Rotating invalid token should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid or expired refresh token"):
            await token_service.rotate_refresh_token("invalid.token.here")


class TestRevokeRefreshToken:
    """Tests for single token revocation."""

    async def test_revoke_refresh_token_success(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Revoke should mark token as revoked."""
        token = await token_service.create_refresh_token(test_user.id)
        await token_service.revoke_refresh_token(token)

        is_valid = await token_service.verify_refresh_token(token)
        assert is_valid is False

    async def test_revoke_nonexistent_token_no_error(
        self, token_service: TokenService
    ) -> None:
        """Revoking nonexistent token should not raise error."""
        # Should not raise
        await token_service.revoke_refresh_token("nonexistent.token.here")


class TestRevokeAllUserTokens:
    """Tests for revoking all tokens of a user."""

    async def test_revoke_all_user_tokens_count(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Should return count of revoked tokens."""
        await token_service.create_refresh_token(test_user.id)
        await token_service.create_refresh_token(test_user.id)
        await token_service.create_refresh_token(test_user.id)

        count = await token_service.revoke_all_user_tokens(test_user.id)
        assert count == 3

    async def test_revoke_all_user_tokens_invalidates_all(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """All user tokens should be invalid after revocation."""
        token1 = await token_service.create_refresh_token(test_user.id)
        token2 = await token_service.create_refresh_token(test_user.id)

        await token_service.revoke_all_user_tokens(test_user.id)

        assert await token_service.verify_refresh_token(token1) is False
        assert await token_service.verify_refresh_token(token2) is False

    async def test_revoke_all_user_tokens_no_tokens(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Should return 0 when user has no tokens."""
        count = await token_service.revoke_all_user_tokens(test_user.id)
        assert count == 0


class TestCleanupExpiredTokens:
    """Tests for expired token cleanup."""

    async def test_cleanup_expired_tokens_count(
        self, token_service: TokenService, test_user: User, db_session: AsyncSession
    ) -> None:
        """Should return count of deleted expired tokens."""
        # Create an expired token directly in DB
        expired_token = RefreshToken(
            user_id=test_user.id,
            token_hash=hashlib.sha256(b"expired_token_1").hexdigest(),
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        db_session.add(expired_token)
        await db_session.commit()

        count = await token_service.cleanup_expired_tokens()
        assert count >= 1

    async def test_cleanup_expired_tokens_keeps_valid(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Should not delete valid tokens."""
        token = await token_service.create_refresh_token(test_user.id)

        await token_service.cleanup_expired_tokens()

        is_valid = await token_service.verify_refresh_token(token)
        assert is_valid is True


class TestGetUserIdFromToken:
    """Tests for extracting user ID from token."""

    async def test_get_user_id_from_access_token(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Should extract user ID from access token."""
        token = await token_service.create_access_token(test_user.id)
        user_id = await token_service.get_user_id_from_token(token)
        assert user_id == test_user.id

    async def test_get_user_id_from_refresh_token(
        self, token_service: TokenService, test_user: User
    ) -> None:
        """Should extract user ID from refresh token."""
        token = await token_service.create_refresh_token(test_user.id)
        user_id = await token_service.get_user_id_from_token(token)
        assert user_id == test_user.id

    async def test_get_user_id_from_invalid_token(
        self, token_service: TokenService
    ) -> None:
        """Should raise ValueError for invalid token."""
        with pytest.raises(ValueError, match="Invalid token"):
            await token_service.get_user_id_from_token("invalid.token.here")
