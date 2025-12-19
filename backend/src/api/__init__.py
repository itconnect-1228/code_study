"""API router structure for the AI Code Learning Platform.

This module provides the main API router with versioned endpoints under /api/v1.
All API routes are organized by feature domain (auth, projects, tasks, etc.)
and mounted to the main router with appropriate prefixes.

Usage:
    from backend.src.api import api_router
    app.include_router(api_router)
"""

from fastapi import APIRouter

# Create the main API router with /api/v1 prefix
api_router = APIRouter(prefix="/api/v1")


@api_router.get("/")
async def api_root() -> dict[str, str]:
    """API v1 root endpoint.

    Returns:
        dict: API version information.
    """
    return {
        "api_version": "v1",
        "status": "active",
    }


# Future routers will be imported and included here as they are implemented:
# from .auth import router as auth_router
# from .projects import router as projects_router
# from .tasks import router as tasks_router
# from .documents import router as documents_router
# from .qa import router as qa_router
# from .progress import router as progress_router
# from .trash import router as trash_router
#
# api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
# api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
# api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
# api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
# api_router.include_router(qa_router, prefix="/questions", tags=["Q&A"])
# api_router.include_router(progress_router, prefix="/progress", tags=["Progress"])
# api_router.include_router(trash_router, prefix="/trash", tags=["Trash"])

__all__ = ["api_router"]
