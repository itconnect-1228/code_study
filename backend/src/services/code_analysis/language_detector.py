"""
Language Detection Service using Pygments.

Provides functions for detecting programming language from:
- File extension (reliable for known extensions)
- File content analysis (using Pygments lexer guessing)

The detected language information includes:
- Language name (e.g., "Python", "JavaScript")
- Lexer aliases (e.g., ["python", "py"])
- Common file extensions (e.g., [".py", ".pyw"])
- MIME types (e.g., ["text/x-python"])

Requirements:
- FR-019: Detect programming language from uploaded code
- FR-020: Support language detection by filename extension
- FR-021: Support content-based language guessing for paste uploads
"""

from dataclasses import dataclass
from pathlib import Path

from pygments.lexers import (
    get_lexer_for_filename,
    get_lexer_by_name,
    guess_lexer,
    get_all_lexers,
    ClassNotFound,
)
from pygments.lexer import Lexer


@dataclass(frozen=True)
class LanguageInfo:
    """
    Information about a detected programming language.

    Attributes:
        name: Human-readable language name (e.g., "Python", "JavaScript")
        aliases: Alternative names/identifiers (e.g., ["python", "py"])
        extensions: Common file extensions including dot (e.g., [".py", ".pyw"])
        mimetypes: MIME types for the language (e.g., ["text/x-python"])
        lexer_name: Pygments lexer class name for internal use
    """

    name: str
    aliases: tuple[str, ...]
    extensions: tuple[str, ...]
    mimetypes: tuple[str, ...]
    lexer_name: str

    @classmethod
    def from_lexer(cls, lexer: Lexer) -> "LanguageInfo":
        """
        Create LanguageInfo from a Pygments lexer instance.

        Args:
            lexer: A Pygments lexer instance.

        Returns:
            LanguageInfo with data extracted from the lexer.
        """
        return cls(
            name=lexer.name,
            aliases=tuple(lexer.aliases),
            extensions=tuple(lexer.filenames),
            mimetypes=tuple(lexer.mimetypes) if lexer.mimetypes else (),
            lexer_name=lexer.__class__.__name__,
        )


# Default language for unknown/undetectable content
UNKNOWN_LANGUAGE = LanguageInfo(
    name="Plain Text",
    aliases=("text", "plain"),
    extensions=(".txt",),
    mimetypes=("text/plain",),
    lexer_name="TextLexer",
)


def detect_language_by_filename(filename: str) -> LanguageInfo | None:
    """
    Detect programming language based on file extension.

    Uses Pygments' lexer registry to match file extensions.
    This is the most reliable detection method when a filename is available.

    Args:
        filename: The filename or path (only extension is used).

    Returns:
        LanguageInfo if a matching language is found, None otherwise.

    Example:
        >>> info = detect_language_by_filename("script.py")
        >>> info.name
        'Python'
        >>> info = detect_language_by_filename("main.js")
        >>> info.name
        'JavaScript'
    """
    if not filename:
        return None

    # Normalize the filename
    path = Path(filename)
    extension = path.suffix.lower()

    if not extension:
        return None

    try:
        # Get lexer for the filename
        lexer = get_lexer_for_filename(filename)
        return LanguageInfo.from_lexer(lexer)
    except ClassNotFound:
        return None


def detect_language_by_content(
    content: str,
    filename: str | None = None
) -> LanguageInfo | None:
    """
    Detect programming language by analyzing code content.

    Uses Pygments' lexer guessing algorithm which analyzes:
    - Shebang lines (#!/usr/bin/python)
    - Content patterns and keywords
    - Syntax structure

    Note: Content-based detection is less reliable than filename-based.
    When a filename is available, use detect_language_by_filename first.

    Args:
        content: The source code content to analyze.
        filename: Optional filename hint for hybrid detection.

    Returns:
        LanguageInfo if a language can be guessed, None otherwise.

    Example:
        >>> info = detect_language_by_content("def hello():\\n    print('Hello')")
        >>> info.name
        'Python'
        >>> info = detect_language_by_content("function foo() { return 42; }")
        >>> info.name
        'JavaScript'
    """
    if not content or not content.strip():
        return None

    try:
        # If filename is provided, try to use it as a hint
        if filename:
            try:
                lexer = get_lexer_for_filename(filename, code=content)
                return LanguageInfo.from_lexer(lexer)
            except ClassNotFound:
                pass

        # Fall back to pure content guessing
        lexer = guess_lexer(content)
        return LanguageInfo.from_lexer(lexer)
    except ClassNotFound:
        return None


def detect_language(
    filename: str | None = None,
    content: str | None = None
) -> LanguageInfo:
    """
    Detect programming language using the best available method.

    Detection priority:
    1. Filename extension (most reliable)
    2. Content analysis with filename hint
    3. Pure content analysis
    4. Returns UNKNOWN_LANGUAGE if all methods fail

    Args:
        filename: The filename or path (optional).
        content: The source code content (optional).

    Returns:
        LanguageInfo for the detected language, or UNKNOWN_LANGUAGE.

    Example:
        >>> info = detect_language(filename="app.py")
        >>> info.name
        'Python'
        >>> info = detect_language(content="console.log('hello');")
        >>> info.name  # May detect JavaScript or similar
        ...
    """
    # Try filename-based detection first
    if filename:
        result = detect_language_by_filename(filename)
        if result:
            return result

    # Try content-based detection
    if content:
        result = detect_language_by_content(content, filename)
        if result:
            return result

    # Return unknown language as fallback
    return UNKNOWN_LANGUAGE


def get_supported_languages() -> list[LanguageInfo]:
    """
    Get a list of all supported programming languages.

    Returns a list of LanguageInfo for every language that Pygments
    can detect. This can be used to show users which languages are
    supported for code analysis.

    Returns:
        List of LanguageInfo for all supported languages.

    Example:
        >>> languages = get_supported_languages()
        >>> len(languages) > 100  # Pygments supports many languages
        True
        >>> any(lang.name == "Python" for lang in languages)
        True
    """
    languages = []
    for name, aliases, patterns, mimetypes in get_all_lexers():
        languages.append(
            LanguageInfo(
                name=name,
                aliases=tuple(aliases),
                extensions=tuple(patterns),
                mimetypes=tuple(mimetypes) if mimetypes else (),
                lexer_name=f"{name}Lexer".replace(" ", ""),
            )
        )
    return languages


def get_language_by_name(name: str) -> LanguageInfo | None:
    """
    Get language information by name or alias.

    Args:
        name: Language name (e.g., "python") or alias (e.g., "py").

    Returns:
        LanguageInfo if found, None otherwise.

    Example:
        >>> info = get_language_by_name("python")
        >>> info.name
        'Python'
        >>> info = get_language_by_name("js")
        >>> info.name
        'JavaScript'
    """
    if not name:
        return None

    try:
        lexer = get_lexer_by_name(name.lower())
        return LanguageInfo.from_lexer(lexer)
    except ClassNotFound:
        return None


def is_language_supported(name: str) -> bool:
    """
    Check if a language is supported by name or alias.

    Args:
        name: Language name or alias to check.

    Returns:
        True if the language is supported, False otherwise.

    Example:
        >>> is_language_supported("python")
        True
        >>> is_language_supported("nonexistent-lang")
        False
    """
    return get_language_by_name(name) is not None


def get_primary_alias(language_info: LanguageInfo) -> str:
    """
    Get the primary (first) alias for a language.

    The primary alias is typically the shortest, most common name
    used to identify the language (e.g., "python" for Python).

    Args:
        language_info: The LanguageInfo to get the alias from.

    Returns:
        The primary alias, or a lowercase version of the name if no aliases.

    Example:
        >>> info = detect_language(filename="script.py")
        >>> get_primary_alias(info)
        'python'
    """
    if language_info.aliases:
        return language_info.aliases[0]
    return language_info.name.lower()


def get_extension_for_language(language_name: str) -> str | None:
    """
    Get the primary file extension for a language.

    Args:
        language_name: Language name or alias.

    Returns:
        Primary file extension (e.g., ".py") or None if not found.

    Example:
        >>> get_extension_for_language("python")
        '*.py'
        >>> get_extension_for_language("javascript")
        '*.js'
    """
    info = get_language_by_name(language_name)
    if info and info.extensions:
        # Return the first extension pattern
        ext = info.extensions[0]
        # Extract just the extension if it's a pattern like "*.py"
        if ext.startswith("*."):
            return ext
        return ext
    return None
