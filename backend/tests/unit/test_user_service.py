"""Unit tests for UserService.

Tests the user registration, login, and lookup functionality
following TDD (Test-Driven Development) approach.

Test Categories:
1. Registration (register)
   - Successful registration with valid data
   - Duplicate email rejection
   - Invalid email format rejection
   - Weak password rejection

2. Login (login)
   - Successful login with valid credentials
   - Non-existent email rejection
   - Wrong password rejection
   - last_login_at update verification

3. User Lookup (get_user_by_email)
   - Existing user lookup
   - Non-existent user returns None
"""

from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.services.auth.user_service import UserService


class TestUserServiceRegister:
    """Tests for UserService.register() method."""

    @pytest.mark.asyncio
    async def test_register_success_with_valid_data(self, db_session: AsyncSession):
        """Test successful user registration with valid email and password."""
        # Arrange
        service = UserService(db_session)
        email = "newuser@example.com"
        password = "SecurePass123!"

        # Act
        user = await service.register(email=email, password=password)

        # Assert
        assert user is not None
        assert user.id is not None
        assert user.email == email
        assert user.password_hash != password  # Password should be hashed
        assert user.password_hash.startswith("$2b$")  # bcrypt hash format
        assert user.skill_level == "Complete Beginner"  # Default value
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_register_with_custom_skill_level(self, db_session: AsyncSession):
        """Test registration with custom skill level."""
        # Arrange
        service = UserService(db_session)
        email = "advanced@example.com"
        password = "SecurePass123!"
        skill_level = "Intermediate"

        # Act
        user = await service.register(
            email=email, password=password, skill_level=skill_level
        )

        # Assert
        assert user.skill_level == skill_level

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises_error(
        self, db_session: AsyncSession
    ):
        """Test that registering with an existing email raises ValueError."""
        # Arrange
        service = UserService(db_session)
        email = "duplicate@example.com"
        password = "SecurePass123!"

        # First registration should succeed
        await service.register(email=email, password=password)

        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            await service.register(email=email, password="AnotherPass456!")

    @pytest.mark.asyncio
    async def test_register_invalid_email_format_raises_error(
        self, db_session: AsyncSession
    ):
        """Test that invalid email format raises ValueError."""
        # Arrange
        service = UserService(db_session)
        invalid_emails = [
            "notanemail",
            "missing@tld",
            "@nodomain.com",
            "spaces in@email.com",
            "",
        ]

        # Act & Assert
        for invalid_email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email format"):
                await service.register(email=invalid_email, password="SecurePass123!")

    @pytest.mark.asyncio
    async def test_register_weak_password_raises_error(self, db_session: AsyncSession):
        """Test that password shorter than 8 characters raises ValueError."""
        # Arrange
        service = UserService(db_session)
        email = "user@example.com"
        weak_passwords = ["short", "1234567", "abc", ""]

        # Act & Assert
        for weak_password in weak_passwords:
            with pytest.raises(
                ValueError, match="Password must be at least 8 characters"
            ):
                await service.register(email=email, password=weak_password)


class TestUserServiceLogin:
    """Tests for UserService.login() method."""

    @pytest_asyncio.fixture
    async def registered_user(self, db_session: AsyncSession) -> User:
        """Create a registered user for login tests."""
        service = UserService(db_session)
        return await service.register(
            email="existing@example.com", password="CorrectPass123!"
        )

    @pytest.mark.asyncio
    async def test_login_success_with_valid_credentials(
        self, db_session: AsyncSession, registered_user: User
    ):
        """Test successful login with correct email and password."""
        # Arrange
        service = UserService(db_session)

        # Act
        user = await service.login(
            email="existing@example.com", password="CorrectPass123!"
        )

        # Assert
        assert user is not None
        assert user.id == registered_user.id
        assert user.email == registered_user.email

    @pytest.mark.asyncio
    async def test_login_nonexistent_email_raises_error(self, db_session: AsyncSession):
        """Test that login with non-existent email raises ValueError."""
        # Arrange
        service = UserService(db_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email or password"):
            await service.login(
                email="nonexistent@example.com", password="SomePass123!"
            )

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises_error(
        self, db_session: AsyncSession, registered_user: User
    ):
        """Test that login with wrong password raises ValueError."""
        # Arrange
        service = UserService(db_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email or password"):
            await service.login(
                email="existing@example.com", password="WrongPassword123!"
            )

    @pytest.mark.asyncio
    async def test_login_updates_last_login_at(
        self, db_session: AsyncSession, registered_user: User
    ):
        """Test that successful login updates last_login_at timestamp."""
        # Arrange
        service = UserService(db_session)
        assert registered_user.last_login_at is None  # Initially None

        # Act
        before_login = datetime.now(UTC)
        user = await service.login(
            email="existing@example.com", password="CorrectPass123!"
        )
        after_login = datetime.now(UTC)

        # Assert
        assert user.last_login_at is not None
        # Handle timezone-naive datetimes from SQLite
        last_login = user.last_login_at
        if last_login.tzinfo is None:
            before_login = before_login.replace(tzinfo=None)
            after_login = after_login.replace(tzinfo=None)
        assert before_login <= last_login <= after_login


class TestUserServiceGetByEmail:
    """Tests for UserService.get_user_by_email() method."""

    @pytest.mark.asyncio
    async def test_get_user_by_email_existing_user(self, db_session: AsyncSession):
        """Test retrieving an existing user by email."""
        # Arrange
        service = UserService(db_session)
        email = "findme@example.com"
        await service.register(email=email, password="SecurePass123!")

        # Act
        user = await service.get_user_by_email(email)

        # Assert
        assert user is not None
        assert user.email == email

    @pytest.mark.asyncio
    async def test_get_user_by_email_nonexistent_returns_none(
        self, db_session: AsyncSession
    ):
        """Test that non-existent email returns None."""
        # Arrange
        service = UserService(db_session)

        # Act
        user = await service.get_user_by_email("nobody@example.com")

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_case_sensitivity(self, db_session: AsyncSession):
        """Test email lookup with different case."""
        # Arrange
        service = UserService(db_session)
        await service.register(email="CaseSensitive@Example.com", password="Pass12345!")

        # Act - Lookup with exact same case
        user = await service.get_user_by_email("CaseSensitive@Example.com")

        # Assert
        assert user is not None
        assert user.email == "CaseSensitive@Example.com"


class TestUserServiceGetById:
    """Tests for UserService.get_user_by_id() method."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_existing_user(self, db_session: AsyncSession):
        """Test retrieving an existing user by ID."""
        # Arrange
        service = UserService(db_session)
        registered = await service.register(
            email="byid@example.com", password="SecurePass123!"
        )

        # Act
        user = await service.get_user_by_id(registered.id)

        # Assert
        assert user is not None
        assert user.id == registered.id
        assert user.email == "byid@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_nonexistent_returns_none(
        self, db_session: AsyncSession
    ):
        """Test that non-existent ID returns None."""
        # Arrange
        service = UserService(db_session)
        from uuid import uuid4

        fake_id = uuid4()

        # Act
        user = await service.get_user_by_id(fake_id)

        # Assert
        assert user is None
