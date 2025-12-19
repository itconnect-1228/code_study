"""Unit tests for database configuration module.

Tests cover:
- PoolConfig dataclass defaults and custom values
- DatabaseConfig dataclass and URL generation
- get_database_config() environment variable loading
- URL encoding for special characters in passwords
- Error handling for missing/invalid configuration
"""

# ruff: noqa: S105, S106  # Test passwords are intentionally hardcoded

import os
from unittest.mock import patch

import pytest

from backend.src.db.config import (
    DatabaseConfig,
    DatabaseConfigError,
    PoolConfig,
    get_database_config,
)


class TestPoolConfig:
    """Tests for PoolConfig dataclass."""

    def test_default_values(self):
        """PoolConfig should have sensible defaults."""
        pool = PoolConfig()

        assert pool.pool_size == 10
        assert pool.max_overflow == 20
        assert pool.pool_timeout == 30
        assert pool.pool_recycle == 3600
        assert pool.pool_pre_ping is True

    def test_custom_values(self):
        """PoolConfig should accept custom values."""
        pool = PoolConfig(
            pool_size=5,
            max_overflow=10,
            pool_timeout=60,
            pool_recycle=1800,
            pool_pre_ping=False,
        )

        assert pool.pool_size == 5
        assert pool.max_overflow == 10
        assert pool.pool_timeout == 60
        assert pool.pool_recycle == 1800
        assert pool.pool_pre_ping is False


class TestDatabaseConfig:
    """Tests for DatabaseConfig dataclass."""

    def test_basic_config(self):
        """DatabaseConfig should store basic connection parameters."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="testuser",
            password="testpass",
        )

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "testdb"
        assert config.user == "testuser"
        assert config.password == "testpass"
        assert config.driver == "postgresql+asyncpg"
        assert config.echo is False

    def test_default_pool_config(self):
        """DatabaseConfig should have default PoolConfig."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="testuser",
        )

        assert isinstance(config.pool, PoolConfig)
        assert config.pool.pool_size == 10

    def test_custom_pool_config(self):
        """DatabaseConfig should accept custom PoolConfig."""
        custom_pool = PoolConfig(pool_size=20)
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="testuser",
            pool=custom_pool,
        )

        assert config.pool.pool_size == 20

    def test_get_connection_url_with_password(self):
        """get_connection_url should include password when requested."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="admin",
            password="secret",
        )

        url = config.get_connection_url()
        assert url == "postgresql+asyncpg://admin:secret@localhost:5432/testdb"

    def test_get_connection_url_without_password(self):
        """get_connection_url should work without password."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="admin",
            password=None,
        )

        url = config.get_connection_url()
        assert url == "postgresql+asyncpg://admin@localhost:5432/testdb"

    def test_get_connection_url_with_special_characters(self):
        """get_connection_url should URL-encode special characters in password."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="admin",
            password="p@ss#word!",
        )

        url = config.get_connection_url()
        # @ should become %40, # should become %23, ! should become %21
        assert "p%40ss%23word%21" in url

    def test_get_safe_url_masks_password(self):
        """get_safe_url should mask the password."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="admin",
            password="supersecret",
        )

        safe_url = config.get_safe_url()
        assert "supersecret" not in safe_url
        assert "****" in safe_url


class TestGetDatabaseConfig:
    """Tests for get_database_config function."""

    def test_load_from_individual_env_vars(self):
        """get_database_config should load from individual environment variables."""
        env = {
            "DB_HOST": "myhost",
            "DB_PORT": "5433",
            "DB_NAME": "mydb",
            "DB_USER": "myuser",
            "DB_PASSWORD": "mypass",
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_database_config()

            assert config.host == "myhost"
            assert config.port == 5433
            assert config.database == "mydb"
            assert config.user == "myuser"
            assert config.password == "mypass"

    def test_load_from_postgres_env_vars(self):
        """get_database_config should support POSTGRES_* environment variables."""
        env = {
            "POSTGRES_HOST": "pghost",
            "POSTGRES_PORT": "5434",
            "POSTGRES_DB": "pgdb",
            "POSTGRES_USER": "pguser",
            "POSTGRES_PASSWORD": "pgpass",
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_database_config()

            assert config.host == "pghost"
            assert config.port == 5434
            assert config.database == "pgdb"
            assert config.user == "pguser"
            assert config.password == "pgpass"

    def test_db_vars_take_precedence(self):
        """DB_* variables should take precedence over POSTGRES_*."""
        env = {
            "DB_HOST": "dbhost",
            "POSTGRES_HOST": "pghost",
            "DB_NAME": "dbname",
            "POSTGRES_DB": "pgdb",
            "DB_USER": "dbuser",
            "POSTGRES_USER": "pguser",
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_database_config()

            assert config.host == "dbhost"
            assert config.database == "dbname"
            assert config.user == "dbuser"

    def test_load_from_database_url(self):
        """get_database_config should parse DATABASE_URL."""
        env = {
            "DATABASE_URL": "postgresql://urluser:urlpass@urlhost:5435/urldb",
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_database_config()

            assert config.host == "urlhost"
            assert config.port == 5435
            assert config.database == "urldb"
            assert config.user == "urluser"
            assert config.password == "urlpass"

    def test_database_url_takes_precedence(self):
        """DATABASE_URL should take precedence over individual variables."""
        env = {
            "DATABASE_URL": "postgresql://urluser:urlpass@urlhost:5435/urldb",
            "DB_HOST": "otherhost",
            "DB_USER": "otheruser",
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_database_config()

            assert config.host == "urlhost"
            assert config.user == "urluser"

    def test_default_port(self):
        """get_database_config should use default port 5432."""
        env = {
            "DB_HOST": "localhost",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_database_config()
            assert config.port == 5432

    def test_missing_required_vars_raises_error(self):
        """get_database_config should raise error for missing required variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(DatabaseConfigError) as exc_info:
                get_database_config()

            assert "DB_HOST" in str(exc_info.value)
            assert "DB_NAME" in str(exc_info.value)
            assert "DB_USER" in str(exc_info.value)

    def test_invalid_port_raises_error(self):
        """get_database_config should raise error for invalid port."""
        env = {
            "DB_HOST": "localhost",
            "DB_PORT": "invalid",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
        }

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(DatabaseConfigError) as exc_info:
                get_database_config()

            assert "Invalid database port" in str(exc_info.value)

    def test_port_out_of_range_raises_error(self):
        """get_database_config should raise error for port out of range."""
        env = {
            "DB_HOST": "localhost",
            "DB_PORT": "99999",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
        }

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(DatabaseConfigError) as exc_info:
                get_database_config()

            assert "Invalid database port" in str(exc_info.value)

    def test_pool_overrides(self):
        """get_database_config should accept pool setting overrides."""
        env = {
            "DB_HOST": "localhost",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_database_config(
                pool_size=50,
                max_overflow=100,
                pool_timeout=120,
            )

            assert config.pool.pool_size == 50
            assert config.pool.max_overflow == 100
            assert config.pool.pool_timeout == 120

    def test_echo_from_env_var(self):
        """get_database_config should read DB_ECHO from environment."""
        env = {
            "DB_HOST": "localhost",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
            "DB_ECHO": "true",
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_database_config()
            assert config.echo is True

    def test_echo_override(self):
        """get_database_config echo parameter should override env var."""
        env = {
            "DB_HOST": "localhost",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
            "DB_ECHO": "true",
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_database_config(echo=False)
            assert config.echo is False

    def test_url_decode_password(self):
        """get_database_config should URL-decode password from DATABASE_URL."""
        # Password with encoded @ symbol
        env = {
            "DATABASE_URL": "postgresql://user:p%40ssword@host:5432/db",
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_database_config()
            assert config.password == "p@ssword"


class TestURLEncoding:
    """Tests for URL encoding of special characters."""

    @pytest.mark.parametrize(
        "password,expected_encoded",
        [
            ("simple", "simple"),
            ("with@symbol", "with%40symbol"),
            ("with#hash", "with%23hash"),
            ("with space", "with+space"),
            ("with/slash", "with%2Fslash"),
            ("with?question", "with%3Fquestion"),
            ("complex@#$%", "complex%40%23%24%25"),
        ],
    )
    def test_password_encoding(self, password: str, expected_encoded: str):
        """Various special characters should be properly URL-encoded."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="admin",
            password=password,
        )

        url = config.get_connection_url()
        assert expected_encoded in url
