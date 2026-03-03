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
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=72,  # Bcrypt limit
        description="Password must be 8-72 characters"
    )
    household_name: Optional[str] = Field(None, description="Name for new household (optional)")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 72:
            raise ValueError('Password must not exceed 72 characters (bcrypt limitation)')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long when encoded (max 72 bytes)')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=72,
        description="New password (8-72 characters)"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 72:
            raise ValueError('Password must not exceed 72 characters (bcrypt limitation)')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long when encoded (max 72 bytes)')
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