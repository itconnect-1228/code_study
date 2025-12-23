"""API dependencies for FastAPI route protection.

This module provides authentication dependencies for protecting API routes:
- get_current_user: Requires valid access token, returns User or raises 401
- get_current_user_optional: Returns User if authenticated, None otherwise

Usage:
    @router.get("/protected")
    async def protected_route(
        current_user: User = Depends(get_current_user)
    ):
        return {"user_id": str(current_user.id)}

    @router.get("/optional-auth")
    async def optional_auth_route(
        current_user: User | None = Depends(get_current_user_optional)
    ):
        if current_user:
            return {"authenticated": True}
        return {"authenticated": False}
"""

from uuid import UUID

from fastapi import Depends, Request
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.exceptions import AuthenticationException
from src.db.session import get_session
from src.models.user import User
from src.utils.jwt import JWT_ALGORITHM, JWT_SECRET_KEY


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> User:
    """Get the current authenticated user from the access token.

    Extracts the access_token from cookies, verifies it, and returns
    the corresponding User from the database.

    Args:
        request: The FastAPI request object.
        db: Async database session.

    Returns:
        User: The authenticated user.

    Raises:
        AuthenticationException: If token is missing, invalid, expired,
            or user not found.
    """
    # Extract access token from cookies
    access_token = request.cookies.get("access_token")

    if not access_token:
        raise AuthenticationException(
            message="Authentication required. Please login.",
            code="MISSING_TOKEN",
        )

    try:
        # Decode and verify the token
        payload = jwt.decode(access_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Verify it's an access token, not a refresh token
        if payload.get("type") != "access":
            raise AuthenticationException(
                message="Invalid token type. Access token required.",
                code="INVALID_TOKEN_TYPE",
            )

        # Extract user ID
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationException(
                message="Invalid token. Missing user identifier.",
                code="INVALID_TOKEN",
            )

        user_id = UUID(user_id_str)

    except JWTError as e:
        raise AuthenticationException(
            message="Invalid or expired token. Please login again.",
            code="INVALID_TOKEN",
        ) from e

    # Query the database for the user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationException(
            message="User not found. Please login again.",
            code="USER_NOT_FOUND",
        )

    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> User | None:
    """Get the current user if authenticated, otherwise None.

    Similar to get_current_user, but returns None instead of raising
    an exception when authentication fails. Useful for routes that
    work differently for authenticated vs anonymous users.

    Args:
        request: The FastAPI request object.
        db: Async database session.

    Returns:
        User | None: The authenticated user, or None if not authenticated.
    """
    try:
        return await get_current_user(request, db)
    except AuthenticationException:
        return None
