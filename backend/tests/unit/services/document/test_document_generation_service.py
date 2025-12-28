"""Unit tests for DocumentGenerationService.

This module tests the document generation service which handles
AI-powered learning document generation with retry logic.

TDD Approach:
- RED: Write failing tests first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code quality

Test Categories:
1. Document creation and retrieval
2. Generation flow with mocked AI
3. Retry logic for failures
4. Content validation
5. Status tracking
"""

import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.learning_document import LearningDocument
from src.models.project import Project
from src.models.task import Task
from src.models.user import User
from src.services.ai.gemini_client import (
    ContentType,
    GeminiClient,
    GeminiError,
    GeminiRateLimitError,
    GeminiResponse,
    GeminiTimeoutError,
)
from src.services.document.document_generation_service import (
    DocumentAlreadyExistsError,
    DocumentGenerationError,
    DocumentGenerationService,
    DocumentValidationError,
    GenerationConfig,
)


# Sample valid 7-chapter document content for tests
VALID_DOCUMENT_CONTENT = {
    "chapter1": {
        "title": "이 코드가 하는 일",
        "summary": "이 코드는 두 숫자를 더하는 함수입니다.",
    },
    "chapter2": {
        "title": "시작하기 전에",
        "concepts": [
            {
                "name": "변수",
                "explanation": "값을 저장하는 상자입니다.",
                "analogy": "이름표가 붙은 상자와 같습니다.",
                "example": "x = 5",
                "use_cases": "데이터를 저장할 때 사용합니다.",
            },
            {
                "name": "함수",
                "explanation": "특정 작업을 수행하는 코드 묶음입니다.",
                "analogy": "레시피와 같습니다.",
                "example": "def add(a, b): return a + b",
                "use_cases": "반복되는 작업을 묶을 때 사용합니다.",
            },
        ],
    },
    "chapter3": {
        "title": "코드 구조",
        "flowchart": "입력 → 처리 → 출력",
        "file_breakdown": {
            "main_section": "메인 함수",
            "components": [{"name": "add", "purpose": "덧셈 수행"}],
        },
        "connections": "함수가 순서대로 실행됩니다.",
    },
    "chapter4": {
        "title": "줄별 설명",
        "explanations": [
            {
                "lines": "1",
                "code": "def add(a, b):",
                "what_it_does": "add라는 이름의 함수를 정의합니다.",
                "syntax_breakdown": {"def": "함수 정의 키워드"},
                "analogy": "레시피의 제목을 쓰는 것과 같습니다.",
                "alternatives": "lambda를 사용할 수도 있습니다.",
                "notes": "함수 이름은 의미있게 짓는 것이 좋습니다.",
            },
        ],
    },
    "chapter5": {
        "title": "실행 과정",
        "steps": [
            {
                "step_number": 1,
                "what_happens": "함수가 호출됩니다.",
                "current_values": {"a": 2, "b": 3},
                "why_it_matters": "계산을 시작합니다.",
            },
        ],
    },
    "chapter6": {
        "title": "배운 핵심 개념",
        "concepts": [
            {
                "name": "함수 정의",
                "what_it_is": "재사용 가능한 코드 블록을 만드는 방법",
                "why_used": "코드 재사용성을 높이기 위해",
                "where_applied": "모든 프로그램에서",
                "in_this_code": "add 함수로 구현됨",
            },
        ],
    },
    "chapter7": {
        "title": "흔한 실수 피하기",
        "mistakes": [
            {
                "mistake": "return 문 빼먹기",
                "wrong_code": "def add(a, b): a + b",
                "right_code": "def add(a, b): return a + b",
                "why_it_matters": "결과가 반환되지 않습니다.",
                "how_to_fix": "return 키워드를 추가하세요.",
            },
            {
                "mistake": "들여쓰기 오류",
                "wrong_code": "def add(a, b):\nreturn a + b",
                "right_code": "def add(a, b):\n    return a + b",
                "why_it_matters": "문법 오류가 발생합니다.",
                "how_to_fix": "4칸 들여쓰기를 사용하세요.",
            },
            {
                "mistake": "콜론 빼먹기",
                "wrong_code": "def add(a, b)",
                "right_code": "def add(a, b):",
                "why_it_matters": "함수 정의가 올바르지 않습니다.",
                "how_to_fix": "함수 정의 끝에 콜론을 추가하세요.",
            },
        ],
    },
}


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def project(db_session: AsyncSession, user: User) -> Project:
    """Create a test project."""
    project = Project(
        user_id=user.id,
        title="Test Project",
        description="Test project description",
    )
    db_session.add(project)
    await db_session.commit()
    return project


@pytest_asyncio.fixture
async def task(db_session: AsyncSession, project: Project) -> Task:
    """Create a test task."""
    task = Task(
        project_id=project.id,
        title="Test Task for Document",
        task_number=1,
        upload_method="paste",
    )
    db_session.add(task)
    await db_session.commit()
    return task


@pytest.fixture
def mock_gemini_client() -> MagicMock:
    """Create a mock GeminiClient."""
    client = MagicMock(spec=GeminiClient)
    return client


@pytest.fixture
def mock_gemini_response() -> GeminiResponse:
    """Create a mock successful Gemini response."""
    return GeminiResponse(
        content=json.dumps(VALID_DOCUMENT_CONTENT),
        json_content=VALID_DOCUMENT_CONTENT,
        usage={"prompt_tokens": 100, "completion_tokens": 500, "total_tokens": 600},
        model="gemini-2.5-flash",
        finish_reason="STOP",
        latency_ms=1500.0,
    )


@pytest_asyncio.fixture
def document_service(
    db_session: AsyncSession,
    mock_gemini_client: MagicMock,
) -> DocumentGenerationService:
    """Create a DocumentGenerationService with mocked AI."""
    return DocumentGenerationService(
        db=db_session,
        gemini_client=mock_gemini_client,
        config=GenerationConfig(max_retries=2, base_delay=0.1),
    )


class TestDocumentGenerationServiceCreate:
    """Test DocumentGenerationService document creation."""

    @pytest.mark.asyncio
    async def test_generate_document_creates_learning_document(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        mock_gemini_response: GeminiResponse,
        task: Task,
    ) -> None:
        """Should create a LearningDocument for the task."""
        mock_gemini_client.generate = AsyncMock(return_value=mock_gemini_response)

        document = await document_service.generate_document(
            task_id=task.id,
            code="def add(a, b): return a + b",
            language="Python",
        )

        assert document is not None
        assert document.task_id == task.id
        assert document.generation_status == "completed"

    @pytest.mark.asyncio
    async def test_generate_document_stores_content(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        mock_gemini_response: GeminiResponse,
        task: Task,
    ) -> None:
        """Should store the generated content in the document."""
        mock_gemini_client.generate = AsyncMock(return_value=mock_gemini_response)

        document = await document_service.generate_document(
            task_id=task.id,
            code="def add(a, b): return a + b",
            language="Python",
        )

        assert document.content is not None
        assert "chapter1" in document.content
        assert "chapter7" in document.content
        assert document.has_content is True

    @pytest.mark.asyncio
    async def test_generate_document_tracks_timestamps(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        mock_gemini_response: GeminiResponse,
        task: Task,
    ) -> None:
        """Should track generation timestamps."""
        mock_gemini_client.generate = AsyncMock(return_value=mock_gemini_response)

        document = await document_service.generate_document(
            task_id=task.id,
            code="def add(a, b): return a + b",
            language="Python",
        )

        assert document.generation_started_at is not None
        assert document.generation_completed_at is not None
        assert document.generation_completed_at >= document.generation_started_at

    @pytest.mark.asyncio
    async def test_generate_document_raises_for_nonexistent_task(
        self,
        document_service: DocumentGenerationService,
    ) -> None:
        """Should raise ValueError for non-existent task."""
        with pytest.raises(ValueError, match="not found"):
            await document_service.generate_document(
                task_id=uuid4(),
                code="def add(a, b): return a + b",
                language="Python",
            )


class TestDocumentGenerationServiceRetry:
    """Test DocumentGenerationService retry logic."""

    @pytest.mark.asyncio
    async def test_retries_on_rate_limit_error(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        mock_gemini_response: GeminiResponse,
        task: Task,
    ) -> None:
        """Should retry when rate limit error occurs."""
        # First call raises rate limit, second succeeds
        mock_gemini_client.generate = AsyncMock(
            side_effect=[
                GeminiRateLimitError("Rate limit exceeded"),
                mock_gemini_response,
            ]
        )

        document = await document_service.generate_document(
            task_id=task.id,
            code="def add(a, b): return a + b",
            language="Python",
        )

        assert document.generation_status == "completed"
        assert mock_gemini_client.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_timeout_error(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        mock_gemini_response: GeminiResponse,
        task: Task,
    ) -> None:
        """Should retry when timeout error occurs."""
        mock_gemini_client.generate = AsyncMock(
            side_effect=[
                GeminiTimeoutError("Request timed out"),
                mock_gemini_response,
            ]
        )

        document = await document_service.generate_document(
            task_id=task.id,
            code="def add(a, b): return a + b",
            language="Python",
        )

        assert document.generation_status == "completed"

    @pytest.mark.asyncio
    async def test_fails_after_max_retries(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        task: Task,
    ) -> None:
        """Should fail after max retries exceeded."""
        mock_gemini_client.generate = AsyncMock(
            side_effect=GeminiError("Persistent error")
        )

        with pytest.raises(DocumentGenerationError, match="failed after"):
            await document_service.generate_document(
                task_id=task.id,
                code="def add(a, b): return a + b",
                language="Python",
            )

        # Verify document is marked as failed
        document = await document_service.get_document_by_task(task.id)
        assert document is not None
        assert document.generation_status == "failed"
        assert document.generation_error is not None


class TestDocumentGenerationServiceValidation:
    """Test DocumentGenerationService content validation."""

    @pytest.mark.asyncio
    async def test_validates_required_chapters(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        task: Task,
    ) -> None:
        """Should reject content missing required chapters."""
        incomplete_content = {"chapter1": {"title": "Test"}}
        mock_gemini_client.generate = AsyncMock(
            return_value=GeminiResponse(
                content=json.dumps(incomplete_content),
                latency_ms=100.0,
            )
        )

        with pytest.raises(DocumentValidationError, match="Missing required chapters"):
            await document_service.generate_document(
                task_id=task.id,
                code="def add(a, b): return a + b",
                language="Python",
            )

    @pytest.mark.asyncio
    async def test_validates_chapter_structure(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        task: Task,
    ) -> None:
        """Should reject content with invalid chapter structure."""
        invalid_content = {
            f"chapter{i}": {"title": f"Chapter {i}"}
            for i in range(1, 8)
        }
        # Chapter 2 needs concepts array
        invalid_content["chapter2"] = {"title": "Test"}  # Missing concepts

        mock_gemini_client.generate = AsyncMock(
            return_value=GeminiResponse(
                content=json.dumps(invalid_content),
                latency_ms=100.0,
            )
        )

        with pytest.raises(DocumentValidationError, match="concepts"):
            await document_service.generate_document(
                task_id=task.id,
                code="def add(a, b): return a + b",
                language="Python",
            )


class TestDocumentGenerationServiceStatus:
    """Test DocumentGenerationService status tracking."""

    @pytest.mark.asyncio
    async def test_get_generation_status_not_found(
        self,
        document_service: DocumentGenerationService,
    ) -> None:
        """Should return not_found for non-existent document."""
        status = await document_service.get_generation_status(uuid4())
        assert status["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_get_generation_status_completed(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        mock_gemini_response: GeminiResponse,
        task: Task,
    ) -> None:
        """Should return completed status after successful generation."""
        mock_gemini_client.generate = AsyncMock(return_value=mock_gemini_response)

        await document_service.generate_document(
            task_id=task.id,
            code="def add(a, b): return a + b",
            language="Python",
        )

        status = await document_service.get_generation_status(task.id)
        assert status["status"] == "completed"
        assert status["started_at"] is not None
        assert status["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_get_generation_status_failed(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        task: Task,
    ) -> None:
        """Should return failed status with error message."""
        mock_gemini_client.generate = AsyncMock(
            side_effect=GeminiError("Test error")
        )

        with pytest.raises(DocumentGenerationError):
            await document_service.generate_document(
                task_id=task.id,
                code="def add(a, b): return a + b",
                language="Python",
            )

        status = await document_service.get_generation_status(task.id)
        assert status["status"] == "failed"
        assert "error" in status


class TestDocumentGenerationServiceRetryFailed:
    """Test DocumentGenerationService retry_failed_document."""

    @pytest.mark.asyncio
    async def test_retry_failed_document_succeeds(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        mock_gemini_response: GeminiResponse,
        task: Task,
    ) -> None:
        """Should successfully retry a failed document."""
        # First attempt fails
        mock_gemini_client.generate = AsyncMock(
            side_effect=GeminiError("First error")
        )

        with pytest.raises(DocumentGenerationError):
            await document_service.generate_document(
                task_id=task.id,
                code="def add(a, b): return a + b",
                language="Python",
            )

        # Verify failed status
        document = await document_service.get_document_by_task(task.id)
        assert document.is_failed

        # Retry succeeds
        mock_gemini_client.generate = AsyncMock(return_value=mock_gemini_response)

        document = await document_service.retry_failed_document(
            task_id=task.id,
            code="def add(a, b): return a + b",
            language="Python",
        )

        assert document.is_completed
        assert document.has_content

    @pytest.mark.asyncio
    async def test_retry_non_failed_document_raises(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        mock_gemini_response: GeminiResponse,
        task: Task,
    ) -> None:
        """Should raise error when retrying non-failed document."""
        mock_gemini_client.generate = AsyncMock(return_value=mock_gemini_response)

        await document_service.generate_document(
            task_id=task.id,
            code="def add(a, b): return a + b",
            language="Python",
        )

        with pytest.raises(ValueError, match="not in failed state"):
            await document_service.retry_failed_document(
                task_id=task.id,
                code="def add(a, b): return a + b",
                language="Python",
            )


class TestDocumentGenerationServiceDuplicate:
    """Test DocumentGenerationService duplicate handling."""

    @pytest.mark.asyncio
    async def test_raises_for_existing_completed_document(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        mock_gemini_response: GeminiResponse,
        task: Task,
    ) -> None:
        """Should raise error when document already exists."""
        mock_gemini_client.generate = AsyncMock(return_value=mock_gemini_response)

        # First generation succeeds
        await document_service.generate_document(
            task_id=task.id,
            code="def add(a, b): return a + b",
            language="Python",
        )

        # Second attempt should fail
        with pytest.raises(DocumentAlreadyExistsError):
            await document_service.generate_document(
                task_id=task.id,
                code="def add(a, b): return a + b",
                language="Python",
            )


class TestDocumentGenerationServiceInputValidation:
    """Test DocumentGenerationService input validation."""

    def test_validate_code_input_empty(
        self,
        document_service: DocumentGenerationService,
    ) -> None:
        """Should reject empty code."""
        is_valid, error = document_service.validate_code_input("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_code_input_too_many_lines(
        self,
        document_service: DocumentGenerationService,
    ) -> None:
        """Should reject code with too many lines."""
        code = "\n".join(["x = 1"] * 2000)
        is_valid, error = document_service.validate_code_input(code, max_lines=1000)
        assert is_valid is False
        assert "line count" in error.lower()

    def test_validate_code_input_valid(
        self,
        document_service: DocumentGenerationService,
    ) -> None:
        """Should accept valid code."""
        code = "def add(a, b): return a + b"
        is_valid, error = document_service.validate_code_input(code)
        assert is_valid is True
        assert error is None


class TestDocumentGenerationServiceJsonParsing:
    """Test DocumentGenerationService JSON parsing."""

    @pytest.mark.asyncio
    async def test_handles_json_with_markdown_blocks(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        task: Task,
    ) -> None:
        """Should handle JSON wrapped in markdown code blocks."""
        wrapped_content = f"```json\n{json.dumps(VALID_DOCUMENT_CONTENT)}\n```"
        mock_gemini_client.generate = AsyncMock(
            return_value=GeminiResponse(
                content=wrapped_content,
                latency_ms=100.0,
            )
        )

        document = await document_service.generate_document(
            task_id=task.id,
            code="def add(a, b): return a + b",
            language="Python",
        )

        assert document.is_completed
        assert document.has_content

    @pytest.mark.asyncio
    async def test_retries_on_json_parse_error(
        self,
        db_session: AsyncSession,
        document_service: DocumentGenerationService,
        mock_gemini_client: MagicMock,
        mock_gemini_response: GeminiResponse,
        task: Task,
    ) -> None:
        """Should retry when JSON parsing fails."""
        mock_gemini_client.generate = AsyncMock(
            side_effect=[
                GeminiResponse(content="invalid json {", latency_ms=100.0),
                mock_gemini_response,
            ]
        )

        document = await document_service.generate_document(
            task_id=task.id,
            code="def add(a, b): return a + b",
            language="Python",
        )

        assert document.is_completed
        assert mock_gemini_client.generate.call_count == 2
