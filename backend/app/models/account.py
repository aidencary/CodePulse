"""Pydantic models for the account CRUD endpoints."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ProfileResponse(BaseModel):
    """Profile data returned to the client."""

    id: str
    email: str
    username: str
    role: str
    profile_picture: str | None = None
    created_at: datetime


class ProfileUpdateRequest(BaseModel):
    """Payload for updating a user's profile."""

    username: str | None = Field(None, min_length=3, max_length=20)
    profile_picture: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username may only contain letters, numbers,"
                " underscores, and hyphens"
            )
        return v

    @field_validator("profile_picture")
    @classmethod
    def validate_profile_picture(cls, v: str | None) -> str | None:
        """Only allow HTTPS URLs for profile pictures."""
        if v is not None and not v.startswith("https://"):
            raise ValueError("Profile picture must be a valid HTTPS URL")
        return v


class ChangePasswordRequest(BaseModel):
    """Payload for changing a user's password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class AvatarUploadResponse(BaseModel):
    """Response after a successful avatar upload."""

    profile_picture: str
