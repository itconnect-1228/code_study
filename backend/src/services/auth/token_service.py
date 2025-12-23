"""Token service for JWT access and refresh token management.

This module provides the TokenService class which handles:
- Access token creation and verification (stateless, 15 min expiry)
- Refresh token creation, verification, and storage (database-backed, 7 day expiry)
- Token rotation (issue new refresh token, revoke old)
- Token revocation (single token or all user tokens)
- Expired token cleanup

Security Features:
- Refresh tokens stored as SHA-256 hashes (never plaintext)
- JTI (JWT ID) for token uniqueness
- Token rotation on refresh (single-use tokens)
- Revocation support for logout

Architecture Notes:
- Service Layer Pattern: Business logic separated from API layer
- Uses async/await for non-blocking database operations
- Relies on jwt.py utilities for JWT encoding/decoding
"""

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from jose import JWTError, jwt
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_token import RefreshToken
from src.utils.jwt import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


class TokenService:
    """Service for JWT token management.

    Handles creation, verification, rotation, and revocation of JWT tokens.
    Access tokens are stateless, while refresh tokens are stored in the
    database for revocation support.

    Attributes:
        db: Async database session for database operations.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize TokenService with database session.

        Args:
            db: Async SQLAlchemy session for database operations.
        """
        self.db = db

    async def create_access_token(
        self,
        user_id: UUID,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a JWT access token for API authentication.

        Access tokens are short-lived (default 15 minutes) and stateless.
        They are not stored in the database.

        Args:
            user_id: UUID of the user.
            expires_delta: Optional custom expiration time.

        Returns:
            Encoded JWT access token string.
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        now = datetime.now(UTC)
        expire = now + expires_delta

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "type": "access",
        }

        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    async def create_refresh_token(
        self,
        user_id: UUID,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a JWT refresh token for obtaining new access tokens.

        Refresh tokens are long-lived (default 7 days) and stored in the
        database as SHA-256 hashes for revocation support.

        Args:
            user_id: UUID of the user.
            expires_delta: Optional custom expiration time.

        Returns:
            Encoded JWT refresh token string.
        """
        if expires_delta is None:
            expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        now = datetime.now(UTC)
        expire = now + expires_delta

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "type": "refresh",
            "jti": str(uuid4()),  # Unique identifier for token uniqueness
        }

        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Store hash in database
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expire,
        )
        self.db.add(db_token)
        await self.db.commit()

        return token

    async def verify_access_token(self, token: str) -> bool:
        """Verify if an access token is valid.

        Checks JWT signature, expiration, and token type.
        Does not query the database (stateless).

        Args:
            token: JWT access token string.

        Returns:
            True if token is valid, False otherwise.
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload.get("type") == "access"
        except JWTError:
            return False

    async def verify_refresh_token(self, token: str) -> bool:
        """Verify if a refresh token is valid.

        Checks JWT signature, expiration, token type, and revocation status
        in the database.

        Args:
            token: JWT refresh token string.

        Returns:
            True if token is valid and not revoked, False otherwise.
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "refresh":
                return False

            # Check database for revocation
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            result = await self.db.execute(stmt)
            db_token = result.scalar_one_or_none()

            # Token must exist, not be revoked, and not be expired
            return db_token is not None and db_token.is_valid
        except JWTError:
            return False

    async def rotate_refresh_token(self, old_token: str) -> str:
        """Rotate a refresh token: revoke old, issue new.

        This implements token rotation for enhanced security.
        Each refresh token can only be used once.

        Args:
            old_token: Current refresh token to rotate.

        Returns:
            New refresh token string.

        Raises:
            ValueError: If old token is invalid or already revoked.
        """
        # Verify old token
        if not await self.verify_refresh_token(old_token):
            raise ValueError("Invalid or expired refresh token")

        # Extract user_id
        user_id = await self.get_user_id_from_token(old_token)

        # Revoke old token
        await self.revoke_refresh_token(old_token)

        # Issue new token
        return await self.create_refresh_token(user_id)

    async def revoke_refresh_token(self, token: str) -> None:
        """Revoke a refresh token.

        Marks the token as revoked in the database. Revoked tokens
        cannot be used for authentication.

        Args:
            token: Refresh token to revoke.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked=True, revoked_at=datetime.now(UTC))
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def revoke_all_user_tokens(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user.

        Used for "logout from all devices" functionality.

        Args:
            user_id: UUID of the user.

        Returns:
            Number of tokens revoked.
        """
        # Count non-revoked tokens first
        count_stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,  # noqa: E712
        )
        result = await self.db.execute(count_stmt)
        count = len(result.scalars().all())

        # Revoke all tokens
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
            )
            .values(revoked=True, revoked_at=datetime.now(UTC))
        )
        await self.db.execute(stmt)
        await self.db.commit()

        return count

    async def cleanup_expired_tokens(self) -> int:
        """Delete expired refresh tokens from the database.

        Should be run periodically to clean up storage.

        Returns:
            Number of tokens deleted.
        """
        # Count expired tokens
        count_stmt = select(RefreshToken).where(
            RefreshToken.expires_at < datetime.now(UTC)
        )
        result = await self.db.execute(count_stmt)
        count = len(result.scalars().all())

        # Delete expired tokens
        stmt = delete(RefreshToken).where(RefreshToken.expires_at < datetime.now(UTC))
        await self.db.execute(stmt)
        await self.db.commit()

        return count

    async def get_user_id_from_token(self, token: str) -> UUID:
        """Extract user ID from a JWT token.

        Works for both access and refresh tokens.

        Args:
            token: JWT token string.

        Returns:
            UUID of the user from the token.

        Raises:
            ValueError: If token is invalid or cannot be decoded.
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id_str = payload.get("sub")
            if user_id_str is None:
                raise ValueError("Invalid token: missing user ID")
            return UUID(user_id_str)
        except JWTError as e:
            raise ValueError(f"Invalid token: {e}") from e
