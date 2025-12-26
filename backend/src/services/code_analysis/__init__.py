"""Code analysis services for the learning platform.

This package provides services for analyzing uploaded code including:
- Language detection using Pygments
- Code complexity analysis
- File storage and management
"""

from .language_detector import (
    LanguageInfo,
    detect_language_by_filename,
    detect_language_by_content,
    detect_language,
    get_supported_languages,
    get_language_by_name,
)

from .complexity_analyzer import (
    CodeComplexity,
    ComplexityLevel,
    analyze_complexity,
    count_lines,
    calculate_nesting_depth,
    count_functions,
    count_classes,
    determine_complexity_level,
)

__all__ = [
    # Language detection
    "LanguageInfo",
    "detect_language_by_filename",
    "detect_language_by_content",
    "detect_language",
    "get_supported_languages",
    "get_language_by_name",
    # Complexity analysis
    "CodeComplexity",
    "ComplexityLevel",
    "analyze_complexity",
    "count_lines",
    "calculate_nesting_depth",
    "count_functions",
    "count_classes",
    "determine_complexity_level",
]
