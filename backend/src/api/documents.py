"""Document API endpoints.

This module provides REST API endpoints for learning document management:
- GET /tasks/{task_id}/document - Get learning document for a task
- GET /tasks/{task_id}/document/status - Get document generation status

Architecture Notes:
- Uses dependency injection for database session and current user
- Validates task ownership before document operations
- Returns 404 for non-existent tasks (security: don't reveal existence)

T097: GET /tasks/{task_id}/document endpoint
T098: GET /tasks/{task_id}/document/status endpoint
"""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.db.session import get_session
from src.models.user import User
from src.services.document.document_generation_service import DocumentGenerationService
from src.services.task_service import TaskService

router = APIRouter(tags=["documents"])


# Response schemas
class DocumentContentResponse(BaseModel):
    """Response schema for document content."""

    chapter1: dict[str, Any] = Field(..., description="What This Code Does")
    chapter2: dict[str, Any] = Field(..., description="Prerequisites")
    chapter3: dict[str, Any] = Field(..., description="Code Structure")
    chapter4: dict[str, Any] = Field(..., description="Line-by-Line Explanation")
    chapter5: dict[str, Any] = Field(..., description="Execution Flow")
    chapter6: dict[str, Any] = Field(..., description="Core Concepts")
    chapter7: dict[str, Any] = Field(..., description="Common Mistakes")


class DocumentResponse(BaseModel):
    """Response schema for a learning document."""

    id: UUID
    task_id: UUID
    generation_status: str
    content: dict[str, Any]
    generation_started_at: datetime | None = None
    generation_completed_at: datetime | None = None
    generation_error: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusResponse(BaseModel):
    """Response schema for document generation status."""

    status: str = Field(
        ...,
        description="Generation status: 'not_found', 'pending', 'in_progress', 'completed', 'failed'",
    )
    started_at: str | None = Field(
        None,
        description="ISO timestamp when generation started",
    )
    completed_at: str | None = Field(
        None,
        description="ISO timestamp when generation completed",
    )
    error: str | None = Field(
        None,
        description="Error message if generation failed",
    )
    estimated_time_remaining: int | None = Field(
        None,
        description="Estimated seconds remaining (only for in_progress status)",
    )


@router.get("/tasks/{task_id}/document", response_model=DocumentResponse)
async def get_document(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentResponse:
    """Get learning document for a task.

    Returns the full learning document with 7-chapter content.
    The document may be in various generation states.

    Args:
        task_id: UUID of the task.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        DocumentResponse with document content and status.

    Raises:
        HTTPException 404: If task not found, user doesn't own it, or no document exists.
    """
    # Validate task ownership
    task_service = TaskService(db)
    if not await task_service.validate_ownership(task_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Get document
    doc_service = DocumentGenerationService(db)
    document = await doc_service.get_document_by_task(task_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning document not found for this task",
        )

    return DocumentResponse.model_validate(document)


@router.get("/tasks/{task_id}/document/status", response_model=DocumentStatusResponse)
async def get_document_status(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentStatusResponse:
    """Get document generation status for a task.

    Returns the current generation status without the full content.
    Useful for polling during async document generation.

    Args:
        task_id: UUID of the task.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        DocumentStatusResponse with status information.

    Raises:
        HTTPException 404: If task not found or user doesn't own it.
    """
    # Validate task ownership
    task_service = TaskService(db)
    if not await task_service.validate_ownership(task_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Get status
    doc_service = DocumentGenerationService(db)
    status_info = await doc_service.get_generation_status(task_id)

    return DocumentStatusResponse(**status_info)
