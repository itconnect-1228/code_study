"""API dependencies for FastAPI route protection.

This module provides authentication dependencies for protecting API routes:
- get_current_user: Requires valid access token, returns User or raises 401
- get_current_user_optional: Returns User if authenticated, None otherwise

The dependencies extract JWT tokens from HTTPOnly cookies and verify them
before querying the database for the user.

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

# Cookie name constant - must match the frontend and auth endpoints
ACCESS_TOKEN_COOKIE = "access_token"  # noqa: S105 - cookie name, not password


def _decode_access_token(token: str) -> UUID:
    """Decode and validate an access token, returning the user ID.

    This private helper function handles the JWT decoding logic
    and validation of token type.

    Args:
        token: The JWT access token string.

    Returns:
        UUID: The user ID from the token.

    Raises:
        AuthenticationException: If the token is invalid, expired,
            or not an access token.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

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

        return UUID(user_id_str)

    except JWTError as e:
        raise AuthenticationException(
            message="Invalid or expired token. Please login again.",
            code="INVALID_TOKEN",
        ) from e


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> User:
    """Get the current authenticated user from the access token.

    Extracts the access_token from cookies, verifies it, and returns
    the corresponding User from the database.

    Args:
        request: The FastAPI request object containing cookies.
        db: Async database session (injected by FastAPI).

    Returns:
        User: The authenticated user object with all fields populated.

    Raises:
        AuthenticationException: If token is missing (MISSING_TOKEN),
            invalid/expired (INVALID_TOKEN), wrong type (INVALID_TOKEN_TYPE),
            or user not found (USER_NOT_FOUND).

    Example:
        @router.get("/me")
        async def get_me(user: User = Depends(get_current_user)):
            return {"email": user.email}
    """
    # Extract access token from cookies
    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE)

    if not access_token:
        raise AuthenticationException(
            message="Authentication required. Please login.",
            code="MISSING_TOKEN",
        )

    # Decode token and get user ID
    user_id = _decode_access_token(access_token)

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
    db: AsyncSession = Depends(get_session),
) -> User | None:
    """Get the current user if authenticated, otherwise None.

    Similar to get_current_user, but returns None instead of raising
    an exception when authentication fails. Useful for routes that
    work differently for authenticated vs anonymous users.

    Args:
        request: The FastAPI request object containing cookies.
        db: Async database session (injected by FastAPI).

    Returns:
        User | None: The authenticated user, or None if not authenticated.

    Example:
        @router.get("/greeting")
        async def greet(user: User | None = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello, {user.email}!"}
            return {"message": "Hello, guest!"}
    """
    try:
        return await get_current_user(request, db)
    except AuthenticationException:
        return None
