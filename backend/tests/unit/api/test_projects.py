"""Unit tests for project API endpoints.

This module tests the project API endpoints:
- GET /projects - List user's projects
- POST /projects - Create new project
- GET /projects/{project_id} - Get project by ID
- PATCH /projects/{project_id} - Update project
- DELETE /projects/{project_id} - Soft delete project

All tests use the async test client and isolated database sessions.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth.user_service import UserService
from src.services.project_service import ProjectService


class TestGetProjectsEndpoint:
    """Tests for GET /projects endpoint (T046)."""

    @pytest.mark.asyncio
    async def test_get_projects_requires_authentication(
        self,
        async_client: AsyncClient,
    ):
        """Test that GET /projects requires authentication."""
        response = await async_client.get("/api/v1/projects")

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_get_projects_empty_list(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /projects returns empty list when user has no projects."""
        # Create and login user
        user_service = UserService(db_session)
        await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        # Login to get token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "Password123!",
            },
        )
        assert login_response.status_code == 200

        # Get projects
        response = await async_client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert "total" in data
        assert data["projects"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_projects_returns_user_projects(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /projects returns user's projects."""
        # Create and login user
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        # Create projects for user
        project_service = ProjectService(db_session)
        await project_service.create(user.id, "Project 1", "Description 1")
        await project_service.create(user.id, "Project 2", "Description 2")
        await db_session.commit()

        # Login to get token
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Get projects
        response = await async_client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 2
        assert data["total"] == 2

        # Verify project data
        project_titles = {p["title"] for p in data["projects"]}
        assert "Project 1" in project_titles
        assert "Project 2" in project_titles

    @pytest.mark.asyncio
    async def test_get_projects_excludes_trashed_by_default(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /projects excludes trashed projects by default."""
        # Create and login user
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        # Create projects
        project_service = ProjectService(db_session)
        await project_service.create(user.id, "Active Project")
        trashed_project = await project_service.create(user.id, "Trashed Project")
        await db_session.commit()

        # Trash one project
        await project_service.soft_delete(trashed_project.id)
        await db_session.commit()

        # Login
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Get projects (should only show active)
        response = await async_client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 1
        assert data["total"] == 1
        assert data["projects"][0]["title"] == "Active Project"

    @pytest.mark.asyncio
    async def test_get_projects_only_returns_own_projects(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /projects only returns authenticated user's projects."""
        # Create two users
        user_service = UserService(db_session)
        user1 = await user_service.register("user1@example.com", "Password123!")
        user2 = await user_service.register("user2@example.com", "Password123!")
        await db_session.commit()

        # Create projects for both users
        project_service = ProjectService(db_session)
        await project_service.create(user1.id, "User 1 Project")
        await project_service.create(user2.id, "User 2 Project")
        await db_session.commit()

        # Login as user1
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user1@example.com", "password": "Password123!"},
        )

        # Get projects (should only see user1's project)
        response = await async_client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 1
        assert data["total"] == 1
        assert data["projects"][0]["title"] == "User 1 Project"


class TestCreateProjectEndpoint:
    """Tests for POST /projects endpoint (T047)."""

    @pytest.mark.asyncio
    async def test_create_project_requires_authentication(
        self,
        async_client: AsyncClient,
    ):
        """Test that POST /projects requires authentication."""
        response = await async_client.post(
            "/api/v1/projects",
            json={"title": "New Project"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_project_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful project creation."""
        # Create and login user
        user_service = UserService(db_session)
        await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Create project
        response = await async_client.post(
            "/api/v1/projects",
            json={
                "title": "My New Project",
                "description": "Project description",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My New Project"
        assert data["description"] == "Project description"
        assert "id" in data
        assert data["deletion_status"] == "active"

    @pytest.mark.asyncio
    async def test_create_project_without_description(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test project creation without optional description."""
        # Create and login user
        user_service = UserService(db_session)
        await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Create project without description
        response = await async_client.post(
            "/api/v1/projects",
            json={"title": "My Project"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My Project"
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_create_project_empty_title_fails(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test project creation with empty title fails."""
        # Create and login user
        user_service = UserService(db_session)
        await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Try to create project with empty title
        response = await async_client.post(
            "/api/v1/projects",
            json={"title": ""},
        )

        assert response.status_code == 422


class TestGetProjectEndpoint:
    """Tests for GET /projects/{project_id} endpoint (T048)."""

    @pytest.mark.asyncio
    async def test_get_project_requires_authentication(
        self,
        async_client: AsyncClient,
    ):
        """Test that GET /projects/{id} requires authentication."""
        response = await async_client.get(
            "/api/v1/projects/00000000-0000-0000-0000-000000000001"
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_project_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful project retrieval."""
        # Create and login user
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        # Create project
        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "My Project", "Description")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Get project
        response = await async_client.get(f"/api/v1/projects/{project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "My Project"
        assert data["description"] == "Description"
        assert data["id"] == str(project.id)

    @pytest.mark.asyncio
    async def test_get_project_not_found(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /projects/{id} returns 404 for non-existent project."""
        # Create and login user
        user_service = UserService(db_session)
        await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Try to get non-existent project
        response = await async_client.get(
            "/api/v1/projects/00000000-0000-0000-0000-000000000001"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_project_forbidden_for_other_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test GET /projects/{id} returns 403 for other user's project."""
        # Create two users
        user_service = UserService(db_session)
        user1 = await user_service.register("user1@example.com", "Password123!")
        await user_service.register("user2@example.com", "Password123!")
        await db_session.commit()

        # Create project for user1
        project_service = ProjectService(db_session)
        project = await project_service.create(user1.id, "User1 Project")
        await db_session.commit()

        # Login as user2
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user2@example.com", "password": "Password123!"},
        )

        # Try to get user1's project
        response = await async_client.get(f"/api/v1/projects/{project.id}")

        assert response.status_code == 403


class TestUpdateProjectEndpoint:
    """Tests for PATCH /projects/{project_id} endpoint (T049)."""

    @pytest.mark.asyncio
    async def test_update_project_requires_authentication(
        self,
        async_client: AsyncClient,
    ):
        """Test that PATCH /projects/{id} requires authentication."""
        response = await async_client.patch(
            "/api/v1/projects/00000000-0000-0000-0000-000000000001",
            json={"title": "New Title"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_project_title_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful project title update."""
        # Create and login user
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        # Create project
        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "Original Title")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Update project
        response = await async_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"title": "New Title"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"

    @pytest.mark.asyncio
    async def test_update_project_description_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful project description update."""
        # Create and login user
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        # Create project
        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "My Project", "Old desc")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Update project
        response = await async_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"description": "New description"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_update_project_not_found(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test PATCH /projects/{id} returns 404 for non-existent project."""
        # Create and login user
        user_service = UserService(db_session)
        await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Try to update non-existent project
        response = await async_client.patch(
            "/api/v1/projects/00000000-0000-0000-0000-000000000001",
            json={"title": "New Title"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project_forbidden_for_other_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test PATCH /projects/{id} returns 403 for other user's project."""
        # Create two users
        user_service = UserService(db_session)
        user1 = await user_service.register("user1@example.com", "Password123!")
        await user_service.register("user2@example.com", "Password123!")
        await db_session.commit()

        # Create project for user1
        project_service = ProjectService(db_session)
        project = await project_service.create(user1.id, "User1 Project")
        await db_session.commit()

        # Login as user2
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user2@example.com", "password": "Password123!"},
        )

        # Try to update user1's project
        response = await async_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"title": "Hacked Title"},
        )

        assert response.status_code == 403


class TestDeleteProjectEndpoint:
    """Tests for DELETE /projects/{project_id} endpoint (T050)."""

    @pytest.mark.asyncio
    async def test_delete_project_requires_authentication(
        self,
        async_client: AsyncClient,
    ):
        """Test that DELETE /projects/{id} requires authentication."""
        response = await async_client.delete(
            "/api/v1/projects/00000000-0000-0000-0000-000000000001"
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_project_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful project soft delete."""
        # Create and login user
        user_service = UserService(db_session)
        user = await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        # Create project
        project_service = ProjectService(db_session)
        project = await project_service.create(user.id, "My Project")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Delete project
        response = await async_client.delete(f"/api/v1/projects/{project.id}")

        assert response.status_code == 204

        # Verify project is trashed (not in active list)
        list_response = await async_client.get("/api/v1/projects")
        assert list_response.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_delete_project_not_found(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test DELETE /projects/{id} returns 404 for non-existent project."""
        # Create and login user
        user_service = UserService(db_session)
        await user_service.register("user@example.com", "Password123!")
        await db_session.commit()

        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
        )

        # Try to delete non-existent project
        response = await async_client.delete(
            "/api/v1/projects/00000000-0000-0000-0000-000000000001"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_forbidden_for_other_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test DELETE /projects/{id} returns 403 for other user's project."""
        # Create two users
        user_service = UserService(db_session)
        user1 = await user_service.register("user1@example.com", "Password123!")
        await user_service.register("user2@example.com", "Password123!")
        await db_session.commit()

        # Create project for user1
        project_service = ProjectService(db_session)
        project = await project_service.create(user1.id, "User1 Project")
        await db_session.commit()

        # Login as user2
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user2@example.com", "password": "Password123!"},
        )

        # Try to delete user1's project
        response = await async_client.delete(f"/api/v1/projects/{project.id}")

        assert response.status_code == 403
