"""Invitation and household members API client."""

from typing import List

from services.client import api_request


def fetch_household_members(household_id: int) -> List[dict]:
    """List members of the fridge with their roles. Any member can call."""
    out = api_request("get", f"/households/{household_id}/members")
    return out if isinstance(out, list) else []


def fetch_household_invites(household_id: int) -> List[dict]:
    """List invitations sent for this fridge (owner only). Includes status: pending, accepted, declined."""
    out = api_request("get", f"/households/{household_id}/invites")
    return out if isinstance(out, list) else []


def fetch_my_invitations() -> List[dict]:
    """List pending invitations for the current user (by email, case-insensitive on backend)."""
    try:
        out = api_request("get", "/invitations/me")
    except Exception:
        return []
    if not isinstance(out, list):
        return []
    return [x for x in out if isinstance(x, dict)]


def create_invite(household_id: int, email: str, role: str) -> dict:
    """Invite a user by email with a role (co_owner | child). Owner only."""
    return api_request(
        "post",
        f"/households/{household_id}/invites",
        json={"email": email.strip().lower(), "role": role},
    )


def accept_invitation(invitation_id: int) -> None:
    """Accept a pending invitation. Updates session (household_id) on success."""
    api_request("post", f"/invitations/{invitation_id}/accept")


def decline_invitation(invitation_id: int) -> None:
    """Decline a pending invitation."""
    api_request("post", f"/invitations/{invitation_id}/decline")
