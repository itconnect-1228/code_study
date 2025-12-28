"""FastAPI application entry point for the AI Code Learning Platform.

This module initializes the FastAPI application with:
- CORS middleware for frontend communication
- Database connection lifecycle management
- Health check and API information endpoints

The app follows the factory pattern for easier testing and configuration.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Configure logging to stdout for Railway
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
print("=== Backend Starting ===", flush=True)

# Load .env file if it exists (for local development)
# In production (Railway), environment variables are set directly
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .api.exceptions import add_exception_handlers
from .db.session import close_db, init_db

logger = logging.getLogger(__name__)


def get_app_settings() -> dict[str, Any]:
    """Load application settings from environment variables.

    Returns:
        dict: Application configuration settings.
    """
    cors_origins_env = os.getenv("CORS_ORIGINS", "")

    # Parse CORS origins from environment variable
    if cors_origins_env:
        cors_origins = [
            origin.strip()
            for origin in cors_origins_env.split(",")
            if origin.strip()
        ]
    else:
        # Default for local development
        cors_origins = ["http://localhost:3000", "http://localhost:5173"]

    # Log CORS configuration for debugging
    logger.info(f"CORS_ORIGINS env: {cors_origins_env!r}")
    logger.info(f"Parsed CORS origins: {cors_origins}")

    return {
        "app_name": os.getenv("APP_NAME", "AI Code Learning Platform"),
        "app_version": os.getenv("APP_VERSION", "1.0.0"),
        "debug": os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
        "cors_origins": cors_origins,
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
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

    # Shutdown: Close database connections
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    print("=== Creating FastAPI app ===", flush=True)
    settings = get_app_settings()
    print(f"=== Settings loaded: CORS origins = {settings['cors_origins']} ===", flush=True)

    app = FastAPI(
        title=settings["app_name"],
        version=settings["app_version"],
        debug=settings["debug"],
        lifespan=lifespan,
    )
    print("=== FastAPI instance created ===", flush=True)

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings["cors_origins"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print("=== CORS middleware added ===", flush=True)

    # Register exception handlers
    add_exception_handlers(app)

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
