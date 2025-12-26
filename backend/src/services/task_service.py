"""Task service for task CRUD operations.

This module provides the TaskService class which handles:
- Task creation with auto-incrementing task_number per project
- Task retrieval by ID or project
- Task update (title, description)
- Soft delete with 30-day trash retention
- Task restoration from trash
- Ownership validation via project

Architecture Notes:
- Service Layer Pattern: Business logic separated from API layer
- Raises ValueError for validation errors (API layer converts to HTTP responses)
- Uses async/await for non-blocking database operations
- Respects soft delete: trashed tasks excluded by default

Example:
    from src.db.session import get_session
    from src.services.task_service import TaskService

    async def list_tasks():
        async with get_session() as session:
            service = TaskService(session)
            tasks = await service.get_by_project(project_id)
            return tasks
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.project import Project
from src.models.task import Task


class TaskService:
    """Service for task CRUD operations.

    This service encapsulates all task-related business logic,
    separating it from the API layer. It handles validation,
    ownership verification through projects, and database operations.

    The service respects soft delete semantics:
    - Active tasks (deletion_status='active') are returned by default
    - Trashed tasks can be included with include_trashed=True

    Attributes:
        db: Async database session for database operations.

    Example:
        async with get_session() as session:
            service = TaskService(session)

            # Create task
            task = await service.create(
                project_id=project.id,
                title="Learn Python",
                upload_method="file"
            )

            # Get task
            task = await service.get_by_id(task_id)

            # Soft delete
            await service.soft_delete(task_id)
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize TaskService with database session.

        Args:
            db: Async SQLAlchemy session for database operations.
        """
        self.db = db

    async def create(
        self,
        project_id: UUID,
        title: str,
        upload_method: str,
        description: str | None = None,
    ) -> Task:
        """Create a new task in a project.

        Creates a new task with auto-incrementing task_number.
        The task_number is unique within the project.

        Args:
            project_id: UUID of the project to add the task to.
            title: Task title (minimum 5 characters).
            upload_method: How code was uploaded ('file', 'folder', 'paste').
            description: Optional task description (max 500 characters).

        Returns:
            Task: The newly created task object.

        Raises:
            ValueError: If title is less than 5 characters.
            ValueError: If project_id does not exist.

        Example:
            task = await service.create(
                project_id=project.id,
                title="Python Basics",
                upload_method="file",
                description="Learn Python fundamentals"
            )
        """
        # Validate title length
        title = title.strip()
        if len(title) < 5:
            raise ValueError("Task title must be at least 5 characters")

        # Verify project exists
        project = await self._get_project(project_id)
        if not project:
            raise ValueError(f"Project with id {project_id} not found")

        # Get next task number for this project
        next_task_number = await self._get_next_task_number(project_id)

        # Create task
        task = Task(
            project_id=project_id,
            task_number=next_task_number,
            title=title,
            description=description,
            upload_method=upload_method,
        )

        self.db.add(task)
        await self.db.commit()

        return task

    async def get_by_id(
        self,
        task_id: UUID,
        include_trashed: bool = False,
    ) -> Task | None:
        """Get a task by its ID.

        Retrieves a task by its UUID. By default, trashed tasks
        are excluded from results.

        Args:
            task_id: UUID of the task to retrieve.
            include_trashed: If True, include trashed tasks. Default False.

        Returns:
            Task if found, None otherwise.

        Example:
            task = await service.get_by_id(task_id)
            if task:
                print(f"Found: {task.title}")
        """
        stmt = select(Task).where(Task.id == task_id)

        if not include_trashed:
            stmt = stmt.where(Task.deletion_status == "active")

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_project(
        self,
        project_id: UUID,
        include_trashed: bool = False,
    ) -> list[Task]:
        """Get all tasks for a project.

        Retrieves all tasks belonging to the specified project.
        By default, only active (non-trashed) tasks are returned.
        Tasks are ordered by task_number.

        Args:
            project_id: UUID of the project whose tasks to retrieve.
            include_trashed: If True, include trashed tasks. Default False.

        Returns:
            List of tasks ordered by task_number (empty if no tasks).

        Example:
            tasks = await service.get_by_project(project_id)
            for t in tasks:
                print(f"Task {t.task_number}: {t.title}")
        """
        stmt = select(Task).where(Task.project_id == project_id)

        if not include_trashed:
            stmt = stmt.where(Task.deletion_status == "active")

        stmt = stmt.order_by(Task.task_number)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        task_id: UUID,
        title: str | None = None,
        description: str | None = None,
    ) -> Task:
        """Update a task's title or description.

        Updates the specified task with new title and/or description.
        Only provided fields are updated (None values are ignored).

        Args:
            task_id: UUID of the task to update.
            title: New task title (if provided, minimum 5 characters).
            description: New task description (can be any value).

        Returns:
            Task: The updated task object.

        Raises:
            ValueError: If task is not found.
            ValueError: If title is provided but less than 5 characters.

        Example:
            updated = await service.update(
                task_id=task.id,
                title="Updated Title",
                description="Updated description"
            )
        """
        task = await self.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")

        if title is not None:
            title = title.strip()
            if len(title) < 5:
                raise ValueError("Task title must be at least 5 characters")
            task.title = title

        if description is not None:
            task.description = description

        await self.db.commit()

        return task

    async def soft_delete(self, task_id: UUID) -> Task:
        """Soft delete a task (move to trash).

        Moves the task to trash with 30-day scheduled deletion.
        The task can be restored from trash before permanent deletion.

        Args:
            task_id: UUID of the task to delete.

        Returns:
            Task: The trashed task object.

        Raises:
            ValueError: If task is not found.
            ValueError: If task is already in trash.

        Example:
            deleted = await service.soft_delete(task.id)
            print(f"Scheduled deletion: {deleted.scheduled_deletion_at}")
        """
        task = await self.get_by_id(task_id, include_trashed=True)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")

        if task.is_trashed:
            raise ValueError(f"Task with id {task_id} is already in trash")

        task.soft_delete()
        await self.db.commit()

        return task

    async def restore(self, task_id: UUID) -> Task:
        """Restore a task from trash.

        Restores a trashed task back to active status.
        Clears all trash-related timestamps.

        Args:
            task_id: UUID of the task to restore.

        Returns:
            Task: The restored task object.

        Raises:
            ValueError: If task is not found.
            ValueError: If task is not in trash.

        Example:
            restored = await service.restore(task.id)
            print(f"Restored: {restored.title}")
        """
        task = await self.get_by_id(task_id, include_trashed=True)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")

        if not task.is_trashed:
            raise ValueError(f"Task with id {task_id} is not in trash")

        task.restore()
        await self.db.commit()

        return task

    async def validate_ownership(
        self,
        task_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Validate that a user owns a task (through project ownership).

        Checks if the specified user is the owner of the project
        that contains the task.

        Args:
            task_id: UUID of the task to check.
            user_id: UUID of the user to verify ownership for.

        Returns:
            True if the user owns the task's project, False otherwise.

        Example:
            if await service.validate_ownership(task_id, user.id):
                await service.update(task_id, title="New Title")
        """
        stmt = (
            select(Task)
            .options(selectinload(Task.project))
            .where(Task.id == task_id)
        )
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return False

        return bool(task.project.user_id == user_id)

    async def _get_next_task_number(self, project_id: UUID) -> int:
        """Get the next task number for a project.

        Calculates the next sequential task number by finding
        the maximum current task number and adding 1.

        Args:
            project_id: UUID of the project.

        Returns:
            int: Next task number (1 if no tasks exist).
        """
        stmt = select(func.max(Task.task_number)).where(
            Task.project_id == project_id
        )
        result = await self.db.execute(stmt)
        max_number = result.scalar()

        return (max_number or 0) + 1

    async def _get_project(self, project_id: UUID) -> Project | None:
        """Get a project by ID (internal helper).

        Args:
            project_id: UUID of the project to retrieve.

        Returns:
            Project if found, None otherwise.
        """
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
