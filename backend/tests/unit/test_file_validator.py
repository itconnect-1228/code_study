"""
Unit tests for file validation utilities.

Tests for file extension, size, binary detection, and excluded paths validation.
Follows TDD cycle: RED -> GREEN -> REFACTOR
"""


class TestFileExtensionValidation:
    """Tests for file extension validation functionality."""

    def test_validate_extension_accepts_python_files(self):
        """Python .py files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("script.py") is True

    def test_validate_extension_accepts_javascript_files(self):
        """JavaScript .js files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("app.js") is True

    def test_validate_extension_accepts_html_files(self):
        """HTML .html files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("index.html") is True

    def test_validate_extension_accepts_css_files(self):
        """CSS .css files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("styles.css") is True

    def test_validate_extension_accepts_java_files(self):
        """Java .java files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("Main.java") is True

    def test_validate_extension_accepts_cpp_files(self):
        """C++ .cpp files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("main.cpp") is True

    def test_validate_extension_accepts_c_files(self):
        """C .c files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("main.c") is True

    def test_validate_extension_accepts_txt_files(self):
        """Text .txt files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("readme.txt") is True

    def test_validate_extension_accepts_md_files(self):
        """Markdown .md files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("README.md") is True

    def test_validate_extension_accepts_typescript_files(self):
        """TypeScript .ts files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("app.ts") is True

    def test_validate_extension_accepts_tsx_files(self):
        """TypeScript React .tsx files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("component.tsx") is True

    def test_validate_extension_accepts_jsx_files(self):
        """React .jsx files should be accepted."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("component.jsx") is True

    def test_validate_extension_rejects_exe_files(self):
        """Executable .exe files should be rejected."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("program.exe") is False

    def test_validate_extension_rejects_dll_files(self):
        """DLL .dll files should be rejected."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("library.dll") is False

    def test_validate_extension_rejects_image_files(self):
        """Image files should be rejected."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("photo.jpg") is False
        assert validate_extension("image.png") is False
        assert validate_extension("icon.gif") is False

    def test_validate_extension_rejects_zip_files(self):
        """Archive .zip files should be rejected."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("archive.zip") is False

    def test_validate_extension_case_insensitive(self):
        """Extension validation should be case insensitive."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("Script.PY") is True
        assert validate_extension("App.JS") is True
        assert validate_extension("README.MD") is True

    def test_validate_extension_with_path(self):
        """Should work with full file paths."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("/path/to/script.py") is True
        assert validate_extension("folder/subfolder/app.js") is True

    def test_validate_extension_with_multiple_dots(self):
        """Should handle filenames with multiple dots."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("file.test.py") is True
        assert validate_extension("my.app.component.tsx") is True

    def test_validate_extension_no_extension(self):
        """Files without extension should be rejected."""
        from src.utils.file_validator import validate_extension

        assert validate_extension("Makefile") is False
        assert validate_extension("Dockerfile") is False


class TestFileSizeValidation:
    """Tests for file size validation functionality."""

    def test_validate_size_accepts_small_file(self):
        """Small files under 10MB should be accepted."""
        from src.utils.file_validator import validate_size

        # 1 KB
        assert validate_size(1024) is True

    def test_validate_size_accepts_10mb_file(self):
        """Exactly 10MB files should be accepted."""
        from src.utils.file_validator import validate_size

        # 10 MB in bytes
        assert validate_size(10 * 1024 * 1024) is True

    def test_validate_size_rejects_over_10mb(self):
        """Files over 10MB should be rejected."""
        from src.utils.file_validator import validate_size

        # 10 MB + 1 byte
        assert validate_size(10 * 1024 * 1024 + 1) is False

    def test_validate_size_rejects_large_file(self):
        """Large files should be rejected."""
        from src.utils.file_validator import validate_size

        # 50 MB
        assert validate_size(50 * 1024 * 1024) is False

    def test_validate_size_accepts_zero_bytes(self):
        """Zero byte files should be accepted."""
        from src.utils.file_validator import validate_size

        assert validate_size(0) is True

    def test_validate_size_accepts_typical_code_file(self):
        """Typical code file sizes should be accepted."""
        from src.utils.file_validator import validate_size

        # 50 KB - typical code file
        assert validate_size(50 * 1024) is True


class TestBinaryDetection:
    """Tests for binary file detection functionality."""

    def test_is_binary_detects_text_content(self):
        """Text content should be detected as non-binary."""
        from src.utils.file_validator import is_binary_content

        text_content = b"def hello():\n    print('Hello, World!')\n"
        assert is_binary_content(text_content) is False

    def test_is_binary_detects_utf8_text(self):
        """UTF-8 text content should be detected as non-binary."""
        from src.utils.file_validator import is_binary_content

        utf8_content = "안녕하세요. Hello, World!".encode()
        assert is_binary_content(utf8_content) is False

    def test_is_binary_detects_null_bytes(self):
        """Content with null bytes should be detected as binary."""
        from src.utils.file_validator import is_binary_content

        binary_content = b"Hello\x00World"
        assert is_binary_content(binary_content) is True

    def test_is_binary_detects_exe_header(self):
        """EXE file header should be detected as binary."""
        from src.utils.file_validator import is_binary_content

        # Windows PE executable header
        exe_header = b"MZ\x90\x00\x03\x00\x00\x00"
        assert is_binary_content(exe_header) is True

    def test_is_binary_detects_png_header(self):
        """PNG file header should be detected as binary."""
        from src.utils.file_validator import is_binary_content

        png_header = b"\x89PNG\r\n\x1a\n"
        assert is_binary_content(png_header) is True

    def test_is_binary_detects_jpg_header(self):
        """JPEG file header should be detected as binary."""
        from src.utils.file_validator import is_binary_content

        jpg_header = b"\xff\xd8\xff\xe0"
        assert is_binary_content(jpg_header) is True

    def test_is_binary_detects_pdf_header(self):
        """PDF file header should be detected as binary."""
        from src.utils.file_validator import is_binary_content

        pdf_header = b"%PDF-1.4\n"
        # PDFs contain binary data after header
        pdf_content = pdf_header + b"\x00\x01\x02"
        assert is_binary_content(pdf_content) is True

    def test_is_binary_handles_empty_content(self):
        """Empty content should be detected as non-binary."""
        from src.utils.file_validator import is_binary_content

        assert is_binary_content(b"") is False

    def test_is_binary_accepts_html_content(self):
        """HTML content should be detected as non-binary."""
        from src.utils.file_validator import is_binary_content

        html_content = b"<!DOCTYPE html>\n<html>\n<head>\n</head>\n</html>"
        assert is_binary_content(html_content) is False

    def test_is_binary_accepts_json_content(self):
        """JSON content should be detected as non-binary."""
        from src.utils.file_validator import is_binary_content

        json_content = b'{"name": "test", "value": 123}'
        assert is_binary_content(json_content) is False


class TestExcludedPathsValidation:
    """Tests for excluded paths detection functionality."""

    def test_is_excluded_path_detects_git_folder(self):
        """'.git' folder should be excluded."""
        from src.utils.file_validator import is_excluded_path

        assert is_excluded_path(".git") is True
        assert is_excluded_path(".git/objects") is True
        assert is_excluded_path("project/.git/HEAD") is True

    def test_is_excluded_path_detects_node_modules(self):
        """'node_modules' folder should be excluded."""
        from src.utils.file_validator import is_excluded_path

        assert is_excluded_path("node_modules") is True
        assert is_excluded_path("node_modules/lodash") is True
        assert is_excluded_path("frontend/node_modules/react") is True

    def test_is_excluded_path_detects_ds_store(self):
        """'.DS_Store' file should be excluded."""
        from src.utils.file_validator import is_excluded_path

        assert is_excluded_path(".DS_Store") is True
        assert is_excluded_path("folder/.DS_Store") is True

    def test_is_excluded_path_detects_pycache(self):
        """'__pycache__' folder should be excluded."""
        from src.utils.file_validator import is_excluded_path

        assert is_excluded_path("__pycache__") is True
        assert is_excluded_path("src/__pycache__") is True
        assert is_excluded_path("backend/src/__pycache__/module.pyc") is True

    def test_is_excluded_path_detects_venv(self):
        """Virtual environment folders should be excluded."""
        from src.utils.file_validator import is_excluded_path

        assert is_excluded_path("venv") is True
        assert is_excluded_path(".venv") is True
        assert is_excluded_path("project/venv/lib") is True

    def test_is_excluded_path_detects_env_files(self):
        """'.env' files should be excluded."""
        from src.utils.file_validator import is_excluded_path

        assert is_excluded_path(".env") is True
        assert is_excluded_path(".env.local") is True
        assert is_excluded_path("config/.env.production") is True

    def test_is_excluded_path_allows_regular_files(self):
        """Regular code files should not be excluded."""
        from src.utils.file_validator import is_excluded_path

        assert is_excluded_path("main.py") is False
        assert is_excluded_path("src/app.js") is False
        assert is_excluded_path("components/Button.tsx") is False

    def test_is_excluded_path_allows_regular_folders(self):
        """Regular folders should not be excluded."""
        from src.utils.file_validator import is_excluded_path

        assert is_excluded_path("src") is False
        assert is_excluded_path("components") is False
        assert is_excluded_path("utils") is False


class TestFileCountValidation:
    """Tests for file count validation functionality."""

    def test_validate_file_count_accepts_single_file(self):
        """Single file upload should be accepted."""
        from src.utils.file_validator import validate_file_count

        assert validate_file_count(1) is True

    def test_validate_file_count_accepts_20_files(self):
        """20 files (maximum) should be accepted."""
        from src.utils.file_validator import validate_file_count

        assert validate_file_count(20) is True

    def test_validate_file_count_rejects_21_files(self):
        """21 files (over maximum) should be rejected."""
        from src.utils.file_validator import validate_file_count

        assert validate_file_count(21) is False

    def test_validate_file_count_rejects_zero_files(self):
        """Zero files should be rejected."""
        from src.utils.file_validator import validate_file_count

        assert validate_file_count(0) is False

    def test_validate_file_count_rejects_large_count(self):
        """Large file count should be rejected."""
        from src.utils.file_validator import validate_file_count

        assert validate_file_count(100) is False


class TestValidationResult:
    """Tests for the validation result dataclass."""

    def test_validation_result_success(self):
        """ValidationResult should represent success state."""
        from src.utils.file_validator import ValidationResult

        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.error_message is None

    def test_validation_result_failure_with_message(self):
        """ValidationResult should include error message on failure."""
        from src.utils.file_validator import ValidationResult

        result = ValidationResult(is_valid=False, error_message="File too large")
        assert result.is_valid is False
        assert result.error_message == "File too large"


class TestValidateFile:
    """Tests for the main validate_file function."""

    def test_validate_file_accepts_valid_python_file(self):
        """Valid Python file should pass all validations."""
        from src.utils.file_validator import validate_file

        content = b"def hello():\n    print('Hello')\n"
        result = validate_file("script.py", content)

        assert result.is_valid is True

    def test_validate_file_rejects_binary_content(self):
        """Binary content should be rejected."""
        from src.utils.file_validator import validate_file

        binary_content = b"\x89PNG\r\n\x1a\n\x00\x00"
        result = validate_file("image.py", binary_content)

        assert result.is_valid is False
        # Error message should indicate text files only (user-friendly wording)
        assert (
            "text" in result.error_message.lower()
            or "source code" in result.error_message.lower()
        )

    def test_validate_file_rejects_invalid_extension(self):
        """Invalid file extension should be rejected."""
        from src.utils.file_validator import validate_file

        content = b"print('hello')"
        result = validate_file("program.exe", content)

        assert result.is_valid is False
        assert (
            "extension" in result.error_message.lower()
            or "format" in result.error_message.lower()
        )

    def test_validate_file_rejects_large_file(self):
        """File over 10MB should be rejected."""
        from src.utils.file_validator import validate_file

        # 11 MB content
        large_content = b"x" * (11 * 1024 * 1024)
        result = validate_file("large.py", large_content)

        assert result.is_valid is False
        assert "size" in result.error_message.lower()

    def test_validate_file_rejects_excluded_path(self):
        """Excluded paths should be rejected."""
        from src.utils.file_validator import validate_file

        content = b"config = {}"
        result = validate_file("node_modules/package/index.js", content)

        assert result.is_valid is False
        assert "excluded" in result.error_message.lower()


class TestGetAllowedExtensions:
    """Tests for retrieving allowed extensions list."""

    def test_get_allowed_extensions_returns_set(self):
        """Should return a set of allowed extensions."""
        from src.utils.file_validator import get_allowed_extensions

        extensions = get_allowed_extensions()
        assert isinstance(extensions, set)

    def test_get_allowed_extensions_includes_common_types(self):
        """Should include all common code file extensions."""
        from src.utils.file_validator import get_allowed_extensions

        extensions = get_allowed_extensions()
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".html" in extensions
        assert ".css" in extensions
        assert ".java" in extensions
        assert ".cpp" in extensions
        assert ".c" in extensions
        assert ".txt" in extensions
        assert ".md" in extensions
