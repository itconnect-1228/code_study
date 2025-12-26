"""Unit tests for TaskService.

This module tests the task service which handles task CRUD operations
with sequential task_number auto-increment per project.

TDD Approach:
- RED: Write failing tests first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code quality
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import Project
from src.models.task import Task
from src.models.user import User
from src.services.task_service import TaskService


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
def task_service(db_session: AsyncSession) -> TaskService:
    """Create a TaskService instance."""
    return TaskService(db_session)


class TestTaskServiceCreate:
    """Test TaskService.create method."""

    @pytest.mark.asyncio
    async def test_create_task_returns_task(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should create and return a task."""
        task = await task_service.create(
            project_id=project.id,
            title="Learn Python Basics",
            upload_method="file",
        )

        assert task is not None
        assert task.title == "Learn Python Basics"
        assert task.upload_method == "file"

    @pytest.mark.asyncio
    async def test_create_task_assigns_task_number_1_for_first_task(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should assign task_number=1 for first task in project."""
        task = await task_service.create(
            project_id=project.id,
            title="First Task Here",
            upload_method="file",
        )

        assert task.task_number == 1

    @pytest.mark.asyncio
    async def test_create_task_increments_task_number(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should increment task_number for subsequent tasks."""
        task1 = await task_service.create(
            project_id=project.id,
            title="First Task Title",
            upload_method="file",
        )
        task2 = await task_service.create(
            project_id=project.id,
            title="Second Task Title",
            upload_method="paste",
        )
        task3 = await task_service.create(
            project_id=project.id,
            title="Third Task Title",
            upload_method="folder",
        )

        assert task1.task_number == 1
        assert task2.task_number == 2
        assert task3.task_number == 3

    @pytest.mark.asyncio
    async def test_create_task_with_description(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should create task with optional description."""
        task = await task_service.create(
            project_id=project.id,
            title="Task with Description",
            upload_method="file",
            description="This is a detailed description",
        )

        assert task.description == "This is a detailed description"

    @pytest.mark.asyncio
    async def test_create_task_invalid_project_raises_error(
        self,
        task_service: TaskService,
    ) -> None:
        """Should raise ValueError for non-existent project."""
        with pytest.raises(ValueError, match="Project.*not found"):
            await task_service.create(
                project_id=uuid4(),
                title="Task for Invalid Project",
                upload_method="file",
            )

    @pytest.mark.asyncio
    async def test_create_task_short_title_raises_error(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should raise ValueError if title is less than 5 characters."""
        with pytest.raises(ValueError, match="at least 5 characters"):
            await task_service.create(
                project_id=project.id,
                title="Abc",  # Only 3 characters
                upload_method="file",
            )


class TestTaskServiceGetById:
    """Test TaskService.get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_task(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should return task when found."""
        created = await task_service.create(
            project_id=project.id,
            title="Task to Retrieve",
            upload_method="file",
        )

        task = await task_service.get_by_id(created.id)

        assert task is not None
        assert task.id == created.id
        assert task.title == "Task to Retrieve"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_nonexistent(
        self,
        task_service: TaskService,
    ) -> None:
        """Should return None for non-existent task."""
        task = await task_service.get_by_id(uuid4())
        assert task is None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_trashed_by_default(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should not return trashed tasks by default."""
        created = await task_service.create(
            project_id=project.id,
            title="Task to be Trashed",
            upload_method="file",
        )
        await task_service.soft_delete(created.id)

        task = await task_service.get_by_id(created.id)
        assert task is None

    @pytest.mark.asyncio
    async def test_get_by_id_includes_trashed_when_requested(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should return trashed task when include_trashed=True."""
        created = await task_service.create(
            project_id=project.id,
            title="Task to be Trashed",
            upload_method="file",
        )
        await task_service.soft_delete(created.id)

        task = await task_service.get_by_id(created.id, include_trashed=True)
        assert task is not None
        assert task.is_trashed


class TestTaskServiceGetByProject:
    """Test TaskService.get_by_project method."""

    @pytest.mark.asyncio
    async def test_get_by_project_returns_all_tasks(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should return all active tasks for a project."""
        await task_service.create(
            project_id=project.id,
            title="First Task Title",
            upload_method="file",
        )
        await task_service.create(
            project_id=project.id,
            title="Second Task Title",
            upload_method="paste",
        )

        tasks = await task_service.get_by_project(project.id)

        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_get_by_project_ordered_by_task_number(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should return tasks ordered by task_number."""
        await task_service.create(
            project_id=project.id,
            title="First Task Title",
            upload_method="file",
        )
        await task_service.create(
            project_id=project.id,
            title="Second Task Title",
            upload_method="paste",
        )
        await task_service.create(
            project_id=project.id,
            title="Third Task Title",
            upload_method="folder",
        )

        tasks = await task_service.get_by_project(project.id)

        assert tasks[0].task_number == 1
        assert tasks[1].task_number == 2
        assert tasks[2].task_number == 3

    @pytest.mark.asyncio
    async def test_get_by_project_excludes_trashed(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should exclude trashed tasks by default."""
        task1 = await task_service.create(
            project_id=project.id,
            title="Active Task Title",
            upload_method="file",
        )
        task2 = await task_service.create(
            project_id=project.id,
            title="Trashed Task Title",
            upload_method="paste",
        )
        await task_service.soft_delete(task2.id)

        tasks = await task_service.get_by_project(project.id)

        assert len(tasks) == 1
        assert tasks[0].id == task1.id

    @pytest.mark.asyncio
    async def test_get_by_project_returns_empty_for_no_tasks(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should return empty list for project with no tasks."""
        tasks = await task_service.get_by_project(project.id)
        assert tasks == []


class TestTaskServiceUpdate:
    """Test TaskService.update method."""

    @pytest.mark.asyncio
    async def test_update_title(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should update task title."""
        task = await task_service.create(
            project_id=project.id,
            title="Original Title Here",
            upload_method="file",
        )

        updated = await task_service.update(task.id, title="Updated Title Here")

        assert updated.title == "Updated Title Here"

    @pytest.mark.asyncio
    async def test_update_description(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should update task description."""
        task = await task_service.create(
            project_id=project.id,
            title="Task for Update",
            upload_method="file",
        )

        updated = await task_service.update(
            task.id,
            description="New description",
        )

        assert updated.description == "New description"

    @pytest.mark.asyncio
    async def test_update_nonexistent_raises_error(
        self,
        task_service: TaskService,
    ) -> None:
        """Should raise ValueError for non-existent task."""
        with pytest.raises(ValueError, match="Task.*not found"):
            await task_service.update(uuid4(), title="New Title Here")


class TestTaskServiceSoftDelete:
    """Test TaskService.soft_delete method."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_trashed_status(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should set deletion_status to 'trashed'."""
        task = await task_service.create(
            project_id=project.id,
            title="Task to Delete",
            upload_method="file",
        )

        deleted = await task_service.soft_delete(task.id)

        assert deleted.is_trashed
        assert deleted.deletion_status == "trashed"

    @pytest.mark.asyncio
    async def test_soft_delete_sets_trashed_at(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should set trashed_at timestamp."""
        task = await task_service.create(
            project_id=project.id,
            title="Task to Delete",
            upload_method="file",
        )

        before = datetime.now(UTC)
        deleted = await task_service.soft_delete(task.id)
        after = datetime.now(UTC)

        assert deleted.trashed_at is not None
        assert before <= deleted.trashed_at <= after

    @pytest.mark.asyncio
    async def test_soft_delete_sets_scheduled_deletion(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should schedule deletion for 30 days later."""
        task = await task_service.create(
            project_id=project.id,
            title="Task to Delete",
            upload_method="file",
        )

        deleted = await task_service.soft_delete(task.id)

        assert deleted.scheduled_deletion_at is not None
        expected_deletion = deleted.trashed_at + timedelta(days=30)
        # Allow 1 second tolerance
        assert abs((deleted.scheduled_deletion_at - expected_deletion).total_seconds()) < 1

    @pytest.mark.asyncio
    async def test_soft_delete_nonexistent_raises_error(
        self,
        task_service: TaskService,
    ) -> None:
        """Should raise ValueError for non-existent task."""
        with pytest.raises(ValueError, match="Task.*not found"):
            await task_service.soft_delete(uuid4())

    @pytest.mark.asyncio
    async def test_soft_delete_already_trashed_raises_error(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should raise ValueError for already trashed task."""
        task = await task_service.create(
            project_id=project.id,
            title="Task to Delete",
            upload_method="file",
        )
        await task_service.soft_delete(task.id)

        with pytest.raises(ValueError, match="already in trash"):
            await task_service.soft_delete(task.id)


class TestTaskServiceRestore:
    """Test TaskService.restore method."""

    @pytest.mark.asyncio
    async def test_restore_sets_active_status(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should set deletion_status back to 'active'."""
        task = await task_service.create(
            project_id=project.id,
            title="Task to Restore",
            upload_method="file",
        )
        await task_service.soft_delete(task.id)

        restored = await task_service.restore(task.id)

        assert restored.is_active
        assert restored.deletion_status == "active"
        assert restored.trashed_at is None
        assert restored.scheduled_deletion_at is None

    @pytest.mark.asyncio
    async def test_restore_active_task_raises_error(
        self,
        task_service: TaskService,
        project: Project,
    ) -> None:
        """Should raise ValueError for active task."""
        task = await task_service.create(
            project_id=project.id,
            title="Active Task Here",
            upload_method="file",
        )

        with pytest.raises(ValueError, match="not in trash"):
            await task_service.restore(task.id)


class TestTaskServiceValidateOwnership:
    """Test TaskService.validate_ownership method."""

    @pytest.mark.asyncio
    async def test_validate_ownership_returns_true_for_owner(
        self,
        task_service: TaskService,
        project: Project,
        user: User,
    ) -> None:
        """Should return True for project owner."""
        task = await task_service.create(
            project_id=project.id,
            title="Task for Owner",
            upload_method="file",
        )

        result = await task_service.validate_ownership(task.id, user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_ownership_returns_false_for_non_owner(
        self,
        task_service: TaskService,
        project: Project,
        db_session: AsyncSession,
    ) -> None:
        """Should return False for non-owner."""
        task = await task_service.create(
            project_id=project.id,
            title="Task for Validation",
            upload_method="file",
        )

        # Create another user
        other_user = User(
            email="other@example.com",
            password_hash="hashed_password",
            
        )
        db_session.add(other_user)
        await db_session.commit()

        result = await task_service.validate_ownership(task.id, other_user.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_ownership_returns_false_for_nonexistent_task(
        self,
        task_service: TaskService,
        user: User,
    ) -> None:
        """Should return False for non-existent task."""
        result = await task_service.validate_ownership(uuid4(), user.id)
        assert result is False
