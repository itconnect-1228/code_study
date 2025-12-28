"""Unit tests for Task SQLAlchemy model.

Tests for Task model creation, validation, soft delete, and constraints.
Follows TDD cycle: RED -> GREEN -> REFACTOR

Test categories:
1. Basic creation - task with required fields
2. Constraints - title minimum length, description maximum length, unique task_number
3. Defaults - deletion_status, timestamps
4. Soft delete - trashed_at, scheduled_deletion_at
5. Project relationship - task belongs to project
6. Upload method - file, folder, paste validation
7. Sequential task_number - unique per project
8. Representation - __repr__ method
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.models.project import Project
from src.models.task import Task
from src.models.user import User


class TestTaskCreation:
    """Tests for basic task creation."""

    @pytest.mark.asyncio
    async def test_create_task_with_valid_data(self, db_session):
        """Task should be creatable with valid project_id, title, and task_number."""
        # Create user and project first
        user = User(
            email="task-owner@example.com",
            password_hash="$2b$12$hashedpassword123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(
            user_id=user.id,
            title="Test Project",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Create task
        task = Task(
            project_id=project.id,
            task_number=1,
            title="Learn Python Basics",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.id is not None
        assert task.project_id == project.id
        assert task.task_number == 1
        assert task.title == "Learn Python Basics"

    @pytest.mark.asyncio
    async def test_task_id_is_uuid(self, db_session):
        """Task ID should be a valid UUID."""
        user = User(
            email="uuid-task@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="UUID Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="UUID Test Task",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert isinstance(task.id, UUID)

    @pytest.mark.asyncio
    async def test_task_with_description(self, db_session):
        """Task should accept optional description."""
        user = User(
            email="desc-task@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Description Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Task with Description",
            description="This task covers the basics of Python variables.",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.description == "This task covers the basics of Python variables."

    @pytest.mark.asyncio
    async def test_task_with_upload_method(self, db_session):
        """Task should accept upload_method field."""
        user = User(
            email="upload-task@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Upload Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="File Upload Task",
            upload_method="file",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.upload_method == "file"

    @pytest.mark.asyncio
    async def test_task_persists_to_database(self, db_session):
        """Task should be retrievable from database after creation."""
        user = User(
            email="persist-task@example.com",
            password_hash="hash456",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Persistent Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Persistent Task",
        )
        db_session.add(task)
        await db_session.commit()

        # Query the task back
        result = await db_session.execute(
            select(Task).where(Task.title == "Persistent Task")
        )
        retrieved_task = result.scalar_one()

        assert retrieved_task.id == task.id
        assert retrieved_task.title == "Persistent Task"


class TestTaskConstraints:
    """Tests for database constraints."""

    @pytest.mark.asyncio
    async def test_task_project_id_required(self, db_session):
        """Task without project_id should raise IntegrityError."""
        task = Task(
            project_id=None,  # type: ignore
            task_number=1,
            title="Orphan Task",
        )
        db_session.add(task)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_task_title_required(self, db_session):
        """Task without title should raise IntegrityError."""
        user = User(
            email="notitle-task@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="No Title Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title=None,  # type: ignore
        )
        db_session.add(task)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_task_number_required(self, db_session):
        """Task without task_number should raise IntegrityError."""
        user = User(
            email="nonumber-task@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="No Number Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=None,  # type: ignore
            title="No Number Task",
        )
        db_session.add(task)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_unique_task_number_per_project(self, db_session):
        """Two tasks with same task_number in same project should raise IntegrityError."""
        user = User(
            email="unique-number@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Unique Number Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task1 = Task(
            project_id=project.id,
            task_number=1,
            title="First Task",
        )
        db_session.add(task1)
        await db_session.commit()

        task2 = Task(
            project_id=project.id,
            task_number=1,  # Duplicate task_number
            title="Second Task",
        )
        db_session.add(task2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_same_task_number_different_projects(self, db_session):
        """Same task_number in different projects should be allowed."""
        user = User(
            email="diff-projects@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project1 = Project(user_id=user.id, title="Project 1")
        project2 = Project(user_id=user.id, title="Project 2")
        db_session.add_all([project1, project2])
        await db_session.commit()
        await db_session.refresh(project1)
        await db_session.refresh(project2)

        task1 = Task(
            project_id=project1.id,
            task_number=1,
            title="Task in Project 1",
        )
        task2 = Task(
            project_id=project2.id,
            task_number=1,  # Same number, different project
            title="Task in Project 2",
        )
        db_session.add_all([task1, task2])
        await db_session.commit()

        assert task1.task_number == task2.task_number
        assert task1.project_id != task2.project_id

    @pytest.mark.skip(reason="PostgreSQL CHECK constraint not enforced in SQLite")
    @pytest.mark.asyncio
    async def test_task_title_minimum_length(self, db_session):
        """Task with title less than 5 characters should be rejected."""
        user = User(
            email="shorttitle@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Short Title Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Hi",  # Less than 5 characters
        )
        db_session.add(task)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.skip(reason="PostgreSQL CHECK constraint not enforced in SQLite")
    @pytest.mark.asyncio
    async def test_task_description_maximum_length(self, db_session):
        """Task with description more than 500 characters should be rejected."""
        user = User(
            email="longdesc@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Long Desc Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Long Description Task",
            description="x" * 501,  # More than 500 characters
        )
        db_session.add(task)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.skip(reason="PostgreSQL CHECK constraint not enforced in SQLite")
    @pytest.mark.asyncio
    async def test_task_upload_method_valid_values(self, db_session):
        """upload_method should only accept 'file', 'folder', or 'paste'."""
        user = User(
            email="invalidupload@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Invalid Upload Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Invalid Upload Method",
            upload_method="invalid",
        )
        db_session.add(task)

        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestTaskDefaults:
    """Tests for default field values."""

    @pytest.mark.asyncio
    async def test_task_deletion_status_default(self, db_session):
        """Task should have 'active' as default deletion_status."""
        user = User(
            email="active-task@example.com",
            password_hash="hash789",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Active Task Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Active Task",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.deletion_status == "active"

    @pytest.mark.asyncio
    async def test_task_timestamps_auto_set(self, db_session):
        """created_at and updated_at should be auto-set."""
        user = User(
            email="timestamps-task@example.com",
            password_hash="hash101",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Timestamp Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        before = datetime.now(UTC)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Timestamp Task",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        after = datetime.now(UTC)

        # Handle timezone-aware vs naive comparison
        created_at = task.created_at
        updated_at = task.updated_at

        # If timestamps are naive (SQLite), compare without timezone
        if created_at.tzinfo is None:
            before = before.replace(tzinfo=None)
            after = after.replace(tzinfo=None)

        assert before <= created_at <= after
        assert before <= updated_at <= after

    @pytest.mark.asyncio
    async def test_task_trashed_at_initially_none(self, db_session):
        """trashed_at should be None for new tasks."""
        user = User(
            email="newtask@example.com",
            password_hash="hash202",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="New Task Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="New Task Here",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.trashed_at is None
        assert task.scheduled_deletion_at is None

    @pytest.mark.asyncio
    async def test_task_upload_method_initially_none(self, db_session):
        """upload_method should be None by default."""
        user = User(
            email="noupload@example.com",
            password_hash="hash303",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="No Upload Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="No Upload Method",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.upload_method is None


class TestTaskSoftDelete:
    """Tests for soft delete functionality."""

    @pytest.mark.asyncio
    async def test_task_can_be_trashed(self, db_session):
        """Task can be moved to trash with proper status and timestamps."""
        user = User(
            email="trash-task@example.com",
            password_hash="hash303",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Trash Task Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="To Be Trashed Task",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Move to trash
        now = datetime.now(UTC)
        task.deletion_status = "trashed"
        task.trashed_at = now
        task.scheduled_deletion_at = now + timedelta(days=30)

        await db_session.commit()
        await db_session.refresh(task)

        assert task.deletion_status == "trashed"
        assert task.trashed_at is not None
        assert task.scheduled_deletion_at is not None

    @pytest.mark.asyncio
    async def test_task_scheduled_deletion_30_days(self, db_session):
        """Scheduled deletion should be 30 days after trashing."""
        user = User(
            email="schedule-task@example.com",
            password_hash="hash404",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Schedule Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Scheduled Deletion Task",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Move to trash
        trashed_time = datetime.now(UTC)
        scheduled_time = trashed_time + timedelta(days=30)
        task.deletion_status = "trashed"
        task.trashed_at = trashed_time
        task.scheduled_deletion_at = scheduled_time

        await db_session.commit()
        await db_session.refresh(task)

        # Verify 30-day difference
        if task.trashed_at.tzinfo is None:
            trashed_time = trashed_time.replace(tzinfo=None)
            scheduled_time = scheduled_time.replace(tzinfo=None)

        time_diff = task.scheduled_deletion_at - task.trashed_at
        assert time_diff.days == 30

    @pytest.mark.skip(reason="PostgreSQL CHECK constraint not enforced in SQLite")
    @pytest.mark.asyncio
    async def test_task_deletion_status_values(self, db_session):
        """deletion_status should only accept 'active' or 'trashed'."""
        user = User(
            email="status-task@example.com",
            password_hash="hash505",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Status Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Invalid Status Task",
            deletion_status="invalid",
        )
        db_session.add(task)

        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestTaskProjectRelationship:
    """Tests for task-project relationship."""

    @pytest.mark.asyncio
    async def test_task_belongs_to_project(self, db_session):
        """Task should be associated with the correct project."""
        user = User(
            email="owner@example.com",
            password_hash="hash1",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project1 = Project(user_id=user.id, title="Project A")
        project2 = Project(user_id=user.id, title="Project B")
        db_session.add_all([project1, project2])
        await db_session.commit()
        await db_session.refresh(project1)
        await db_session.refresh(project2)

        task = Task(
            project_id=project1.id,
            task_number=1,
            title="Project A Task",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.project_id == project1.id
        assert task.project_id != project2.id

    @pytest.mark.asyncio
    async def test_project_can_have_multiple_tasks(self, db_session):
        """A project can have multiple tasks."""
        user = User(
            email="multitask@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Multi Task Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task1 = Task(project_id=project.id, task_number=1, title="First Task Here")
        task2 = Task(project_id=project.id, task_number=2, title="Second Task Here")
        task3 = Task(project_id=project.id, task_number=3, title="Third Task Here")

        db_session.add_all([task1, task2, task3])
        await db_session.commit()

        # Query all tasks for project
        result = await db_session.execute(
            select(Task).where(Task.project_id == project.id)
        )
        tasks = result.scalars().all()

        assert len(tasks) == 3


class TestTaskSequentialNumber:
    """Tests for sequential task_number within project."""

    @pytest.mark.asyncio
    async def test_task_numbers_sequential_in_project(self, db_session):
        """Task numbers should be sequential within a project."""
        user = User(
            email="sequential@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Sequential Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Create tasks with sequential numbers
        task1 = Task(project_id=project.id, task_number=1, title="First Task Seq")
        task2 = Task(project_id=project.id, task_number=2, title="Second Task Seq")
        task3 = Task(project_id=project.id, task_number=3, title="Third Task Seq")

        db_session.add_all([task1, task2, task3])
        await db_session.commit()

        # Query and verify order
        result = await db_session.execute(
            select(Task).where(Task.project_id == project.id).order_by(Task.task_number)
        )
        tasks = result.scalars().all()

        assert tasks[0].task_number == 1
        assert tasks[1].task_number == 2
        assert tasks[2].task_number == 3


class TestTaskUploadMethod:
    """Tests for upload_method field."""

    @pytest.mark.asyncio
    async def test_upload_method_file(self, db_session):
        """upload_method can be 'file'."""
        user = User(
            email="file-upload@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="File Upload Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="File Upload Task",
            upload_method="file",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.upload_method == "file"

    @pytest.mark.asyncio
    async def test_upload_method_folder(self, db_session):
        """upload_method can be 'folder'."""
        user = User(
            email="folder-upload@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Folder Upload Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Folder Upload Task",
            upload_method="folder",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.upload_method == "folder"

    @pytest.mark.asyncio
    async def test_upload_method_paste(self, db_session):
        """upload_method can be 'paste'."""
        user = User(
            email="paste-upload@example.com",
            password_hash="hash123",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Paste Upload Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Paste Upload Task",
            upload_method="paste",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.upload_method == "paste"


class TestTaskRepr:
    """Tests for Task string representation."""

    @pytest.mark.asyncio
    async def test_task_repr(self, db_session):
        """__repr__ should return readable task representation."""
        user = User(
            email="repr-task@example.com",
            password_hash="hash606",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Repr Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Repr Test Task",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        repr_str = repr(task)

        assert "Task" in repr_str
        assert "Repr Test Task" in repr_str or "task_number=1" in repr_str


class TestTaskHelperMethods:
    """Tests for Task helper methods."""

    @pytest.mark.asyncio
    async def test_soft_delete_method(self, db_session):
        """soft_delete() should move task to trash with proper timestamps."""
        user = User(
            email="softdelete-task@example.com",
            password_hash="hash707",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Soft Delete Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="To Be Soft Deleted",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Use soft_delete method
        task.soft_delete()
        await db_session.commit()
        await db_session.refresh(task)

        assert task.deletion_status == "trashed"
        assert task.trashed_at is not None
        assert task.scheduled_deletion_at is not None
        assert task.is_trashed is True
        assert task.is_active is False

    @pytest.mark.asyncio
    async def test_restore_method(self, db_session):
        """restore() should restore task from trash."""
        user = User(
            email="restore-task@example.com",
            password_hash="hash808",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Restore Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="To Be Restored Task",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Soft delete then restore
        task.soft_delete()
        await db_session.commit()
        await db_session.refresh(task)

        task.restore()
        await db_session.commit()
        await db_session.refresh(task)

        assert task.deletion_status == "active"
        assert task.trashed_at is None
        assert task.scheduled_deletion_at is None
        assert task.is_trashed is False
        assert task.is_active is True

    @pytest.mark.asyncio
    async def test_is_trashed_property(self, db_session):
        """is_trashed property should return correct status."""
        user = User(
            email="istrashed-task@example.com",
            password_hash="hash909",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = Project(user_id=user.id, title="Is Trashed Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        task = Task(
            project_id=project.id,
            task_number=1,
            title="Check Trashed Task",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Initially active
        assert task.is_trashed is False
        assert task.is_active is True

        # After soft delete
        task.soft_delete()
        assert task.is_trashed is True
        assert task.is_active is False
