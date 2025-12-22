"""Unit tests for RefreshToken SQLAlchemy model.

Tests for RefreshToken model creation, validation, and constraints.
Follows TDD cycle: RED -> GREEN -> REFACTOR

Test categories:
1. Basic creation - token with required fields
2. Constraints - token_hash uniqueness, required fields
3. Defaults - revoked defaults to False
4. Relationships - user_id foreign key with CASCADE delete
5. Representation - __repr__ method
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.models.refresh_token import RefreshToken
from src.models.user import User


class TestRefreshTokenCreation:
    """Tests for basic RefreshToken creation."""

    @pytest.mark.asyncio
    async def test_create_refresh_token_with_valid_data(self, db_session):
        """RefreshToken should be creatable with valid data."""
        # Create user first (foreign key dependency)
        user = User(
            email="tokenuser@example.com",
            password_hash="$2b$12$hashedpassword",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        expires_at = datetime.now(UTC) + timedelta(days=7)
        token = RefreshToken(
            user_id=user.id,
            token_hash="sha256_hashed_token_value_here",
            expires_at=expires_at,
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        assert token.id is not None
        assert token.user_id == user.id
        assert token.token_hash == "sha256_hashed_token_value_here"

    @pytest.mark.asyncio
    async def test_refresh_token_id_is_uuid(self, db_session):
        """RefreshToken ID should be a valid UUID."""
        from uuid import UUID

        user = User(email="uuid-token@example.com", password_hash="hash123")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = RefreshToken(
            user_id=user.id,
            token_hash="unique_hash_for_uuid_test",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        assert isinstance(token.id, UUID)


class TestRefreshTokenConstraints:
    """Tests for database constraints."""

    @pytest.mark.asyncio
    async def test_token_hash_uniqueness(self, db_session):
        """Duplicate token_hash should raise IntegrityError."""
        user = User(email="unique-token@example.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token1 = RefreshToken(
            user_id=user.id,
            token_hash="duplicate_hash_value",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(token1)
        await db_session.commit()

        token2 = RefreshToken(
            user_id=user.id,
            token_hash="duplicate_hash_value",  # Same hash
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(token2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_id_required(self, db_session):
        """RefreshToken without user_id should raise IntegrityError."""
        token = RefreshToken(
            user_id=None,  # type: ignore
            token_hash="hash_no_user",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(token)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_token_hash_required(self, db_session):
        """RefreshToken without token_hash should raise IntegrityError."""
        user = User(email="no-hash@example.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = RefreshToken(
            user_id=user.id,
            token_hash=None,  # type: ignore
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(token)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_expires_at_required(self, db_session):
        """RefreshToken without expires_at should raise IntegrityError."""
        user = User(email="no-expires@example.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = RefreshToken(
            user_id=user.id,
            token_hash="hash_no_expires",
            expires_at=None,  # type: ignore
        )
        db_session.add(token)

        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestRefreshTokenDefaults:
    """Tests for default field values."""

    @pytest.mark.asyncio
    async def test_revoked_default_false(self, db_session):
        """revoked should default to False."""
        user = User(email="default-revoked@example.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = RefreshToken(
            user_id=user.id,
            token_hash="hash_default_revoked",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        assert token.revoked is False

    @pytest.mark.asyncio
    async def test_revoked_at_default_none(self, db_session):
        """revoked_at should default to None."""
        user = User(email="default-revoked-at@example.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = RefreshToken(
            user_id=user.id,
            token_hash="hash_default_revoked_at",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        assert token.revoked_at is None

    @pytest.mark.asyncio
    async def test_created_at_auto_set(self, db_session):
        """created_at should be auto-set on creation."""
        user = User(email="auto-created@example.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        before = datetime.now(UTC)
        token = RefreshToken(
            user_id=user.id,
            token_hash="hash_auto_created",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)
        after = datetime.now(UTC)

        created_at = token.created_at
        if created_at.tzinfo is None:
            before = before.replace(tzinfo=None)
            after = after.replace(tzinfo=None)

        assert before <= created_at <= after


class TestRefreshTokenRevocation:
    """Tests for token revocation functionality."""

    @pytest.mark.asyncio
    async def test_revoke_token(self, db_session):
        """Token should be revocable with revoked=True and revoked_at timestamp."""
        user = User(email="revoke-test@example.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = RefreshToken(
            user_id=user.id,
            token_hash="hash_to_revoke",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        # Revoke the token
        revoke_time = datetime.now(UTC)
        token.revoked = True
        token.revoked_at = revoke_time
        await db_session.commit()
        await db_session.refresh(token)

        assert token.revoked is True
        assert token.revoked_at is not None


class TestRefreshTokenRelationships:
    """Tests for foreign key relationships."""

    @pytest.mark.asyncio
    async def test_multiple_tokens_per_user(self, db_session):
        """User should be able to have multiple refresh tokens."""
        user = User(email="multi-token@example.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token1 = RefreshToken(
            user_id=user.id,
            token_hash="hash_token_1",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        token2 = RefreshToken(
            user_id=user.id,
            token_hash="hash_token_2",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(token1)
        db_session.add(token2)
        await db_session.commit()

        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id)
        )
        tokens = result.scalars().all()

        assert len(tokens) == 2

    @pytest.mark.asyncio
    async def test_foreign_key_cascade_delete_defined(self, db_session):
        """ForeignKey should be defined with ondelete='CASCADE'.

        Note: SQLite doesn't enforce foreign key constraints by default,
        so we verify the constraint definition rather than the behavior.
        """
        from sqlalchemy import inspect

        # Get the foreign key from the model
        mapper = inspect(RefreshToken)
        user_id_column = mapper.columns["user_id"]

        # Check that user_id is a foreign key
        assert len(user_id_column.foreign_keys) == 1

        # Get the foreign key and check cascade
        fk = next(iter(user_id_column.foreign_keys))
        assert fk.ondelete == "CASCADE"


class TestRefreshTokenRepr:
    """Tests for RefreshToken string representation."""

    @pytest.mark.asyncio
    async def test_refresh_token_repr(self, db_session):
        """__repr__ should return readable token representation."""
        user = User(email="repr-token@example.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = RefreshToken(
            user_id=user.id,
            token_hash="secret_hash_value",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        repr_str = repr(token)

        assert "RefreshToken" in repr_str
        assert str(token.id) in repr_str
        # Token hash should NOT be in repr for security
        assert "secret_hash_value" not in repr_str
