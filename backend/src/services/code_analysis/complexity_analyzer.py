"""
Code Complexity Analyzer Service.

Provides functions for analyzing code complexity metrics including:
- Line counts (total, code, comment, blank)
- Nesting depth analysis
- Function and class counting
- Complexity level determination

Supports multiple programming languages:
- Python
- JavaScript/TypeScript
- Java
- C/C++

Requirements:
- Research §6: Code complexity assessment (line count, nesting depth, function count)
- Data Model: complexity_level ('beginner', 'intermediate', 'advanced')
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import TypedDict


class ComplexityLevel(Enum):
    """Complexity level classification for code."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LineCountResult(TypedDict):
    """Result of line counting analysis."""

    total: int
    code: int
    comment: int
    blank: int


class NestingDepthResult(TypedDict):
    """Result of nesting depth analysis."""

    max_depth: int
    average_depth: float


@dataclass(frozen=True)
class CodeComplexity:
    """
    Comprehensive code complexity metrics.

    Attributes:
        total_lines: Total number of lines in the code.
        code_lines: Number of lines containing actual code.
        comment_lines: Number of lines that are comments.
        blank_lines: Number of empty or whitespace-only lines.
        max_nesting_depth: Maximum indentation/nesting depth found.
        average_nesting_depth: Average nesting depth across the code.
        function_count: Number of function/method definitions.
        class_count: Number of class definitions.
        complexity_level: Overall complexity classification.
    """

    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    max_nesting_depth: int
    average_nesting_depth: float
    function_count: int
    class_count: int
    complexity_level: ComplexityLevel


# Language-specific comment patterns
COMMENT_PATTERNS: dict[str, dict[str, list[str]]] = {
    "python": {
        "line": [r"^\s*#"],
        "block_start": [r'^\s*"""', r"^\s*'''"],
        "block_end": [r'"""', r"'''"],
    },
    "javascript": {
        "line": [r"^\s*//"],
        "block_start": [r"/\*"],
        "block_end": [r"\*/"],
    },
    "typescript": {
        "line": [r"^\s*//"],
        "block_start": [r"/\*"],
        "block_end": [r"\*/"],
    },
    "java": {
        "line": [r"^\s*//"],
        "block_start": [r"/\*"],
        "block_end": [r"\*/"],
    },
    "c": {
        "line": [r"^\s*//"],
        "block_start": [r"/\*"],
        "block_end": [r"\*/"],
    },
    "cpp": {
        "line": [r"^\s*//"],
        "block_start": [r"/\*"],
        "block_end": [r"\*/"],
    },
}

# Function patterns for different languages
FUNCTION_PATTERNS: dict[str, list[str]] = {
    "python": [
        r"^\s*(?:async\s+)?def\s+\w+\s*\(",
    ],
    "javascript": [
        r"^\s*(?:async\s+)?function\s+\w+\s*\(",
        r"^\s*(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?function",
        r"^\s*(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
        r"^\s*(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\w+\s*=>",
        r"^\s*\w+\s*\([^)]*\)\s*\{",  # Method definitions
    ],
    "typescript": [
        r"^\s*(?:async\s+)?function\s+\w+",
        r"^\s*(?:export\s+)?(?:const|let|var)\s+\w+\s*(?::\s*\w+\s*)?=\s*(?:async\s+)?\(",
        r"^\s*(?:export\s+)?(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?function",
        r"^\s*\w+\s*\([^)]*\)\s*(?::\s*\w+)?\s*\{",  # Method definitions
    ],
    "java": [
        r"^\s*(?:public|private|protected|static|\s)*\s+\w+\s+\w+\s*\([^)]*\)\s*(?:throws\s+\w+(?:\s*,\s*\w+)*)?\s*\{",
    ],
    "c": [
        r"^\s*(?:static\s+)?(?:inline\s+)?(?:unsigned\s+)?(?:const\s+)?(?:void|int|char|float|double|long|short|bool|\w+(?:\s*\*)*)\s+\w+\s*\([^)]*\)\s*\{",
    ],
    "cpp": [
        r"^\s*(?:static\s+)?(?:inline\s+)?(?:virtual\s+)?(?:const\s+)?(?:void|int|char|float|double|long|short|bool|\w+(?:\s*\*)*|\w+::\w+)\s+(?:\w+::)?\w+\s*\([^)]*\)\s*(?:const)?\s*(?:override)?\s*\{",
    ],
}

# Class patterns for different languages
CLASS_PATTERNS: dict[str, list[str]] = {
    "python": [
        r"^\s*class\s+\w+",
    ],
    "javascript": [
        r"^\s*class\s+\w+",
    ],
    "typescript": [
        r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+\w+",
    ],
    "java": [
        r"^\s*(?:public\s+|private\s+|protected\s+)?(?:abstract\s+)?(?:final\s+)?class\s+\w+",
    ],
    "c": [],  # C doesn't have classes
    "cpp": [
        r"^\s*(?:template\s*<[^>]*>\s*)?class\s+\w+",
        r"^\s*struct\s+\w+",
    ],
}

# Nesting increase patterns (blocks that increase nesting)
NESTING_PATTERNS: dict[str, list[str]] = {
    "python": [
        r"^\s*(?:def|async\s+def|class|if|elif|else|for|while|try|except|finally|with|match|case)\b",
    ],
    "javascript": [
        r"\{",
    ],
    "typescript": [
        r"\{",
    ],
    "java": [
        r"\{",
    ],
    "c": [
        r"\{",
    ],
    "cpp": [
        r"\{",
    ],
}


def _normalize_language(language: str | None) -> str:
    """Normalize language name to lowercase standard form."""
    if not language:
        return "python"  # Default to Python

    lang = language.lower().strip()

    # Handle common aliases
    aliases = {
        "py": "python",
        "python3": "python",
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "c++": "cpp",
    }

    return aliases.get(lang, lang)


def count_lines(content: str, language: str | None = None) -> LineCountResult:
    """
    Count lines in code by category.

    Categorizes lines as:
    - code: Lines containing actual code
    - comment: Lines that are comments (line or block)
    - blank: Empty or whitespace-only lines

    Args:
        content: The source code content.
        language: Programming language for comment detection.

    Returns:
        Dictionary with 'total', 'code', 'comment', 'blank' counts.
    """
    if not content:
        return {"total": 0, "code": 0, "comment": 0, "blank": 0}

    lang = _normalize_language(language)
    lines = content.split("\n")
    total = len(lines)

    blank_count = 0
    comment_count = 0
    code_count = 0

    in_block_comment = False
    patterns = COMMENT_PATTERNS.get(lang, COMMENT_PATTERNS["python"])

    line_comment_patterns = [re.compile(p) for p in patterns.get("line", [])]
    block_start_patterns = patterns.get("block_start", [])
    block_end_patterns = patterns.get("block_end", [])

    for line in lines:
        stripped = line.strip()

        # Check for blank line
        if not stripped:
            blank_count += 1
            continue

        # Check for block comment state
        if in_block_comment:
            comment_count += 1
            for end_pattern in block_end_patterns:
                if re.search(end_pattern, line):
                    in_block_comment = False
            continue

        # Check for block comment start
        for i, start_pattern in enumerate(block_start_patterns):
            if re.search(start_pattern, line):
                # Check if it ends on the same line
                if i < len(block_end_patterns):
                    end_pattern = block_end_patterns[i]
                    # For Python docstrings, need to check if it's a single line
                    if lang == "python":
                        # Count occurrences of the pattern
                        quote = '"""' if '"""' in stripped else "'''"
                        if stripped.count(quote) >= 2:
                            # Single line docstring, treat as comment
                            comment_count += 1
                            continue
                    if not re.search(
                        end_pattern,
                        line[line.index(start_pattern[0]) + 1 :]
                        if start_pattern[0] in "/\"'"
                        else line,
                    ):
                        in_block_comment = True
                comment_count += 1
                break
        else:
            # Check for line comments
            is_comment = any(p.match(stripped) for p in line_comment_patterns)
            if is_comment:
                comment_count += 1
            else:
                code_count += 1

    return {
        "total": total,
        "code": code_count,
        "comment": comment_count,
        "blank": blank_count,
    }


def calculate_nesting_depth(
    content: str, language: str | None = None
) -> NestingDepthResult:
    """
    Calculate nesting depth metrics for code.

    For brace-based languages (JS, Java, C), counts brace nesting.
    For Python, analyzes indentation levels.

    Args:
        content: The source code content.
        language: Programming language for pattern matching.

    Returns:
        Dictionary with 'max_depth' and 'average_depth'.
    """
    if not content or not content.strip():
        return {"max_depth": 0, "average_depth": 0.0}

    lang = _normalize_language(language)
    lines = content.split("\n")

    if lang == "python":
        # Python uses indentation for nesting
        return _calculate_python_nesting(lines)
    else:
        # Brace-based languages
        return _calculate_brace_nesting(content)


def _calculate_python_nesting(lines: list[str]) -> NestingDepthResult:
    """Calculate nesting depth for Python based on indentation."""
    depths = []
    base_indent = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Calculate indent level
        leading_spaces = len(line) - len(line.lstrip())

        # Detect indent unit (spaces per level)
        if base_indent is None and leading_spaces > 0:
            base_indent = leading_spaces

        if base_indent and base_indent > 0:
            depth = leading_spaces // base_indent
        else:
            depth = 0

        depths.append(depth)

    if not depths:
        return {"max_depth": 0, "average_depth": 0.0}

    max_depth = max(depths)
    avg_depth = sum(depths) / len(depths)

    return {"max_depth": max_depth, "average_depth": round(avg_depth, 2)}


def _calculate_brace_nesting(content: str) -> NestingDepthResult:
    """Calculate nesting depth for brace-based languages."""
    depths = []
    current_depth = 0

    # Track string and comment state to avoid counting braces in strings/comments
    in_string = False
    string_char = None
    in_line_comment = False
    in_block_comment = False

    i = 0
    while i < len(content):
        char = content[i]
        prev_char = content[i - 1] if i > 0 else ""

        # Handle newlines
        if char == "\n":
            in_line_comment = False
            depths.append(current_depth)
            i += 1
            continue

        # Skip if in line comment
        if in_line_comment:
            i += 1
            continue

        # Handle block comments
        if in_block_comment:
            if char == "*" and i + 1 < len(content) and content[i + 1] == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        # Check for comment start
        if not in_string:
            if char == "/" and i + 1 < len(content):
                next_char = content[i + 1]
                if next_char == "/":
                    in_line_comment = True
                    i += 2
                    continue
                elif next_char == "*":
                    in_block_comment = True
                    i += 2
                    continue

        # Handle strings
        if char in "\"'" and prev_char != "\\":
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
            i += 1
            continue

        # Count braces if not in string/comment
        if not in_string and not in_line_comment and not in_block_comment:
            if char == "{":
                current_depth += 1
            elif char == "}":
                current_depth = max(0, current_depth - 1)

        i += 1

    if not depths:
        depths.append(current_depth)

    max_depth = max(depths) if depths else 0
    avg_depth = sum(depths) / len(depths) if depths else 0.0

    return {"max_depth": max_depth, "average_depth": round(avg_depth, 2)}


def count_functions(content: str, language: str | None = None) -> int:
    """
    Count function/method definitions in code.

    Supports multiple language patterns including:
    - Python: def, async def
    - JavaScript: function, arrow functions, methods
    - TypeScript: typed functions
    - Java: method definitions
    - C/C++: function definitions

    Args:
        content: The source code content.
        language: Programming language for pattern matching.

    Returns:
        Number of function definitions found.
    """
    if not content:
        return 0

    lang = _normalize_language(language)
    patterns = FUNCTION_PATTERNS.get(lang, FUNCTION_PATTERNS["python"])

    count = 0
    lines = content.split("\n")

    for line in lines:
        for pattern in patterns:
            if re.search(pattern, line):
                count += 1
                break  # Count each line only once

    return count


def count_classes(content: str, language: str | None = None) -> int:
    """
    Count class definitions in code.

    Supports:
    - Python: class
    - JavaScript/TypeScript: class
    - Java: class
    - C++: class, struct

    Args:
        content: The source code content.
        language: Programming language for pattern matching.

    Returns:
        Number of class definitions found.
    """
    if not content:
        return 0

    lang = _normalize_language(language)
    patterns = CLASS_PATTERNS.get(lang, CLASS_PATTERNS["python"])

    count = 0
    lines = content.split("\n")

    for line in lines:
        for pattern in patterns:
            if re.search(pattern, line):
                count += 1
                break  # Count each line only once

    return count


def determine_complexity_level(
    total_lines: int,
    max_nesting_depth: int,
    function_count: int,
    class_count: int,
) -> ComplexityLevel:
    """
    Determine overall complexity level based on metrics.

    Scoring algorithm:
    - Lines: <50 = 0, 50-200 = 1, 200-500 = 2, >500 = 3
    - Nesting: <3 = 0, 3-4 = 1, 5-6 = 2, >6 = 3
    - Functions: <5 = 0, 5-15 = 1, 15-30 = 2, >30 = 3
    - Classes: <2 = 0, 2-5 = 1, 5-10 = 2, >10 = 3

    Total score:
    - 0-3: Beginner
    - 4-7: Intermediate
    - 8+: Advanced

    Args:
        total_lines: Total lines of code.
        max_nesting_depth: Maximum nesting depth.
        function_count: Number of functions.
        class_count: Number of classes.

    Returns:
        ComplexityLevel enum value.
    """
    score = 0

    # Line count scoring
    if total_lines >= 500:
        score += 3
    elif total_lines >= 200:
        score += 2
    elif total_lines >= 50:
        score += 1

    # Nesting depth scoring
    if max_nesting_depth > 6:
        score += 3
    elif max_nesting_depth >= 5:
        score += 2
    elif max_nesting_depth >= 3:
        score += 1

    # Function count scoring
    if function_count > 30:
        score += 3
    elif function_count >= 15:
        score += 2
    elif function_count >= 5:
        score += 1

    # Class count scoring
    if class_count > 10:
        score += 3
    elif class_count >= 5:
        score += 2
    elif class_count >= 2:
        score += 1

    # Determine level based on score
    if score >= 8:
        return ComplexityLevel.ADVANCED
    elif score >= 4:
        return ComplexityLevel.INTERMEDIATE
    else:
        return ComplexityLevel.BEGINNER


def analyze_complexity(content: str, language: str | None = None) -> CodeComplexity:
    """
    Analyze code complexity and return comprehensive metrics.

    Performs full analysis including:
    - Line counting (total, code, comment, blank)
    - Nesting depth analysis
    - Function and class counting
    - Complexity level determination

    Args:
        content: The source code content to analyze.
        language: Optional programming language hint.

    Returns:
        CodeComplexity dataclass with all metrics.

    Example:
        >>> result = analyze_complexity("def foo(): pass", language="python")
        >>> result.function_count
        1
        >>> result.complexity_level
        <ComplexityLevel.BEGINNER: 'beginner'>
    """
    # Get line counts
    line_counts = count_lines(content, language)

    # Get nesting depth
    nesting = calculate_nesting_depth(content, language)

    # Count functions and classes
    func_count = count_functions(content, language)
    class_count = count_classes(content, language)

    # Determine complexity level
    level = determine_complexity_level(
        total_lines=line_counts["total"],
        max_nesting_depth=nesting["max_depth"],
        function_count=func_count,
        class_count=class_count,
    )

    return CodeComplexity(
        total_lines=line_counts["total"],
        code_lines=line_counts["code"],
        comment_lines=line_counts["comment"],
        blank_lines=line_counts["blank"],
        max_nesting_depth=nesting["max_depth"],
        average_nesting_depth=nesting["average_depth"],
        function_count=func_count,
        class_count=class_count,
        complexity_level=level,
    )
