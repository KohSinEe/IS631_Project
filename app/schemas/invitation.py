"""Schemas for household invitations."""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr, Field, field_serializer

from app.models.enums import HouseholdRoleEnum, InvitationStatusEnum


class InviteCreate(BaseModel):
    """Schema for creating an invitation."""
    email: EmailStr = Field(..., description="Email of the user to invite")
    role: HouseholdRoleEnum = Field(..., description="Role to assign: co_owner or child")


class InvitationResponse(BaseModel):
    """Schema for invitation in API responses."""
    id: int
    household_id: int
    inviter_id: int
    invitee_email: str
    role: str  # co_owner | child
    status: str  # pending | accepted | declined
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("role", "status")
    @classmethod
    def serialize_enum(cls, v: Any) -> str:
        if v is None:
            return ""
        return getattr(v, "value", str(v))


class InvitationListForUser(BaseModel):
    """Invitation with household name for 'my pending invites' list."""
    id: int
    household_id: int
    household_name: str
    inviter_name: Optional[str] = None
    role: str
    status: str
    created_at: datetime


class HouseholdMemberResponse(BaseModel):
    """A household member with their role (for member list)."""
    id: int
    email: str
    name: Optional[str] = None
    role: str  # "owner" | "co_owner" | "child"
