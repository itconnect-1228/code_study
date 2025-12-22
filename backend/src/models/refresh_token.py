"""RefreshToken model for JWT authentication token storage.

This module defines the RefreshToken SQLAlchemy model which stores
refresh tokens used for JWT token rotation. Only token hashes are
stored, never plaintext tokens.

The model corresponds to the 'refresh_tokens' table in PostgreSQL and includes:
- UUID primary key for distributed system compatibility
- Foreign key to User with CASCADE delete
- SHA-256 hashed token storage (never plaintext)
- Expiration timestamp for automatic token invalidation
- Revocation tracking for logout functionality

Example:
    from backend.src.models import RefreshToken
    from backend.src.db import get_session
    import hashlib

    token_value = "random_secure_token"
    token_hash = hashlib.sha256(token_value.encode()).hexdigest()

    async with get_session_context() as session:
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=7)
        )
        session.add(refresh_token)
        await session.commit()
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class RefreshToken(Base):
    """JWT refresh token for authentication.

    Stores hashed refresh tokens that allow users to obtain new access
    tokens without re-authenticating. Tokens can be revoked on logout
    and expire after 7 days.

    Attributes:
        id: Unique identifier (UUID v4, auto-generated).
        user_id: Foreign key to User (CASCADE delete).
        token_hash: SHA-256 hash of the token (unique, never plaintext).
        expires_at: Token expiration timestamp (required).
        created_at: Token creation timestamp (UTC, auto-set).
        revoked: Whether token has been revoked (default: False).
        revoked_at: When token was revoked (nullable).

    Table Constraints:
        - token_hash must be unique
        - user_id is required and references users table
        - expires_at is required
        - Cascade delete when user is deleted

    Indexes:
        - idx_refresh_tokens_user_id: Fast lookup by user
        - idx_refresh_tokens_hash: Fast token verification
        - idx_refresh_tokens_expires: Efficient expired token cleanup

    Example:
        token = RefreshToken(
            user_id=user.id,
            token_hash="5e884898da28047d1eb85...",
            expires_at=datetime.now(UTC) + timedelta(days=7)
        )
    """

    __tablename__ = "refresh_tokens"

    # Primary key - UUID for security and distributed compatibility
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    # Foreign key to User - CASCADE delete when user is deleted
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Token fields
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    # Expiration
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )

    # Timestamp fields
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    # Revocation fields
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=None,
    )

    # Table-level indexes
    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id"),
        Index("idx_refresh_tokens_hash", "token_hash"),
        Index("idx_refresh_tokens_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        """Return string representation for debugging.

        Note: Does NOT include token_hash for security reasons.

        Returns:
            str: RefreshToken representation with id and user_id.
        """
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"
