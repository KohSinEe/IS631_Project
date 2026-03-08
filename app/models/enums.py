"""Shared enums for models."""

from enum import Enum as PyEnum


class HouseholdRoleEnum(str, PyEnum):
    """Role a user can have in a household. Owner is implied by household.owner_id."""
    CO_OWNER = "co_owner"
    CHILD = "child"


class InvitationStatusEnum(str, PyEnum):
    """Status of an invitation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
