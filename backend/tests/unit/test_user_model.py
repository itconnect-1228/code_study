"""Unit tests for User SQLAlchemy model.

Tests for User model creation, validation, and constraints.
Follows TDD cycle: RED -> GREEN -> REFACTOR

Test categories:
1. Basic creation - user with required fields
2. Constraints - email uniqueness, required fields
3. Defaults - skill level, timestamps
4. Validation - email format (Python-level)
5. Representation - __repr__ method
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.models.user import User


class TestUserCreation:
    """Tests for basic user creation."""

    @pytest.mark.asyncio
    async def test_create_user_with_valid_data(self, db_session):
        """User should be creatable with valid email and password hash."""
        user = User(
            email="test@example.com",
            password_hash="$2b$12$hashedpassword123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.password_hash == "$2b$12$hashedpassword123"

    @pytest.mark.asyncio
    async def test_user_id_is_uuid(self, db_session):
        """User ID should be a valid UUID."""
        from uuid import UUID

        user = User(
            email="uuid-test@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert isinstance(user.id, UUID)

    @pytest.mark.asyncio
    async def test_user_persists_to_database(self, db_session):
        """User should be retrievable from database after creation."""
        user = User(
            email="persist@example.com",
            password_hash="hash456",
        )
        db_session.add(user)
        await db_session.commit()

        # Query the user back
        result = await db_session.execute(
            select(User).where(User.email == "persist@example.com")
        )
        retrieved_user = result.scalar_one()

        assert retrieved_user.id == user.id
        assert retrieved_user.email == "persist@example.com"


class TestUserConstraints:
    """Tests for database constraints."""

    @pytest.mark.asyncio
    async def test_user_email_uniqueness(self, db_session):
        """Duplicate emails should raise IntegrityError."""
        user1 = User(
            email="duplicate@example.com",
            password_hash="hash1",
        )
        db_session.add(user1)
        await db_session.commit()

        user2 = User(
            email="duplicate@example.com",
            password_hash="hash2",
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_email_required(self, db_session):
        """User without email should raise IntegrityError."""
        user = User(
            email=None,  # type: ignore
            password_hash="hash123",
        )
        db_session.add(user)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_password_hash_required(self, db_session):
        """User without password hash should raise IntegrityError."""
        user = User(
            email="nohash@example.com",
            password_hash=None,  # type: ignore
        )
        db_session.add(user)

        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestUserDefaults:
    """Tests for default field values."""

    @pytest.mark.asyncio
    async def test_user_skill_level_default(self, db_session):
        """User should have 'Complete Beginner' as default skill level."""
        user = User(
            email="beginner@example.com",
            password_hash="hash789",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.skill_level == "Complete Beginner"

    @pytest.mark.asyncio
    async def test_user_skill_level_custom(self, db_session):
        """User should accept custom skill level."""
        user = User(
            email="advanced@example.com",
            password_hash="hash789",
            skill_level="Advanced",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.skill_level == "Advanced"

    @pytest.mark.asyncio
    async def test_user_timestamps_auto_set(self, db_session):
        """created_at and updated_at should be auto-set on creation."""
        before = datetime.now(UTC)

        user = User(
            email="timestamps@example.com",
            password_hash="hash101",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        after = datetime.now(UTC)

        # Handle timezone-aware vs naive comparison
        created_at = user.created_at
        updated_at = user.updated_at

        # If timestamps are naive (SQLite), compare without timezone
        if created_at.tzinfo is None:
            before = before.replace(tzinfo=None)
            after = after.replace(tzinfo=None)

        assert before <= created_at <= after
        assert before <= updated_at <= after

    @pytest.mark.asyncio
    async def test_user_last_login_initially_none(self, db_session):
        """last_login_at should be None for new users."""
        user = User(
            email="newuser@example.com",
            password_hash="hash202",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.last_login_at is None


class TestEmailValidation:
    """Tests for email validation."""

    @pytest.mark.skip(reason="PostgreSQL regex constraint not available in SQLite")
    @pytest.mark.asyncio
    async def test_user_email_validation_constraint(self, db_session):
        """Invalid email format should be rejected by database constraint.

        Note: This test is skipped because SQLite doesn't support
        PostgreSQL's regex (~*) operator. In production with PostgreSQL,
        this constraint will be enforced at the database level.
        """
        user = User(
            email="not-an-email",
            password_hash="hash303",
        )
        db_session.add(user)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    def test_is_valid_email_with_valid_emails(self):
        """is_valid_email should return True for valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "user+tag@example.co.uk",
            "user123@subdomain.domain.com",
            "USER@EXAMPLE.COM",
        ]

        for email in valid_emails:
            assert User.is_valid_email(email) is True, f"Should accept: {email}"

    def test_is_valid_email_with_invalid_emails(self):
        """is_valid_email should return False for invalid emails."""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user@.",
            "user@.com",
            "",
            "user name@example.com",
        ]

        for email in invalid_emails:
            assert User.is_valid_email(email) is False, f"Should reject: {email}"


class TestUserRepr:
    """Tests for User string representation."""

    @pytest.mark.asyncio
    async def test_user_repr(self, db_session):
        """__repr__ should return readable user representation."""
        user = User(
            email="repr@example.com",
            password_hash="hash404",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repr_str = repr(user)

        assert "User" in repr_str
        assert "repr@example.com" in repr_str
        assert str(user.id) in repr_str
        # Password should NOT be in repr for security
        assert "hash404" not in repr_str
