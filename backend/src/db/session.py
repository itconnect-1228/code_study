"""Database session management for the AI Code Learning Platform.

This module provides async database session management using SQLAlchemy 2.0.
It implements connection pooling, session factory, and FastAPI dependency
injection for database operations.

Key components:
- Base: DeclarativeBase for all ORM models
- AsyncEngine: Connection pool manager (one per application)
- AsyncSession: Database session for each request
- get_session: FastAPI dependency for automatic session management

Configuration is managed by the config module (config.py).
"""

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

from .config import DatabaseConfig, get_database_config


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
_current_config: DatabaseConfig | None = None


def get_database_url() -> str:
    """Get the database URL from environment variables.

    This function uses the config module to properly load and validate
    database configuration, including URL encoding for special characters.

    Returns:
        str: The database URL with asyncpg driver.

    Raises:
        DatabaseConfigError: If required environment variables are missing.
    """
    config = get_database_config()
    return config.get_connection_url()


def init_db(
    config: DatabaseConfig | None = None,
    echo: bool | None = None,
    pool_size: int | None = None,
    max_overflow: int | None = None,
    pool_timeout: int | None = None,
    pool_recycle: int | None = None,
    pool_pre_ping: bool | None = None,
) -> None:
    """Initialize the database engine and session maker.

    This function should be called once at application startup.
    It creates the connection pool and session factory.

    Configuration can be provided in three ways (in order of precedence):
    1. Explicit parameters (echo, pool_size, etc.)
    2. DatabaseConfig object (config parameter)
    3. Environment variables (via get_database_config())

    Args:
        config: Optional DatabaseConfig object with all settings.
        echo: If True, log all SQL statements (useful for debugging).
        pool_size: Number of connections to maintain in the pool.
        max_overflow: Maximum additional connections beyond pool_size.
        pool_timeout: Seconds to wait for a connection from pool.
        pool_recycle: Seconds after which to recycle connections.
        pool_pre_ping: If True, test connections before use.

    Example:
        # Simple startup with environment variables
        @app.on_event("startup")
        async def startup():
            init_db()

        # With explicit config
        config = get_database_config(echo=True, pool_size=20)
        init_db(config=config)

        # Override specific settings
        init_db(echo=True, pool_size=5)
    """
    global _engine, _async_session_maker, _current_config

    # Load config from environment if not provided
    if config is None:
        config = get_database_config()

    # Apply parameter overrides
    final_echo = echo if echo is not None else config.echo
    final_pool_size = pool_size if pool_size is not None else config.pool.pool_size
    final_max_overflow = (
        max_overflow if max_overflow is not None else config.pool.max_overflow
    )
    final_pool_timeout = (
        pool_timeout if pool_timeout is not None else config.pool.pool_timeout
    )
    final_pool_recycle = (
        pool_recycle if pool_recycle is not None else config.pool.pool_recycle
    )
    final_pool_pre_ping = (
        pool_pre_ping if pool_pre_ping is not None else config.pool.pool_pre_ping
    )

    database_url = config.get_connection_url()

    _engine = create_async_engine(
        database_url,
        echo=final_echo,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=final_pool_size,
        max_overflow=final_max_overflow,
        pool_timeout=final_pool_timeout,
        pool_recycle=final_pool_recycle,
        pool_pre_ping=final_pool_pre_ping,
    )

    _async_session_maker = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    _current_config = config


async def close_db() -> None:
    """Close the database engine and dispose of connection pool.

    This function should be called at application shutdown to properly
    release database connections.

    Example:
        @app.on_event("shutdown")
        async def shutdown():
            await close_db()
    """
    global _engine, _async_session_maker, _current_config

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        _current_config = None


def get_current_config() -> DatabaseConfig | None:
    """Get the current database configuration.

    Returns the configuration used to initialize the database,
    or None if database is not initialized.

    Returns:
        DatabaseConfig | None: The current configuration or None.

    Example:
        config = get_current_config()
        if config:
            print(f"Connected to: {config.get_safe_url()}")
    """
    return _current_config


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
