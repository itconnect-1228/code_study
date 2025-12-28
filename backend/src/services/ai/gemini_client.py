"""
Gemini API Client Wrapper.

Provides a high-level interface for interacting with Google's Gemini API.
Features:
- Async-compatible API calls
- Exponential backoff retry logic
- Structured JSON output support
- Safety settings for educational content
- Request/response logging
- Error handling with custom exceptions

Requirements:
- FR-021: AI integration for document generation
- FR-083: Performance target < 3 minutes for 500 LOC
- FR-087: Q&A responses < 10 seconds
- research.md: Retry up to 3 times with exponential backoff
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import google.generativeai as genai
from google.generativeai.types import (
    HarmCategory,
    HarmBlockThreshold,
    GenerationConfig,
)
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Type of content generation request."""

    DOCUMENT = "document"  # 7-chapter learning document
    PRACTICE = "practice"  # Practice problems with hints
    QA = "qa"  # Q&A responses


@dataclass(frozen=True)
class GeminiConfig:
    """
    Configuration for Gemini API client.

    Attributes:
        api_key: Google AI API key
        model: Model identifier (e.g., "gemini-2.5-flash")
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts for failed requests
        base_delay: Base delay for exponential backoff (seconds)
    """

    api_key: str
    model: str = "gemini-3-flash-preview"
    timeout: int = 180
    max_retries: int = 3
    base_delay: float = 1.0

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """
        Create configuration from environment variables.

        Environment variables:
        - GEMINI_API_KEY: Required API key
        - GEMINI_MODEL: Model name (default: gemini-2.5-flash)
        - AI_REQUEST_TIMEOUT: Timeout in seconds (default: 180)
        - AI_MAX_RETRIES: Max retry attempts (default: 3)

        Raises:
            ValueError: If GEMINI_API_KEY is not set
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required. "
                "Get your API key from https://makersuite.google.com/app/apikey"
            )

        return cls(
            api_key=api_key,
            model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
            timeout=int(os.getenv("AI_REQUEST_TIMEOUT", "180")),
            max_retries=int(os.getenv("AI_MAX_RETRIES", "3")),
        )


@dataclass
class GeminiResponse:
    """
    Response from Gemini API call.

    Attributes:
        content: The generated text content
        json_content: Parsed JSON if response was structured
        usage: Token usage statistics
        model: Model that generated the response
        finish_reason: Why the generation stopped
        latency_ms: Request latency in milliseconds
    """

    content: str
    json_content: dict[str, Any] | None = None
    usage: dict[str, int] = field(default_factory=dict)
    model: str = ""
    finish_reason: str = ""
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "content": self.content,
            "json_content": self.json_content,
            "usage": self.usage,
            "model": self.model,
            "finish_reason": self.finish_reason,
            "latency_ms": self.latency_ms,
        }


class GeminiError(Exception):
    """Base exception for Gemini API errors."""

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None,
        retry_count: int = 0,
    ):
        super().__init__(message)
        self.original_error = original_error
        self.retry_count = retry_count


class GeminiRateLimitError(GeminiError):
    """Raised when API rate limit is exceeded."""

    pass


class GeminiContentFilterError(GeminiError):
    """Raised when content is blocked by safety filters."""

    pass


class GeminiTimeoutError(GeminiError):
    """Raised when request times out."""

    pass


class GeminiClient:
    """
    Google Gemini API client wrapper.

    Provides async-compatible methods for generating content with:
    - Automatic retry logic with exponential backoff
    - Structured JSON output support
    - Safety settings for educational content
    - Comprehensive logging

    Example:
        >>> config = GeminiConfig.from_env()
        >>> client = GeminiClient(config)
        >>> response = await client.generate(
        ...     prompt="Explain Python functions to a beginner",
        ...     content_type=ContentType.DOCUMENT
        ... )
        >>> print(response.content)
    """

    # Safety settings for beginner-appropriate educational content
    SAFETY_SETTINGS = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    # Default generation configs by content type
    GENERATION_CONFIGS = {
        ContentType.DOCUMENT: GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
        ),
        ContentType.PRACTICE: GenerationConfig(
            temperature=0.8,
            top_p=0.95,
            top_k=40,
            max_output_tokens=4096,
        ),
        ContentType.QA: GenerationConfig(
            temperature=0.7,
            top_p=0.90,
            top_k=40,
            max_output_tokens=2048,
        ),
    }

    def __init__(self, config: GeminiConfig | None = None):
        """
        Initialize Gemini client.

        Args:
            config: Configuration settings. If None, loads from environment.
        """
        self.config = config or GeminiConfig.from_env()
        genai.configure(api_key=self.config.api_key)
        self._model = genai.GenerativeModel(
            model_name=self.config.model,
            safety_settings=self.SAFETY_SETTINGS,
        )
        logger.info(
            f"GeminiClient initialized with model: {self.config.model}, "
            f"timeout: {self.config.timeout}s, max_retries: {self.config.max_retries}"
        )

    async def generate(
        self,
        prompt: str,
        content_type: ContentType = ContentType.DOCUMENT,
        system_instruction: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> GeminiResponse:
        """
        Generate content using Gemini API.

        Args:
            prompt: The input prompt for generation
            content_type: Type of content (affects generation config)
            system_instruction: Optional system-level instruction
            response_schema: Optional JSON schema for structured output

        Returns:
            GeminiResponse with generated content

        Raises:
            GeminiError: On API errors after retries exhausted
            GeminiRateLimitError: When rate limit is exceeded
            GeminiContentFilterError: When content is blocked
            GeminiTimeoutError: When request times out
        """
        generation_config = self.GENERATION_CONFIGS.get(
            content_type,
            self.GENERATION_CONFIGS[ContentType.DOCUMENT],
        )

        # Configure JSON mode if schema is provided
        if response_schema:
            generation_config = GenerationConfig(
                temperature=generation_config.temperature,
                top_p=generation_config.top_p,
                top_k=generation_config.top_k,
                max_output_tokens=generation_config.max_output_tokens,
                response_mime_type="application/json",
            )

        # Create model with system instruction if provided
        model = self._model
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=self.config.model,
                safety_settings=self.SAFETY_SETTINGS,
                system_instruction=system_instruction,
            )

        return await self._generate_with_retry(
            model=model,
            prompt=prompt,
            generation_config=generation_config,
            content_type=content_type,
        )

    async def generate_document(
        self,
        code: str,
        language: str,
        filename: str | None = None,
        additional_context: str | None = None,
    ) -> GeminiResponse:
        """
        Generate a 7-chapter learning document for code.

        This is a convenience method for document generation with
        pre-configured system instruction and formatting.

        Args:
            code: Source code to analyze and explain
            language: Programming language (e.g., "Python", "JavaScript")
            filename: Optional original filename for context
            additional_context: Optional extra context about the code

        Returns:
            GeminiResponse with structured document content
        """
        system_instruction = (
            "You are an expert programming teacher explaining code to complete beginners "
            "with zero programming knowledge. Always use everyday language, real-life "
            "analogies, and step-by-step explanations. Avoid technical jargon - if you "
            "must use a technical term, explain it immediately with a simple analogy."
        )

        file_context = f" (from file: {filename})" if filename else ""
        extra_context = f"\n\nAdditional Context:\n{additional_context}" if additional_context else ""

        prompt = f"""Analyze the following {language} code{file_context} and create a comprehensive learning document.

Code:
```{language.lower()}
{code}
```
{extra_context}

Generate a 7-chapter learning document with the following structure:
1. Summary: Brief overview of what the code does (2-3 sentences)
2. Prerequisites: 5 key concepts needed to understand this code, each with:
   - Concept name
   - Simple explanation (1-2 sentences)
   - Real-life analogy
3. Structure: High-level code structure and flow
4. Line-by-Line: Detailed explanation of each significant line or block
5. Key Concepts: Deep dive into important programming concepts used
6. Common Mistakes: Potential errors and misconceptions beginners might have
7. Next Steps: What to learn next based on this code

Format your response as JSON with this structure:
{{
    "summary": "...",
    "prerequisites": [
        {{"name": "...", "explanation": "...", "analogy": "..."}}
    ],
    "structure": "...",
    "line_by_line": [
        {{"lines": "1-3", "code": "...", "explanation": "..."}}
    ],
    "key_concepts": [
        {{"concept": "...", "explanation": "...", "example": "..."}}
    ],
    "common_mistakes": [
        {{"mistake": "...", "why": "...", "fix": "..."}}
    ],
    "next_steps": [
        {{"topic": "...", "reason": "..."}}
    ]
}}"""

        response = await self.generate(
            prompt=prompt,
            content_type=ContentType.DOCUMENT,
            system_instruction=system_instruction,
            response_schema={"type": "object"},  # Enable JSON mode
        )

        # Parse JSON response
        if response.content:
            try:
                response.json_content = json.loads(response.content)
            except json.JSONDecodeError:
                logger.warning("Failed to parse document response as JSON")

        return response

    async def generate_qa_response(
        self,
        question: str,
        code_context: str,
        document_context: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> GeminiResponse:
        """
        Generate a Q&A response about code.

        Args:
            question: User's question
            code_context: Relevant code snippet
            document_context: Optional context from learning document
            conversation_history: Optional previous Q&A for context

        Returns:
            GeminiResponse with answer
        """
        system_instruction = (
            "You are a patient programming tutor answering questions from complete beginners. "
            "Always provide clear, concise answers with examples. Use analogies when helpful. "
            "If the question is about specific code, reference line numbers when relevant."
        )

        history_text = ""
        if conversation_history:
            history_text = "\n\nPrevious conversation:\n"
            for entry in conversation_history[-5:]:  # Last 5 exchanges
                history_text += f"Q: {entry.get('question', '')}\nA: {entry.get('answer', '')}\n\n"

        doc_context = ""
        if document_context:
            doc_context = f"\n\nRelevant documentation:\n{document_context}"

        prompt = f"""Answer the following question about this code:

Code:
```
{code_context}
```
{doc_context}
{history_text}

Question: {question}

Provide a clear, beginner-friendly answer. Include:
1. Direct answer to the question
2. Simple explanation using analogies if helpful
3. Code example if relevant
4. Related concepts the beginner might want to learn"""

        return await self.generate(
            prompt=prompt,
            content_type=ContentType.QA,
            system_instruction=system_instruction,
        )

    async def _generate_with_retry(
        self,
        model: genai.GenerativeModel,
        prompt: str,
        generation_config: GenerationConfig,
        content_type: ContentType,
    ) -> GeminiResponse:
        """
        Execute generation with exponential backoff retry.

        Args:
            model: The generative model to use
            prompt: Input prompt
            generation_config: Generation parameters
            content_type: Type of content being generated

        Returns:
            GeminiResponse on success

        Raises:
            GeminiError: On failure after all retries
        """
        last_error: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                start_time = time.time()

                logger.debug(
                    f"Gemini request attempt {attempt + 1}/{self.config.max_retries + 1} "
                    f"for {content_type.value}"
                )

                # Run sync API call in executor for async compatibility
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: model.generate_content(
                            prompt,
                            generation_config=generation_config,
                        ),
                    ),
                    timeout=self.config.timeout,
                )

                latency_ms = (time.time() - start_time) * 1000

                # Extract response data
                content = ""
                finish_reason = ""

                if response.candidates:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        content = candidate.content.parts[0].text
                    finish_reason = str(candidate.finish_reason) if candidate.finish_reason else ""

                # Extract usage stats
                usage = {}
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    usage = {
                        "prompt_tokens": getattr(
                            response.usage_metadata, "prompt_token_count", 0
                        ),
                        "completion_tokens": getattr(
                            response.usage_metadata, "candidates_token_count", 0
                        ),
                        "total_tokens": getattr(
                            response.usage_metadata, "total_token_count", 0
                        ),
                    }

                logger.info(
                    f"Gemini request completed: {content_type.value}, "
                    f"latency={latency_ms:.0f}ms, tokens={usage.get('total_tokens', 'N/A')}"
                )

                return GeminiResponse(
                    content=content,
                    usage=usage,
                    model=self.config.model,
                    finish_reason=finish_reason,
                    latency_ms=latency_ms,
                )

            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(
                    f"Gemini request timeout after {self.config.timeout}s "
                    f"(attempt {attempt + 1}/{self.config.max_retries + 1})"
                )
                if attempt == self.config.max_retries:
                    raise GeminiTimeoutError(
                        f"Request timed out after {self.config.timeout}s",
                        original_error=e,
                        retry_count=attempt + 1,
                    )

            except google_exceptions.ResourceExhausted as e:
                last_error = e
                logger.warning(
                    f"Gemini rate limit exceeded (attempt {attempt + 1}/{self.config.max_retries + 1})"
                )
                if attempt == self.config.max_retries:
                    raise GeminiRateLimitError(
                        "API rate limit exceeded. Please try again later.",
                        original_error=e,
                        retry_count=attempt + 1,
                    )

            except google_exceptions.InvalidArgument as e:
                # Content filter or invalid prompt - don't retry
                error_msg = str(e)
                if "safety" in error_msg.lower() or "block" in error_msg.lower():
                    raise GeminiContentFilterError(
                        "Content was blocked by safety filters. Please modify your input.",
                        original_error=e,
                        retry_count=attempt + 1,
                    )
                raise GeminiError(
                    f"Invalid request: {error_msg}",
                    original_error=e,
                    retry_count=attempt + 1,
                )

            except Exception as e:
                last_error = e
                logger.error(
                    f"Gemini request failed (attempt {attempt + 1}/{self.config.max_retries + 1}): {e}"
                )
                if attempt == self.config.max_retries:
                    raise GeminiError(
                        f"Request failed after {self.config.max_retries + 1} attempts: {e}",
                        original_error=e,
                        retry_count=attempt + 1,
                    )

            # Exponential backoff before retry
            if attempt < self.config.max_retries:
                delay = self.config.base_delay * (2**attempt)
                logger.info(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)

        # Should not reach here, but just in case
        raise GeminiError(
            "Unexpected error in retry logic",
            original_error=last_error,
            retry_count=self.config.max_retries + 1,
        )

    def get_model_info(self) -> dict[str, Any]:
        """
        Get information about the configured model.

        Returns:
            Dictionary with model name, config, and safety settings
        """
        return {
            "model": self.config.model,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
            "safety_settings": {
                str(k): str(v) for k, v in self.SAFETY_SETTINGS.items()
            },
        }

    async def health_check(self) -> bool:
        """
        Check if the Gemini API is accessible.

        Returns:
            True if API is reachable and responding

        Example:
            >>> client = GeminiClient()
            >>> is_healthy = await client.health_check()
            >>> print(f"Gemini API status: {'OK' if is_healthy else 'UNAVAILABLE'}")
        """
        try:
            response = await self.generate(
                prompt="Say 'OK' if you can hear me.",
                content_type=ContentType.QA,
            )
            return bool(response.content)
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False
