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
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_token import RefreshToken
from src.models.user import User
from src.services.auth.token_service import TokenService
from src.utils.security import hash_password


class TestCreateAccessToken:
    """Tests for access token creation."""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for token tests."""
        user = User(
            email="accesstoken@example.com",
            password_hash=hash_password("TestPassword123!"),
            skill_level="Complete Beginner",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_create_access_token_returns_string(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Access token should be a non-empty string."""
        service = TokenService(db_session)
        token = await service.create_access_token(test_user.id)
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_create_access_token_contains_user_id(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Access token should contain the user ID."""
        service = TokenService(db_session)
        token = await service.create_access_token(test_user.id)
        # Verify by decoding token
        user_id = await service.get_user_id_from_token(token)
        assert user_id == test_user.id

    @pytest.mark.asyncio
    async def test_create_access_token_with_custom_expiry(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Access token should support custom expiry time."""
        service = TokenService(db_session)
        token = await service.create_access_token(
            test_user.id, expires_delta=timedelta(minutes=5)
        )
        assert isinstance(token, str)
        assert len(token) > 0


class TestCreateRefreshToken:
    """Tests for refresh token creation."""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for token tests."""
        user = User(
            email="refreshtoken@example.com",
            password_hash=hash_password("TestPassword123!"),
            skill_level="Complete Beginner",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_create_refresh_token_returns_string(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Refresh token should be a non-empty string."""
        service = TokenService(db_session)
        token = await service.create_refresh_token(test_user.id)
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_create_refresh_token_stored_in_database(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Refresh token hash should be stored in the database."""
        service = TokenService(db_session)
        token = await service.create_refresh_token(test_user.id)

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

    @pytest.mark.asyncio
    async def test_create_multiple_refresh_tokens_unique(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Multiple refresh tokens should be unique."""
        service = TokenService(db_session)
        token1 = await service.create_refresh_token(test_user.id)
        token2 = await service.create_refresh_token(test_user.id)
        assert token1 != token2

    @pytest.mark.asyncio
    async def test_create_refresh_token_with_custom_expiry(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Refresh token should support custom expiry time."""
        service = TokenService(db_session)
        token = await service.create_refresh_token(
            test_user.id, expires_delta=timedelta(days=1)
        )
        assert isinstance(token, str)


class TestVerifyAccessToken:
    """Tests for access token verification."""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for token tests."""
        user = User(
            email="verifyaccess@example.com",
            password_hash=hash_password("TestPassword123!"),
            skill_level="Complete Beginner",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_verify_valid_access_token(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Valid access token should be verified successfully."""
        service = TokenService(db_session)
        token = await service.create_access_token(test_user.id)
        is_valid = await service.verify_access_token(token)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_verify_invalid_access_token(self, db_session: AsyncSession) -> None:
        """Invalid access token should fail verification."""
        service = TokenService(db_session)
        is_valid = await service.verify_access_token("invalid.token.here")
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_verify_expired_access_token(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Expired access token should fail verification."""
        service = TokenService(db_session)
        token = await service.create_access_token(
            test_user.id, expires_delta=timedelta(seconds=-1)
        )
        is_valid = await service.verify_access_token(token)
        assert is_valid is False


class TestVerifyRefreshToken:
    """Tests for refresh token verification."""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for token tests."""
        user = User(
            email="verifyrefresh@example.com",
            password_hash=hash_password("TestPassword123!"),
            skill_level="Complete Beginner",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_verify_valid_refresh_token(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Valid refresh token should be verified successfully."""
        service = TokenService(db_session)
        token = await service.create_refresh_token(test_user.id)
        is_valid = await service.verify_refresh_token(token)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_verify_invalid_refresh_token(self, db_session: AsyncSession) -> None:
        """Invalid refresh token should fail verification."""
        service = TokenService(db_session)
        is_valid = await service.verify_refresh_token("invalid.token.here")
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_verify_revoked_refresh_token(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Revoked refresh token should fail verification."""
        service = TokenService(db_session)
        token = await service.create_refresh_token(test_user.id)
        await service.revoke_refresh_token(token)
        is_valid = await service.verify_refresh_token(token)
        assert is_valid is False


class TestRotateRefreshToken:
    """Tests for refresh token rotation."""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for token tests."""
        user = User(
            email="rotate@example.com",
            password_hash=hash_password("TestPassword123!"),
            skill_level="Complete Beginner",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_rotate_refresh_token_returns_new_token(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Rotation should return a new refresh token."""
        service = TokenService(db_session)
        old_token = await service.create_refresh_token(test_user.id)
        new_token = await service.rotate_refresh_token(old_token)
        assert new_token != old_token
        assert isinstance(new_token, str)

    @pytest.mark.asyncio
    async def test_rotate_refresh_token_revokes_old_token(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Rotation should revoke the old token."""
        service = TokenService(db_session)
        old_token = await service.create_refresh_token(test_user.id)
        await service.rotate_refresh_token(old_token)

        is_valid = await service.verify_refresh_token(old_token)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_rotate_refresh_token_new_token_valid(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """New token from rotation should be valid."""
        service = TokenService(db_session)
        old_token = await service.create_refresh_token(test_user.id)
        new_token = await service.rotate_refresh_token(old_token)

        is_valid = await service.verify_refresh_token(new_token)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_rotate_invalid_token_raises_error(
        self, db_session: AsyncSession
    ) -> None:
        """Rotating invalid token should raise ValueError."""
        service = TokenService(db_session)
        with pytest.raises(ValueError, match="Invalid or expired refresh token"):
            await service.rotate_refresh_token("invalid.token.here")


class TestRevokeRefreshToken:
    """Tests for single token revocation."""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for token tests."""
        user = User(
            email="revoke@example.com",
            password_hash=hash_password("TestPassword123!"),
            skill_level="Complete Beginner",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_revoke_refresh_token_success(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Revoke should mark token as revoked."""
        service = TokenService(db_session)
        token = await service.create_refresh_token(test_user.id)
        await service.revoke_refresh_token(token)

        is_valid = await service.verify_refresh_token(token)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_token_no_error(
        self, db_session: AsyncSession
    ) -> None:
        """Revoking nonexistent token should not raise error."""
        service = TokenService(db_session)
        # Should not raise
        await service.revoke_refresh_token("nonexistent.token.here")


class TestRevokeAllUserTokens:
    """Tests for revoking all tokens of a user."""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for token tests."""
        user = User(
            email="revokeall@example.com",
            password_hash=hash_password("TestPassword123!"),
            skill_level="Complete Beginner",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens_count(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Should return count of revoked tokens."""
        service = TokenService(db_session)
        await service.create_refresh_token(test_user.id)
        await service.create_refresh_token(test_user.id)
        await service.create_refresh_token(test_user.id)

        count = await service.revoke_all_user_tokens(test_user.id)
        assert count == 3

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens_invalidates_all(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """All user tokens should be invalid after revocation."""
        service = TokenService(db_session)
        token1 = await service.create_refresh_token(test_user.id)
        token2 = await service.create_refresh_token(test_user.id)

        await service.revoke_all_user_tokens(test_user.id)

        assert await service.verify_refresh_token(token1) is False
        assert await service.verify_refresh_token(token2) is False

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens_no_tokens(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Should return 0 when user has no tokens."""
        service = TokenService(db_session)
        count = await service.revoke_all_user_tokens(test_user.id)
        assert count == 0


class TestCleanupExpiredTokens:
    """Tests for expired token cleanup."""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for token tests."""
        user = User(
            email="cleanup@example.com",
            password_hash=hash_password("TestPassword123!"),
            skill_level="Complete Beginner",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_count(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Should return count of deleted expired tokens."""
        service = TokenService(db_session)

        # Create an expired token directly in DB
        expired_token = RefreshToken(
            user_id=test_user.id,
            token_hash=hashlib.sha256(b"expired_token_1").hexdigest(),
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        db_session.add(expired_token)
        await db_session.commit()

        count = await service.cleanup_expired_tokens()
        assert count >= 1

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_keeps_valid(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Should not delete valid tokens."""
        service = TokenService(db_session)
        token = await service.create_refresh_token(test_user.id)

        await service.cleanup_expired_tokens()

        is_valid = await service.verify_refresh_token(token)
        assert is_valid is True


class TestGetUserIdFromToken:
    """Tests for extracting user ID from token."""

    @pytest_asyncio.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create a test user for token tests."""
        user = User(
            email="getuserid@example.com",
            password_hash=hash_password("TestPassword123!"),
            skill_level="Complete Beginner",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_get_user_id_from_access_token(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Should extract user ID from access token."""
        service = TokenService(db_session)
        token = await service.create_access_token(test_user.id)
        user_id = await service.get_user_id_from_token(token)
        assert user_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_user_id_from_refresh_token(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Should extract user ID from refresh token."""
        service = TokenService(db_session)
        token = await service.create_refresh_token(test_user.id)
        user_id = await service.get_user_id_from_token(token)
        assert user_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_user_id_from_invalid_token(
        self, db_session: AsyncSession
    ) -> None:
        """Should raise ValueError for invalid token."""
        service = TokenService(db_session)
        with pytest.raises(ValueError, match="Invalid token"):
            await service.get_user_id_from_token("invalid.token.here")
