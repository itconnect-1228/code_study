"""SQLAlchemy ORM models for the AI Code Learning Platform.

This package contains all database models that inherit from Base
(defined in db.session). Each model corresponds to a database table
and defines the structure, relationships, and constraints.

Current models:
- User: Platform user with authentication credentials
- RefreshToken: JWT refresh tokens for authentication
- Project: Learning container for related tasks
- Task: Single learning unit within a project
- UploadedCode: Code upload metadata for a task
- CodeFile: Individual file within uploaded code

Example:
    from backend.src.models import User, RefreshToken, Project, Task, UploadedCode, CodeFile
    from backend.src.db import Base, get_session

    # Create a new user
    user = User(email="test@example.com", password_hash="hashed_password")
    session.add(user)
    await session.commit()

    # Create a project for the user
    project = Project(user_id=user.id, title="My First Project")
    session.add(project)
    await session.commit()

    # Create a task in the project
    task = Task(project_id=project.id, task_number=1, title="Learn Python")
    session.add(task)
    await session.commit()

    # Add uploaded code metadata to the task
    uploaded_code = UploadedCode(
        task_id=task.id,
        detected_language="python",
        complexity_level="beginner",
        total_lines=50
    )
    session.add(uploaded_code)
    await session.commit()

    # Add a code file to the uploaded code
    code_file = CodeFile(
        uploaded_code_id=uploaded_code.id,
        file_name="main.py",
        file_extension=".py",
        storage_path="storage/uploads/user123/task456/main.py"
    )
    session.add(code_file)
    await session.commit()
"""

from .code_file import CodeFile
from .project import Project
from .refresh_token import RefreshToken
from .task import Task
from .uploaded_code import UploadedCode
from .user import User

__all__ = [
    "CodeFile",
    "Project",
    "RefreshToken",
    "Task",
    "UploadedCode",
    "User",
]
