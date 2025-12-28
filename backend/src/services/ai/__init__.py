"""AI services package for LLM integration.

This package provides interfaces for AI/LLM services used in document generation,
practice problem creation, and Q&A features.

Available Services:
- GeminiClient: Google Gemini API wrapper with retry logic and structured output
- PromptBuilder: Builder for 7-chapter document generation prompts
- PracticePromptBuilder: Builder for practice problem generation prompts
- QAPromptBuilder: Builder for Q&A response prompts
"""

from src.services.ai.gemini_client import (
    ContentType,
    GeminiClient,
    GeminiConfig,
    GeminiContentFilterError,
    GeminiError,
    GeminiRateLimitError,
    GeminiResponse,
    GeminiTimeoutError,
)
from src.services.ai.prompts import (
    DOCUMENT_JSON_SCHEMA,
    SYSTEM_INSTRUCTION_DOCUMENT,
    SYSTEM_INSTRUCTION_PRACTICE,
    SYSTEM_INSTRUCTION_QA,
    PracticePromptBuilder,
    PromptBuilder,
    QAPromptBuilder,
    create_document_prompt,
    create_practice_prompt,
    create_qa_prompt,
)

__all__ = [
    # Gemini Client
    "GeminiClient",
    "GeminiConfig",
    "GeminiResponse",
    "GeminiError",
    "GeminiRateLimitError",
    "GeminiContentFilterError",
    "GeminiTimeoutError",
    "ContentType",
    # Prompt Builders
    "PromptBuilder",
    "PracticePromptBuilder",
    "QAPromptBuilder",
    # System Instructions
    "SYSTEM_INSTRUCTION_DOCUMENT",
    "SYSTEM_INSTRUCTION_PRACTICE",
    "SYSTEM_INSTRUCTION_QA",
    # Schemas
    "DOCUMENT_JSON_SCHEMA",
    # Convenience Functions
    "create_document_prompt",
    "create_practice_prompt",
    "create_qa_prompt",
]
