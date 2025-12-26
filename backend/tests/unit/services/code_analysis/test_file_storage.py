"""Unit tests for FileStorageService.

This module tests the file storage service that manages uploaded code files.
Storage path format: storage/uploads/{user_id}/{task_id}/{uuid}.{ext}

TDD Approach:
- RED: Write failing tests first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code quality
"""

from pathlib import Path
from uuid import uuid4

import pytest

from src.services.code_analysis.file_storage import FileStorageService


class TestFileStorageServiceInit:
    """Test FileStorageService initialization."""

    def test_init_with_path_object(self, tmp_path: Path) -> None:
        """Should accept Path object as base_path."""
        storage = FileStorageService(base_path=tmp_path)
        assert storage.base_path == tmp_path

    def test_init_with_string_path(self, tmp_path: Path) -> None:
        """Should accept string as base_path and convert to Path."""
        storage = FileStorageService(base_path=str(tmp_path))
        assert storage.base_path == tmp_path


class TestFileStorageServiceGetStorageDir:
    """Test get_storage_dir method."""

    def test_get_storage_dir_returns_correct_path(self, tmp_path: Path) -> None:
        """Should return path: base_path/storage/uploads/{user_id}/{task_id}/."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()

        result = storage.get_storage_dir(user_id, task_id)

        expected = tmp_path / "storage" / "uploads" / str(user_id) / str(task_id)
        assert result == expected


class TestFileStorageServiceSaveFile:
    """Test save_file method."""

    def test_save_file_creates_directory_if_not_exists(self, tmp_path: Path) -> None:
        """Should create storage directory automatically."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()
        content = b"print('hello world')"
        filename = "main.py"

        storage.save_file(
            user_id=user_id,
            task_id=task_id,
            filename=filename,
            content=content,
        )

        storage_dir = storage.get_storage_dir(user_id, task_id)
        assert storage_dir.exists()

    def test_save_file_creates_file_with_content(self, tmp_path: Path) -> None:
        """Should save file with correct content."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()
        content = b"print('hello world')"
        filename = "main.py"

        file_info = storage.save_file(
            user_id=user_id,
            task_id=task_id,
            filename=filename,
            content=content,
        )

        assert file_info.path.exists()
        assert file_info.path.read_bytes() == content

    def test_save_file_preserves_extension(self, tmp_path: Path) -> None:
        """Should preserve the original file extension."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()
        content = b"function hello() {}"
        filename = "script.js"

        file_info = storage.save_file(
            user_id=user_id,
            task_id=task_id,
            filename=filename,
            content=content,
        )

        assert file_info.path.suffix == ".js"

    def test_save_file_uses_uuid_for_stored_name(self, tmp_path: Path) -> None:
        """Should use UUID for stored filename to avoid conflicts."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()
        content = b"test content"
        filename = "test.py"

        file_info = storage.save_file(
            user_id=user_id,
            task_id=task_id,
            filename=filename,
            content=content,
        )

        # Filename should be a UUID, not the original name
        assert file_info.path.stem != "test"
        # Should be a valid UUID format (36 chars with hyphens)
        assert len(file_info.path.stem) == 36

    def test_save_file_returns_file_info(self, tmp_path: Path) -> None:
        """Should return FileInfo with original name, stored name, and path."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()
        content = b"test content"
        filename = "original.py"

        result = storage.save_file(
            user_id=user_id,
            task_id=task_id,
            filename=filename,
            content=content,
        )

        assert result.original_name == "original.py"
        assert result.stored_name.endswith(".py")
        assert result.path.exists()
        assert result.size == len(content)


class TestFileStorageServiceSaveFiles:
    """Test save_files method for batch file saving."""

    def test_save_files_empty_list_returns_empty(self, tmp_path: Path) -> None:
        """Should return empty list for empty input."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()

        result = storage.save_files(user_id=user_id, task_id=task_id, files=[])

        assert result == []

    def test_save_files_saves_multiple_files(self, tmp_path: Path) -> None:
        """Should save all files and return list of FileInfo."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()
        files = [
            ("main.py", b"print('main')"),
            ("helper.py", b"def helper(): pass"),
            ("utils.js", b"function util() {}"),
        ]

        results = storage.save_files(user_id=user_id, task_id=task_id, files=files)

        assert len(results) == 3
        for file_info in results:
            assert file_info.path.exists()


class TestFileStorageServiceGetFilePath:
    """Test get_file_path method."""

    def test_get_file_path_returns_correct_path(self, tmp_path: Path) -> None:
        """Should return full path for stored filename."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()
        stored_filename = "abc123.py"

        result = storage.get_file_path(user_id, task_id, stored_filename)

        expected = (
            tmp_path
            / "storage"
            / "uploads"
            / str(user_id)
            / str(task_id)
            / stored_filename
        )
        assert result == expected


class TestFileStorageServiceListFiles:
    """Test list_files method."""

    def test_list_files_empty_directory_returns_empty(self, tmp_path: Path) -> None:
        """Should return empty list for non-existent directory."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()

        result = storage.list_files(user_id, task_id)

        assert result == []

    def test_list_files_returns_all_files(self, tmp_path: Path) -> None:
        """Should return all files in the task directory."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()

        # Save some files first
        storage.save_file(user_id, task_id, "a.py", b"a")
        storage.save_file(user_id, task_id, "b.py", b"b")
        storage.save_file(user_id, task_id, "c.js", b"c")

        result = storage.list_files(user_id, task_id)

        assert len(result) == 3


class TestFileStorageServiceDeleteFiles:
    """Test delete_files method."""

    def test_delete_files_removes_directory(self, tmp_path: Path) -> None:
        """Should remove entire task storage directory."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()

        # Save a file first
        storage.save_file(user_id, task_id, "test.py", b"test")
        storage_dir = storage.get_storage_dir(user_id, task_id)
        assert storage_dir.exists()

        # Delete all files
        storage.delete_files(user_id, task_id)

        assert not storage_dir.exists()

    def test_delete_files_nonexistent_directory_no_error(
        self, tmp_path: Path
    ) -> None:
        """Should not raise error for non-existent directory."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()

        # Should not raise
        storage.delete_files(user_id, task_id)


class TestFileStorageServiceReadFile:
    """Test read_file method."""

    def test_read_file_returns_content(self, tmp_path: Path) -> None:
        """Should read and return file content."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()
        content = b"print('hello')"

        file_info = storage.save_file(user_id, task_id, "test.py", content)
        result = storage.read_file(user_id, task_id, file_info.stored_name)

        assert result == content

    def test_read_file_not_found_raises_error(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for non-existent file."""
        storage = FileStorageService(base_path=tmp_path)
        user_id = uuid4()
        task_id = uuid4()

        with pytest.raises(FileNotFoundError):
            storage.read_file(user_id, task_id, "nonexistent.py")
