"""API router configuration for the AI Code Learning Platform.

This module provides the main API router with versioned endpoints under /api/v1.
All API routes are organized by feature domain (auth, projects, tasks, etc.)
and mounted to the main router with appropriate prefixes.

Usage:
    from backend.src.api import api_router
    app.include_router(api_router)
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from .auth import router as auth_router
from .projects import router as projects_router

# Create the main API router with /api/v1 prefix
api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health")
async def api_health_check() -> dict[str, Any]:
    """API v1 health check endpoint.

    Provides health status with API version information.
    This is separate from the root /health endpoint and includes
    API-specific versioning information.

    Returns:
        dict: Health status with API version and timestamp.
    """
    return {
        "status": "healthy",
        "api_version": "v1",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@api_router.get("/info")
async def api_info() -> dict[str, Any]:
    """API v1 information endpoint.

    Provides information about available API endpoints and their purposes.
    This serves as a discovery endpoint for API consumers.

    Returns:
        dict: API information including version and available endpoints.
    """
    return {
        "api_version": "v1",
        "description": "AI Code Learning Platform API",
        "endpoints": {
            "health": "/api/v1/health - API health check",
            "auth": "/api/v1/auth/* - Authentication endpoints",
            "projects": "/api/v1/projects/* - Project management (coming soon)",
            "tasks": "/api/v1/tasks/* - Task management (coming soon)",
            "documents": "/api/v1/documents/* - Learning documents (coming soon)",
            "practice": "/api/v1/practice/* - Practice problems (coming soon)",
            "qa": "/api/v1/questions/* - Q&A system (coming soon)",
            "progress": "/api/v1/progress/* - Progress tracking (coming soon)",
            "trash": "/api/v1/trash/* - Trash management (coming soon)",
        },
        "documentation": "/docs",
    }


# Register routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])

# Future routers will be imported and included here as they are implemented:
# from .tasks import router as tasks_router
# from .documents import router as documents_router
# from .qa import router as qa_router
# from .progress import router as progress_router
# from .trash import router as trash_router
#
# api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
# api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
# api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
# api_router.include_router(qa_router, prefix="/questions", tags=["Q&A"])
# api_router.include_router(progress_router, prefix="/progress", tags=["Progress"])
# api_router.include_router(trash_router, prefix="/trash", tags=["Trash"])
