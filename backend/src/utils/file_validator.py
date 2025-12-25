"""
File Validation Utilities.

Provides functions for validating uploaded code files including:
- File extension validation (whitelist of allowed code file types)
- File size validation (maximum 10MB per FR-014)
- Binary file detection (reject non-text files per FR-016)
- Excluded path detection (skip .git, node_modules, etc. per FR-017)

Requirements:
- FR-014: Maximum upload size MUST be 10MB total per task
- FR-015: System MUST support these file formats: .py, .js, .html, .css, .java, .cpp, .c, .txt, .md
- FR-016: System MUST reject binary files with clear error message
- FR-017: System MUST automatically exclude .git, node_modules, .DS_Store, __pycache__
- FR-018: System MUST allow 1-20 files per upload
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

# Configuration constants
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB per FR-014
MIN_FILE_COUNT = 1  # FR-018
MAX_FILE_COUNT = 20  # FR-018

# Allowed file extensions (FR-015)
# Extended to include common code file types beyond the spec minimum
ALLOWED_EXTENSIONS: set[str] = {
    # Specified in FR-015
    ".py",    # Python
    ".js",    # JavaScript
    ".html",  # HTML
    ".css",   # CSS
    ".java",  # Java
    ".cpp",   # C++
    ".c",     # C
    ".txt",   # Text
    ".md",    # Markdown
    # Additional common code file types
    ".ts",    # TypeScript
    ".tsx",   # TypeScript React
    ".jsx",   # JavaScript React
    ".json",  # JSON
    ".xml",   # XML
    ".yaml",  # YAML
    ".yml",   # YAML alternative
    ".sql",   # SQL
    ".sh",    # Shell script
    ".bash",  # Bash script
    ".h",     # C/C++ header
    ".hpp",   # C++ header
    ".go",    # Go
    ".rs",    # Rust
    ".rb",    # Ruby
    ".php",   # PHP
    ".swift", # Swift
    ".kt",    # Kotlin
    ".scala", # Scala
    ".r",     # R
    ".vue",   # Vue.js
    ".svelte", # Svelte
}

# Excluded paths/patterns (FR-017)
# These folders/files are automatically excluded from folder uploads
EXCLUDED_PATHS: set[str] = {
    ".git",
    "node_modules",
    ".DS_Store",
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "eggs",
    "*.egg-info",
    ".eggs",
}

# Binary file signatures (magic bytes) for detection
BINARY_SIGNATURES: list[bytes] = [
    b"MZ",           # Windows executable
    b"\x89PNG",      # PNG image
    b"\xff\xd8\xff", # JPEG image
    b"GIF8",         # GIF image
    b"PK\x03\x04",   # ZIP archive
    b"\x1f\x8b",     # GZIP
    b"Rar!",         # RAR archive
    b"\x7fELF",      # ELF executable (Linux)
    b"\xca\xfe\xba\xbe",  # Mach-O (macOS)
]


@dataclass
class ValidationResult:
    """Result of a file validation check."""

    is_valid: bool
    error_message: str | None = None


def get_allowed_extensions() -> set[str]:
    """
    Get the set of allowed file extensions.

    Returns:
        Set of allowed file extensions including the leading dot.

    Example:
        >>> extensions = get_allowed_extensions()
        >>> ".py" in extensions
        True
    """
    return ALLOWED_EXTENSIONS.copy()


def validate_extension(filename: str) -> bool:
    """
    Validate if a file has an allowed extension.

    Args:
        filename: The filename or path to validate.

    Returns:
        True if the extension is allowed, False otherwise.

    Example:
        >>> validate_extension("script.py")
        True
        >>> validate_extension("program.exe")
        False
    """
    # Extract just the filename from path
    path = Path(filename)

    # Get the extension (lowercase for case-insensitive comparison)
    extension = path.suffix.lower()

    # Check if extension exists and is allowed
    if not extension:
        return False

    return extension in ALLOWED_EXTENSIONS


def validate_size(size_bytes: int) -> bool:
    """
    Validate if a file size is within the allowed limit.

    Args:
        size_bytes: The file size in bytes.

    Returns:
        True if the size is within the 10MB limit, False otherwise.

    Example:
        >>> validate_size(1024)  # 1 KB
        True
        >>> validate_size(11 * 1024 * 1024)  # 11 MB
        False
    """
    return size_bytes <= MAX_FILE_SIZE_BYTES


def is_binary_content(content: bytes) -> bool:
    """
    Detect if file content is binary (non-text).

    Uses multiple detection methods:
    1. Check for known binary file signatures (magic bytes)
    2. Check for null bytes (common in binary files)
    3. Check for high ratio of non-printable characters

    Args:
        content: The file content as bytes.

    Returns:
        True if the content appears to be binary, False if it's text.

    Example:
        >>> is_binary_content(b"print('hello')")
        False
        >>> is_binary_content(b"\\x89PNG\\r\\n")
        True
    """
    if not content:
        return False

    # Check for binary file signatures
    for signature in BINARY_SIGNATURES:
        if content.startswith(signature):
            return True

    # Check for null bytes (strong indicator of binary)
    if b"\x00" in content:
        return True

    # Sample the first 8KB for non-printable character analysis
    sample_size = min(len(content), 8192)
    sample = content[:sample_size]

    # Count non-printable characters (excluding common whitespace)
    # Printable ASCII range: 0x20 (space) to 0x7E (~)
    # Plus common whitespace: tab (0x09), newline (0x0A), carriage return (0x0D)
    non_printable_count = 0
    for byte in sample:
        if byte < 0x09 or (byte > 0x0D and byte < 0x20) or byte > 0x7E:
            # Allow high bytes for UTF-8 encoded characters (0x80-0xFF)
            if byte < 0x80:
                non_printable_count += 1

    # If more than 30% non-printable (excluding UTF-8), likely binary
    if sample_size > 0 and (non_printable_count / sample_size) > 0.30:
        return True

    return False


def is_excluded_path(path: str) -> bool:
    """
    Check if a path should be excluded from upload.

    Excluded paths include version control directories, dependency folders,
    environment files, and build artifacts.

    Args:
        path: The file or folder path to check.

    Returns:
        True if the path should be excluded, False otherwise.

    Example:
        >>> is_excluded_path(".git")
        True
        >>> is_excluded_path("node_modules/lodash")
        True
        >>> is_excluded_path("src/main.py")
        False
    """
    # Normalize path separators
    normalized_path = path.replace("\\", "/")

    # Split into parts
    parts = normalized_path.split("/")

    # Check each part of the path
    for part in parts:
        # Direct match with excluded paths
        if part in EXCLUDED_PATHS:
            return True

        # Check for .env* pattern
        if part.startswith(".env"):
            return True

    return False


def validate_file_count(count: int) -> bool:
    """
    Validate if the file count is within allowed range.

    Args:
        count: The number of files to upload.

    Returns:
        True if count is between 1 and 20 (inclusive), False otherwise.

    Example:
        >>> validate_file_count(5)
        True
        >>> validate_file_count(0)
        False
        >>> validate_file_count(21)
        False
    """
    return MIN_FILE_COUNT <= count <= MAX_FILE_COUNT


def validate_file(filename: str, content: bytes) -> ValidationResult:
    """
    Perform complete validation of a file for upload.

    Checks in order:
    1. Excluded path detection
    2. File extension validation
    3. File size validation
    4. Binary content detection

    Args:
        filename: The filename or path to validate.
        content: The file content as bytes.

    Returns:
        ValidationResult with is_valid=True if all checks pass,
        or is_valid=False with an error_message describing the failure.

    Example:
        >>> result = validate_file("script.py", b"print('hello')")
        >>> result.is_valid
        True
    """
    # Check for excluded paths first
    if is_excluded_path(filename):
        return ValidationResult(
            is_valid=False,
            error_message=f"File path is excluded: {filename}. "
                         "Common build/system folders are automatically excluded."
        )

    # Check file extension
    if not validate_extension(filename):
        allowed_list = ", ".join(sorted(ALLOWED_EXTENSIONS)[:10]) + "..."
        return ValidationResult(
            is_valid=False,
            error_message=f"Unsupported file format. "
                         f"Allowed extensions: {allowed_list}"
        )

    # Check file size
    if not validate_size(len(content)):
        size_mb = len(content) / (1024 * 1024)
        return ValidationResult(
            is_valid=False,
            error_message=f"File size ({size_mb:.1f}MB) exceeds maximum limit of 10MB."
        )

    # Check for binary content
    if is_binary_content(content):
        return ValidationResult(
            is_valid=False,
            error_message="Only source code text files are supported. "
                         "Please upload .py, .js, .html, or other text-based code files."
        )

    # All checks passed
    return ValidationResult(is_valid=True)


def validate_upload(
    files: list[tuple[str, bytes]]
) -> ValidationResult:
    """
    Validate an entire upload batch.

    Checks:
    1. File count is within allowed range (1-20)
    2. Total size is within limit (10MB)
    3. Each individual file passes validation

    Args:
        files: List of (filename, content) tuples.

    Returns:
        ValidationResult with is_valid=True if all checks pass,
        or is_valid=False with an error_message describing the first failure.

    Example:
        >>> files = [("main.py", b"print('hello')"), ("utils.py", b"def foo(): pass")]
        >>> result = validate_upload(files)
        >>> result.is_valid
        True
    """
    # Check file count
    if not validate_file_count(len(files)):
        if len(files) == 0:
            return ValidationResult(
                is_valid=False,
                error_message="No files provided. Please upload at least one file."
            )
        return ValidationResult(
            is_valid=False,
            error_message=f"Maximum 20 files per upload. "
                         f"You provided {len(files)} files."
        )

    # Check total size
    total_size = sum(len(content) for _, content in files)
    if not validate_size(total_size):
        total_mb = total_size / (1024 * 1024)
        return ValidationResult(
            is_valid=False,
            error_message=f"Total upload size ({total_mb:.1f}MB) exceeds maximum limit of 10MB."
        )

    # Validate each file
    for filename, content in files:
        result = validate_file(filename, content)
        if not result.is_valid:
            return result

    return ValidationResult(is_valid=True)
