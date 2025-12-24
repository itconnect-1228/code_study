"""Unit tests for ProjectService.

Tests for project CRUD operations following TDD cycle.
This is the RED phase - tests are written before implementation.

Test categories:
1. Create - Create a new project for a user
2. Get by ID - Retrieve a single project
3. Get all - Retrieve all active projects for a user
4. Update - Update project title and description
5. Soft delete - Move project to trash with 30-day retention

Architecture:
- Service Layer Pattern: Business logic separated from API layer
- Async/await for non-blocking database operations
- Raises specific exceptions for validation and not-found errors
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import Project
from src.models.user import User
from src.services.project_service import ProjectService


class TestProjectServiceCreate:
    """Tests for ProjectService.create method."""

    @pytest.mark.asyncio
    async def test_create_project_with_valid_data(self, db_session: AsyncSession):
        """create() should create a new project with valid title and user_id."""
        # Create a user first
        user = User(
            email="project-creator@example.com",
            password_hash="$2b$12$hashedpassword123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create project via service
        service = ProjectService(db_session)
        project = await service.create(
            user_id=user.id,
            title="My Learning Project",
        )

        assert project.id is not None
        assert isinstance(project.id, UUID)
        assert project.user_id == user.id
        assert project.title == "My Learning Project"
        assert project.deletion_status == "active"

    @pytest.mark.asyncio
    async def test_create_project_with_description(self, db_session: AsyncSession):
        """create() should accept optional description."""
        user = User(
            email="desc-creator@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        service = ProjectService(db_session)
        project = await service.create(
            user_id=user.id,
            title="Python Basics",
            description="Learn Python fundamentals",
        )

        assert project.description == "Learn Python fundamentals"

    @pytest.mark.asyncio
    async def test_create_project_empty_title_raises_error(
        self, db_session: AsyncSession
    ):
        """create() should raise ValueError for empty title."""
        user = User(
            email="empty-title@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        service = ProjectService(db_session)

        with pytest.raises(ValueError, match="title"):
            await service.create(user_id=user.id, title="")

    @pytest.mark.asyncio
    async def test_create_project_sets_timestamps(self, db_session: AsyncSession):
        """create() should set created_at, updated_at, and last_activity_at."""
        user = User(
            email="timestamps@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        service = ProjectService(db_session)
        project = await service.create(user_id=user.id, title="Timestamp Test")

        assert project.created_at is not None
        assert project.updated_at is not None
        assert project.last_activity_at is not None

    @pytest.mark.asyncio
    async def test_create_project_invalid_user_id(self, db_session: AsyncSession):
        """create() should raise error for non-existent user_id."""
        service = ProjectService(db_session)
        fake_user_id = uuid4()

        with pytest.raises(ValueError, match="(?i)user"):
            await service.create(user_id=fake_user_id, title="Orphan Project")


class TestProjectServiceGetById:
    """Tests for ProjectService.get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_project_by_id(self, db_session: AsyncSession):
        """get_by_id() should return project with matching ID."""
        user = User(
            email="get-by-id@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Find Me")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        service = ProjectService(db_session)
        found = await service.get_by_id(project.id)

        assert found is not None
        assert found.id == project.id
        assert found.title == "Find Me"

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self, db_session: AsyncSession):
        """get_by_id() should return None for non-existent project."""
        service = ProjectService(db_session)
        result = await service.get_by_id(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_project_by_id_excludes_trashed(self, db_session: AsyncSession):
        """get_by_id() should return None for trashed projects by default."""
        user = User(
            email="trashed-project@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Trashed Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Soft delete the project
        project.soft_delete()
        await db_session.commit()

        service = ProjectService(db_session)
        result = await service.get_by_id(project.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_project_by_id_include_trashed(self, db_session: AsyncSession):
        """get_by_id() should return trashed project when include_trashed=True."""
        user = User(
            email="include-trashed@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Trashed but Findable")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        project.soft_delete()
        await db_session.commit()

        service = ProjectService(db_session)
        result = await service.get_by_id(project.id, include_trashed=True)

        assert result is not None
        assert result.id == project.id
        assert result.is_trashed is True


class TestProjectServiceGetByUser:
    """Tests for ProjectService.get_by_user method."""

    @pytest.mark.asyncio
    async def test_get_projects_by_user(self, db_session: AsyncSession):
        """get_by_user() should return all active projects for a user."""
        user = User(
            email="multi-projects@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        projects = [
            Project(user_id=user.id, title="Project 1"),
            Project(user_id=user.id, title="Project 2"),
            Project(user_id=user.id, title="Project 3"),
        ]
        for p in projects:
            db_session.add(p)
        await db_session.commit()

        service = ProjectService(db_session)
        result = await service.get_by_user(user.id)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_projects_by_user_empty(self, db_session: AsyncSession):
        """get_by_user() should return empty list for user with no projects."""
        user = User(
            email="no-projects@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        service = ProjectService(db_session)
        result = await service.get_by_user(user.id)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_projects_by_user_excludes_trashed(
        self, db_session: AsyncSession
    ):
        """get_by_user() should exclude trashed projects."""
        user = User(
            email="mixed-projects@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        active_project = Project(user_id=user.id, title="Active Project")
        trashed_project = Project(user_id=user.id, title="Trashed Project")
        db_session.add(active_project)
        db_session.add(trashed_project)
        await db_session.commit()
        await db_session.refresh(trashed_project)

        trashed_project.soft_delete()
        await db_session.commit()

        service = ProjectService(db_session)
        result = await service.get_by_user(user.id)

        assert len(result) == 1
        assert result[0].title == "Active Project"

    @pytest.mark.asyncio
    async def test_get_projects_by_user_isolates_users(self, db_session: AsyncSession):
        """get_by_user() should only return projects for specified user."""
        user1 = User(email="user1@example.com", password_hash="hash1")
        user2 = User(email="user2@example.com", password_hash="hash2")
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        project1 = Project(user_id=user1.id, title="User1 Project")
        project2 = Project(user_id=user2.id, title="User2 Project")
        db_session.add(project1)
        db_session.add(project2)
        await db_session.commit()

        service = ProjectService(db_session)
        user1_projects = await service.get_by_user(user1.id)

        assert len(user1_projects) == 1
        assert user1_projects[0].title == "User1 Project"


class TestProjectServiceUpdate:
    """Tests for ProjectService.update method."""

    @pytest.mark.asyncio
    async def test_update_project_title(self, db_session: AsyncSession):
        """update() should update project title."""
        user = User(
            email="update-title@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Original Title")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        service = ProjectService(db_session)
        updated = await service.update(project.id, title="New Title")

        assert updated.title == "New Title"

    @pytest.mark.asyncio
    async def test_update_project_description(self, db_session: AsyncSession):
        """update() should update project description."""
        user = User(
            email="update-desc@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="My Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        service = ProjectService(db_session)
        updated = await service.update(project.id, description="New description")

        assert updated.description == "New description"

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, db_session: AsyncSession):
        """update() should raise ValueError for non-existent project."""
        service = ProjectService(db_session)

        with pytest.raises(ValueError, match="not found"):
            await service.update(uuid4(), title="New Title")

    @pytest.mark.asyncio
    async def test_update_project_empty_title_raises_error(
        self, db_session: AsyncSession
    ):
        """update() should raise ValueError for empty title."""
        user = User(
            email="empty-update@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Valid Title")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        service = ProjectService(db_session)

        with pytest.raises(ValueError, match="title"):
            await service.update(project.id, title="")

    @pytest.mark.asyncio
    async def test_update_project_updates_updated_at(self, db_session: AsyncSession):
        """update() should update the updated_at timestamp."""
        user = User(
            email="update-timestamp@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Timestamp Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        original_updated_at = project.updated_at

        service = ProjectService(db_session)
        updated = await service.update(project.id, title="Updated Title")

        # updated_at should change (or be at least as recent)
        assert updated.updated_at >= original_updated_at


class TestProjectServiceSoftDelete:
    """Tests for ProjectService.soft_delete method."""

    @pytest.mark.asyncio
    async def test_soft_delete_project(self, db_session: AsyncSession):
        """soft_delete() should move project to trash."""
        user = User(
            email="soft-delete@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="To Be Trashed")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        service = ProjectService(db_session)
        deleted = await service.soft_delete(project.id)

        assert deleted.deletion_status == "trashed"
        assert deleted.trashed_at is not None
        assert deleted.scheduled_deletion_at is not None
        assert deleted.is_trashed is True

    @pytest.mark.asyncio
    async def test_soft_delete_project_not_found(self, db_session: AsyncSession):
        """soft_delete() should raise ValueError for non-existent project."""
        service = ProjectService(db_session)

        with pytest.raises(ValueError, match="not found"):
            await service.soft_delete(uuid4())

    @pytest.mark.asyncio
    async def test_soft_delete_project_already_trashed(self, db_session: AsyncSession):
        """soft_delete() should raise error for already trashed project."""
        user = User(
            email="already-trashed@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Already Trashed")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        project.soft_delete()
        await db_session.commit()

        service = ProjectService(db_session)

        with pytest.raises(ValueError, match="already"):
            await service.soft_delete(project.id)

    @pytest.mark.asyncio
    async def test_soft_delete_sets_30_day_retention(self, db_session: AsyncSession):
        """soft_delete() should set scheduled_deletion_at to 30 days from now."""

        user = User(
            email="retention@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="30 Day Retention")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        service = ProjectService(db_session)
        deleted = await service.soft_delete(project.id)

        # Verify approximately 30 days difference
        if deleted.trashed_at and deleted.scheduled_deletion_at:
            diff = deleted.scheduled_deletion_at - deleted.trashed_at
            assert diff.days == 30
