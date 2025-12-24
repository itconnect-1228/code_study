"""Services package for business logic layer.

This package contains service classes that encapsulate business logic
and coordinate between API endpoints and data models.

Service Layer Benefits:
- Separation of concerns: Business logic is isolated from HTTP handling
- Testability: Services can be tested independently
- Reusability: Same service can be used by multiple endpoints

Available Services:
- ProjectService: CRUD operations for projects
- UserService: User authentication and management (auth subpackage)
- TokenService: JWT token management (auth subpackage)
"""

from src.services.project_service import ProjectService

__all__ = ["ProjectService"]
