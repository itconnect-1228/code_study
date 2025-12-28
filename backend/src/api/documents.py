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


# Response schemas - Frontend expects these exact field names
class ChaptersResponse(BaseModel):
    """Response schema for document chapters (Frontend format)."""

    summary: dict[str, Any] = Field(..., description="Chapter 1: What This Code Does")
    prerequisites: dict[str, Any] = Field(..., description="Chapter 2: Prerequisites")
    coreLogic: dict[str, Any] = Field(..., description="Chapter 3: Code Structure")
    lineByLine: dict[str, Any] = Field(
        ..., description="Chapter 4: Line-by-Line Explanation"
    )
    syntaxReference: dict[str, Any] = Field(
        ..., description="Chapter 5: Execution Flow"
    )
    commonPatterns: dict[str, Any] = Field(..., description="Chapter 6: Core Concepts")
    exercises: dict[str, Any] = Field(..., description="Chapter 7: Common Mistakes")


def transform_status_to_frontend(db_status: str) -> str:
    """Transform DB status to Frontend expected values.

    DB stores: 'pending', 'in_progress', 'completed', 'failed'
    Frontend expects: 'pending', 'generating', 'completed', 'error'
    """
    status_mapping = {
        "pending": "pending",
        "in_progress": "generating",  # DB 'in_progress' → Frontend 'generating'
        "completed": "completed",
        "failed": "error",  # DB 'failed' → Frontend 'error'
    }
    return status_mapping.get(db_status, db_status)


def transform_content_to_chapters(content: dict[str, Any]) -> dict[str, Any]:
    """Transform DB content (chapter1-7) to Frontend format (named chapters).

    DB stores: chapter1, chapter2, chapter3, chapter4, chapter5, chapter6, chapter7
    Frontend expects: summary, prerequisites, coreLogic, lineByLine, syntaxReference, commonPatterns, exercises

    Field Mapping:
    - Chapter 4: AI's `lines`/`what_it_does` → Frontend's `lineNumber`/`explanation`
    - Chapter 5: AI's `steps` → Frontend's `items` with `syntax`/`description`
    - Chapter 6: AI's `concepts` → Frontend's `patterns` with `name`/`description`
    - Chapter 7: AI's `mistakes` → Frontend's `items` with `question`/`hint`
    """
    if not content:
        return {}

    # Transform Chapter 4: lineByLine
    # AI: {lines: "1-3", code, what_it_does, ...}
    # Frontend: {lineNumber: 1, code, explanation}
    raw_explanations = content.get("chapter4", {}).get("explanations", [])
    line_explanations = []
    for item in raw_explanations:
        # Parse line number from "1-3" format
        lines_str = item.get("lines", "0")
        try:
            line_num = (
                int(lines_str.split("-")[0])
                if isinstance(lines_str, str)
                else int(lines_str)
            )
        except (ValueError, AttributeError):
            line_num = 0
        line_explanations.append(
            {
                "lineNumber": line_num,
                "code": item.get("code", ""),
                "explanation": item.get("what_it_does", ""),
            }
        )

    # Transform Chapter 5: syntaxReference
    # AI: {step_number, what_happens, current_values, why_it_matters}
    # Frontend: {syntax, description}
    raw_steps = content.get("chapter5", {}).get("steps", [])
    syntax_items = []
    for item in raw_steps:
        step_num = item.get("step_number", "")
        what_happens = item.get("what_happens", "")
        why_matters = item.get("why_it_matters", "")
        syntax_items.append(
            {
                "syntax": f"Step {step_num}",
                "description": f"{what_happens}"
                + (f" - {why_matters}" if why_matters else ""),
            }
        )

    # Transform Chapter 6: commonPatterns
    # AI: {name, what_it_is, why_used, where_applied, in_this_code}
    # Frontend: {name, description}
    raw_concepts = content.get("chapter6", {}).get("concepts", [])
    patterns = []
    for item in raw_concepts:
        patterns.append(
            {
                "name": item.get("name", ""),
                "description": item.get("what_it_is", "")
                + (
                    f" {item.get('in_this_code', '')}"
                    if item.get("in_this_code")
                    else ""
                ),
            }
        )

    # Transform Chapter 7: exercises
    # AI: {mistake, wrong_code, right_code, why_it_matters, how_to_fix}
    # Frontend: {question, hint}
    raw_mistakes = content.get("chapter7", {}).get("mistakes", [])
    exercises = []
    for item in raw_mistakes:
        exercises.append(
            {
                "question": item.get("mistake", ""),
                "hint": item.get("how_to_fix", ""),
            }
        )

    return {
        "summary": {
            "title": content.get("chapter1", {}).get("title", ""),
            "content": content.get("chapter1", {}).get("summary", ""),
        },
        "prerequisites": {
            "title": content.get("chapter2", {}).get("title", ""),
            "concepts": content.get("chapter2", {}).get("concepts", []),
        },
        "coreLogic": {
            "title": content.get("chapter3", {}).get("title", ""),
            "content": content.get("chapter3", {}).get("flowchart", ""),
        },
        "lineByLine": {
            "title": content.get("chapter4", {}).get("title", ""),
            "explanations": line_explanations,
        },
        "syntaxReference": {
            "title": content.get("chapter5", {}).get("title", ""),
            "items": syntax_items,
        },
        "commonPatterns": {
            "title": content.get("chapter6", {}).get("title", ""),
            "patterns": patterns,
        },
        "exercises": {
            "title": content.get("chapter7", {}).get("title", ""),
            "items": exercises,
        },
    }


class DocumentResponse(BaseModel):
    """Response schema for a learning document (Frontend format)."""

    id: UUID
    task_id: UUID
    status: str  # Frontend expects 'status', not 'generation_status'
    chapters: dict[str, Any]  # Frontend expects 'chapters', not 'content'
    error_message: str | None = None  # Frontend expects 'error_message'
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

    # Transform DB model to Frontend-expected format
    return DocumentResponse(
        id=document.id,
        task_id=document.task_id,
        status=transform_status_to_frontend(
            document.generation_status
        ),  # Transform status
        chapters=transform_content_to_chapters(document.content),  # Transform content
        error_message=document.generation_error,  # Rename field
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


class GenerateDocumentResponse(BaseModel):
    """Response schema for document generation request (Frontend format)."""

    id: UUID
    task_id: UUID
    status: str  # Frontend expects 'status', not 'generation_status'
    message: str

    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/tasks/{task_id}/document/generate", response_model=GenerateDocumentResponse
)
async def generate_document(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> GenerateDocumentResponse:
    """Trigger document generation for a task.

    Initiates AI-powered learning document generation for the task's uploaded code.
    Returns immediately with generation status (async generation).

    Args:
        task_id: UUID of the task.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        GenerateDocumentResponse with document ID and initial status.

    Raises:
        HTTPException 404: If task not found or user doesn't own it.
        HTTPException 400: If no code uploaded or document already exists.
    """
    from pathlib import Path

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from src.models.task import Task
    from src.models.uploaded_code import UploadedCode

    # Get task with uploaded code
    stmt = (
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.uploaded_code).selectinload(UploadedCode.code_files))
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Validate ownership via project
    from src.services.task_service import TaskService

    task_service = TaskService(db)
    if not await task_service.validate_ownership(task_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check if code is uploaded
    if not task.uploaded_code or not task.uploaded_code.code_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No code uploaded for this task",
        )

    # Read code content from files
    code_contents = []
    for code_file in task.uploaded_code.code_files:
        try:
            file_path = Path(code_file.storage_path)
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                code_contents.append(f"# File: {code_file.file_name}\n{content}")
        except Exception:
            continue

    if not code_contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read uploaded code files",
        )

    combined_code = "\n\n".join(code_contents)
    language = task.uploaded_code.detected_language or "Unknown"
    filename = (
        task.uploaded_code.code_files[0].file_name
        if task.uploaded_code.code_files
        else None
    )

    # Generate document
    doc_service = DocumentGenerationService(db)

    try:
        document = await doc_service.generate_document(
            task_id=task_id,
            code=combined_code,
            language=language,
            filename=filename,
        )
        return GenerateDocumentResponse(
            id=document.id,
            task_id=document.task_id,
            status=transform_status_to_frontend(
                document.generation_status
            ),  # Transform status
            message="Document generation completed",
        )
    except Exception as e:
        # Check if document was created but failed
        existing_doc = await doc_service.get_document_by_task(task_id)
        if existing_doc:
            return GenerateDocumentResponse(
                id=existing_doc.id,
                task_id=existing_doc.task_id,
                status=transform_status_to_frontend(
                    existing_doc.generation_status
                ),  # Transform status
                message=str(e)
                if existing_doc.is_failed
                else "Document generation in progress",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document generation failed: {e!s}",
        )


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

    # Transform status to Frontend format
    status_info["status"] = transform_status_to_frontend(status_info["status"])

    return DocumentStatusResponse(**status_info)
