"""Celery tasks package for async background processing.

This package contains the Celery application configuration and task definitions
for handling long-running operations like:
- AI-powered document generation
- Practice problem generation
- Scheduled trash cleanup (30-day retention)

Example usage:
    from backend.src.tasks.celery_app import celery_app

    @celery_app.task
    def generate_document(task_id: int) -> dict:
        # Long-running AI operation
        pass
"""

from backend.src.tasks.celery_app import celery_app

__all__ = ["celery_app"]
