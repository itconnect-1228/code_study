"""Alembic environment configuration for database migrations.

This module configures Alembic to work with our async SQLAlchemy setup.
It supports both online (async) and offline (sync) migration modes.
"""

import asyncio
import os
from logging.config import fileConfig
from urllib.parse import quote_plus

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import our models and Base
from src.db.session import Base
from src.models import (  # noqa: F401 - imported for metadata registration
    CodeFile,
    LearningDocument,
    Project,
    RefreshToken,
    Task,
    UploadedCode,
    User,
)

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata


def get_database_url() -> str:
    """Get database URL from environment variables."""
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Convert postgresql:// to postgresql+asyncpg://
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return database_url

    # Build URL from individual components
    host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST")
    port = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT") or "5432"
    database = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")

    if not all([host, database, user]):
        raise ValueError(
            "Database configuration incomplete. "
            "Set DATABASE_URL or DB_HOST, DB_NAME, DB_USER environment variables."
        )

    if password:
        encoded_password = quote_plus(password)
        credentials = f"{user}:{encoded_password}"
    else:
        credentials = user

    return f"postgresql+asyncpg://{credentials}@{host}:{port}/{database}"


def get_sync_database_url() -> str:
    """Get database URL for sync operations (offline mode)."""
    url = get_database_url()
    # Convert async driver to sync driver for offline mode
    return url.replace("postgresql+asyncpg://", "postgresql://")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_sync_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations using provided connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}

    # Override sqlalchemy.url with environment-based URL
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
