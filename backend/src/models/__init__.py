"""SQLAlchemy ORM models for the AI Code Learning Platform.

This package contains all database models that inherit from Base
(defined in db.session). Each model corresponds to a database table
and defines the structure, relationships, and constraints.

Current models:
- User: Platform user with authentication credentials
- RefreshToken: JWT refresh tokens for authentication
- Project: Learning container for related tasks
- Task: Single learning unit within a project

Example:
    from backend.src.models import User, RefreshToken, Project, Task
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
"""

from .project import Project
from .refresh_token import RefreshToken
from .task import Task
from .user import User

__all__ = [
    "Project",
    "RefreshToken",
    "Task",
    "User",
]
