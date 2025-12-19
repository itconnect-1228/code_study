"""Database module for the AI Code Learning Platform.

This module provides database connectivity and session management
using SQLAlchemy 2.0 with async support.

Exports:
    Base: DeclarativeBase for ORM models
    init_db: Initialize database engine (call at startup)
    close_db: Close database connections (call at shutdown)
    get_session: FastAPI dependency for database sessions
    get_session_context: Context manager for non-FastAPI use
    get_engine: Get the database engine
    get_session_maker: Get the session factory
    check_db_connection: Health check for database

Example:
    from backend.src.db import Base, init_db, get_session

    # Define a model
    class User(Base):
        __tablename__ = "users"
        ...

    # Initialize at startup
    init_db()

    # Use in FastAPI route
    @app.get("/users")
    async def get_users(session: AsyncSession = Depends(get_session)):
        ...
"""

from .session import (
    Base,
    check_db_connection,
    close_db,
    get_engine,
    get_session,
    get_session_context,
    get_session_maker,
    init_db,
)

__all__ = [
    "Base",
    "check_db_connection",
    "close_db",
    "get_engine",
    "get_session",
    "get_session_context",
    "get_session_maker",
    "init_db",
]
