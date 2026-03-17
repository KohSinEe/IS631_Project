"""User schemas for validation."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, field_serializer


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""

    household_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Optional household/fridge name at registration.",
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=12,
        description="Password must be 8-12 characters, include uppercase, lowercase, number, and special character.",
    )
    password_confirm: str = Field(
        ..., min_length=8, max_length=72, description="Password confirmation (must match password)"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password requirements."""
        import re

        if len(v) < 8 or len(v) > 12:
            raise ValueError("Password must be 8-12 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, v: str, values) -> str:
        password = values.data.get("password")
        if password and v != password:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("household_name")
    @classmethod
    def validate_household_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        value = v.strip()
        return value or None


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    name: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for changing password."""

    current_password: str
    new_password: str = Field(
        ..., min_length=8, max_length=72, description="New password (8-72 characters)"
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 72:
            raise ValueError("Password must not exceed 72 characters (bcrypt limitation)")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long when encoded (max 72 bytes)")
        return v


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    household_id: Optional[int] = None
    is_active: bool
    is_household_owner: bool = False
    household_role: Optional[str] = None  # "co_owner" | "child" | None (owner)
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("household_role")
    @classmethod
    def serialize_household_role(cls, v):
        if v is None:
            return None
        return getattr(v, "value", v)


class UserInDB(UserResponse):
    """User schema with hashed password (internal use only)."""

    hashed_password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr
    new_password: str


class PasswordResetStartRequest(BaseModel):
    """Start password reset by sending verification code to user."""

    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Complete password reset using verification code."""

    email: EmailStr
    confirmation_code: str = Field(..., min_length=1, max_length=20)
    new_password: str = Field(..., min_length=8, max_length=72)
