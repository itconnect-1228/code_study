"""
Password Hashing Utilities.

Provides functions for securely hashing and verifying passwords using bcrypt.

bcrypt is chosen for password hashing because:
- It's intentionally slow (resistant to brute-force attacks)
- It automatically generates and stores salt with the hash
- It supports adjustable cost factor for future-proofing
"""

import os

import bcrypt

# Configuration from environment variables with defaults
# Cost factor: 12 = 2^12 = 4,096 iterations (good balance of security/performance)
BCRYPT_COST_FACTOR = int(os.environ.get("BCRYPT_COST_FACTOR", "12"))


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain-text password to hash.

    Returns:
        The hashed password as a string.

    Note:
        bcrypt has a 72-byte limit on password length. Passwords longer
        than 72 bytes will be truncated. This is generally not a problem
        as most passwords are well under this limit.

    Example:
        >>> hashed = hash_password("my-secure-password")
        >>> hashed.startswith("$2b$")
        True
    """
    # Convert password to bytes (UTF-8 encoding)
    password_bytes = password.encode("utf-8")

    # bcrypt has a 72-byte limit - truncate if necessary
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Generate salt with configured cost factor
    salt = bcrypt.gensalt(rounds=BCRYPT_COST_FACTOR)

    # Hash the password
    hashed: bytes = bcrypt.hashpw(password_bytes, salt)

    # Return as string for database storage
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: The plain-text password to verify.
        hashed_password: The previously hashed password to check against.

    Returns:
        True if the password matches the hash, False otherwise.

    Note:
        This function is resistant to timing attacks because bcrypt.checkpw
        uses constant-time comparison internally.

    Example:
        >>> hashed = hash_password("my-password")
        >>> verify_password("my-password", hashed)
        True
        >>> verify_password("wrong-password", hashed)
        False
    """
    try:
        # Convert to bytes
        password_bytes = plain_password.encode("utf-8")

        # Apply same 72-byte limit as hashing
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        hash_bytes = hashed_password.encode("utf-8")

        # Verify password using bcrypt's constant-time comparison
        result: bool = bcrypt.checkpw(password_bytes, hash_bytes)
        return result
    except (ValueError, TypeError):
        # Invalid hash format or other errors
        return False
