"""Authentication API endpoints.

This module provides authentication endpoints:
- POST /auth/register - User registration (T028)
- POST /auth/login - User login with JWT (T029)
- POST /auth/logout - User logout (T030)
- POST /auth/refresh - Token refresh (T031)

Tokens:
- Access token: Short-lived (15 min), stored in HttpOnly cookie
- Refresh token: Long-lived (7 days), stored in HttpOnly cookie

Security:
- Passwords are hashed with bcrypt
- Tokens use JWT with HS256 algorithm
- Refresh tokens implement rotation (single-use)
"""

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.api.exceptions import AuthenticationException, ConflictException
from src.api.schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.db.session import get_session
from src.models.user import User
from src.services.auth.token_service import TokenService
from src.services.auth.user_service import UserService

router = APIRouter()

# Cookie configuration constants
REFRESH_TOKEN_COOKIE = "refresh_token"  # noqa: S105
ACCESS_TOKEN_COOKIE = "access_token"  # noqa: S105
COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds
ACCESS_COOKIE_MAX_AGE = 15 * 60  # 15 minutes
COOKIE_HTTPONLY = True
COOKIE_SECURE = False  # Set to True in production with HTTPS
COOKIE_SAMESITE = "lax"


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> User:
    """Register a new user account.

    Creates a new user with email and password. Validates:
    - Email format (RFC 5322)
    - Password strength (min 8 characters)
    - Email uniqueness

    Args:
        request: Registration request with email and password.
        db: Database session (injected).

    Returns:
        User: The newly created user (without password hash).

    Raises:
        ConflictException: If email is already registered (409).
        ValidationException: If email/password validation fails (422).
    """
    user_service = UserService(db)

    # Check if email already exists
    existing_user = await user_service.get_user_by_email(request.email)
    if existing_user:
        raise ConflictException(
            message="Email address is already registered",
            code="EMAIL_ALREADY_EXISTS",
        )

    # Create user
    user = await user_service.register(
        email=request.email,
        password=request.password,
    )
    await db.commit()

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict:
    """Authenticate user and return JWT tokens.

    Validates credentials and returns:
    - Access token (in response body and HttpOnly cookie)
    - Refresh token (as HttpOnly cookie only)

    Args:
        request: Login request with email and password.
        response: FastAPI response object (for setting cookies).
        db: Database session (injected).

    Returns:
        dict: Token response with access_token and user info.

    Raises:
        AuthenticationException: If credentials are invalid (401).
    """
    user_service = UserService(db)
    token_service = TokenService(db)

    # Authenticate user
    try:
        user = await user_service.login(request.email, request.password)
    except ValueError as e:
        raise AuthenticationException(
            message="Invalid email or password",
            code="INVALID_CREDENTIALS",
        ) from e

    # Generate tokens
    access_token = await token_service.create_access_token(user.id)
    refresh_token = await token_service.create_refresh_token(user.id)

    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=COOKIE_MAX_AGE,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

    # Set access token as HttpOnly cookie (for browser-based clients)
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        max_age=ACCESS_COOKIE_MAX_AGE,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict:
    """Logout user and revoke refresh token.

    Requires authentication. Revokes all refresh tokens for the user
    and clears cookies.

    Args:
        response: FastAPI response object (for clearing cookies).
        current_user: Authenticated user (injected).
        db: Database session (injected).

    Returns:
        dict: Success message.
    """
    token_service = TokenService(db)

    # Revoke all user tokens (for logout from this device)
    await token_service.revoke_all_user_tokens(current_user.id)

    # Clear cookies
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE)
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE)

    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_session),  # noqa: B008
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
) -> dict:
    """Refresh access token using refresh token.

    Implements token rotation: old refresh token is revoked
    and a new one is issued along with a new access token.

    Args:
        response: FastAPI response object (for setting cookies).
        db: Database session (injected).
        refresh_token: Refresh token from cookie.

    Returns:
        dict: Token response with new access_token and user info.

    Raises:
        AuthenticationException: If refresh token is invalid/expired (401).
    """
    if not refresh_token:
        raise AuthenticationException(
            message="Refresh token required",
            code="MISSING_REFRESH_TOKEN",
        )

    token_service = TokenService(db)
    user_service = UserService(db)

    # Verify refresh token
    if not await token_service.verify_refresh_token(refresh_token):
        raise AuthenticationException(
            message="Invalid or expired refresh token",
            code="INVALID_REFRESH_TOKEN",
        )

    # Get user ID from token
    try:
        user_id = await token_service.get_user_id_from_token(refresh_token)
    except ValueError as e:
        raise AuthenticationException(
            message="Invalid refresh token",
            code="INVALID_REFRESH_TOKEN",
        ) from e

    # Get user
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise AuthenticationException(
            message="User not found",
            code="USER_NOT_FOUND",
        )

    # Rotate tokens
    new_refresh_token = await token_service.rotate_refresh_token(refresh_token)
    new_access_token = await token_service.create_access_token(user.id)

    # Set new cookies
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=new_refresh_token,
        max_age=COOKIE_MAX_AGE,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=new_access_token,
        max_age=ACCESS_COOKIE_MAX_AGE,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user": user,
    }
