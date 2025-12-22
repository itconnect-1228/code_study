"""SQLAlchemy ORM models for the AI Code Learning Platform.

This package contains all database models that inherit from Base
(defined in db.session). Each model corresponds to a database table
and defines the structure, relationships, and constraints.

Current models:
- User: Platform user with authentication credentials
- RefreshToken: JWT refresh tokens for authentication

Example:
    from backend.src.models import User, RefreshToken
    from backend.src.db import Base, get_session

    # Create a new user
    user = User(email="test@example.com", password_hash="hashed_password")
    session.add(user)
    await session.commit()
"""

from .refresh_token import RefreshToken
from .user import User

__all__ = [
    "RefreshToken",
    "User",
]
