"""UploadedCode model for code metadata within tasks.

This module defines the UploadedCode SQLAlchemy model which stores
metadata and analysis results for code uploaded by users.

The model corresponds to the 'uploaded_code' table in PostgreSQL and includes:
- UUID primary key for distributed system compatibility
- One-to-one relationship with Task via unique foreign key
- Code analysis metadata (language, complexity, line count)
- Upload size tracking with 10MB limit enforcement

Example:
    from backend.src.models import UploadedCode
    from backend.src.db import get_session_context

    async with get_session_context() as session:
        uploaded_code = UploadedCode(
            task_id=task.id,
            detected_language="python",
            complexity_level="beginner",
            total_lines=50,
            total_files=1,
            upload_size_bytes=1024
        )
        session.add(uploaded_code)
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class UploadedCode(Base):
    """Code upload metadata for a task.

    Represents the uploaded code associated with a single task.
    Stores metadata from code analysis including language detection
    and complexity assessment.

    Attributes:
        id: Unique identifier (UUID v4, auto-generated).
        task_id: Foreign key to the owning task (one-to-one, unique).
        detected_language: Programming language detected (e.g., 'python', 'javascript').
        complexity_level: Code complexity assessment ('beginner', 'intermediate', 'advanced').
        total_lines: Total lines of code across all files.
        total_files: Number of files uploaded.
        upload_size_bytes: Total size in bytes (max 10MB = 10,485,760 bytes).
        created_at: Upload timestamp (UTC, auto-set).

    Table Constraints:
        - Complexity level must be 'beginner', 'intermediate', or 'advanced' (PostgreSQL CHECK)
        - Upload size must not exceed 10MB (PostgreSQL CHECK)
        - Task ID must be unique (one uploaded code per task)
        - Task foreign key with CASCADE delete

    Indexes:
        - idx_uploaded_code_task_id: Fast lookup by task

    Relationships:
        - Belongs to Task (one-to-one via unique task_id)
        - Has many CodeFiles (will be defined in CodeFile model)

    Business Rules:
        - Maximum upload size 10MB (FR-014)
        - One uploaded code per task
        - Permanently deleted when task is permanently deleted

    Example:
        uploaded_code = UploadedCode(
            task_id=task.id,
            detected_language="python",
            complexity_level="beginner",
            total_lines=100,
            total_files=3,
            upload_size_bytes=5120
        )
    """

    __tablename__ = "uploaded_code"

    # Primary key - UUID for security and distributed compatibility
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    # Task relationship (one-to-one via unique constraint)
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # Enforces one-to-one relationship
        index=False,  # We define index separately for naming
    )

    # Code analysis metadata
    detected_language: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )
    complexity_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    # File statistics
    total_lines: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
    total_files: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
    upload_size_bytes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    # Timestamp field (TIMESTAMP WITH TIME ZONE for PostgreSQL)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    # Relationship to Task (for eager loading if needed)
    task = relationship("Task", back_populates="uploaded_code")

    # Relationship to CodeFiles (one-to-many)
    code_files = relationship(
        "CodeFile",
        back_populates="uploaded_code",
        cascade="all, delete-orphan",
    )

    # Table-level constraints and indexes
    __table_args__ = (
        # Complexity level must be valid
        CheckConstraint(
            "complexity_level IS NULL OR complexity_level IN ('beginner', 'intermediate', 'advanced')",
            name="valid_complexity_level",
        ),
        # Upload size must not exceed 10MB (10,485,760 bytes)
        CheckConstraint(
            "upload_size_bytes IS NULL OR upload_size_bytes <= 10485760",
            name="valid_upload_size",
        ),
        # Index for task lookup
        Index("idx_uploaded_code_task_id", "task_id"),
    )

    def __repr__(self) -> str:
        """Return string representation for debugging.

        Returns:
            str: UploadedCode representation with id and detected_language.
        """
        return f"<UploadedCode(id={self.id}, task_id={self.task_id}, language={self.detected_language!r})>"

    @property
    def size_mb(self) -> float | None:
        """Get upload size in megabytes.

        Returns:
            float | None: Size in MB, or None if upload_size_bytes is not set.
        """
        if self.upload_size_bytes is None:
            return None
        return self.upload_size_bytes / (1024 * 1024)

    @property
    def is_size_valid(self) -> bool:
        """Check if upload size is within the 10MB limit.

        Returns:
            bool: True if size is valid (or not set), False if exceeds limit.
        """
        if self.upload_size_bytes is None:
            return True
        return self.upload_size_bytes <= 10485760

    def validate_size(self) -> None:
        """Validate upload size and raise error if exceeds limit.

        Raises:
            ValueError: If upload_size_bytes exceeds 10MB limit.
        """
        if self.upload_size_bytes is not None and self.upload_size_bytes > 10485760:
            size_mb = self.upload_size_bytes / (1024 * 1024)
            raise ValueError(
                f"Upload size {size_mb:.2f}MB exceeds the 10MB limit (FR-014)"
            )
