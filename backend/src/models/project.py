"""Project model for organizing learning tasks.

This module defines the Project SQLAlchemy model which represents
a learning container for related tasks.

The model corresponds to the 'projects' table in PostgreSQL and includes:
- UUID primary key for distributed system compatibility
- User ownership via foreign key
- Soft delete with 30-day trash retention
- Automatic timestamp management

Example:
    from backend.src.models import Project
    from backend.src.db import get_session_context

    async with get_session_context() as session:
        project = Project(
            user_id=user.id,
            title="Python Basics"
        )
        session.add(project)
        await session.commit()
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class Project(Base):
    """Learning project container for related tasks.

    Represents a project that groups related learning tasks together.
    Projects support soft deletion with 30-day trash retention.

    Attributes:
        id: Unique identifier (UUID v4, auto-generated).
        user_id: Foreign key to the owning user.
        title: Project name (required, min 1 character).
        description: Optional project description.
        created_at: Project creation timestamp (UTC, auto-set).
        updated_at: Last modification timestamp (UTC, auto-updated).
        last_activity_at: Last task activity timestamp (UTC, auto-set).
        deletion_status: 'active' or 'trashed' (default: 'active').
        trashed_at: When project was moved to trash (nullable).
        scheduled_deletion_at: When project will be permanently deleted (nullable).

    Table Constraints:
        - Title must be at least 1 character (PostgreSQL CHECK)
        - Deletion status must be 'active' or 'trashed' (PostgreSQL CHECK)
        - User foreign key with CASCADE delete

    Indexes:
        - idx_projects_user_id: Fast lookup by user
        - idx_projects_deletion_status: Filter by deletion status
        - idx_projects_user_active: Partial index for active projects per user

    Example:
        project = Project(
            user_id=user.id,
            title="Learning Python",
            description="A project to learn Python basics"
        )
    """

    __tablename__ = "projects"

    # Primary key - UUID for security and distributed compatibility
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    # User relationship
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=False,  # We define index separately for naming
    )

    # Project info
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
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
    last_activity_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
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

    # Relationship to User (for eager loading if needed)
    user = relationship("User", back_populates="projects")

    # Table-level constraints and indexes
    __table_args__ = (
        # Title minimum length constraint (PostgreSQL)
        CheckConstraint(
            "char_length(title) >= 1",
            name="title_min_length",
        ),
        # Deletion status must be 'active' or 'trashed'
        CheckConstraint(
            "deletion_status IN ('active', 'trashed')",
            name="valid_deletion_status",
        ),
        # Index for user lookup
        Index("idx_projects_user_id", "user_id"),
        # Index for deletion status filtering
        Index("idx_projects_deletion_status", "deletion_status"),
    )

    def __repr__(self) -> str:
        """Return string representation for debugging.

        Returns:
            str: Project representation with id and title.
        """
        return f"<Project(id={self.id}, title={self.title!r})>"

    def soft_delete(self) -> None:
        """Move project to trash with 30-day scheduled deletion.

        Sets deletion_status to 'trashed', records the current timestamp
        as trashed_at, and schedules permanent deletion for 30 days later.

        Example:
            project.soft_delete()
            await session.commit()
            # Project is now in trash
        """
        from datetime import timedelta

        now = datetime.now(UTC)
        self.deletion_status = "trashed"
        self.trashed_at = now
        self.scheduled_deletion_at = now + timedelta(days=30)

    def restore(self) -> None:
        """Restore project from trash.

        Sets deletion_status back to 'active' and clears trash timestamps.

        Example:
            project.restore()
            await session.commit()
            # Project is now active again
        """
        self.deletion_status = "active"
        self.trashed_at = None
        self.scheduled_deletion_at = None

    @property
    def is_trashed(self) -> bool:
        """Check if project is in trash.

        Returns:
            bool: True if project is in trash, False otherwise.
        """
        return self.deletion_status == "trashed"

    @property
    def is_active(self) -> bool:
        """Check if project is active (not in trash).

        Returns:
            bool: True if project is active, False otherwise.
        """
        return self.deletion_status == "active"
