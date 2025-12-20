"""Unit tests for Celery application configuration module.

Tests cover:
- CeleryConfig dataclass defaults and custom values
- get_celery_config() environment variable loading
- create_celery_app() app creation and configuration
- Error handling for invalid configuration values
- Security settings (JSON-only serialization)
"""

import os
from unittest.mock import patch

import pytest

from backend.src.tasks.celery_app import (
    CeleryConfig,
    CeleryConfigError,
    create_celery_app,
    get_celery_config,
)


class TestCeleryConfig:
    """Tests for CeleryConfig dataclass."""

    def test_default_values(self):
        """CeleryConfig should have sensible defaults."""
        config = CeleryConfig()

        assert config.broker_url == "redis://localhost:6379/1"
        assert config.result_backend == "redis://localhost:6379/2"
        assert config.task_time_limit == 600
        assert config.task_soft_time_limit == 540
        assert config.task_acks_late is True
        assert config.task_reject_on_worker_lost is True
        assert config.worker_prefetch_multiplier == 1
        assert config.accept_content == ["json"]
        assert config.task_serializer == "json"
        assert config.result_serializer == "json"
        assert config.timezone == "UTC"
        assert config.task_track_started is True

    def test_custom_values(self):
        """CeleryConfig should accept custom values."""
        config = CeleryConfig(
            broker_url="redis://custom:6380/0",
            result_backend="redis://custom:6380/1",
            task_time_limit=300,
            task_soft_time_limit=240,
            worker_prefetch_multiplier=2,
        )

        assert config.broker_url == "redis://custom:6380/0"
        assert config.result_backend == "redis://custom:6380/1"
        assert config.task_time_limit == 300
        assert config.task_soft_time_limit == 240
        assert config.worker_prefetch_multiplier == 2

    def test_accept_content_list_not_shared(self):
        """Each CeleryConfig should have its own accept_content list."""
        config1 = CeleryConfig()
        config2 = CeleryConfig()

        config1.accept_content.append("pickle")  # Modify one instance

        # Other instance should be unaffected
        assert "pickle" not in config2.accept_content


class TestGetCeleryConfig:
    """Tests for get_celery_config function."""

    def test_load_defaults_without_env_vars(self):
        """get_celery_config should return defaults when no env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_celery_config()

            assert config.broker_url == "redis://localhost:6379/1"
            assert config.result_backend == "redis://localhost:6379/2"

    def test_load_broker_url_from_env(self):
        """get_celery_config should load CELERY_BROKER_URL from environment."""
        env = {"CELERY_BROKER_URL": "redis://myredis:6380/0"}

        with patch.dict(os.environ, env, clear=True):
            config = get_celery_config()

            assert config.broker_url == "redis://myredis:6380/0"

    def test_load_result_backend_from_env(self):
        """get_celery_config should load CELERY_RESULT_BACKEND from environment."""
        env = {"CELERY_RESULT_BACKEND": "redis://myredis:6380/1"}

        with patch.dict(os.environ, env, clear=True):
            config = get_celery_config()

            assert config.result_backend == "redis://myredis:6380/1"

    def test_load_time_limit_from_env(self):
        """get_celery_config should load CELERY_TASK_TIME_LIMIT from environment."""
        env = {"CELERY_TASK_TIME_LIMIT": "900"}

        with patch.dict(os.environ, env, clear=True):
            config = get_celery_config()

            assert config.task_time_limit == 900

    def test_load_soft_time_limit_from_env(self):
        """get_celery_config should load CELERY_TASK_SOFT_TIME_LIMIT from environment."""
        env = {
            "CELERY_TASK_TIME_LIMIT": "600",
            "CELERY_TASK_SOFT_TIME_LIMIT": "500",
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_celery_config()

            assert config.task_soft_time_limit == 500

    def test_soft_limit_adjusted_when_exceeds_hard_limit(self):
        """get_celery_config should adjust soft limit to be less than hard limit."""
        env = {
            "CELERY_TASK_TIME_LIMIT": "300",
            "CELERY_TASK_SOFT_TIME_LIMIT": "400",  # Exceeds hard limit
        }

        with patch.dict(os.environ, env, clear=True):
            config = get_celery_config()

            # Should be adjusted to 300 - 60 = 240
            assert config.task_soft_time_limit == 240

    def test_load_prefetch_from_env(self):
        """get_celery_config should load CELERY_WORKER_PREFETCH from environment."""
        env = {"CELERY_WORKER_PREFETCH": "4"}

        with patch.dict(os.environ, env, clear=True):
            config = get_celery_config()

            assert config.worker_prefetch_multiplier == 4

    def test_invalid_time_limit_raises_error(self):
        """get_celery_config should raise error for invalid time limit."""
        env = {"CELERY_TASK_TIME_LIMIT": "not-a-number"}

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(CeleryConfigError) as exc_info:
                get_celery_config()

            assert "CELERY_TASK_TIME_LIMIT" in str(exc_info.value)

    def test_negative_time_limit_raises_error(self):
        """get_celery_config should raise error for negative time limit."""
        env = {"CELERY_TASK_TIME_LIMIT": "-100"}

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(CeleryConfigError) as exc_info:
                get_celery_config()

            assert "CELERY_TASK_TIME_LIMIT" in str(exc_info.value)

    def test_zero_time_limit_raises_error(self):
        """get_celery_config should raise error for zero time limit."""
        env = {"CELERY_TASK_TIME_LIMIT": "0"}

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(CeleryConfigError) as exc_info:
                get_celery_config()

            assert "CELERY_TASK_TIME_LIMIT" in str(exc_info.value)

    def test_invalid_prefetch_raises_error(self):
        """get_celery_config should raise error for invalid prefetch multiplier."""
        env = {"CELERY_WORKER_PREFETCH": "invalid"}

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(CeleryConfigError) as exc_info:
                get_celery_config()

            assert "CELERY_WORKER_PREFETCH" in str(exc_info.value)


class TestCreateCeleryApp:
    """Tests for create_celery_app function."""

    def test_creates_celery_app(self):
        """create_celery_app should return a Celery application."""
        from celery import Celery

        config = CeleryConfig()
        app = create_celery_app(config)

        assert isinstance(app, Celery)

    def test_app_name_is_codelearn(self):
        """create_celery_app should create app with name 'codelearn'."""
        config = CeleryConfig()
        app = create_celery_app(config)

        assert app.main == "codelearn"

    def test_app_uses_broker_url_from_config(self):
        """create_celery_app should configure broker_url from config."""
        config = CeleryConfig(broker_url="redis://testbroker:6379/0")
        app = create_celery_app(config)

        assert app.conf.broker_url == "redis://testbroker:6379/0"

    def test_app_uses_result_backend_from_config(self):
        """create_celery_app should configure result_backend from config."""
        config = CeleryConfig(result_backend="redis://testresults:6379/1")
        app = create_celery_app(config)

        assert app.conf.result_backend == "redis://testresults:6379/1"

    def test_app_uses_json_serialization_only(self):
        """create_celery_app should configure JSON-only serialization for security."""
        config = CeleryConfig()
        app = create_celery_app(config)

        assert app.conf.accept_content == ["json"]
        assert app.conf.task_serializer == "json"
        assert app.conf.result_serializer == "json"

    def test_app_uses_utc_timezone(self):
        """create_celery_app should configure UTC timezone."""
        config = CeleryConfig()
        app = create_celery_app(config)

        assert app.conf.timezone == "UTC"

    def test_app_enables_task_tracking(self):
        """create_celery_app should enable task_track_started."""
        config = CeleryConfig()
        app = create_celery_app(config)

        assert app.conf.task_track_started is True

    def test_app_enables_late_ack(self):
        """create_celery_app should enable task_acks_late for reliability."""
        config = CeleryConfig()
        app = create_celery_app(config)

        assert app.conf.task_acks_late is True

    def test_app_sets_time_limits(self):
        """create_celery_app should set task time limits."""
        config = CeleryConfig(task_time_limit=900, task_soft_time_limit=800)
        app = create_celery_app(config)

        assert app.conf.task_time_limit == 900
        assert app.conf.task_soft_time_limit == 800

    def test_create_without_config_uses_defaults(self):
        """create_celery_app without config should use environment defaults."""
        with patch.dict(os.environ, {}, clear=True):
            app = create_celery_app()

            assert app.conf.broker_url == "redis://localhost:6379/1"


class TestCeleryAppModule:
    """Tests for the module-level celery_app instance."""

    def test_celery_app_exists(self):
        """celery_app should be available at module level."""
        from backend.src.tasks.celery_app import celery_app

        assert celery_app is not None

    def test_celery_app_is_celery_instance(self):
        """celery_app should be a Celery instance."""
        from celery import Celery

        from backend.src.tasks.celery_app import celery_app

        assert isinstance(celery_app, Celery)

    def test_celery_app_can_be_imported_from_package(self):
        """celery_app should be importable from tasks package."""
        from backend.src.tasks import celery_app

        assert celery_app is not None
