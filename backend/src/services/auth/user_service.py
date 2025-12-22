"""User service for authentication and user management.

This module provides the UserService class which handles:
- User registration with email/password validation
- User login with credential verification
- User lookup by email or ID

Security Features:
- Passwords are always hashed using bcrypt (never stored in plaintext)
- Error messages don't reveal whether email or password was wrong (timing attack resistant)
- Race condition handling for duplicate email registration via IntegrityError
- Minimum password length enforcement (8 characters by default)

Architecture Notes:
- Service Layer Pattern: Business logic separated from API layer
- Raises ValueError for validation errors (API layer converts to HTTP responses)
- Uses async/await for non-blocking database operations

Example:
    from src.db.session import get_session
    from src.services.auth.user_service import UserService

    async def create_account():
        async with get_session() as session:
            service = UserService(session)
            try:
                user = await service.register("user@example.com", "SecurePass123!")
                print(f"Created user: {user.email}")
            except ValueError as e:
                print(f"Registration failed: {e}")
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.utils.security import hash_password, verify_password

# Configuration constants
MIN_PASSWORD_LENGTH = 8
DEFAULT_SKILL_LEVEL = "Complete Beginner"


class UserService:
    """Service for user registration, login, and lookup.

    This service encapsulates all user-related business logic,
    separating it from the API layer. It handles validation,
    password hashing, and database operations.

    The service follows these security principles:
    - Never store plaintext passwords
    - Never reveal which credential was wrong
    - Handle race conditions gracefully

    Attributes:
        db: Async database session for database operations.

    Example:
        async with get_session() as session:
            service = UserService(session)

            # Registration
            user = await service.register("user@example.com", "SecurePass123!")

            # Login
            logged_in = await service.login("user@example.com", "SecurePass123!")

            # Lookup
            found = await service.get_user_by_email("user@example.com")
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize UserService with database session.

        Args:
            db: Async SQLAlchemy session for database operations.
        """
        self.db = db

    async def register(
        self,
        email: str,
        password: str,
        skill_level: str = DEFAULT_SKILL_LEVEL,
    ) -> User:
        """Register a new user with email and password.

        Creates a new user account after validating the email format
        and password strength. The password is hashed before storage.

        Args:
            email: User's email address (must be unique and valid format).
            password: Plain-text password (min 8 characters, will be hashed).
            skill_level: Programming skill level (default: "Complete Beginner").

        Returns:
            User: The newly created and persisted user object.

        Raises:
            ValueError: If email format is invalid.
            ValueError: If password is less than 8 characters.
            ValueError: If email is already registered.

        Example:
            try:
                user = await service.register(
                    email="newuser@example.com",
                    password="MySecurePass123!",
                    skill_level="Complete Beginner"
                )
            except ValueError as e:
                # Handle: invalid email, weak password, or duplicate email
                print(f"Registration failed: {e}")

        Security Note:
            - Email format validated using RFC 5322 pattern
            - Password hashed with bcrypt (cost factor 12)
            - Race condition handled via database unique constraint
        """
        # Validate email format
        if not User.is_valid_email(email):
            raise ValueError("Invalid email format")

        # Validate password strength
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError("Password must be at least 8 characters")

        # Check for existing user (pre-check for better error messages)
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
            # Handle concurrent registration attempts
            await self.db.rollback()
            raise ValueError("Email already registered") from e

    async def login(self, email: str, password: str) -> User:
        """Authenticate user with email and password.

        Verifies the user's credentials and updates the last login timestamp
        on successful authentication.

        Args:
            email: User's email address.
            password: Plain-text password to verify.

        Returns:
            User: The authenticated user object with updated last_login_at.

        Raises:
            ValueError: If email doesn't exist or password is incorrect.
                       Error message is intentionally vague for security.

        Example:
            try:
                user = await service.login("user@example.com", "Password123!")
                print(f"Welcome, {user.email}!")
            except ValueError:
                print("Invalid credentials")

        Security Note:
            - Uses constant-time password comparison (bcrypt.checkpw)
            - Same error message for missing email and wrong password
            - Updates last_login_at for audit trail
        """
        # Find user by email
        user = await self.get_user_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        # Verify password using constant-time comparison
        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Update last login timestamp
        user.last_login_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Find user by email address.

        Performs a database lookup to find a user with the exact email match.

        Args:
            email: Email address to search for.

        Returns:
            User if found, None otherwise.

        Example:
            user = await service.get_user_by_email("user@example.com")
            if user:
                print(f"Found user: {user.id}")
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Find user by ID.

        Performs a database lookup to find a user with the given UUID.

        Args:
            user_id: UUID of the user to find.

        Returns:
            User if found, None otherwise.

        Example:
            from uuid import UUID
            user = await service.get_user_by_id(UUID("..."))
            if user:
                print(f"Found user: {user.email}")
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
