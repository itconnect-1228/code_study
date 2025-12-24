"""Unit tests for Project SQLAlchemy model.

Tests for Project model creation, validation, soft delete, and constraints.
Follows TDD cycle: RED -> GREEN -> REFACTOR

Test categories:
1. Basic creation - project with required fields
2. Constraints - title minimum length, required fields
3. Defaults - deletion_status, timestamps
4. Soft delete - trashed_at, scheduled_deletion_at
5. User relationship - project belongs to user
6. Representation - __repr__ method
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.models.project import Project
from src.models.user import User


class TestProjectCreation:
    """Tests for basic project creation."""

    @pytest.mark.asyncio
    async def test_create_project_with_valid_data(self, db_session):
        """Project should be creatable with valid title and user_id."""
        # Create a user first
        user = User(
            email="project-owner@example.com",
            password_hash="$2b$12$hashedpassword123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create project
        project = Project(
            user_id=user.id,
            title="My Learning Project",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.id is not None
        assert project.user_id == user.id
        assert project.title == "My Learning Project"

    @pytest.mark.asyncio
    async def test_project_id_is_uuid(self, db_session):
        """Project ID should be a valid UUID."""
        user = User(
            email="uuid-project@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="UUID Test Project",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert isinstance(project.id, UUID)

    @pytest.mark.asyncio
    async def test_project_with_description(self, db_session):
        """Project should accept optional description."""
        user = User(
            email="desc-project@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="Project with Description",
            description="This is a learning project about Python basics.",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.description == "This is a learning project about Python basics."

    @pytest.mark.asyncio
    async def test_project_persists_to_database(self, db_session):
        """Project should be retrievable from database after creation."""
        user = User(
            email="persist-project@example.com",
            password_hash="hash456",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="Persistent Project",
        )
        db_session.add(project)
        await db_session.commit()

        # Query the project back
        result = await db_session.execute(
            select(Project).where(Project.title == "Persistent Project")
        )
        retrieved_project = result.scalar_one()

        assert retrieved_project.id == project.id
        assert retrieved_project.title == "Persistent Project"


class TestProjectConstraints:
    """Tests for database constraints."""

    @pytest.mark.asyncio
    async def test_project_title_required(self, db_session):
        """Project without title should raise IntegrityError."""
        user = User(
            email="notitle@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title=None,  # type: ignore
        )
        db_session.add(project)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_project_user_id_required(self, db_session):
        """Project without user_id should raise IntegrityError."""
        project = Project(
            user_id=None,  # type: ignore
            title="Orphan Project",
        )
        db_session.add(project)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.skip(reason="PostgreSQL CHECK constraint not enforced in SQLite")
    @pytest.mark.asyncio
    async def test_project_title_minimum_length(self, db_session):
        """Project with empty title should be rejected."""
        user = User(
            email="emptytitle@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="",  # Empty title should fail
        )
        db_session.add(project)

        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestProjectDefaults:
    """Tests for default field values."""

    @pytest.mark.asyncio
    async def test_project_deletion_status_default(self, db_session):
        """Project should have 'active' as default deletion_status."""
        user = User(
            email="active@example.com",
            password_hash="hash789",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="Active Project",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.deletion_status == "active"

    @pytest.mark.asyncio
    async def test_project_timestamps_auto_set(self, db_session):
        """created_at, updated_at, last_activity_at should be auto-set."""
        user = User(
            email="timestamps@example.com",
            password_hash="hash101",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        before = datetime.now(UTC)

        project = Project(
            user_id=user.id,
            title="Timestamp Project",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        after = datetime.now(UTC)

        # Handle timezone-aware vs naive comparison
        created_at = project.created_at
        updated_at = project.updated_at
        last_activity_at = project.last_activity_at

        # If timestamps are naive (SQLite), compare without timezone
        if created_at.tzinfo is None:
            before = before.replace(tzinfo=None)
            after = after.replace(tzinfo=None)

        assert before <= created_at <= after
        assert before <= updated_at <= after
        assert before <= last_activity_at <= after

    @pytest.mark.asyncio
    async def test_project_trashed_at_initially_none(self, db_session):
        """trashed_at should be None for new projects."""
        user = User(
            email="newproject@example.com",
            password_hash="hash202",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="New Project",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.trashed_at is None
        assert project.scheduled_deletion_at is None


class TestProjectSoftDelete:
    """Tests for soft delete functionality."""

    @pytest.mark.asyncio
    async def test_project_can_be_trashed(self, db_session):
        """Project can be moved to trash with proper status and timestamps."""
        user = User(
            email="trash@example.com",
            password_hash="hash303",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="To Be Trashed",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Move to trash
        now = datetime.now(UTC)
        project.deletion_status = "trashed"
        project.trashed_at = now
        project.scheduled_deletion_at = now + timedelta(days=30)

        await db_session.commit()
        await db_session.refresh(project)

        assert project.deletion_status == "trashed"
        assert project.trashed_at is not None
        assert project.scheduled_deletion_at is not None

    @pytest.mark.asyncio
    async def test_project_scheduled_deletion_30_days(self, db_session):
        """Scheduled deletion should be 30 days after trashing."""
        user = User(
            email="schedule@example.com",
            password_hash="hash404",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="Scheduled Deletion",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Move to trash
        trashed_time = datetime.now(UTC)
        scheduled_time = trashed_time + timedelta(days=30)
        project.deletion_status = "trashed"
        project.trashed_at = trashed_time
        project.scheduled_deletion_at = scheduled_time

        await db_session.commit()
        await db_session.refresh(project)

        # Verify 30-day difference
        if project.trashed_at.tzinfo is None:
            trashed_time = trashed_time.replace(tzinfo=None)
            scheduled_time = scheduled_time.replace(tzinfo=None)

        time_diff = project.scheduled_deletion_at - project.trashed_at
        assert time_diff.days == 30

    @pytest.mark.skip(reason="PostgreSQL CHECK constraint not enforced in SQLite")
    @pytest.mark.asyncio
    async def test_project_deletion_status_values(self, db_session):
        """deletion_status should only accept 'active' or 'trashed'."""
        user = User(
            email="status@example.com",
            password_hash="hash505",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="Invalid Status",
            deletion_status="invalid",
        )
        db_session.add(project)

        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestProjectUserRelationship:
    """Tests for project-user relationship."""

    @pytest.mark.asyncio
    async def test_project_belongs_to_user(self, db_session):
        """Project should be associated with the correct user."""
        user1 = User(
            email="owner1@example.com",
            password_hash="hash1",
        )
        user2 = User(
            email="owner2@example.com",
            password_hash="hash2",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        project = Project(
            user_id=user1.id,
            title="User1's Project",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.user_id == user1.id
        assert project.user_id != user2.id

    @pytest.mark.asyncio
    async def test_user_can_have_multiple_projects(self, db_session):
        """A user can own multiple projects."""
        user = User(
            email="multiproject@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project1 = Project(user_id=user.id, title="Project 1")
        project2 = Project(user_id=user.id, title="Project 2")
        project3 = Project(user_id=user.id, title="Project 3")

        db_session.add_all([project1, project2, project3])
        await db_session.commit()

        # Query all projects for user
        result = await db_session.execute(
            select(Project).where(Project.user_id == user.id)
        )
        projects = result.scalars().all()

        assert len(projects) == 3


class TestProjectRepr:
    """Tests for Project string representation."""

    @pytest.mark.asyncio
    async def test_project_repr(self, db_session):
        """__repr__ should return readable project representation."""
        user = User(
            email="repr@example.com",
            password_hash="hash606",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="Repr Project",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        repr_str = repr(project)

        assert "Project" in repr_str
        assert "Repr Project" in repr_str
        assert str(project.id) in repr_str


class TestProjectHelperMethods:
    """Tests for Project helper methods."""

    @pytest.mark.asyncio
    async def test_soft_delete_method(self, db_session):
        """soft_delete() should move project to trash with proper timestamps."""
        user = User(
            email="softdelete@example.com",
            password_hash="hash707",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="To Be Soft Deleted",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Use soft_delete method
        project.soft_delete()
        await db_session.commit()
        await db_session.refresh(project)

        assert project.deletion_status == "trashed"
        assert project.trashed_at is not None
        assert project.scheduled_deletion_at is not None
        assert project.is_trashed is True
        assert project.is_active is False

    @pytest.mark.asyncio
    async def test_restore_method(self, db_session):
        """restore() should restore project from trash."""
        user = User(
            email="restore@example.com",
            password_hash="hash808",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="To Be Restored",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Soft delete then restore
        project.soft_delete()
        await db_session.commit()
        await db_session.refresh(project)

        project.restore()
        await db_session.commit()
        await db_session.refresh(project)

        assert project.deletion_status == "active"
        assert project.trashed_at is None
        assert project.scheduled_deletion_at is None
        assert project.is_trashed is False
        assert project.is_active is True

    @pytest.mark.asyncio
    async def test_is_trashed_property(self, db_session):
        """is_trashed property should return correct status."""
        user = User(
            email="istrashed@example.com",
            password_hash="hash909",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="Check Trashed",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Initially active
        assert project.is_trashed is False
        assert project.is_active is True

        # After soft delete
        project.soft_delete()
        assert project.is_trashed is True
        assert project.is_active is False
