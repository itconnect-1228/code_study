"""User service for authentication and user management.

This module provides the UserService class which handles:
- User registration with email/password
- User login with credential verification
- User lookup by email or ID

Security Features:
- Passwords are always hashed using bcrypt (never stored in plaintext)
- Error messages don't reveal whether email or password was wrong
- Race condition handling for duplicate email registration
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.utils.security import hash_password, verify_password


class UserService:
    """Service for user registration, login, and lookup.

    This service encapsulates all user-related business logic,
    separating it from the API layer. It handles validation,
    password hashing, and database operations.

    Attributes:
        db: Async database session for database operations.

    Example:
        async with get_session() as session:
            service = UserService(session)
            user = await service.register("user@example.com", "SecurePass123!")
    """

    def __init__(self, db: AsyncSession):
        """Initialize UserService with database session.

        Args:
            db: Async SQLAlchemy session for database operations.
        """
        self.db = db

    async def register(
        self,
        email: str,
        password: str,
        skill_level: str = "Complete Beginner",
    ) -> User:
        """Register a new user.

        Args:
            email: User's email address (must be unique and valid format).
            password: Plain-text password (min 8 characters, will be hashed).
            skill_level: Programming skill level (default: "Complete Beginner").

        Returns:
            User: The newly created user object.

        Raises:
            ValueError: If email format is invalid.
            ValueError: If password is less than 8 characters.
            ValueError: If email is already registered.
        """
        # Validate email format
        if not User.is_valid_email(email):
            raise ValueError("Invalid email format")

        # Validate password length
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        # Check for existing user
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")

        # Hash password and create user
        password_hash = hash_password(password)
        user = User(
            email=email,
            password_hash=password_hash,
            skill_level=skill_level,
        )

        # Save to database with race condition handling
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("Email already registered") from e

    async def login(self, email: str, password: str) -> User:
        """Authenticate user with email and password.

        Args:
            email: User's email address.
            password: Plain-text password to verify.

        Returns:
            User: The authenticated user object.

        Raises:
            ValueError: If email doesn't exist or password is incorrect.
                       Error message is intentionally vague for security.
        """
        # Find user by email
        user = await self.get_user_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        # Verify password
        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Update last_login_at
        user.last_login_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Find user by email address.

        Args:
            email: Email address to search for.

        Returns:
            User if found, None otherwise.
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Find user by ID.

        Args:
            user_id: UUID of the user to find.

        Returns:
            User if found, None otherwise.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
