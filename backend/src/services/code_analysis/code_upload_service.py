"""Code upload service for handling file, folder, and paste uploads.

This module provides the CodeUploadService class which handles:
- Single file upload
- Multiple file upload (folder)
- Paste code upload
- Language detection
- Complexity analysis
- Storage management

Architecture Notes:
- Service Layer Pattern: Business logic separated from API layer
- Integrates with FileStorageService for file management
- Uses language_detector and complexity_analyzer for code analysis
- Creates UploadedCode and CodeFile records in database

Example:
    from src.services.code_analysis.code_upload_service import CodeUploadService

    service = CodeUploadService(db=session, storage=storage_service)
    result = await service.upload_file(
        user_id=user.id,
        task_id=task.id,
        filename="main.py",
        content=b"print('hello')"
    )
"""

from dataclasses import dataclass
from pathlib import Path as PathLib
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.code_file import CodeFile
from src.models.uploaded_code import UploadedCode
from src.services.code_analysis.complexity_analyzer import analyze_complexity
from src.services.code_analysis.file_storage import FileStorageService
from src.services.code_analysis.language_detector import detect_language


# Language to file extension mapping
LANGUAGE_EXTENSIONS = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "java": ".java",
    "c": ".c",
    "cpp": ".cpp",
    "c++": ".cpp",
    "csharp": ".cs",
    "c#": ".cs",
    "go": ".go",
    "rust": ".rs",
    "ruby": ".rb",
    "php": ".php",
    "swift": ".swift",
    "kotlin": ".kt",
    "scala": ".scala",
    "html": ".html",
    "css": ".css",
    "sql": ".sql",
    "shell": ".sh",
    "bash": ".sh",
    "powershell": ".ps1",
    "yaml": ".yaml",
    "json": ".json",
    "xml": ".xml",
    "markdown": ".md",
}


@dataclass
class UploadResult:
    """Result of a code upload operation."""

    uploaded_code: UploadedCode
    code_files: list[CodeFile]


class CodeUploadService:
    """Service for handling code uploads."""

    def __init__(
        self,
        db: AsyncSession,
        storage: FileStorageService,
    ) -> None:
        self.db = db
        self.storage = storage

    async def upload_file(
        self,
        user_id: UUID,
        task_id: UUID,
        filename: str,
        content: bytes,
    ) -> UploadResult:
        return await self.upload_files(
            user_id=user_id,
            task_id=task_id,
            files=[(filename, content)],
        )

    async def upload_files(
        self,
        user_id: UUID,
        task_id: UUID,
        files: list[tuple[str, bytes]],
    ) -> UploadResult:
        file_infos = self.storage.save_files(user_id, task_id, files)

        total_size = sum(len(content) for _, content in files)
        total_lines = 0
        all_content = b""

        for _, content in files:
            all_content += content + b"\n"
            total_lines += content.count(b"\n") + 1

        try:
            decoded_content = all_content.decode("utf-8", errors="replace")
        except Exception:
            decoded_content = ""

        first_filename = files[0][0] if files else "unknown.txt"
        lang_info = detect_language(first_filename, decoded_content)
        detected_language = lang_info.name.lower() if lang_info else None

        if decoded_content:
            complexity_result = analyze_complexity(decoded_content)
            complexity_level = complexity_result.complexity_level.value.lower()
        else:
            complexity_level = "beginner"

        uploaded_code = UploadedCode(
            task_id=task_id,
            detected_language=detected_language,
            complexity_level=complexity_level,
            total_lines=total_lines,
            total_files=len(files),
            upload_size_bytes=total_size,
        )
        self.db.add(uploaded_code)
        await self.db.flush()

        code_files = []
        for i, (original_filename, content) in enumerate(files):
            file_info = file_infos[i]
            file_ext = PathLib(original_filename).suffix

            code_file = CodeFile(
                uploaded_code_id=uploaded_code.id,
                file_name=original_filename,
                file_path=original_filename,
                file_extension=file_ext,
                file_size_bytes=len(content),
                storage_path=str(file_info.path),
            )
            self.db.add(code_file)
            code_files.append(code_file)

        await self.db.commit()

        return UploadResult(
            uploaded_code=uploaded_code,
            code_files=code_files,
        )

    async def upload_paste(
        self,
        user_id: UUID,
        task_id: UUID,
        code: str,
        language: str,
    ) -> UploadResult:
        extension = LANGUAGE_EXTENSIONS.get(language.lower(), ".txt")
        filename = f"pasted_code{extension}"

        content = code.encode("utf-8")

        file_info = self.storage.save_file(user_id, task_id, filename, content)

        total_lines = code.count("\n") + 1

        complexity_result = analyze_complexity(code)
        complexity_level = complexity_result.complexity_level.value.lower()

        uploaded_code = UploadedCode(
            task_id=task_id,
            detected_language=language.lower(),
            complexity_level=complexity_level,
            total_lines=total_lines,
            total_files=1,
            upload_size_bytes=len(content),
        )
        self.db.add(uploaded_code)
        await self.db.flush()

        code_file = CodeFile(
            uploaded_code_id=uploaded_code.id,
            file_name=filename,
            file_path=filename,
            file_extension=extension,
            file_size_bytes=len(content),
            storage_path=str(file_info.path),
        )
        self.db.add(code_file)

        await self.db.commit()

        return UploadResult(
            uploaded_code=uploaded_code,
            code_files=[code_file],
        )

    async def upload_folder(
        self,
        user_id: UUID,
        task_id: UUID,
        files: list[tuple[str, bytes]],
    ) -> UploadResult:
        return await self.upload_files(user_id, task_id, files)
