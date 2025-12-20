"""Celery application configuration for background task processing.

This module configures the Celery application with Redis as the message broker
and result backend. It handles long-running tasks that would block the HTTP
request-response cycle, such as AI document generation.

Think of this as a kitchen in a restaurant:
- Redis is the order ticket holder (message queue)
- Celery workers are the cooks who pick up tickets and make food
- The result backend is where completed dishes wait for pickup

Configuration is loaded from environment variables:
- CELERY_BROKER_URL: Redis URL for task queue (default: redis://localhost:6379/1)
- CELERY_RESULT_BACKEND: Redis URL for results (default: redis://localhost:6379/2)
- CELERY_TASK_TIME_LIMIT: Max seconds per task (default: 600 = 10 minutes)

Example:
    from backend.src.tasks.celery_app import celery_app

    @celery_app.task(bind=True, max_retries=3)
    def generate_learning_document(self, task_id: int) -> dict:
        try:
            # AI-powered document generation
            return {"status": "completed", "task_id": task_id}
        except Exception as exc:
            self.retry(exc=exc, countdown=60)
"""

import os
from dataclasses import dataclass, field

from celery import Celery


class CeleryConfigError(Exception):
    """Raised when Celery configuration is invalid or incomplete."""

    pass


@dataclass
class CeleryConfig:
    """Celery application configuration settings.

    Attributes:
        broker_url: Redis URL for the message broker (where tasks wait).
            Like the kitchen's order ticket system.
        result_backend: Redis URL for storing task results.
            Like the "food ready" counter where completed dishes wait.
        task_time_limit: Maximum seconds a task can run before being killed.
            Prevents runaway tasks from blocking workers forever.
        task_soft_time_limit: Soft limit that raises SoftTimeLimitExceeded.
            Gives tasks a chance to clean up before hard kill.
        task_acks_late: If True, acknowledge task completion only after success.
            Ensures failed tasks can be retried by another worker.
        task_reject_on_worker_lost: Requeue task if worker dies unexpectedly.
            Prevents task loss during deployments or crashes.
        worker_prefetch_multiplier: How many tasks to prefetch per worker.
            Set to 1 for long-running AI tasks to ensure fair distribution.
        accept_content: List of accepted serialization formats.
            Only JSON for security (pickle can execute arbitrary code).
        task_serializer: Format for serializing task arguments.
        result_serializer: Format for serializing task results.
        timezone: Timezone for scheduled tasks.
        task_track_started: If True, update state when task starts.
            Enables "in progress" status for long tasks.
    """

    broker_url: str = "redis://localhost:6379/1"
    result_backend: str = "redis://localhost:6379/2"
    task_time_limit: int = 600  # 10 minutes max
    task_soft_time_limit: int = 540  # 9 minutes, gives 1 min to cleanup
    task_acks_late: bool = True
    task_reject_on_worker_lost: bool = True
    worker_prefetch_multiplier: int = 1
    accept_content: list[str] = field(default_factory=lambda: ["json"])
    task_serializer: str = "json"
    result_serializer: str = "json"
    timezone: str = "UTC"
    task_track_started: bool = True


def get_celery_config() -> CeleryConfig:
    """Load Celery configuration from environment variables.

    Environment Variables:
        CELERY_BROKER_URL: Redis URL for task queue
        CELERY_RESULT_BACKEND: Redis URL for results
        CELERY_TASK_TIME_LIMIT: Max seconds per task (default: 600)
        CELERY_TASK_SOFT_TIME_LIMIT: Soft limit seconds (default: 540)
        CELERY_WORKER_PREFETCH: Prefetch multiplier (default: 1)

    Returns:
        CeleryConfig: Configured settings for Celery app.

    Raises:
        CeleryConfigError: If configuration values are invalid.
    """
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # Parse time limits with validation
    time_limit_str = os.getenv("CELERY_TASK_TIME_LIMIT", "600")
    soft_limit_str = os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "540")
    prefetch_str = os.getenv("CELERY_WORKER_PREFETCH", "1")

    try:
        time_limit = int(time_limit_str)
        if time_limit < 1:
            raise ValueError("Time limit must be positive")
    except ValueError as err:
        raise CeleryConfigError(
            f"Invalid CELERY_TASK_TIME_LIMIT: {time_limit_str}. Must be a positive integer."
        ) from err

    try:
        soft_limit = int(soft_limit_str)
        if soft_limit < 1:
            raise ValueError("Soft limit must be positive")
        if soft_limit >= time_limit:
            # Adjust soft limit to be less than hard limit
            soft_limit = max(1, time_limit - 60)
    except ValueError as err:
        raise CeleryConfigError(
            f"Invalid CELERY_TASK_SOFT_TIME_LIMIT: {soft_limit_str}. Must be a positive integer."
        ) from err

    try:
        prefetch = int(prefetch_str)
        if prefetch < 1:
            raise ValueError("Prefetch must be positive")
    except ValueError as err:
        raise CeleryConfigError(
            f"Invalid CELERY_WORKER_PREFETCH: {prefetch_str}. Must be a positive integer."
        ) from err

    return CeleryConfig(
        broker_url=broker_url,
        result_backend=result_backend,
        task_time_limit=time_limit,
        task_soft_time_limit=soft_limit,
        worker_prefetch_multiplier=prefetch,
    )


def create_celery_app(config: CeleryConfig | None = None) -> Celery:
    """Create and configure the Celery application.

    Args:
        config: Optional configuration. If None, loads from environment.

    Returns:
        Celery: Configured Celery application instance.

    Example:
        # Using default config from environment
        app = create_celery_app()

        # Using custom config
        config = CeleryConfig(broker_url="redis://custom:6379/0")
        app = create_celery_app(config)
    """
    if config is None:
        config = get_celery_config()

    app = Celery("codelearn")

    # Apply configuration
    app.conf.update(
        broker_url=config.broker_url,
        result_backend=config.result_backend,
        task_time_limit=config.task_time_limit,
        task_soft_time_limit=config.task_soft_time_limit,
        task_acks_late=config.task_acks_late,
        task_reject_on_worker_lost=config.task_reject_on_worker_lost,
        worker_prefetch_multiplier=config.worker_prefetch_multiplier,
        accept_content=config.accept_content,
        task_serializer=config.task_serializer,
        result_serializer=config.result_serializer,
        timezone=config.timezone,
        task_track_started=config.task_track_started,
    )

    # Configure task autodiscovery for future task modules
    app.autodiscover_tasks(["backend.src.tasks"])

    return app


# Create the default Celery application instance
celery_app = create_celery_app()
