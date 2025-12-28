"""Document Generation Service.

This module provides the DocumentGenerationService class which handles:
- AI-powered learning document generation from code
- Retry logic with exponential backoff for reliability
- Status tracking during async generation
- JSON parsing and validation of generated content

Architecture Notes:
- Service Layer Pattern: Business logic separated from API layer
- Uses GeminiClient for AI generation (has built-in retry)
- Additional application-level retry for complete generation flow
- Stores results in LearningDocument model

Requirements:
- FR-021: AI integration for document generation
- FR-026 through FR-034: 7-chapter document structure
- FR-083: Performance target < 3 minutes for 500 LOC
- FR-088-FR-094: Retry logic for AI service reliability
- research.md: Retry up to 3 times with exponential backoff

Example:
    from src.db.session import get_session_context
    from src.services.document import DocumentGenerationService

    async with get_session_context() as session:
        service = DocumentGenerationService(session)
        document = await service.generate_document(
            task_id=task.id,
            code="def hello(): print('Hello')",
            language="Python",
            filename="hello.py"
        )
        print(f"Generated document status: {document.generation_status}")
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.learning_document import LearningDocument
from src.models.task import Task
from src.services.ai.gemini_client import (
    ContentType,
    GeminiClient,
    GeminiError,
    GeminiRateLimitError,
    GeminiTimeoutError,
)
from src.services.ai.prompts import (
    DOCUMENT_JSON_SCHEMA,
    PromptBuilder,
)

logger = logging.getLogger(__name__)


class DocumentGenerationError(Exception):
    """Base exception for document generation errors."""

    def __init__(
        self,
        message: str,
        task_id: UUID | None = None,
        original_error: Exception | None = None,
        retry_count: int = 0,
    ):
        super().__init__(message)
        self.task_id = task_id
        self.original_error = original_error
        self.retry_count = retry_count


class DocumentValidationError(DocumentGenerationError):
    """Raised when generated content fails validation."""

    pass


class DocumentAlreadyExistsError(DocumentGenerationError):
    """Raised when a document already exists for the task."""

    pass


@dataclass(frozen=True)
class GenerationConfig:
    """Configuration for document generation.

    Attributes:
        max_retries: Maximum retry attempts for the complete generation flow
        base_delay: Base delay for exponential backoff (seconds)
        max_delay: Maximum delay between retries (seconds)
        timeout: Overall timeout for generation (seconds)
    """

    max_retries: int = 3
    base_delay: float = 2.0
    max_delay: float = 30.0
    timeout: int = 300  # 5 minutes (spec requires < 3 min for 500 LOC)


class DocumentGenerationService:
    """Service for AI-powered learning document generation.

    This service handles the complete flow of generating educational
    documents from code using Google Gemini API. It includes:
    - Prompt construction for 7-chapter document structure
    - API call with retry logic
    - Response parsing and validation
    - Status tracking in LearningDocument model

    The service implements retry logic at two levels:
    1. GeminiClient level: Retries individual API calls
    2. Service level: Retries the complete generation flow

    Attributes:
        db: Async database session for database operations.
        gemini_client: GeminiClient instance for AI generation.
        config: GenerationConfig for retry behavior.

    Example:
        async with get_session_context() as session:
            service = DocumentGenerationService(session)

            # Generate document for a task
            document = await service.generate_document(
                task_id=task.id,
                code=code_content,
                language="Python",
                filename="example.py"
            )

            if document.is_completed:
                print("Document generated successfully!")
                chapter1 = document.get_chapter(1)
                print(f"Summary: {chapter1['summary']}")
    """

    # Required chapters for validation
    REQUIRED_CHAPTERS = [
        "chapter1",
        "chapter2",
        "chapter3",
        "chapter4",
        "chapter5",
        "chapter6",
        "chapter7",
    ]

    # Placeholder content for pending documents (satisfies DB constraint)
    PLACEHOLDER_CONTENT: ClassVar[dict[str, Any]] = {
        "chapter1": {"title": "생성 중...", "summary": ""},
        "chapter2": {"title": "생성 중...", "concepts": []},
        "chapter3": {"title": "생성 중...", "flowchart": "", "file_breakdown": {}},
        "chapter4": {"title": "생성 중...", "explanations": []},
        "chapter5": {"title": "생성 중...", "steps": []},
        "chapter6": {"title": "생성 중...", "concepts": []},
        "chapter7": {"title": "생성 중...", "mistakes": []},
    }

    def __init__(
        self,
        db: AsyncSession,
        gemini_client: GeminiClient | None = None,
        config: GenerationConfig | None = None,
    ) -> None:
        """Initialize DocumentGenerationService.

        Args:
            db: Async SQLAlchemy session for database operations.
            gemini_client: Optional GeminiClient instance. If None, creates
                a new client from environment variables.
            config: Optional GenerationConfig. If None, uses defaults.
        """
        self.db = db
        self.gemini_client = gemini_client or GeminiClient()
        self.config = config or GenerationConfig()

    async def generate_document(
        self,
        task_id: UUID,
        code: str,
        language: str,
        filename: str | None = None,
        additional_context: str | None = None,
        file_structure: dict[str, Any] | None = None,
        celery_task_id: str | None = None,
    ) -> LearningDocument:
        """Generate a 7-chapter learning document for code.

        This method orchestrates the complete document generation flow:
        1. Create or get existing LearningDocument record
        2. Mark generation as started
        3. Build prompts using PromptBuilder
        4. Call Gemini API with retry logic
        5. Parse and validate response
        6. Store content and mark as completed

        Args:
            task_id: UUID of the task to generate document for.
            code: Source code to analyze and explain.
            language: Programming language (e.g., "Python", "JavaScript").
            filename: Optional original filename for context.
            additional_context: Optional extra context about the code.
            file_structure: Optional folder structure for multi-file uploads.
            celery_task_id: Optional Celery task ID for tracking.

        Returns:
            LearningDocument: The document with generation status and content.

        Raises:
            DocumentGenerationError: If generation fails after all retries.
            DocumentValidationError: If generated content fails validation.
            DocumentAlreadyExistsError: If a completed document already exists.

        Example:
            document = await service.generate_document(
                task_id=task.id,
                code="def greet(name): return f'Hello, {name}!'",
                language="Python",
                filename="greet.py"
            )
        """
        # Get or create LearningDocument
        document = await self._get_or_create_document(task_id)

        # Check if already completed
        if document.is_completed and document.has_content:
            raise DocumentAlreadyExistsError(
                f"Document already exists for task {task_id}",
                task_id=task_id,
            )

        # Mark generation as started
        document.start_generation(celery_task_id)
        await self.db.commit()

        try:
            # Build prompts
            prompt_builder = PromptBuilder(
                code=code,
                language=language,
                filename=filename,
                additional_context=additional_context,
                file_structure=file_structure,
            )
            system_instruction = prompt_builder.get_system_instruction()
            prompt = prompt_builder.build_document_prompt()

            # Generate with retry
            content = await self._generate_with_retry(
                system_instruction=system_instruction,
                prompt=prompt,
                task_id=task_id,
            )

            # Validate and store content
            validated_content = self._validate_content(content, task_id)
            document.complete_generation(validated_content)
            await self.db.commit()

            logger.info(
                f"Document generation completed for task {task_id}. "
                f"Chapters: {len(validated_content)}"
            )

            return document

        except Exception as e:
            # Mark as failed
            error_message = str(e)
            document.fail_generation(error_message)
            await self.db.commit()

            logger.error(f"Document generation failed for task {task_id}: {e}")

            if isinstance(e, (DocumentGenerationError, DocumentValidationError)):
                raise
            raise DocumentGenerationError(
                f"Generation failed: {error_message}",
                task_id=task_id,
                original_error=e,
            )

    async def get_document_by_task(
        self,
        task_id: UUID,
    ) -> LearningDocument | None:
        """Get the learning document for a task.

        Args:
            task_id: UUID of the task.

        Returns:
            LearningDocument if exists, None otherwise.

        Example:
            document = await service.get_document_by_task(task.id)
            if document and document.is_completed:
                print(document.content)
        """
        stmt = select(LearningDocument).where(LearningDocument.task_id == task_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_generation_status(
        self,
        task_id: UUID,
    ) -> dict[str, Any]:
        """Get the current generation status for a task.

        Returns a status dictionary suitable for API responses.

        Args:
            task_id: UUID of the task.

        Returns:
            dict: Status information including:
                - status: 'pending', 'in_progress', 'completed', 'failed', or 'not_found'
                - started_at: When generation started (if applicable)
                - completed_at: When generation completed (if applicable)
                - error: Error message (if failed)
                - estimated_time_remaining: Estimated seconds remaining (if in_progress)

        Example:
            status = await service.get_generation_status(task.id)
            print(f"Status: {status['status']}")
        """
        document = await self.get_document_by_task(task_id)

        if not document:
            return {"status": "not_found"}

        status_info = {
            "status": document.generation_status,
            "started_at": (
                document.generation_started_at.isoformat()
                if document.generation_started_at
                else None
            ),
            "completed_at": (
                document.generation_completed_at.isoformat()
                if document.generation_completed_at
                else None
            ),
        }

        if document.is_failed:
            status_info["error"] = document.generation_error

        if document.is_in_progress and document.generation_started_at:
            elapsed = (
                datetime.now(UTC) - document.generation_started_at
            ).total_seconds()
            # Estimate based on 3-minute target
            estimated_remaining = max(0, 180 - elapsed)
            status_info["estimated_time_remaining"] = int(estimated_remaining)

        return status_info

    async def retry_failed_document(
        self,
        task_id: UUID,
        code: str,
        language: str,
        filename: str | None = None,
        additional_context: str | None = None,
        file_structure: dict[str, Any] | None = None,
    ) -> LearningDocument:
        """Retry generation for a failed document.

        Resets the document status and attempts generation again.

        Args:
            task_id: UUID of the task with failed document.
            code: Source code to analyze.
            language: Programming language.
            filename: Optional original filename.
            additional_context: Optional extra context.
            file_structure: Optional folder structure.

        Returns:
            LearningDocument: The document with new generation attempt.

        Raises:
            ValueError: If no document exists or document is not failed.
            DocumentGenerationError: If retry generation fails.

        Example:
            # After a failed generation
            document = await service.retry_failed_document(
                task_id=task.id,
                code=code_content,
                language="Python"
            )
        """
        document = await self.get_document_by_task(task_id)

        if not document:
            raise ValueError(f"No document found for task {task_id}")

        if not document.is_failed:
            raise ValueError(
                f"Document is not in failed state. Current status: {document.generation_status}"
            )

        # Reset document status
        document.generation_status = "pending"
        document.generation_error = None
        document.generation_started_at = None
        document.generation_completed_at = None
        await self.db.commit()

        # Attempt generation again
        return await self.generate_document(
            task_id=task_id,
            code=code,
            language=language,
            filename=filename,
            additional_context=additional_context,
            file_structure=file_structure,
        )

    async def _get_or_create_document(
        self,
        task_id: UUID,
    ) -> LearningDocument:
        """Get existing document or create a new one.

        Args:
            task_id: UUID of the task.

        Returns:
            LearningDocument: Existing or newly created document.

        Raises:
            ValueError: If task does not exist.
        """
        # Check if document exists
        document = await self.get_document_by_task(task_id)

        if document:
            return document

        # Verify task exists
        task_stmt = select(Task).where(Task.id == task_id)
        task_result = await self.db.execute(task_stmt)
        task = task_result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Create new document with placeholder content
        document = LearningDocument(
            task_id=task_id,
            content=self.PLACEHOLDER_CONTENT.copy(),
            generation_status="pending",
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Created new LearningDocument for task {task_id}")

        return document

    async def _generate_with_retry(
        self,
        system_instruction: str,
        prompt: str,
        task_id: UUID,
    ) -> dict[str, Any]:
        """Generate document content with retry logic.

        Implements exponential backoff retry for the complete generation flow.
        This is in addition to the retry logic in GeminiClient.

        Args:
            system_instruction: System instruction for the AI.
            prompt: The complete prompt for document generation.
            task_id: UUID of the task (for logging).

        Returns:
            dict: Parsed JSON content with 7 chapters.

        Raises:
            DocumentGenerationError: If all retries fail.
        """
        last_error: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                logger.info(
                    f"Document generation attempt {attempt + 1}/{self.config.max_retries + 1} "
                    f"for task {task_id}"
                )

                # Call Gemini API
                response = await self.gemini_client.generate(
                    prompt=prompt,
                    content_type=ContentType.DOCUMENT,
                    system_instruction=system_instruction,
                    response_schema=DOCUMENT_JSON_SCHEMA,
                )

                # Parse JSON response
                if response.content:
                    content = self._parse_json_response(response.content)
                    logger.info(
                        f"Document generation successful for task {task_id}. "
                        f"Latency: {response.latency_ms:.0f}ms, "
                        f"Tokens: {response.usage.get('total_tokens', 'N/A')}"
                    )
                    return content
                else:
                    raise DocumentGenerationError(
                        "Empty response from AI service",
                        task_id=task_id,
                    )

            except GeminiRateLimitError as e:
                last_error = e
                logger.warning(
                    f"Rate limit hit on attempt {attempt + 1}/{self.config.max_retries + 1}"
                )
                # Longer delay for rate limits
                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.base_delay * (3**attempt),
                        self.config.max_delay,
                    )
                    logger.info(f"Rate limit retry in {delay:.1f}s...")
                    await asyncio.sleep(delay)

            except GeminiTimeoutError as e:
                last_error = e
                logger.warning(
                    f"Timeout on attempt {attempt + 1}/{self.config.max_retries + 1}"
                )
                if attempt < self.config.max_retries:
                    delay = self.config.base_delay * (2**attempt)
                    logger.info(f"Timeout retry in {delay:.1f}s...")
                    await asyncio.sleep(delay)

            except GeminiError as e:
                last_error = e
                logger.error(
                    f"Gemini error on attempt {attempt + 1}/{self.config.max_retries + 1}: {e}"
                )
                if attempt < self.config.max_retries:
                    delay = self.config.base_delay * (2**attempt)
                    await asyncio.sleep(delay)

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(
                    f"JSON parse error on attempt {attempt + 1}/{self.config.max_retries + 1}: {e}"
                )
                if attempt < self.config.max_retries:
                    delay = self.config.base_delay
                    await asyncio.sleep(delay)

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error during generation: {e}")
                if attempt < self.config.max_retries:
                    delay = self.config.base_delay * (2**attempt)
                    await asyncio.sleep(delay)

        raise DocumentGenerationError(
            f"Document generation failed after {self.config.max_retries + 1} attempts: {last_error}",
            task_id=task_id,
            original_error=last_error,
            retry_count=self.config.max_retries + 1,
        )

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parse JSON response from AI.

        Handles common issues with AI-generated JSON:
        - Leading/trailing whitespace
        - Markdown code blocks
        - Common escape issues

        Args:
            content: Raw response content.

        Returns:
            dict: Parsed JSON content.

        Raises:
            json.JSONDecodeError: If content is not valid JSON.
        """
        # Strip whitespace
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        # Parse JSON
        return json.loads(content)

    def _validate_content(
        self,
        content: dict[str, Any],
        task_id: UUID,
    ) -> dict[str, Any]:
        """Validate generated document content.

        Ensures the content has all required chapters with minimum structure.

        Args:
            content: Parsed JSON content from AI.
            task_id: UUID of the task (for error messages).

        Returns:
            dict: Validated content (same as input if valid).

        Raises:
            DocumentValidationError: If content is missing required chapters
                or has invalid structure.
        """
        # Check for required chapters
        missing_chapters = [
            chapter for chapter in self.REQUIRED_CHAPTERS if chapter not in content
        ]

        if missing_chapters:
            raise DocumentValidationError(
                f"Missing required chapters: {missing_chapters}",
                task_id=task_id,
            )

        # Validate chapter structure
        for chapter_key in self.REQUIRED_CHAPTERS:
            chapter = content[chapter_key]
            if not isinstance(chapter, dict):
                raise DocumentValidationError(
                    f"Invalid chapter structure for {chapter_key}: expected dict",
                    task_id=task_id,
                )

            # Chapter must have at least a title
            if "title" not in chapter:
                raise DocumentValidationError(
                    f"Missing title in {chapter_key}",
                    task_id=task_id,
                )

        # Specific validations for certain chapters
        # Chapter 2: Must have concepts array
        if "concepts" not in content["chapter2"]:
            raise DocumentValidationError(
                "Chapter 2 must have concepts array",
                task_id=task_id,
            )

        if not isinstance(content["chapter2"]["concepts"], list):
            raise DocumentValidationError(
                "Chapter 2 concepts must be an array",
                task_id=task_id,
            )

        # Chapter 4: Must have explanations array
        if "explanations" not in content["chapter4"]:
            raise DocumentValidationError(
                "Chapter 4 must have explanations array",
                task_id=task_id,
            )

        # Chapter 7: Must have mistakes array
        if "mistakes" not in content["chapter7"]:
            raise DocumentValidationError(
                "Chapter 7 must have mistakes array",
                task_id=task_id,
            )

        logger.debug(f"Content validation passed for task {task_id}")

        return content

    def validate_code_input(
        self,
        code: str,
        max_lines: int = 1000,
        max_chars: int = 100000,
    ) -> tuple[bool, str | None]:
        """Validate code input before generation.

        Checks code size limits to ensure reasonable generation time.

        Args:
            code: Source code to validate.
            max_lines: Maximum allowed lines (default 1000).
            max_chars: Maximum allowed characters (default 100000).

        Returns:
            Tuple of (is_valid, error_message).

        Example:
            is_valid, error = service.validate_code_input(code)
            if not is_valid:
                raise ValueError(error)
        """
        if not code or not code.strip():
            return False, "Code cannot be empty"

        lines = code.count("\n") + 1
        if lines > max_lines:
            return False, f"Code exceeds maximum line count ({lines} > {max_lines})"

        if len(code) > max_chars:
            return (
                False,
                f"Code exceeds maximum character count ({len(code)} > {max_chars})",
            )

        return True, None
