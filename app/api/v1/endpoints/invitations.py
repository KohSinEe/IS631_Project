"""Endpoints for viewing and responding to household invitations."""

from typing import List

from fastapi import APIRouter, HTTPException, status

from app.dependencies import DatabaseDep, CurrentUserDep
from app.models.enums import InvitationStatusEnum
from app.models.invitation import Invitation
from app.models.user import User
from app.schemas.invitation import InvitationListForUser


router = APIRouter()


@router.get("/me", response_model=List[InvitationListForUser])
def list_my_invitations(
    current_user: CurrentUserDep,
    db: DatabaseDep,
):
    """
    List pending invitations for the current user (by email).
    """
    from app.models.household import Household

    invites = (
        db.query(Invitation)
        .filter(
            Invitation.invitee_email == current_user.email,
            Invitation.status == InvitationStatusEnum.PENDING,
        )
        .order_by(Invitation.created_at.desc())
        .all()
    )
    result = []
    for inv in invites:
        household = db.query(Household).filter(Household.id == inv.household_id).first()
        inviter = db.query(User).filter(User.id == inv.inviter_id).first()
        result.append(
            InvitationListForUser(
                id=inv.id,
                household_id=inv.household_id,
                household_name=household.name if household else "",
                inviter_name=inviter.name if inviter else inviter.email if inviter else None,
                role=inv.role.value if hasattr(inv.role, "value") else str(inv.role),
                status=inv.status.value if hasattr(inv.status, "value") else str(inv.status),
                created_at=inv.created_at,
            )
        )
    return result


@router.post("/{invitation_id}/accept", status_code=status.HTTP_200_OK)
def accept_invitation(
    invitation_id: int,
    current_user: CurrentUserDep,
    db: DatabaseDep,
):
    """
    Accept a pending invitation. Joins the current user to the household with the invited role.
    """
    inv = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    if inv.invitee_email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to another email",
        )
    if inv.status != InvitationStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation is no longer pending",
        )
    if current_user.household_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already belong to a fridge. Leave it first before accepting.",
        )

    current_user.household_id = inv.household_id
    current_user.household_role = inv.role
    inv.status = InvitationStatusEnum.ACCEPTED
    db.commit()
    return {"message": "Invitation accepted. You have joined the fridge."}


@router.post("/{invitation_id}/decline", status_code=status.HTTP_200_OK)
def decline_invitation(
    invitation_id: int,
    current_user: CurrentUserDep,
    db: DatabaseDep,
):
    """Decline a pending invitation."""
    inv = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    if inv.invitee_email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to another email",
        )
    if inv.status != InvitationStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation is no longer pending",
        )

    inv.status = InvitationStatusEnum.DECLINED
    db.commit()
    return {"message": "Invitation declined."}
