"""Task API endpoints.

This module provides REST API endpoints for task management:
- GET /projects/{project_id}/tasks - List tasks for a project
- POST /projects/{project_id}/tasks - Create a new task with file upload
- GET /tasks/{task_id} - Get task details
- PATCH /tasks/{task_id} - Update task
- DELETE /tasks/{task_id} - Soft delete task
- GET /tasks/{task_id}/code - Get uploaded code files

Architecture Notes:
- Uses dependency injection for database session and current user
- Validates project ownership before task operations
- Supports multipart/form-data for file uploads
"""

from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.db.session import get_session
from src.models.user import User
from src.services.code_analysis.code_upload_service import CodeUploadService
from src.services.code_analysis.file_storage import FileStorageService
from src.services.project_service import ProjectService
from src.services.task_service import TaskService
from src.utils.file_validator import validate_upload


router = APIRouter(tags=["tasks"])


# Request/Response schemas
class TaskCreate(BaseModel):
    """Request schema for creating a task."""

    title: str = Field(..., min_length=5, max_length=255)
    description: str | None = Field(None, max_length=500)


class TaskUpdate(BaseModel):
    """Request schema for updating a task."""

    title: str | None = Field(None, min_length=5, max_length=255)
    description: str | None = Field(None, max_length=500)


class TaskResponse(BaseModel):
    """Response schema for a task."""

    id: UUID
    project_id: UUID
    task_number: int
    title: str
    description: str | None
    upload_method: str | None
    deletion_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Response schema for a list of tasks."""

    tasks: list[TaskResponse]
    total: int


class CodeFileResponse(BaseModel):
    """Response schema for a code file (Frontend format)."""

    id: UUID
    filename: str  # Frontend expects 'filename' not 'file_name'
    relative_path: str | None = None  # Frontend expects 'relative_path'
    content: str | None = None  # File content (read from storage)
    language: str | None = None  # Programming language
    line_count: int = 0  # Frontend expects 'line_count'
    size_bytes: int | None = None  # Frontend expects 'size_bytes' not 'file_size_bytes'

    class Config:
        from_attributes = True


class UploadedCodeResponse(BaseModel):
    """Response schema for uploaded code with files (Full format)."""

    id: UUID
    detected_language: str | None
    complexity_level: str | None
    total_lines: int | None
    total_files: int | None
    upload_size_bytes: int | None
    code_files: list[CodeFileResponse]

    class Config:
        from_attributes = True


class CodeFilesResponse(BaseModel):
    """Response schema for code files list (Frontend format)."""

    files: list[CodeFileResponse]
    total: int


# Storage configuration
STORAGE_BASE_PATH = Path("storage")


def get_storage_service() -> FileStorageService:
    """Get file storage service."""
    return FileStorageService(base_path=STORAGE_BASE_PATH)


@router.get("/projects/{project_id}/tasks", response_model=TaskListResponse)
async def list_tasks(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TaskListResponse:
    """List all tasks for a project.

    Args:
        project_id: UUID of the project.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        TaskListResponse with tasks and total count.

    Raises:
        HTTPException 403: If user doesn't own the project.
        HTTPException 404: If project not found.
    """
    # Verify project ownership
    project_service = ProjectService(db)
    if not await project_service.validate_ownership(project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    task_service = TaskService(db)
    tasks = await task_service.get_by_project(project_id)
    task_responses = [TaskResponse.model_validate(t) for t in tasks]
    return TaskListResponse(tasks=task_responses, total=len(task_responses))


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: UUID,
    title: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    storage: Annotated[FileStorageService, Depends(get_storage_service)],
    description: Annotated[str | None, Form()] = None,
    files: list[UploadFile] = File(default=[]),
    code: Annotated[str | None, Form()] = None,
    language: Annotated[str | None, Form()] = None,
) -> TaskResponse:
    """Create a new task with optional file upload.

    Supports three upload methods:
    - file: Single or multiple files via multipart/form-data
    - folder: Multiple files with preserved paths
    - paste: Code string with language specification

    Args:
        project_id: UUID of the project.
        title: Task title (min 5 chars).
        db: Database session.
        current_user: Authenticated user.
        storage: File storage service.
        description: Optional task description.
        files: Uploaded files.
        code: Pasted code (for paste upload).
        language: Language for pasted code.

    Returns:
        Created task.

    Raises:
        HTTPException 403: If user doesn't own the project.
        HTTPException 400: If upload data is invalid.
    """
    # Verify project ownership
    project_service = ProjectService(db)
    if not await project_service.validate_ownership(project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Determine upload method
    if files:
        upload_method = "file" if len(files) == 1 else "folder"
    elif code:
        upload_method = "paste"
    else:
        upload_method = None

    # Validate title length
    if len(title.strip()) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task title must be at least 5 characters",
        )

    # Read and validate files BEFORE creating task
    file_data: list[tuple[str, bytes]] = []
    if files:
        for f in files:
            content = await f.read()
            file_data.append((f.filename or "unnamed", content))

        # Validate files
        validation_result = validate_upload(file_data)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result.error_message,
            )

    # Create task only after validation passes
    task_service = TaskService(db)
    try:
        task = await task_service.create(
            project_id=project_id,
            title=title,
            upload_method=upload_method,
            description=description,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Handle file uploads if present (already validated)
    if file_data or code:
        upload_service = CodeUploadService(db=db, storage=storage)

        if file_data:
            await upload_service.upload_files(
                user_id=current_user.id,
                task_id=task.id,
                files=file_data,
            )
        elif code and language:
            await upload_service.upload_paste(
                user_id=current_user.id,
                task_id=task.id,
                code=code,
                language=language,
            )

    return TaskResponse.model_validate(task)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TaskResponse:
    """Get task details.

    Args:
        task_id: UUID of the task.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Task details.

    Raises:
        HTTPException 404: If task not found or user doesn't have access.
    """
    task_service = TaskService(db)

    # Validate ownership
    if not await task_service.validate_ownership(task_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task = await task_service.get_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return TaskResponse.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    update_data: TaskUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TaskResponse:
    """Update task title or description.

    Args:
        task_id: UUID of the task.
        update_data: Fields to update.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Updated task.

    Raises:
        HTTPException 404: If task not found or user doesn't have access.
        HTTPException 400: If update data is invalid.
    """
    task_service = TaskService(db)

    # Validate ownership
    if not await task_service.validate_ownership(task_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    try:
        task = await task_service.update(
            task_id=task_id,
            title=update_data.title,
            description=update_data.description,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return TaskResponse.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Soft delete a task (move to trash).

    Args:
        task_id: UUID of the task.
        db: Database session.
        current_user: Authenticated user.

    Raises:
        HTTPException 404: If task not found or user doesn't have access.
    """
    task_service = TaskService(db)

    # Validate ownership
    if not await task_service.validate_ownership(task_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    try:
        await task_service.soft_delete(task_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/tasks/{task_id}/code", response_model=CodeFilesResponse)
async def get_task_code(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CodeFilesResponse:
    """Get uploaded code files for a task.

    Args:
        task_id: UUID of the task.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Uploaded code with file list.

    Raises:
        HTTPException 404: If task not found or has no code.
    """
    task_service = TaskService(db)

    # Validate ownership
    if not await task_service.validate_ownership(task_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task = await task_service.get_by_id_with_code(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if not task.uploaded_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No code uploaded for this task",
        )

    # Build code file responses with content
    code_file_responses = []
    for cf in task.uploaded_code.code_files:
        content = None
        line_count = 0
        try:
            # Read file content from storage
            storage_path = Path(cf.storage_path)
            if storage_path.exists():
                content = storage_path.read_text(encoding="utf-8")
                line_count = len(content.splitlines())
        except Exception:
            pass  # Content will be None if read fails

        code_file_responses.append(
            CodeFileResponse(
                id=cf.id,
                filename=cf.file_name,  # Frontend format
                relative_path=cf.file_path,  # Frontend format
                content=content,
                language=task.uploaded_code.detected_language,
                line_count=line_count,  # Frontend format
                size_bytes=cf.file_size_bytes,  # Frontend format
            )
        )

    return CodeFilesResponse(
        files=code_file_responses,
        total=len(code_file_responses),
    )
