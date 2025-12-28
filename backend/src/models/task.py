"""Task model for learning units within projects.

This module defines the Task SQLAlchemy model which represents
a single learning unit focused on one code upload.

The model corresponds to the 'tasks' table in PostgreSQL and includes:
- UUID primary key for distributed system compatibility
- Project ownership via foreign key
- Sequential task_number unique within each project
- Soft delete with 30-day trash retention
- Automatic timestamp management

Example:
    from backend.src.models import Task
    from backend.src.db import get_session_context

    async with get_session_context() as session:
        task = Task(
            project_id=project.id,
            task_number=1,
            title="Learn Python Basics"
        )
        session.add(task)
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class Task(Base):
    """Learning task within a project.

    Represents a single learning unit focused on one code upload.
    Tasks have sequential numbers within a project and support soft deletion.

    Attributes:
        id: Unique identifier (UUID v4, auto-generated).
        project_id: Foreign key to the owning project.
        task_number: Sequential number within project (immutable once assigned).
        title: Task name (required, min 5 characters per FR-008).
        description: Optional description (max 500 characters per FR-009).
        upload_method: How code was uploaded ('file', 'folder', 'paste').
        created_at: Task creation timestamp (UTC, auto-set).
        updated_at: Last modification timestamp (UTC, auto-updated).
        deletion_status: 'active' or 'trashed' (default: 'active').
        trashed_at: When task was moved to trash (nullable).
        scheduled_deletion_at: When task will be permanently deleted (nullable).

    Table Constraints:
        - Title must be at least 5 characters (PostgreSQL CHECK)
        - Description must be at most 500 characters (PostgreSQL CHECK)
        - Upload method must be 'file', 'folder', or 'paste' (PostgreSQL CHECK)
        - Deletion status must be 'active' or 'trashed' (PostgreSQL CHECK)
        - Task number must be unique within project (UNIQUE constraint)
        - Project foreign key with CASCADE delete

    Indexes:
        - idx_tasks_project_id: Fast lookup by project
        - idx_tasks_deletion_status: Filter by deletion status
        - idx_tasks_number_order: Order tasks by number within project

    Example:
        task = Task(
            project_id=project.id,
            task_number=1,
            title="Learning Python Variables",
            description="Understanding how variables work in Python"
        )
    """

    __tablename__ = "tasks"

    # Primary key - UUID for security and distributed compatibility
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    # Project relationship
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=False,  # We define index separately for naming
    )

    # Task number - sequential within project
    task_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Task info
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    upload_method: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    # Timestamp fields (TIMESTAMP WITH TIME ZONE for PostgreSQL)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Soft delete fields
    deletion_status: Mapped[str] = mapped_column(
        String(20),
        default="active",
    )
    trashed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=None,
    )
    scheduled_deletion_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=None,
    )

    # Relationship to Project (for eager loading if needed)
    project = relationship("Project", back_populates="tasks")

    # Relationship to UploadedCode (one-to-one)
    uploaded_code = relationship(
        "UploadedCode",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Relationship to LearningDocument (one-to-one)
    learning_document = relationship(
        "LearningDocument",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Table-level constraints and indexes
    __table_args__ = (
        # Title minimum length constraint (PostgreSQL)
        CheckConstraint(
            "char_length(title) >= 5",
            name="title_min_length",
        ),
        # Description maximum length constraint (PostgreSQL)
        CheckConstraint(
            "description IS NULL OR char_length(description) <= 500",
            name="description_max_length",
        ),
        # Upload method must be valid
        CheckConstraint(
            "upload_method IS NULL OR upload_method IN ('file', 'folder', 'paste')",
            name="valid_upload_method",
        ),
        # Deletion status must be 'active' or 'trashed'
        CheckConstraint(
            "deletion_status IN ('active', 'trashed')",
            name="valid_deletion_status",
        ),
        # Task number unique within project
        UniqueConstraint(
            "project_id",
            "task_number",
            name="unique_task_number_per_project",
        ),
        # Index for project lookup
        Index("idx_tasks_project_id", "project_id"),
        # Index for deletion status filtering
        Index("idx_tasks_deletion_status", "deletion_status"),
        # Index for task ordering within project
        Index("idx_tasks_number_order", "project_id", "task_number"),
    )

    def __repr__(self) -> str:
        """Return string representation for debugging.

        Returns:
            str: Task representation with id, task_number, and title.
        """
        return f"<Task(id={self.id}, task_number={self.task_number}, title={self.title!r})>"

    def soft_delete(self) -> None:
        """Move task to trash with 30-day scheduled deletion.

        Sets deletion_status to 'trashed', records the current timestamp
        as trashed_at, and schedules permanent deletion for 30 days later.

        Example:
            task.soft_delete()
            await session.commit()
            # Task is now in trash
        """
        from datetime import timedelta

        now = datetime.now(UTC)
        self.deletion_status = "trashed"
        self.trashed_at = now
        self.scheduled_deletion_at = now + timedelta(days=30)

    def restore(self) -> None:
        """Restore task from trash.

        Sets deletion_status back to 'active' and clears trash timestamps.

        Example:
            task.restore()
            await session.commit()
            # Task is now active again
        """
        self.deletion_status = "active"
        self.trashed_at = None
        self.scheduled_deletion_at = None

    @property
    def is_trashed(self) -> bool:
        """Check if task is in trash.

        Returns:
            bool: True if task is in trash, False otherwise.
        """
        return self.deletion_status == "trashed"

    @property
    def is_active(self) -> bool:
        """Check if task is active (not in trash).

        Returns:
            bool: True if task is active, False otherwise.
        """
        return self.deletion_status == "active"
