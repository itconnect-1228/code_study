"""User model for authentication and profile management.

This module defines the User SQLAlchemy model which stores user
authentication credentials and basic profile information.

The model corresponds to the 'users' table in PostgreSQL and includes:
- UUID primary key for distributed system compatibility
- Email-based authentication with uniqueness constraint
- Secure password storage (hash only, never plaintext)
- Default skill level for new learners
- Automatic timestamp management

Example:
    from backend.src.models import User
    from backend.src.db import get_session

    async with get_session_context() as session:
        user = User(
            email="learner@example.com",
            password_hash="$2b$12$..."  # bcrypt hash
        )
        session.add(user)
        await session.commit()
"""

import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class User(Base):
    """Platform user with authentication and profile information.

    Represents a user account in the AI Code Learning Platform.
    Users own projects, create tasks, and track learning progress.

    Attributes:
        id: Unique identifier (UUID v4, auto-generated).
        email: User's email address (unique, required, validated).
        password_hash: bcrypt-hashed password (never store plaintext).
        skill_level: Programming skill level (default: 'Complete Beginner').
        created_at: Account creation timestamp (UTC, auto-set).
        updated_at: Last profile update timestamp (UTC, auto-updated).
        last_login_at: Last successful login timestamp (nullable).

    Table Constraints:
        - Email must be unique
        - Email must match valid email format (PostgreSQL regex)
        - Password hash is required

    Indexes:
        - idx_users_email: Fast email lookup for login

    Example:
        user = User(
            email="student@school.edu",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4v.d1M2yYrk3X6Oe"
        )
    """

    __tablename__ = "users"

    # Primary key - UUID for security and distributed compatibility
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=False,  # We define index separately for naming
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Profile fields
    skill_level: Mapped[str] = mapped_column(
        String(50),
        default="Complete Beginner",
    )

    # Timestamp fields (TIMESTAMP WITH TIME ZONE for PostgreSQL)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=None,
    )

    # Relationship to Projects
    projects = relationship(
        "Project",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Table-level constraints and indexes
    __table_args__ = (
        # Email validation constraint (PostgreSQL regex)
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'",
            name="valid_email",
        ),
        # Index for fast email lookup during login
        Index("idx_users_email", "email"),
    )

    def __repr__(self) -> str:
        """Return string representation for debugging.

        Returns:
            str: User representation with id and email.
        """
        return f"<User(id={self.id}, email={self.email!r})>"

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format using Python regex.

        This method provides application-level email validation,
        useful for databases that don't support PostgreSQL regex
        (like SQLite in tests) or for pre-validation before insert.

        Args:
            email: Email address to validate.

        Returns:
            bool: True if email format is valid, False otherwise.

        Example:
            if not User.is_valid_email(form_data.email):
                raise ValueError("Invalid email format")
        """
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
        return bool(re.match(pattern, email, re.IGNORECASE))
