"""File storage service for uploaded code files.

This module provides the FileStorageService class which handles
file storage operations for uploaded code including:
- Saving files to the filesystem
- Reading file content
- Listing files for a task
- Deleting task files

Storage Structure:
    storage/uploads/{user_id}/{task_id}/{uuid}.{ext}

Example:
    from pathlib import Path
    from src.services.code_analysis.file_storage import FileStorageService

    storage = FileStorageService(base_path=Path("./storage"))
    file_info = storage.save_file(
        user_id=user.id,
        task_id=task.id,
        filename="main.py",
        content=b"print('hello')"
    )
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4


@dataclass
class FileInfo:
    """Information about a stored file.

    Attributes:
        original_name: The original filename from upload.
        stored_name: The UUID-based stored filename.
        path: Full path to the stored file.
        size: File size in bytes.
    """

    original_name: str
    stored_name: str
    path: Path
    size: int


class FileStorageService:
    """Service for managing uploaded code files on the filesystem.

    This service handles saving, reading, listing, and deleting files
    for code uploads. Files are stored using UUID-based names to avoid
    conflicts, with the original extension preserved.

    Storage Structure:
        {base_path}/storage/uploads/{user_id}/{task_id}/{uuid}.{ext}

    Attributes:
        base_path: Base directory for all file storage.

    Example:
        storage = FileStorageService(base_path=Path("./"))

        # Save a file
        file_info = storage.save_file(
            user_id=user_id,
            task_id=task_id,
            filename="main.py",
            content=b"print('hello')"
        )

        # Read file content
        content = storage.read_file(user_id, task_id, file_info.stored_name)

        # List all files for a task
        files = storage.list_files(user_id, task_id)

        # Delete all task files
        storage.delete_files(user_id, task_id)
    """

    def __init__(self, base_path: Path | str) -> None:
        """Initialize FileStorageService.

        Args:
            base_path: Base directory for file storage.
                Can be Path object or string path.
        """
        self.base_path = Path(base_path) if isinstance(base_path, str) else base_path

    def get_storage_dir(self, user_id: UUID, task_id: UUID) -> Path:
        """Get the storage directory path for a task.

        Args:
            user_id: UUID of the user who owns the task.
            task_id: UUID of the task.

        Returns:
            Path: Directory path for storing task files.
        """
        return self.base_path / "storage" / "uploads" / str(user_id) / str(task_id)

    def save_file(
        self,
        user_id: UUID,
        task_id: UUID,
        filename: str,
        content: bytes,
    ) -> FileInfo:
        """Save a file to storage.

        Creates the storage directory if it doesn't exist, generates a
        UUID-based filename to avoid conflicts, and saves the file content.

        Args:
            user_id: UUID of the user who owns the task.
            task_id: UUID of the task.
            filename: Original filename (used to preserve extension).
            content: File content as bytes.

        Returns:
            FileInfo: Information about the saved file.

        Example:
            file_info = storage.save_file(
                user_id=user_id,
                task_id=task_id,
                filename="main.py",
                content=b"print('hello')"
            )
            print(f"Saved to: {file_info.path}")
        """
        storage_dir = self.get_storage_dir(user_id, task_id)
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Extract extension from original filename
        original_path = Path(filename)
        extension = original_path.suffix

        # Generate UUID-based filename
        stored_name = f"{uuid4()}{extension}"
        file_path = storage_dir / stored_name

        # Write file content
        file_path.write_bytes(content)

        return FileInfo(
            original_name=filename,
            stored_name=stored_name,
            path=file_path,
            size=len(content),
        )

    def save_files(
        self,
        user_id: UUID,
        task_id: UUID,
        files: list[tuple[str, bytes]],
    ) -> list[FileInfo]:
        """Save multiple files to storage.

        Args:
            user_id: UUID of the user who owns the task.
            task_id: UUID of the task.
            files: List of (filename, content) tuples.

        Returns:
            list[FileInfo]: List of information about saved files.

        Example:
            files = [
                ("main.py", b"print('main')"),
                ("utils.py", b"def helper(): pass"),
            ]
            file_infos = storage.save_files(user_id, task_id, files)
        """
        if not files:
            return []

        return [
            self.save_file(user_id, task_id, filename, content)
            for filename, content in files
        ]

    def get_file_path(
        self,
        user_id: UUID,
        task_id: UUID,
        stored_filename: str,
    ) -> Path:
        """Get the full path for a stored file.

        Args:
            user_id: UUID of the user who owns the task.
            task_id: UUID of the task.
            stored_filename: The UUID-based stored filename.

        Returns:
            Path: Full path to the file.
        """
        return self.get_storage_dir(user_id, task_id) / stored_filename

    def list_files(self, user_id: UUID, task_id: UUID) -> list[Path]:
        """List all files in a task's storage directory.

        Args:
            user_id: UUID of the user who owns the task.
            task_id: UUID of the task.

        Returns:
            list[Path]: List of file paths in the task directory.
                Empty list if directory doesn't exist.
        """
        storage_dir = self.get_storage_dir(user_id, task_id)
        if not storage_dir.exists():
            return []
        return list(storage_dir.iterdir())

    def delete_files(self, user_id: UUID, task_id: UUID) -> None:
        """Delete all files for a task.

        Removes the entire task storage directory and all its contents.
        Does nothing if the directory doesn't exist.

        Args:
            user_id: UUID of the user who owns the task.
            task_id: UUID of the task.
        """
        storage_dir = self.get_storage_dir(user_id, task_id)
        if storage_dir.exists():
            shutil.rmtree(storage_dir)

    def read_file(
        self,
        user_id: UUID,
        task_id: UUID,
        stored_filename: str,
    ) -> bytes:
        """Read file content.

        Args:
            user_id: UUID of the user who owns the task.
            task_id: UUID of the task.
            stored_filename: The UUID-based stored filename.

        Returns:
            bytes: File content.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        file_path = self.get_file_path(user_id, task_id, stored_filename)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {stored_filename}")
        return file_path.read_bytes()
