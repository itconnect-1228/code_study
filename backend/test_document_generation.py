"""
DocumentGenerationService 단계별 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from datetime import UTC, datetime

from sqlalchemy import select

from src.db.session import get_session_context, init_db
from src.models.code_file import CodeFile
from src.models.project import Project
from src.models.task import Task
from src.models.uploaded_code import UploadedCode
from src.models.user import User
from src.services.document import DocumentGenerationService

TEST_CODE = """def greet(name):
    print(f"Hello, {name}!")

greet("World")
"""


def print_step(step_num, title):
    print("")
    print("=" * 60)
    print(f"Step {step_num}: {title}")
    print("=" * 60)


def print_result(label, value):
    print(f"  [OK] {label}: {value}")


async def run_test():
    print("")
    print("DocumentGenerationService Step-by-Step Test")
    print("=" * 60)

    # Initialize database connection
    init_db()
    print("[DB] Database initialized")

    async with get_session_context() as session:
        print_step(1, "User, Project, Task 생성")

        stmt = select(User).where(User.email == "test-doc-gen@example.com")
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(email="test-doc-gen@example.com", password_hash="test_hash")
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print_result("New User created", user.email)
        else:
            print_result("Using existing User", user.email)
        print_result("User ID", user.id)

        project = Project(
            user_id=user.id, title="Document Generation Test", description="Test"
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        print_result("Project created", project.title)
        print_result("Project ID", project.id)

        task = Task(
            project_id=project.id,
            title="Python Greet Test",
            task_number=1,
            upload_method="paste",
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        print_result("Task created", task.title)
        print_result("Task ID", task.id)

        print_step(2, "UploadedCode 생성 (language=python, complexity=beginner)")
        uploaded_code = UploadedCode(
            task_id=task.id,
            detected_language="python",
            complexity_level="beginner",
            total_lines=4,
            total_files=1,
            upload_size_bytes=len(TEST_CODE.encode()),
        )
        session.add(uploaded_code)
        await session.commit()
        await session.refresh(uploaded_code)
        print_result("UploadedCode ID", uploaded_code.id)
        print_result("Language", uploaded_code.detected_language)
        print_result("Complexity", uploaded_code.complexity_level)

        print_step(3, "CodeFile 생성 (Python 코드)")
        print("")
        print("Code to save:")
        print("-" * 40)
        for i, line in enumerate(TEST_CODE.strip().split("\n"), 1):
            print(f"  {i:2d} | {line}")
        print("-" * 40)

        storage_dir = (
            Path(__file__).parent / "storage" / "uploads" / str(user.id) / str(task.id)
        )
        storage_dir.mkdir(parents=True, exist_ok=True)
        storage_path = storage_dir / "greet.py"
        storage_path.write_text(TEST_CODE, encoding="utf-8")

        code_file = CodeFile(
            uploaded_code_id=uploaded_code.id,
            file_name="greet.py",
            file_path="greet.py",
            file_extension=".py",
            file_size_bytes=len(TEST_CODE.encode()),
            storage_path=str(storage_path),
            mime_type="text/x-python",
        )
        session.add(code_file)
        await session.commit()
        await session.refresh(code_file)
        print_result("CodeFile created", code_file.file_name)
        print_result("Storage Path", code_file.storage_path)

        print_step(4, "DocumentGenerationService.generate_document() 호출")
        print("")
        print("[WAIT] AI generating document... (30-60 seconds)")

        service = DocumentGenerationService(session)
        start_time = datetime.now(UTC)

        try:
            document = await service.generate_document(
                task_id=task.id,
                code=TEST_CODE,
                language="Python",
                filename="greet.py",
            )
            elapsed = (datetime.now(UTC) - start_time).total_seconds()
            print("")
            print(f"[SUCCESS] Complete! ({elapsed:.1f}s)")
        except Exception as e:
            elapsed = (datetime.now(UTC) - start_time).total_seconds()
            print("")
            print(f"[FAILED] {e}")
            document = await service.get_document_by_task(task.id)
            if document:
                print_result("Status", document.generation_status)
                print_result("Error", document.generation_error)
            return

        print_step(5, "LearningDocument 확인")
        print_result("Generation Status", document.generation_status)
        print_result("is completed?", document.generation_status == "completed")

        required = [
            "chapter1",
            "chapter2",
            "chapter3",
            "chapter4",
            "chapter5",
            "chapter6",
            "chapter7",
        ]
        all_exist = all(ch in document.content for ch in required)
        print_result("All 7 chapters exist?", all_exist)

        print("")
        print("Chapter Check:")
        for ch_key in required:
            if ch_key in document.content:
                ch = document.content[ch_key]
                title = ch.get("title", "N/A")
                has_content = len(str(ch)) > 50
                print(f"  [OK] {ch_key}: {title} (has content: {has_content})")
            else:
                print(f"  [FAIL] {ch_key}: MISSING")

        print("")
        print("=" * 60)
        print("CHAPTER DETAILS")
        print("=" * 60)

        if "chapter1" in document.content:
            ch1 = document.content["chapter1"]
            print("")
            print(f"[Chapter 1: {ch1.get('title', 'N/A')}]")
            s = ch1.get("summary", "")
            if len(s) > 200:
                print(f"Summary: {s[:200]}...")
            else:
                print(f"Summary: {s}")

        if "chapter2" in document.content:
            ch2 = document.content["chapter2"]
            concepts = ch2.get("concepts", [])
            print("")
            print(f"[Chapter 2: {ch2.get('title', 'N/A')}]")
            print(f"Concepts count: {len(concepts)}")
            for i, c in enumerate(concepts[:3], 1):
                name = c.get("name", "?")
                explanation = c.get("explanation", "")[:60]
                print(f"  {i}. {name}: {explanation}...")

        if "chapter7" in document.content:
            ch7 = document.content["chapter7"]
            mistakes = ch7.get("mistakes", [])
            print("")
            print(f"[Chapter 7: {ch7.get('title', 'N/A')}]")
            print(f"Mistakes count: {len(mistakes)}")
            for i, m in enumerate(mistakes[:2], 1):
                mistake_text = m.get("mistake", "")[:60]
                print(f"  {i}. {mistake_text}...")

        print("")
        print("=" * 60)
        print("TEST COMPLETE!")
        print("=" * 60)
        print(f"  Generation Status: {document.generation_status}")
        print(f"  All 7 chapters: {all_exist}")
        print(f"  has_content: {document.has_content}")
        print(f"  Generation Time: {elapsed:.1f}s")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_test())
