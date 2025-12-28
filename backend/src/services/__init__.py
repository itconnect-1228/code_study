"""Services package for business logic layer.

This package contains service classes that encapsulate business logic
and coordinate between API endpoints and data models.

Service Layer Benefits:
- Separation of concerns: Business logic is isolated from HTTP handling
- Testability: Services can be tested independently
- Reusability: Same service can be used by multiple endpoints

Available Services:
- ProjectService: CRUD operations for projects
  - create, get_by_id, get_by_user, update, soft_delete
  - validate_ownership: Authorization check for project access
- UserService: User authentication and management (auth subpackage)
- TokenService: JWT token management (auth subpackage)
- GeminiClient: Google Gemini API wrapper (ai subpackage)
  - generate: Generic content generation
  - generate_document: 7-chapter learning document generation
  - generate_qa_response: Q&A response generation
- DocumentGenerationService: AI-powered learning document generation (document subpackage)
  - generate_document: Generate 7-chapter learning document from code
  - get_document_by_task: Retrieve document for a task
  - get_generation_status: Get current generation status
  - retry_failed_document: Retry failed generation
"""

from src.services.project_service import ProjectService
from src.services.document import DocumentGenerationService

__all__ = ["ProjectService", "DocumentGenerationService"]
