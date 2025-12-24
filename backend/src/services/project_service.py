"""Project service for project CRUD operations.

This is a stub file for TDD RED phase - will be fully implemented in GREEN phase.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class ProjectService:
    """Service for project CRUD operations.

    Stub implementation for TDD RED phase.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize ProjectService with database session."""
        self.db = db

    async def create(self, user_id: UUID, title: str, description: str | None = None):
        """Create a new project - NOT IMPLEMENTED."""
        raise NotImplementedError("create() not implemented")

    async def get_by_id(self, project_id: UUID, include_trashed: bool = False):
        """Get project by ID - NOT IMPLEMENTED."""
        raise NotImplementedError("get_by_id() not implemented")

    async def get_by_user(self, user_id: UUID):
        """Get all projects for a user - NOT IMPLEMENTED."""
        raise NotImplementedError("get_by_user() not implemented")

    async def update(
        self, project_id: UUID, title: str | None = None, description: str | None = None
    ):
        """Update a project - NOT IMPLEMENTED."""
        raise NotImplementedError("update() not implemented")

    async def soft_delete(self, project_id: UUID):
        """Soft delete a project - NOT IMPLEMENTED."""
        raise NotImplementedError("soft_delete() not implemented")
