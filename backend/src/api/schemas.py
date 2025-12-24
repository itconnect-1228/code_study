"""Pydantic schemas for API request and response validation.

This module defines:
- Request schemas: Data structures for incoming requests
- Response schemas: Data structures for API responses
- Validation rules: Email format, password strength, etc.
"""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Request schema for user registration.

    Validates:
    - Email format (RFC 5322)
    - Password minimum length (8 characters)
    """

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., min_length=8, description="User's password (min 8 chars)"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets minimum requirements.

        Args:
            v: Password string to validate.

        Returns:
            str: Validated password.

        Raises:
            ValueError: If password is less than 8 characters.
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(BaseModel):
    """Response schema for user data.

    Note: Password hash is never included in responses.
    """

    id: UUID = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    skill_level: str = Field(..., description="User's programming skill level")

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Response schema for login endpoint.

    Access token is returned in the response body.
    Refresh token is set as HttpOnly cookie (not in response).
    """

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user information")


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str = Field(..., description="Response message")


# Project schemas


class CreateProjectRequest(BaseModel):
    """Request schema for creating a new project."""

    title: str = Field(..., min_length=1, max_length=200, description="Project title")
    description: str | None = Field(None, max_length=2000, description="Project description")


class UpdateProjectRequest(BaseModel):
    """Request schema for updating a project."""

    title: str | None = Field(None, min_length=1, max_length=200, description="Project title")
    description: str | None = Field(None, max_length=2000, description="Project description")


class ProjectResponse(BaseModel):
    """Response schema for a single project."""

    id: UUID = Field(..., description="Project unique identifier")
    title: str = Field(..., description="Project title")
    description: str | None = Field(None, description="Project description")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    last_activity_at: str = Field(..., description="Last activity timestamp")
    deletion_status: str = Field(..., description="Deletion status (active/trashed)")
    trashed_at: str | None = Field(None, description="Trash timestamp")

    model_config = {"from_attributes": True}

    @classmethod
    def from_project(cls, project) -> "ProjectResponse":
        """Create ProjectResponse from Project model."""
        return cls(
            id=project.id,
            title=project.title,
            description=project.description,
            created_at=project.created_at.isoformat() if project.created_at else "",
            updated_at=project.updated_at.isoformat() if project.updated_at else "",
            last_activity_at=project.last_activity_at.isoformat() if project.last_activity_at else "",
            deletion_status=project.deletion_status,
            trashed_at=project.trashed_at.isoformat() if project.trashed_at else None,
        )


class ProjectListResponse(BaseModel):
    """Response schema for project list."""

    projects: list[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")
