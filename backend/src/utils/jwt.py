"""
JWT Token Utilities.

Provides functions for generating, verifying, and decoding JWT tokens
for user authentication.

Token Types:
- Access Token: Short-lived (15 minutes), used for API authentication
- Refresh Token: Long-lived (7 days), used to obtain new access tokens
"""

import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

# Configuration from environment variables with defaults
JWT_SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "development-secret-key-change-in-production-32bytes"
)
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class TokenExpiredError(Exception):
    """Raised when a token has expired."""

    pass


class TokenInvalidError(Exception):
    """Raised when a token is invalid or cannot be decoded."""

    pass


@dataclass
class TokenData:
    """Data contained in a JWT token payload."""

    user_id: int
    exp: datetime
    additional_data: dict = field(default_factory=dict)


def create_access_token(
    user_id: int,
    expires_delta: timedelta | None = None,
    additional_data: dict | None = None,
) -> str:
    """
    Create a JWT access token for user authentication.

    Args:
        user_id: The unique identifier of the user.
        expires_delta: Optional custom expiration time. Defaults to 15 minutes.
        additional_data: Optional additional data to include in the token payload.

    Returns:
        Encoded JWT token string.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    return _create_token(
        user_id=user_id,
        expires_delta=expires_delta,
        additional_data=additional_data,
        token_type="access",  # noqa: S106 - not a password, just token type identifier
    )


def create_refresh_token(
    user_id: int,
    expires_delta: timedelta | None = None,
    additional_data: dict | None = None,
) -> str:
    """
    Create a JWT refresh token for obtaining new access tokens.

    Args:
        user_id: The unique identifier of the user.
        expires_delta: Optional custom expiration time. Defaults to 7 days.
        additional_data: Optional additional data to include in the token payload.

    Returns:
        Encoded JWT token string.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    return _create_token(
        user_id=user_id,
        expires_delta=expires_delta,
        additional_data=additional_data,
        token_type="refresh",  # noqa: S106 - not a password, just token type identifier
    )


def _create_token(
    user_id: int,
    expires_delta: timedelta,
    additional_data: dict | None,
    token_type: str,
) -> str:
    """
    Internal function to create a JWT token.

    Args:
        user_id: The unique identifier of the user.
        expires_delta: Expiration time delta from now.
        additional_data: Optional additional data for the payload.
        token_type: Type of token ("access" or "refresh").

    Returns:
        Encoded JWT token string.
    """
    expire = datetime.now(UTC) + expires_delta

    payload = {"user_id": user_id, "exp": expire, "type": token_type}

    if additional_data:
        payload["additional_data"] = additional_data

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> bool:
    """
    Verify if a JWT token is valid and not expired.

    Args:
        token: The JWT token string to verify.

    Returns:
        True if the token is valid, False otherwise.
    """
    try:
        jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return True
    except JWTError:
        return False


def decode_token(token: str) -> TokenData:
    """
    Decode a JWT token and extract its payload.

    Args:
        token: The JWT token string to decode.

    Returns:
        TokenData object containing the decoded payload.

    Raises:
        TokenExpiredError: If the token has expired.
        TokenInvalidError: If the token is invalid or cannot be decoded.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Parse expiration datetime
        exp = payload.get("exp")
        if isinstance(exp, int | float):
            exp_datetime = datetime.fromtimestamp(exp, tz=UTC)
        else:
            exp_datetime = exp

        return TokenData(
            user_id=payload["user_id"],
            exp=exp_datetime,
            additional_data=payload.get("additional_data", {}),
        )
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredError("Token has expired") from e
    except JWTError as e:
        raise TokenInvalidError(f"Invalid token: {e}") from e
