"""Unit tests for document API endpoints.

This module tests the document API endpoints:
- GET /tasks/{task_id}/document - Get learning document for a task
- GET /tasks/{task_id}/document/status - Get document generation status

All tests use the async test client and isolated database sessions.
TDD approach: These tests are written BEFORE the implementation.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.learning_document import LearningDocument
from src.services.auth.user_service import UserService
from src.services.project_service import ProjectService
from src.services.task_service import TaskService

# Sample complete document content for testing
SAMPLE_DOCUMENT_CONTENT = {
    "chapter1": {"title": "What This Code Does", "summary": "Test summary"},
    "chapter2": {"title": "Prerequisites", "concepts": ["concept1", "concept2"]},
    "chapter3": {
        "title": "Code Structure",
        "flowchart": "graph TD",
        "file_breakdown": {},
    },
    "chapter4": {
        "title": "Line-by-Line",
        "explanations": [{"line": 1, "explanation": "test"}],
    },
    "chapter5": {"title": "Execution Flow", "steps": ["step1", "step2"]},
    "chapter6": {
        "title": "Core Concepts",
        "concepts": [{"name": "test", "description": "test"}],
    },
    "chapter7": {
        "title": "Common Mistakes",
        "mistakes": [{"mistake": "test", "fix": "test"}],
    },
}


class TestGetDocumentEndpoint:
    """Tests for GET /tasks/{task_id}/document endpoint (T097)."""

    @pytest.mark.asyncio
    async def test_get_document_requires_authentication(
        self,
        async_client: AsyncClient,
    ):
        """Test that GET /tasks/{id}/document requires authentication."""
        response = await async_client.get(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000001/document"
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_get_document_task_not_found(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document returns 404 for non-existent task."""
        # Create and login user
        user_service = UserService(db_session)
        await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Try to get document for non-existent task
        response = await async_client.get(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000001/document"
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_document_forbidden_for_other_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document returns 404 for other user's task."""
        # Create two users
        user_service = UserService(db_session)
        user1 = await user_service.register("user1@example.com", "Password123!")
        await user_service.register("user2@example.com", "Password123!")
        await db_session.commit()

        # Create project and task for user1
        project_service = ProjectService(db_session)
        project = await project_service.create(user1.id, "User1 Project")
        await db_session.commit()

        task_service = TaskService(db_session)
        task = await task_service.create(
            project.id, "User1 Task Title", upload_method="file"
        )
        await db_session.commit()

        # Login as user2
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user2@example.com", "password": "Password123!"},
        )

        # Try to get document for user1's task (should return 404 for security)
        response = await async_client.get(f"/api/v1/tasks/{task.id}/document")

        # Return 404 instead of 403 for security (don't reveal task existence)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_not_found_when_no_document(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document returns 404 when document doesn't exist."""
        # Create user, project, and task
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "My Project")
        await db_session.commit()

        task_service = TaskService(db_session)
        task = await task_service.create(
            project.id, "My Task Title", upload_method="file"
        )
        await db_session.commit()

        # Login
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Try to get document (none exists)
        response = await async_client.get(f"/api/v1/tasks/{task.id}/document")

        assert response.status_code == 404
        data = response.json()
        assert "document" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_document_success_with_completed_document(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document returns document when completed."""
        # Create user, project, and task
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "My Project")
        await db_session.commit()

        task_service = TaskService(db_session)
        task = await task_service.create(
            project.id, "My Task Title", upload_method="file"
        )
        await db_session.commit()

        # Create completed document
        document = LearningDocument(
            task_id=task.id,
            content=SAMPLE_DOCUMENT_CONTENT,
            generation_status="completed",
        )
        db_session.add(document)
        await db_session.commit()

        # Login
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Get document
        response = await async_client.get(f"/api/v1/tasks/{task.id}/document")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(document.id)
        assert data["task_id"] == str(task.id)
        assert data["generation_status"] == "completed"
        assert "content" in data
        assert "chapter1" in data["content"]
        assert data["content"]["chapter1"]["title"] == "What This Code Does"

    @pytest.mark.asyncio
    async def test_get_document_returns_pending_document(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document returns document even when pending."""
        # Create user, project, and task
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "My Project")
        await db_session.commit()

        task_service = TaskService(db_session)
        task = await task_service.create(
            project.id, "My Task Title", upload_method="file"
        )
        await db_session.commit()

        # Create pending document with placeholder content
        placeholder_content = {
            "chapter1": {"title": "Generating...", "summary": ""},
            "chapter2": {"title": "Generating...", "concepts": []},
            "chapter3": {
                "title": "Generating...",
                "flowchart": "",
                "file_breakdown": {},
            },
            "chapter4": {"title": "Generating...", "explanations": []},
            "chapter5": {"title": "Generating...", "steps": []},
            "chapter6": {"title": "Generating...", "concepts": []},
            "chapter7": {"title": "Generating...", "mistakes": []},
        }
        document = LearningDocument(
            task_id=task.id,
            content=placeholder_content,
            generation_status="pending",
        )
        db_session.add(document)
        await db_session.commit()

        # Login
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Get document
        response = await async_client.get(f"/api/v1/tasks/{task.id}/document")

        assert response.status_code == 200
        data = response.json()
        assert data["generation_status"] == "pending"


class TestGetDocumentStatusEndpoint:
    """Tests for GET /tasks/{task_id}/document/status endpoint (T098)."""

    @pytest.mark.asyncio
    async def test_get_document_status_requires_authentication(
        self,
        async_client: AsyncClient,
    ):
        """Test that GET /tasks/{id}/document/status requires authentication."""
        response = await async_client.get(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000001/document/status"
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_get_document_status_task_not_found(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document/status returns 404 for non-existent task."""
        # Create and login user
        user_service = UserService(db_session)
        await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Try to get status for non-existent task
        response = await async_client.get(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000001/document/status"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_status_forbidden_for_other_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document/status returns 404 for other user's task."""
        # Create two users
        user_service = UserService(db_session)
        user1 = await user_service.register("user1@example.com", "Password123!")
        await user_service.register("user2@example.com", "Password123!")
        await db_session.commit()

        # Create project and task for user1
        project_service = ProjectService(db_session)
        project = await project_service.create(user1.id, "User1 Project")
        await db_session.commit()

        task_service = TaskService(db_session)
        task = await task_service.create(
            project.id, "User1 Task Title", upload_method="file"
        )
        await db_session.commit()

        # Login as user2
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user2@example.com", "password": "Password123!"},
        )

        # Try to get status for user1's task
        response = await async_client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_status_not_found_when_no_document(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document/status returns not_found status when no document."""
        # Create user, project, and task
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "My Project")
        await db_session.commit()

        task_service = TaskService(db_session)
        task = await task_service.create(
            project.id, "My Task Title", upload_method="file"
        )
        await db_session.commit()

        # Login
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Get status (no document exists)
        response = await async_client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_get_document_status_pending(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document/status returns pending status."""
        # Create user, project, and task
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "My Project")
        await db_session.commit()

        task_service = TaskService(db_session)
        task = await task_service.create(
            project.id, "My Task Title", upload_method="file"
        )
        await db_session.commit()

        # Create pending document
        placeholder_content = {
            "chapter1": {"title": "Generating...", "summary": ""},
            "chapter2": {"title": "Generating...", "concepts": []},
            "chapter3": {
                "title": "Generating...",
                "flowchart": "",
                "file_breakdown": {},
            },
            "chapter4": {"title": "Generating...", "explanations": []},
            "chapter5": {"title": "Generating...", "steps": []},
            "chapter6": {"title": "Generating...", "concepts": []},
            "chapter7": {"title": "Generating...", "mistakes": []},
        }
        document = LearningDocument(
            task_id=task.id,
            content=placeholder_content,
            generation_status="pending",
        )
        db_session.add(document)
        await db_session.commit()

        # Login
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Get status
        response = await async_client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "started_at" in data
        assert data["started_at"] is None

    @pytest.mark.asyncio
    async def test_get_document_status_in_progress(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document/status returns in_progress status with timing."""
        from datetime import UTC, datetime

        # Create user, project, and task
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "My Project")
        await db_session.commit()

        task_service = TaskService(db_session)
        task = await task_service.create(
            project.id, "My Task Title", upload_method="file"
        )
        await db_session.commit()

        # Create in_progress document
        placeholder_content = {
            "chapter1": {"title": "Generating...", "summary": ""},
            "chapter2": {"title": "Generating...", "concepts": []},
            "chapter3": {
                "title": "Generating...",
                "flowchart": "",
                "file_breakdown": {},
            },
            "chapter4": {"title": "Generating...", "explanations": []},
            "chapter5": {"title": "Generating...", "steps": []},
            "chapter6": {"title": "Generating...", "concepts": []},
            "chapter7": {"title": "Generating...", "mistakes": []},
        }
        document = LearningDocument(
            task_id=task.id,
            content=placeholder_content,
            generation_status="in_progress",
            generation_started_at=datetime.now(UTC),
        )
        db_session.add(document)
        await db_session.commit()

        # Login
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Get status
        response = await async_client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["started_at"] is not None
        assert "estimated_time_remaining" in data

    @pytest.mark.asyncio
    async def test_get_document_status_completed(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document/status returns completed status."""
        from datetime import UTC, datetime

        # Create user, project, and task
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "My Project")
        await db_session.commit()

        task_service = TaskService(db_session)
        task = await task_service.create(
            project.id, "My Task Title", upload_method="file"
        )
        await db_session.commit()

        # Create completed document
        document = LearningDocument(
            task_id=task.id,
            content=SAMPLE_DOCUMENT_CONTENT,
            generation_status="completed",
            generation_started_at=datetime.now(UTC),
            generation_completed_at=datetime.now(UTC),
        )
        db_session.add(document)
        await db_session.commit()

        # Login
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Get status
        response = await async_client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["started_at"] is not None
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_get_document_status_failed(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /tasks/{id}/document/status returns failed status with error."""
        from datetime import UTC, datetime

        # Create user, project, and task
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "My Project")
        await db_session.commit()

        task_service = TaskService(db_session)
        task = await task_service.create(
            project.id, "My Task Title", upload_method="file"
        )
        await db_session.commit()

        # Create failed document
        placeholder_content = {
            "chapter1": {"title": "Failed", "summary": ""},
            "chapter2": {"title": "Failed", "concepts": []},
            "chapter3": {"title": "Failed", "flowchart": "", "file_breakdown": {}},
            "chapter4": {"title": "Failed", "explanations": []},
            "chapter5": {"title": "Failed", "steps": []},
            "chapter6": {"title": "Failed", "concepts": []},
            "chapter7": {"title": "Failed", "mistakes": []},
        }
        document = LearningDocument(
            task_id=task.id,
            content=placeholder_content,
            generation_status="failed",
            generation_started_at=datetime.now(UTC),
            generation_completed_at=datetime.now(UTC),
            generation_error="API rate limit exceeded",
        )
        db_session.add(document)
        await db_session.commit()

        # Login
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Get status
        response = await async_client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "error" in data
        assert data["error"] == "API rate limit exceeded"
