"""Database session management for the AI Code Learning Platform.

This module provides async database session management using SQLAlchemy 2.0.
It implements connection pooling, session factory, and FastAPI dependency
injection for database operations.

Key components:
- Base: DeclarativeBase for all ORM models
- AsyncEngine: Connection pool manager (one per application)
- AsyncSession: Database session for each request
- get_session: FastAPI dependency for automatic session management
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    All database models should inherit from this class to be properly
    registered with SQLAlchemy's metadata and work with Alembic migrations.

    Example:
        class User(Base):
            __tablename__ = "users"
            id = Column(UUID, primary_key=True)
            email = Column(String(255), unique=True)
    """

    pass


# Global engine and session maker (initialized by init_db)
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """Get the database URL from environment variables.

    Supports both DATABASE_URL (full URL) and individual components.
    For async SQLAlchemy, the URL must use the asyncpg driver.

    Returns:
        str: The database URL with asyncpg driver.

    Raises:
        ValueError: If DATABASE_URL is not set.
    """
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Ensure we use asyncpg driver for async operations
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return database_url

    # Fallback to individual components
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "code_learning")

    return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def init_db(
    echo: bool = False,
    pool_size: int = 10,
    max_overflow: int = 20,
    pool_timeout: int = 30,
    pool_recycle: int = 3600,
    pool_pre_ping: bool = True,
) -> None:
    """Initialize the database engine and session maker.

    This function should be called once at application startup.
    It creates the connection pool and session factory.

    Args:
        echo: If True, log all SQL statements (useful for debugging).
        pool_size: Number of connections to maintain in the pool.
        max_overflow: Maximum additional connections beyond pool_size.
        pool_timeout: Seconds to wait for a connection from pool.
        pool_recycle: Seconds after which to recycle connections.
        pool_pre_ping: If True, test connections before use.

    Example:
        @app.on_event("startup")
        async def startup():
            init_db(echo=True)  # Enable SQL logging in development
    """
    global _engine, _async_session_maker

    database_url = get_database_url()

    _engine = create_async_engine(
        database_url,
        echo=echo,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=pool_pre_ping,
    )

    _async_session_maker = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def close_db() -> None:
    """Close the database engine and dispose of connection pool.

    This function should be called at application shutdown to properly
    release database connections.

    Example:
        @app.on_event("shutdown")
        async def shutdown():
            await close_db()
    """
    global _engine, _async_session_maker

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None


def get_engine() -> AsyncEngine:
    """Get the current database engine.

    Returns:
        AsyncEngine: The SQLAlchemy async engine.

    Raises:
        RuntimeError: If database is not initialized.
    """
    if _engine is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() at application startup."
        )
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get the current session maker.

    Returns:
        async_sessionmaker: Factory for creating AsyncSession instances.

    Raises:
        RuntimeError: If database is not initialized.
    """
    if _async_session_maker is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() at application startup."
        )
    return _async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session.

    Creates a new session for each request and ensures proper cleanup.
    Sessions are NOT auto-committed - you must explicitly call commit().

    Yields:
        AsyncSession: A database session for the request.

    Example:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(User))
            return result.scalars().all()

    Note:
        Changes are NOT automatically committed. You must call:
        await session.commit()
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session (for non-FastAPI use).

    Creates a session that can be used with async with statement.
    Useful for background tasks, scripts, and testing.

    Yields:
        AsyncSession: A database session.

    Example:
        async with get_session_context() as session:
            user = User(email="test@example.com")
            session.add(user)
            await session.commit()
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> bool:
    """Check if the database connection is healthy.

    Executes a simple query to verify database connectivity.
    Useful for health check endpoints.

    Returns:
        bool: True if connection is successful, False otherwise.

    Example:
        @app.get("/health")
        async def health_check():
            db_healthy = await check_db_connection()
            return {"database": "ok" if db_healthy else "error"}
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
