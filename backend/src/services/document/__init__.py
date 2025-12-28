"""Document services package for learning document generation.

This package provides services for:
- AI-powered learning document generation
- Document status tracking and retrieval
- Document queue management (future)

Available Services:
- DocumentGenerationService: Generates 7-chapter learning documents from code
"""

from src.services.document.document_generation_service import DocumentGenerationService

__all__ = ["DocumentGenerationService"]
