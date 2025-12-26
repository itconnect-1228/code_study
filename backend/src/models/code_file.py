"""CodeFile model for individual files within uploaded code.

This module defines the CodeFile SQLAlchemy model which represents
individual code files within an uploaded code set.

The model corresponds to the 'code_files' table in PostgreSQL and includes:
- UUID primary key for distributed system compatibility
- Many-to-one relationship with UploadedCode
- File metadata (name, path, extension, size, MIME type)
- Storage path for filesystem/S3 location

Example:
    from backend.src.models import CodeFile
    from backend.src.db import get_session_context

    async with get_session_context() as session:
        code_file = CodeFile(
            uploaded_code_id=uploaded_code.id,
            file_name="main.py",
            file_extension=".py",
            file_size_bytes=1024,
            storage_path="storage/uploads/user123/task456/file789.py"
        )
        session.add(code_file)
        await session.commit()
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


# Supported file extensions per FR-015
SUPPORTED_EXTENSIONS = (
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".html",
    ".css",
    ".java",
    ".cpp",
    ".c",
    ".txt",
    ".md",
)


class CodeFile(Base):
    """Individual code file within an uploaded code set.

    Represents a single file that was uploaded as part of a code upload.
    Stores file metadata and the path to the actual file in storage.

    Attributes:
        id: Unique identifier (UUID v4, auto-generated).
        uploaded_code_id: Foreign key to the parent UploadedCode.
        file_name: Original filename as uploaded by user.
        file_path: Relative path within folder structure (for folder uploads).
        file_extension: File extension for validation (e.g., '.py', '.js').
        file_size_bytes: Individual file size in bytes.
        storage_path: Actual path on filesystem/S3 where file is stored.
        mime_type: MIME type for validation (e.g., 'text/x-python').
        created_at: File upload timestamp (UTC, auto-set).

    Table Constraints:
        - File extension must be one of the supported extensions (PostgreSQL CHECK)
        - UploadedCode foreign key with CASCADE delete
        - Storage path is required (NOT NULL)
        - File name is required (NOT NULL)

    Indexes:
        - idx_code_files_uploaded_code_id: Fast lookup by uploaded code

    Relationships:
        - Belongs to UploadedCode (many-to-one)

    Business Rules:
        - Only supported extensions allowed (FR-015)
        - Binary files rejected (FR-016)
        - 1-20 files per upload (FR-018)
        - Storage path format: storage/uploads/{user_id}/{task_id}/{uuid}.{ext}

    Example:
        code_file = CodeFile(
            uploaded_code_id=uploaded_code.id,
            file_name="hello.py",
            file_path="src/hello.py",  # For folder uploads
            file_extension=".py",
            file_size_bytes=256,
            storage_path="storage/uploads/abc123/def456/ghi789.py",
            mime_type="text/x-python"
        )
    """

    __tablename__ = "code_files"

    # Primary key - UUID for security and distributed compatibility
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    # UploadedCode relationship (many-to-one)
    uploaded_code_id: Mapped[UUID] = mapped_column(
        ForeignKey("uploaded_code.id", ondelete="CASCADE"),
        nullable=False,
        index=False,  # We define index separately for naming
    )

    # File metadata
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    file_extension: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )
    file_size_bytes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    # Storage location
    storage_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )

    # Timestamp field (TIMESTAMP WITH TIME ZONE for PostgreSQL)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    # Relationship to UploadedCode (for eager loading if needed)
    uploaded_code = relationship("UploadedCode", back_populates="code_files")

    # Table-level constraints and indexes
    __table_args__ = (
        # File extension must be supported (FR-015)
        CheckConstraint(
            "file_extension IS NULL OR file_extension IN ("
            "'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', "
            "'.java', '.cpp', '.c', '.txt', '.md')",
            name="supported_extension",
        ),
        # Index for uploaded code lookup
        Index("idx_code_files_uploaded_code_id", "uploaded_code_id"),
    )

    def __repr__(self) -> str:
        """Return string representation for debugging.

        Returns:
            str: CodeFile representation with id, file_name, and extension.
        """
        return f"<CodeFile(id={self.id}, file_name={self.file_name!r}, ext={self.file_extension!r})>"

    @property
    def is_extension_valid(self) -> bool:
        """Check if file extension is in the supported list.

        Returns:
            bool: True if extension is valid (or not set), False otherwise.
        """
        if self.file_extension is None:
            return True
        return self.file_extension in SUPPORTED_EXTENSIONS

    @property
    def size_kb(self) -> float | None:
        """Get file size in kilobytes.

        Returns:
            float | None: Size in KB, or None if file_size_bytes is not set.
        """
        if self.file_size_bytes is None:
            return None
        return self.file_size_bytes / 1024

    def validate_extension(self) -> None:
        """Validate file extension and raise error if not supported.

        Raises:
            ValueError: If file_extension is not in the supported list.
        """
        if self.file_extension is not None and self.file_extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"File extension '{self.file_extension}' is not supported. "
                f"Allowed extensions: {', '.join(SUPPORTED_EXTENSIONS)} (FR-015)"
            )
