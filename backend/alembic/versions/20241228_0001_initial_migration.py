"""Initial migration - create all tables

Revision ID: 0001
Revises:
Create Date: 2024-12-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("skill_level", sa.String(length=50), nullable=False, server_default="Complete Beginner"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'",
            name="valid_email",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=False)

    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_activity_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deletion_status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("trashed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("scheduled_deletion_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("char_length(title) >= 1", name="title_min_length"),
        sa.CheckConstraint("deletion_status IN ('active', 'trashed')", name="valid_deletion_status"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_projects_user_id", "projects", ["user_id"], unique=False)
    op.create_index("idx_projects_deletion_status", "projects", ["deletion_status"], unique=False)

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("task_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("upload_method", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deletion_status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("trashed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("scheduled_deletion_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("char_length(title) >= 5", name="tasks_title_min_length"),
        sa.CheckConstraint(
            "description IS NULL OR char_length(description) <= 500",
            name="description_max_length",
        ),
        sa.CheckConstraint(
            "upload_method IS NULL OR upload_method IN ('file', 'folder', 'paste')",
            name="valid_upload_method",
        ),
        sa.CheckConstraint("deletion_status IN ('active', 'trashed')", name="tasks_valid_deletion_status"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "task_number", name="unique_task_number_per_project"),
    )
    op.create_index("idx_tasks_project_id", "tasks", ["project_id"], unique=False)
    op.create_index("idx_tasks_deletion_status", "tasks", ["deletion_status"], unique=False)
    op.create_index("idx_tasks_number_order", "tasks", ["project_id", "task_number"], unique=False)

    # Create refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("idx_refresh_tokens_hash", "refresh_tokens", ["token_hash"], unique=False)
    op.create_index("idx_refresh_tokens_expires", "refresh_tokens", ["expires_at"], unique=False)

    # Create uploaded_code table
    op.create_table(
        "uploaded_code",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("detected_language", sa.String(length=50), nullable=True),
        sa.Column("complexity_level", sa.String(length=20), nullable=True),
        sa.Column("total_lines", sa.Integer(), nullable=True),
        sa.Column("total_files", sa.Integer(), nullable=True),
        sa.Column("upload_size_bytes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "complexity_level IS NULL OR complexity_level IN ('beginner', 'intermediate', 'advanced')",
            name="valid_complexity_level",
        ),
        sa.CheckConstraint(
            "upload_size_bytes IS NULL OR upload_size_bytes <= 10485760",
            name="valid_upload_size",
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index("idx_uploaded_code_task_id", "uploaded_code", ["task_id"], unique=False)

    # Create code_files table
    op.create_table(
        "code_files",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("uploaded_code_id", sa.UUID(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("file_extension", sa.String(length=20), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "file_extension IS NULL OR file_extension IN ("
            "'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', "
            "'.java', '.cpp', '.c', '.txt', '.md')",
            name="supported_extension",
        ),
        sa.ForeignKeyConstraint(["uploaded_code_id"], ["uploaded_code.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_code_files_uploaded_code_id", "code_files", ["uploaded_code_id"], unique=False)

    # Create learning_documents table
    op.create_table(
        "learning_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("generation_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("generation_started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("generation_completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("generation_error", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "generation_status IN ('pending', 'in_progress', 'completed', 'failed')",
            name="valid_generation_status",
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index("idx_learning_documents_task_id", "learning_documents", ["task_id"], unique=False)
    op.create_index("idx_learning_documents_status", "learning_documents", ["generation_status"], unique=False)
    op.create_index("idx_learning_documents_celery_task", "learning_documents", ["celery_task_id"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation (respecting foreign key dependencies)
    op.drop_index("idx_learning_documents_celery_task", table_name="learning_documents")
    op.drop_index("idx_learning_documents_status", table_name="learning_documents")
    op.drop_index("idx_learning_documents_task_id", table_name="learning_documents")
    op.drop_table("learning_documents")

    op.drop_index("idx_code_files_uploaded_code_id", table_name="code_files")
    op.drop_table("code_files")

    op.drop_index("idx_uploaded_code_task_id", table_name="uploaded_code")
    op.drop_table("uploaded_code")

    op.drop_index("idx_refresh_tokens_expires", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_hash", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("idx_tasks_number_order", table_name="tasks")
    op.drop_index("idx_tasks_deletion_status", table_name="tasks")
    op.drop_index("idx_tasks_project_id", table_name="tasks")
    op.drop_table("tasks")

    op.drop_index("idx_projects_deletion_status", table_name="projects")
    op.drop_index("idx_projects_user_id", table_name="projects")
    op.drop_table("projects")

    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
