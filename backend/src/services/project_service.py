"""Project service for project CRUD operations.

This module provides the ProjectService class which handles:
- Project creation with user ownership
- Project retrieval by ID or user
- Project update (title, description)
- Soft delete with 30-day trash retention

Architecture Notes:
- Service Layer Pattern: Business logic separated from API layer
- Raises ValueError for validation errors (API layer converts to HTTP responses)
- Uses async/await for non-blocking database operations
- Respects soft delete: trashed projects excluded by default

Example:
    from src.db.session import get_session
    from src.services.project_service import ProjectService

    async def list_projects():
        async with get_session() as session:
            service = ProjectService(session)
            projects = await service.get_by_user(user_id)
            return projects
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import Project
from src.models.user import User


class ProjectService:
    """Service for project CRUD operations.

    This service encapsulates all project-related business logic,
    separating it from the API layer. It handles validation,
    ownership verification, and database operations.

    The service respects soft delete semantics:
    - Active projects (deletion_status='active') are returned by default
    - Trashed projects can be included with include_trashed=True

    Attributes:
        db: Async database session for database operations.

    Example:
        async with get_session() as session:
            service = ProjectService(session)

            # Create project
            project = await service.create(user_id, "My Project")

            # Get project
            project = await service.get_by_id(project_id)

            # Update project
            updated = await service.update(project_id, title="New Title")

            # Soft delete
            await service.soft_delete(project_id)
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize ProjectService with database session.

        Args:
            db: Async SQLAlchemy session for database operations.
        """
        self.db = db

    async def create(
        self,
        user_id: UUID,
        title: str,
        description: str | None = None,
    ) -> Project:
        """Create a new project for a user.

        Creates a new project with the given title and optional description.
        The project is associated with the specified user.

        Args:
            user_id: UUID of the user who owns the project.
            title: Project title (minimum 1 character).
            description: Optional project description.

        Returns:
            Project: The newly created and persisted project object.

        Raises:
            ValueError: If title is empty.
            ValueError: If user_id does not exist.

        Example:
            project = await service.create(
                user_id=user.id,
                title="Python Basics",
                description="Learn Python fundamentals"
            )
        """
        # Validate title
        if not title or len(title.strip()) == 0:
            raise ValueError("Project title cannot be empty")

        # Verify user exists
        user = await self._get_user(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # Create project
        project = Project(
            user_id=user_id,
            title=title.strip(),
            description=description,
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def get_by_id(
        self,
        project_id: UUID,
        include_trashed: bool = False,
    ) -> Project | None:
        """Get a project by its ID.

        Retrieves a project by its UUID. By default, trashed projects
        are excluded from results.

        Args:
            project_id: UUID of the project to retrieve.
            include_trashed: If True, include trashed projects. Default False.

        Returns:
            Project if found, None otherwise.

        Example:
            project = await service.get_by_id(project_id)
            if project:
                print(f"Found: {project.title}")
        """
        stmt = select(Project).where(Project.id == project_id)

        if not include_trashed:
            stmt = stmt.where(Project.deletion_status == "active")

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        include_trashed: bool = False,
    ) -> list[Project]:
        """Get all projects for a user.

        Retrieves all projects owned by the specified user.
        By default, only active (non-trashed) projects are returned.

        Args:
            user_id: UUID of the user whose projects to retrieve.
            include_trashed: If True, include trashed projects. Default False.

        Returns:
            List of projects (empty list if user has no projects).

        Example:
            projects = await service.get_by_user(user_id)
            for p in projects:
                print(f"- {p.title}")
        """
        stmt = select(Project).where(Project.user_id == user_id)

        if not include_trashed:
            stmt = stmt.where(Project.deletion_status == "active")

        # Order by last activity (most recent first)
        stmt = stmt.order_by(Project.last_activity_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        project_id: UUID,
        title: str | None = None,
        description: str | None = None,
    ) -> Project:
        """Update a project's title or description.

        Updates the specified project with new title and/or description.
        Only provided fields are updated (None values are ignored).

        Args:
            project_id: UUID of the project to update.
            title: New project title (if provided, must not be empty).
            description: New project description (can be set to any value).

        Returns:
            Project: The updated project object.

        Raises:
            ValueError: If project is not found.
            ValueError: If title is provided but empty.

        Example:
            updated = await service.update(
                project_id=project.id,
                title="New Title",
                description="Updated description"
            )
        """
        # Get project (active only)
        project = await self.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with id {project_id} not found")

        # Validate title if provided
        if title is not None:
            if len(title.strip()) == 0:
                raise ValueError("Project title cannot be empty")
            project.title = title.strip()

        # Update description (can be None to clear it)
        if description is not None:
            project.description = description

        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def soft_delete(self, project_id: UUID) -> Project:
        """Soft delete a project (move to trash).

        Moves the project to trash with 30-day scheduled deletion.
        The project can be restored from trash before permanent deletion.

        Args:
            project_id: UUID of the project to delete.

        Returns:
            Project: The trashed project object.

        Raises:
            ValueError: If project is not found.
            ValueError: If project is already in trash.

        Example:
            deleted = await service.soft_delete(project.id)
            print(f"Project trashed. Scheduled deletion: {deleted.scheduled_deletion_at}")
        """
        # Get project including trashed to check current status
        project = await self.get_by_id(project_id, include_trashed=True)
        if not project:
            raise ValueError(f"Project with id {project_id} not found")

        if project.is_trashed:
            raise ValueError(f"Project with id {project_id} is already in trash")

        # Use the model's soft_delete method
        project.soft_delete()

        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def validate_ownership(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Validate that a user owns a project.

        Checks if the specified user is the owner of the given project.
        Used for authorization before modifying or deleting a project.

        Security note: Returns False for non-existent projects to prevent
        information leakage (attacker cannot determine if a project exists).

        Args:
            project_id: UUID of the project to check.
            user_id: UUID of the user to verify ownership for.

        Returns:
            True if the user owns the project, False otherwise.

        Example:
            if await service.validate_ownership(project_id, current_user.id):
                # User is authorized to modify this project
                await service.update(project_id, title="New Title")
            else:
                # Access denied
                raise HTTPException(status_code=403, detail="Access denied")
        """
        project = await self.get_by_id(project_id)
        if not project:
            return False
        return bool(project.user_id == user_id)

    async def _get_user(self, user_id: UUID) -> User | None:
        """Get a user by ID (internal helper).

        Args:
            user_id: UUID of the user to retrieve.

        Returns:
            User if found, None otherwise.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
