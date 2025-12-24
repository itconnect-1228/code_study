"""Pytest configuration and shared fixtures.

This module provides common fixtures for testing, including:
- Async database session with SQLite in-memory database
- Async HTTP client for API endpoint testing
- User factory for creating test users

Note: SQLite is used for testing instead of PostgreSQL because:
1. No external database server required
2. In-memory database is extremely fast
3. Tests are isolated (fresh database per test)

PostgreSQL-specific features (like regex constraints) are handled
by removing incompatible constraints during test setup.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.session import Base, get_session
from src.main import create_app

# Import all models to ensure they're registered with Base.metadata
# This must happen BEFORE Base.metadata.create_all is called
from src.models.project import Project  # noqa: F401
from src.models.refresh_token import RefreshToken  # noqa: F401
from src.models.user import User  # noqa: F401


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy for pytest-asyncio."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture
async def db_session():
    """Create an async SQLite in-memory database session for testing.

    This fixture:
    1. Creates an in-memory SQLite database
    2. Removes PostgreSQL-specific constraints (like regex)
    3. Creates all tables
    4. Yields a session for the test
    5. Cleans up after the test

    Yields:
        AsyncSession: A database session for the test.
    """
    # Create in-memory SQLite engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Get the users table metadata if it exists
    users_table = Base.metadata.tables.get("users")
    if users_table is not None:
        # Remove PostgreSQL-specific constraints that don't work in SQLite
        # (regex email validation constraint)
        users_table.constraints = {
            c
            for c in users_table.constraints
            if not (hasattr(c, "name") and c.name == "valid_email")
        }

    # Get the projects table metadata if it exists
    projects_table = Base.metadata.tables.get("projects")
    if projects_table is not None:
        # Remove PostgreSQL-specific constraints that don't work in SQLite
        # (char_length function and CHECK constraints)
        projects_table.constraints = {
            c
            for c in projects_table.constraints
            if not (
                hasattr(c, "name")
                and c.name in ("title_min_length", "valid_deletion_status")
            )
        }

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Yield session for test
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession):
    """Create an async HTTP client for testing API endpoints.

    This fixture:
    1. Creates a FastAPI test app
    2. Overrides the get_session dependency to use test database
    3. Provides an AsyncClient for making HTTP requests
    4. Automatically handles cleanup

    Args:
        db_session: The test database session fixture.

    Yields:
        AsyncClient: Test client for making API requests.
    """
    # Create test app without lifespan (no real DB connection)
    app = create_app()

    # Override database session dependency
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    # Create and yield client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Cleanup
    app.dependency_overrides.clear()
