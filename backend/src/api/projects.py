"""Project API endpoints.

This module provides project management endpoints:
- GET /projects - List user's projects (T046)
- POST /projects - Create new project (T047)
- GET /projects/{project_id} - Get project by ID (T048)
- PATCH /projects/{project_id} - Update project (T049)
- DELETE /projects/{project_id} - Soft delete project (T050)

All endpoints require authentication via access token cookie.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.api.exceptions import AuthorizationException, NotFoundException
from src.api.schemas import (
    CreateProjectRequest,
    ProjectListResponse,
    ProjectResponse,
    UpdateProjectRequest,
)
from src.db.session import get_session
from src.models.user import User
from src.services.project_service import ProjectService

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
async def get_projects(
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
    include_trashed: bool = False,
) -> dict:
    """Get all projects for the current user.

    Returns a list of projects owned by the authenticated user.
    By default, trashed projects are excluded.

    Args:
        current_user: Authenticated user (injected).
        db: Database session (injected).
        include_trashed: If True, include trashed projects.

    Returns:
        dict: Project list response with projects and total count.
    """
    project_service = ProjectService(db)
    projects = await project_service.get_by_user(
        current_user.id, include_trashed=include_trashed
    )

    return {
        "projects": [ProjectResponse.from_project(p) for p in projects],
        "total": len(projects),
    }


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> ProjectResponse:
    """Create a new project.

    Creates a new project with the given title and optional description.
    The project is automatically associated with the authenticated user.

    Args:
        request: Project creation request with title and description.
        current_user: Authenticated user (injected).
        db: Database session (injected).

    Returns:
        ProjectResponse: The created project.

    Raises:
        ValidationException: If title is empty (422).
    """
    project_service = ProjectService(db)
    project = await project_service.create(
        user_id=current_user.id,
        title=request.title,
        description=request.description,
    )

    return ProjectResponse.from_project(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> ProjectResponse:
    """Get a specific project by ID.

    Retrieves a single project by its UUID. The user must own the project.

    Args:
        project_id: UUID of the project to retrieve.
        current_user: Authenticated user (injected).
        db: Database session (injected).

    Returns:
        ProjectResponse: The requested project.

    Raises:
        NotFoundException: If project doesn't exist (404).
        AuthorizationException: If user doesn't own the project (403).
    """
    project_service = ProjectService(db)

    # Check if project exists
    project = await project_service.get_by_id(project_id)
    if not project:
        raise NotFoundException(
            message="Project not found",
            code="PROJECT_NOT_FOUND",
        )

    # Check ownership
    if not await project_service.validate_ownership(project_id, current_user.id):
        raise AuthorizationException(
            message="You do not have permission to access this project",
            code="ACCESS_DENIED",
        )

    return ProjectResponse.from_project(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    request: UpdateProjectRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> ProjectResponse:
    """Update a project's title or description.

    Updates the specified project. Only provided fields are updated.
    The user must own the project.

    Args:
        project_id: UUID of the project to update.
        request: Update request with optional title and description.
        current_user: Authenticated user (injected).
        db: Database session (injected).

    Returns:
        ProjectResponse: The updated project.

    Raises:
        NotFoundException: If project doesn't exist (404).
        AuthorizationException: If user doesn't own the project (403).
    """
    project_service = ProjectService(db)

    # Check if project exists
    project = await project_service.get_by_id(project_id)
    if not project:
        raise NotFoundException(
            message="Project not found",
            code="PROJECT_NOT_FOUND",
        )

    # Check ownership
    if not await project_service.validate_ownership(project_id, current_user.id):
        raise AuthorizationException(
            message="You do not have permission to modify this project",
            code="ACCESS_DENIED",
        )

    # Update project
    updated_project = await project_service.update(
        project_id=project_id,
        title=request.title,
        description=request.description,
    )

    return ProjectResponse.from_project(updated_project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> Response:
    """Soft delete a project (move to trash).

    Moves the project to trash with 30-day scheduled deletion.
    The project can be restored from trash before permanent deletion.
    The user must own the project.

    Args:
        project_id: UUID of the project to delete.
        current_user: Authenticated user (injected).
        db: Database session (injected).

    Returns:
        Response: 204 No Content on success.

    Raises:
        NotFoundException: If project doesn't exist (404).
        AuthorizationException: If user doesn't own the project (403).
    """
    project_service = ProjectService(db)

    # Check if project exists
    project = await project_service.get_by_id(project_id)
    if not project:
        raise NotFoundException(
            message="Project not found",
            code="PROJECT_NOT_FOUND",
        )

    # Check ownership
    if not await project_service.validate_ownership(project_id, current_user.id):
        raise AuthorizationException(
            message="You do not have permission to delete this project",
            code="ACCESS_DENIED",
        )

    # Soft delete project
    await project_service.soft_delete(project_id)

    return Response(status_code=204)
