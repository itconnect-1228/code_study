"""Database configuration module for the AI Code Learning Platform.

This module provides database configuration management, separating
configuration concerns from session management. It handles:
- Loading database connection parameters from environment variables
- Validation of required configuration values
- Connection URL generation with proper URL encoding
- Connection pool settings management

The separation of config from session follows the Single Responsibility
Principle, making configuration easier to test and modify independently.

Example:
    from backend.src.db.config import get_database_config

    config = get_database_config()
    print(f"Connecting to {config.host}:{config.port}/{config.database}")
    url = config.get_connection_url()
"""

import os
from dataclasses import dataclass, field
from urllib.parse import quote_plus


class DatabaseConfigError(Exception):
    """Raised when database configuration is invalid or incomplete."""

    pass


@dataclass
class PoolConfig:
    """Connection pool configuration settings.

    Attributes:
        pool_size: Number of connections to maintain in the pool.
            Think of it as "always keep 10 taxi cabs ready at the stand."
        max_overflow: Maximum additional connections beyond pool_size.
            Like hiring extra cabs during rush hour.
        pool_timeout: Seconds to wait for a connection from pool.
            How long a passenger waits before giving up.
        pool_recycle: Seconds after which to recycle connections.
            Replace old cabs with fresh ones to avoid breakdowns.
        pool_pre_ping: If True, test connections before use.
            Check if the cab actually starts before assigning it.
    """

    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True


@dataclass
class DatabaseConfig:
    """Database connection configuration.

    Stores all parameters needed to connect to the PostgreSQL database.
    Configuration can be loaded from environment variables or set directly.

    Attributes:
        host: Database server hostname or IP address.
        port: Database server port (default 5432 for PostgreSQL).
        database: Name of the database to connect to.
        user: Database user for authentication.
        password: Database password for authentication (optional for trust auth).
        driver: SQLAlchemy driver to use (default asyncpg for async).
        echo: If True, log all SQL statements (debugging).
        pool: Connection pool configuration settings.
    """

    host: str
    port: int
    database: str
    user: str
    password: str | None = None
    driver: str = "postgresql+asyncpg"
    echo: bool = False
    pool: PoolConfig = field(default_factory=PoolConfig)

    def get_connection_url(self, include_password: bool = True) -> str:
        """Generate the SQLAlchemy database connection URL.

        Creates a properly formatted connection URL with URL-encoded password
        to handle special characters safely.

        Args:
            include_password: If True, include password in URL.
                Set to False for logging to avoid exposing credentials.

        Returns:
            str: SQLAlchemy-compatible database URL.

        Example:
            config = DatabaseConfig(
                host="localhost",
                port=5432,
                database="mydb",
                user="admin",
                password="p@ss#word!"
            )
            url = config.get_connection_url()
            # Returns: postgresql+asyncpg://admin:p%40ss%23word%21@localhost:5432/mydb
        """
        if self.password and include_password:
            # URL-encode password to handle special characters like @ # ? /
            encoded_password = quote_plus(self.password)
            credentials = f"{self.user}:{encoded_password}"
        elif self.password and not include_password:
            credentials = f"{self.user}:****"
        else:
            credentials = self.user

        return f"{self.driver}://{credentials}@{self.host}:{self.port}/{self.database}"

    def get_safe_url(self) -> str:
        """Get connection URL with password masked for logging.

        Returns:
            str: Connection URL with password replaced by asterisks.
        """
        return self.get_connection_url(include_password=False)


def get_database_config(
    pool_size: int | None = None,
    max_overflow: int | None = None,
    pool_timeout: int | None = None,
    pool_recycle: int | None = None,
    pool_pre_ping: bool | None = None,
    echo: bool | None = None,
) -> DatabaseConfig:
    """Load database configuration from environment variables.

    Reads database connection parameters from environment and validates
    that all required values are present. Pool settings can be overridden
    via function arguments.

    Environment Variables:
        DATABASE_URL: Full connection URL (optional, takes precedence)
        DB_HOST or POSTGRES_HOST: Database hostname (required if no URL)
        DB_PORT or POSTGRES_PORT: Database port (default: 5432)
        DB_NAME or POSTGRES_DB: Database name (required if no URL)
        DB_USER or POSTGRES_USER: Database username (required if no URL)
        DB_PASSWORD or POSTGRES_PASSWORD: Database password (optional)
        DB_ECHO: Enable SQL logging (default: false)

    Args:
        pool_size: Override default pool size.
        max_overflow: Override default max overflow.
        pool_timeout: Override default pool timeout.
        pool_recycle: Override default pool recycle time.
        pool_pre_ping: Override default pre-ping setting.
        echo: Override SQL logging setting.

    Returns:
        DatabaseConfig: Configured database settings.

    Raises:
        DatabaseConfigError: If required environment variables are missing.

    Example:
        # Load from environment with custom pool settings
        config = get_database_config(pool_size=20, echo=True)
    """
    # Check for full DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return _parse_database_url(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            echo=echo,
        )

    # Load individual components
    host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST")
    port_str = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT") or "5432"
    database = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")

    # Validate required fields
    missing = []
    if not host:
        missing.append("DB_HOST or POSTGRES_HOST")
    if not database:
        missing.append("DB_NAME or POSTGRES_DB")
    if not user:
        missing.append("DB_USER or POSTGRES_USER")

    if missing:
        raise DatabaseConfigError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Set these variables or provide DATABASE_URL."
        )

    # Parse port
    try:
        port = int(port_str)
        if port < 1 or port > 65535:
            raise ValueError("Port out of range")
    except ValueError as err:
        raise DatabaseConfigError(
            f"Invalid database port: {port_str}. Must be a number between 1 and 65535."
        ) from err

    # Determine echo setting
    echo_value = (
        echo if echo is not None else _parse_bool(os.getenv("DB_ECHO", "false"))
    )

    # Build pool config with overrides
    pool_config = PoolConfig(
        pool_size=pool_size if pool_size is not None else 10,
        max_overflow=max_overflow if max_overflow is not None else 20,
        pool_timeout=pool_timeout if pool_timeout is not None else 30,
        pool_recycle=pool_recycle if pool_recycle is not None else 3600,
        pool_pre_ping=pool_pre_ping if pool_pre_ping is not None else True,
    )

    # These assertions help mypy understand the values are not None
    assert host is not None
    assert database is not None
    assert user is not None

    return DatabaseConfig(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        echo=echo_value,
        pool=pool_config,
    )


def _parse_database_url(
    url: str,
    pool_size: int | None = None,
    max_overflow: int | None = None,
    pool_timeout: int | None = None,
    pool_recycle: int | None = None,
    pool_pre_ping: bool | None = None,
    echo: bool | None = None,
) -> DatabaseConfig:
    """Parse a database URL into DatabaseConfig components.

    Handles both postgresql:// and postgresql+asyncpg:// URL formats.

    Args:
        url: Database URL to parse.
        Other args: Pool setting overrides.

    Returns:
        DatabaseConfig: Parsed configuration.

    Raises:
        DatabaseConfigError: If URL format is invalid.
    """
    from urllib.parse import unquote, urlparse

    # Normalize driver prefix
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise DatabaseConfigError(f"Invalid DATABASE_URL format: {e}") from e

    if not parsed.hostname:
        raise DatabaseConfigError("DATABASE_URL missing hostname")
    if not parsed.path or parsed.path == "/":
        raise DatabaseConfigError("DATABASE_URL missing database name")
    if not parsed.username:
        raise DatabaseConfigError("DATABASE_URL missing username")

    # Build pool config
    pool_config = PoolConfig(
        pool_size=pool_size if pool_size is not None else 10,
        max_overflow=max_overflow if max_overflow is not None else 20,
        pool_timeout=pool_timeout if pool_timeout is not None else 30,
        pool_recycle=pool_recycle if pool_recycle is not None else 3600,
        pool_pre_ping=pool_pre_ping if pool_pre_ping is not None else True,
    )

    echo_value = (
        echo if echo is not None else _parse_bool(os.getenv("DB_ECHO", "false"))
    )

    return DatabaseConfig(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/"),
        user=parsed.username,
        password=unquote(parsed.password) if parsed.password else None,
        driver="postgresql+asyncpg",
        echo=echo_value,
        pool=pool_config,
    )


def _parse_bool(value: str) -> bool:
    """Parse a string value as boolean.

    Args:
        value: String to parse.

    Returns:
        bool: True if value is "true", "1", "yes", or "on" (case-insensitive).
    """
    return value.lower() in ("true", "1", "yes", "on")
