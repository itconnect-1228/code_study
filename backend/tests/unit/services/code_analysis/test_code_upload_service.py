"""Unit tests for CodeUploadService.

This module tests the code upload service which handles file/folder/paste
uploads with language detection and complexity analysis.

TDD Approach:
- RED: Write failing tests first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code quality
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.code_file import CodeFile
from src.models.project import Project
from src.models.task import Task
from src.models.uploaded_code import UploadedCode
from src.models.user import User
from src.services.code_analysis.code_upload_service import (
    CodeUploadService,
    UploadResult,
)
from src.services.code_analysis.file_storage import FileInfo, FileStorageService


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
    )
    db_session.add(project)
    await db_session.commit()
    return project


@pytest_asyncio.fixture
async def task(db_session: AsyncSession, project: Project) -> Task:
    """Create a test task."""
    task = Task(
        project_id=project.id,
        task_number=1,
        title="Test Task Title",
        upload_method="file",
    )
    db_session.add(task)
    await db_session.commit()
    return task


@pytest.fixture
def storage_service(tmp_path: Path) -> FileStorageService:
    """Create a FileStorageService instance."""
    return FileStorageService(base_path=tmp_path)


@pytest.fixture
def upload_service(
    db_session: AsyncSession,
    storage_service: FileStorageService,
) -> CodeUploadService:
    """Create a CodeUploadService instance."""
    return CodeUploadService(db=db_session, storage=storage_service)


class TestCodeUploadServiceUploadFile:
    """Test single file upload."""

    @pytest.mark.asyncio
    async def test_upload_file_creates_uploaded_code(
        self,
        upload_service: CodeUploadService,
        user: User,
        task: Task,
    ) -> None:
        """Should create UploadedCode record."""
        content = b"print('hello world')"
        filename = "main.py"

        result = await upload_service.upload_file(
            user_id=user.id,
            task_id=task.id,
            filename=filename,
            content=content,
        )

        assert result.uploaded_code is not None
        assert result.uploaded_code.task_id == task.id

    @pytest.mark.asyncio
    async def test_upload_file_creates_code_file(
        self,
        upload_service: CodeUploadService,
        user: User,
        task: Task,
    ) -> None:
        """Should create CodeFile record."""
        content = b"print('hello world')"
        filename = "main.py"

        result = await upload_service.upload_file(
            user_id=user.id,
            task_id=task.id,
            filename=filename,
            content=content,
        )

        assert len(result.code_files) == 1
        assert result.code_files[0].file_name == "main.py"

    @pytest.mark.asyncio
    async def test_upload_file_detects_language(
        self,
        upload_service: CodeUploadService,
        user: User,
        task: Task,
    ) -> None:
        """Should detect programming language."""
        content = b"def hello(): pass"
        filename = "main.py"

        result = await upload_service.upload_file(
            user_id=user.id,
            task_id=task.id,
            filename=filename,
            content=content,
        )

        assert result.uploaded_code.detected_language == "python"

    @pytest.mark.asyncio
    async def test_upload_file_calculates_complexity(
        self,
        upload_service: CodeUploadService,
        user: User,
        task: Task,
    ) -> None:
        """Should calculate code complexity."""
        content = b"x = 1\ny = 2\nz = x + y"
        filename = "simple.py"

        result = await upload_service.upload_file(
            user_id=user.id,
            task_id=task.id,
            filename=filename,
            content=content,
        )

        assert result.uploaded_code.complexity_level is not None
        assert result.uploaded_code.total_lines == 3


class TestCodeUploadServiceUploadFiles:
    """Test multiple file upload."""

    @pytest.mark.asyncio
    async def test_upload_files_creates_multiple_code_files(
        self,
        upload_service: CodeUploadService,
        user: User,
        task: Task,
    ) -> None:
        """Should create CodeFile for each uploaded file."""
        files = [
            ("main.py", b"print('main')"),
            ("utils.py", b"def helper(): pass"),
            ("config.py", b"DEBUG = True"),
        ]

        result = await upload_service.upload_files(
            user_id=user.id,
            task_id=task.id,
            files=files,
        )

        assert len(result.code_files) == 3

    @pytest.mark.asyncio
    async def test_upload_files_calculates_total_size(
        self,
        upload_service: CodeUploadService,
        user: User,
        task: Task,
    ) -> None:
        """Should calculate total upload size."""
        files = [
            ("a.py", b"x = 1"),  # 5 bytes
            ("b.py", b"y = 2"),  # 5 bytes
        ]

        result = await upload_service.upload_files(
            user_id=user.id,
            task_id=task.id,
            files=files,
        )

        assert result.uploaded_code.upload_size_bytes == 10


class TestCodeUploadServiceUploadPaste:
    """Test paste code upload."""

    @pytest.mark.asyncio
    async def test_upload_paste_creates_single_file(
        self,
        upload_service: CodeUploadService,
        user: User,
        task: Task,
    ) -> None:
        """Should create single CodeFile for pasted code."""
        code = "print('hello world')"

        result = await upload_service.upload_paste(
            user_id=user.id,
            task_id=task.id,
            code=code,
            language="python",
        )

        assert len(result.code_files) == 1
        assert result.uploaded_code.detected_language == "python"

    @pytest.mark.asyncio
    async def test_upload_paste_uses_provided_language(
        self,
        upload_service: CodeUploadService,
        user: User,
        task: Task,
    ) -> None:
        """Should use provided language instead of detection."""
        code = "console.log('hello')"

        result = await upload_service.upload_paste(
            user_id=user.id,
            task_id=task.id,
            code=code,
            language="javascript",
        )

        assert result.uploaded_code.detected_language == "javascript"

    @pytest.mark.asyncio
    async def test_upload_paste_generates_filename_from_language(
        self,
        upload_service: CodeUploadService,
        user: User,
        task: Task,
    ) -> None:
        """Should generate filename based on language."""
        code = "x = 1"

        result = await upload_service.upload_paste(
            user_id=user.id,
            task_id=task.id,
            code=code,
            language="python",
        )

        assert result.code_files[0].file_name.endswith(".py")


class TestCodeUploadServiceUploadFolder:
    """Test folder upload with structure preservation."""

    @pytest.mark.asyncio
    async def test_upload_folder_preserves_relative_paths(
        self,
        upload_service: CodeUploadService,
        user: User,
        task: Task,
    ) -> None:
        """Should preserve relative paths for folder structure."""
        files = [
            ("src/main.py", b"print('main')"),
            ("src/utils/helper.py", b"def helper(): pass"),
            ("tests/test_main.py", b"def test_main(): pass"),
        ]

        result = await upload_service.upload_folder(
            user_id=user.id,
            task_id=task.id,
            files=files,
        )

        filenames = [cf.file_name for cf in result.code_files]
        assert "src/main.py" in filenames
        assert "src/utils/helper.py" in filenames


class TestUploadResult:
    """Test UploadResult dataclass."""

    def test_upload_result_has_required_fields(self) -> None:
        """UploadResult should have uploaded_code and code_files."""
        uploaded_code = MagicMock(spec=UploadedCode)
        code_files = [MagicMock(spec=CodeFile)]

        result = UploadResult(
            uploaded_code=uploaded_code,
            code_files=code_files,
        )

        assert result.uploaded_code == uploaded_code
        assert result.code_files == code_files
