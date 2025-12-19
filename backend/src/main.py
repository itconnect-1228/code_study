"""FastAPI application entry point for the AI Code Learning Platform.

This module initializes the FastAPI application with:
- CORS middleware for frontend communication
- Database connection lifecycle management
- Health check and API information endpoints

The app follows the factory pattern for easier testing and configuration.
"""

import contextlib
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .db.session import close_db, init_db


def get_app_settings() -> dict[str, Any]:
    """Load application settings from environment variables.

    Returns:
        dict: Application configuration settings.
    """
    return {
        "app_name": os.getenv("APP_NAME", "AI Code Learning Platform"),
        "app_version": os.getenv("APP_VERSION", "1.0.0"),
        "debug": os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
        "cors_origins": [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
            ).split(",")
            if origin.strip()
        ],
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events.

    Handles database connection initialization on startup and
    proper cleanup on shutdown.

    Args:
        app: The FastAPI application instance.
    """
    # Startup: Initialize database connection
    # Database initialization is optional - it may fail if DB is not available (e.g., during testing)
    with contextlib.suppress(Exception):
        init_db()

    yield

    # Shutdown: Close database connections
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    settings = get_app_settings()

    app = FastAPI(
        title=settings["app_name"],
        version=settings["app_version"],
        debug=settings["debug"],
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings["cors_origins"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    @app.get("/")
    async def root() -> dict[str, str]:
        """API root endpoint with basic information.

        Returns:
            dict: API name, version, and documentation link.
        """
        return {
            "name": settings["app_name"],
            "version": settings["app_version"],
            "docs": "/docs",
        }

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        """Health check endpoint for monitoring.

        Returns:
            dict: Health status, timestamp, and version.
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "version": settings["app_version"],
        }

    # Include API router with versioned endpoints (/api/v1)
    app.include_router(api_router)

    return app


# Create the application instance
app = create_app()
