"""Household (fridge) management endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, status

from app.dependencies import DatabaseDep, CurrentUserDep
from app.models.household import Household
from app.models.invitation import Invitation
from app.models.enums import InvitationStatusEnum
from app.models.user import User
from app.schemas.invitation import InviteCreate, InvitationResponse, HouseholdMemberResponse
from app.schemas.household import HouseholdCreate, HouseholdResponse


router = APIRouter()


@router.delete("/{household_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_household(
    household_id: int,
    current_user: CurrentUserDep,
    db: DatabaseDep,
):
    """
    Delete the household (fridge) and all its contents.

    Only the household owner can delete. All members are removed from the
    household and all items in the fridge are permanently deleted.
    """
    if current_user.household_id != household_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this household",
        )
    if not current_user.is_household_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the fridge owner can delete it",
        )

    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household not found",
        )

    # Unlink all users from this household so FK allows delete
    db.query(User).filter(User.household_id == household_id).update(
        {User.household_id: None, User.household_role: None}
    )
    # Delete household (items are cascade-deleted)
    db.delete(household)
    db.commit()

    return None


def _ensure_owner_and_household(
    current_user: User,
    household_id: int,
    db,
) -> Household:
    """Raise if not owner of this household; return the household."""
    if current_user.household_id != household_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this household",
        )
    if not current_user.is_household_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the fridge owner can invite members",
        )
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household not found",
        )
    return household


@router.post(
    "/{household_id}/invites",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    household_id: int,
    body: InviteCreate,
    current_user: CurrentUserDep,
    db: DatabaseDep,
):
    """
    Invite a user to the fridge by email and assign a role (Co-owner or Child).
    Only the household owner can invite. The invitee must have an existing account.
    """
    household = _ensure_owner_and_household(current_user, household_id, db)

    invitee = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with this email. They must register first.",
        )
    if invitee.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot invite yourself",
        )
    if invitee.household_id == household_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already in your fridge",
        )
    existing = (
        db.query(Invitation)
        .filter(
            Invitation.household_id == household_id,
            Invitation.invitee_email == body.email.lower().strip(),
            Invitation.status == InvitationStatusEnum.PENDING,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An invitation has already been sent to this email",
        )

    inv = Invitation(
        household_id=household_id,
        inviter_id=current_user.id,
        invitee_email=body.email.lower().strip(),
        role=body.role,
        status=InvitationStatusEnum.PENDING,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.get("/{household_id}/invites", response_model=List[InvitationResponse])
def list_invitations(
    household_id: int,
    current_user: CurrentUserDep,
    db: DatabaseDep,
):
    """List invitations sent for this household. Owner only."""
    _ensure_owner_and_household(current_user, household_id, db)
    invites = (
        db.query(Invitation)
        .filter(Invitation.household_id == household_id)
        .order_by(Invitation.created_at.desc())
        .all()
    )
    return invites


@router.get("/{household_id}/members", response_model=List[HouseholdMemberResponse])
def list_household_members(
    household_id: int,
    current_user: CurrentUserDep,
    db: DatabaseDep,
):
    """
    List all members of the fridge with their role.
    Any member of the household can view this list.
    """
    if current_user.household_id != household_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this household",
        )
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household not found",
        )
    users = db.query(User).filter(User.household_id == household_id).all()
    result = []
    for u in users:
        if household.owner_id == u.id:
            role = "owner"
        else:
            role = u.household_role.value if u.household_role else "child"
        result.append(
            HouseholdMemberResponse(
                id=u.id,
                email=u.email,
                name=u.name,
                role=role,
            )
        )
    return result

@router.post("", response_model=HouseholdResponse, status_code=status.HTTP_201_CREATED)
def create_household(
    body: HouseholdCreate,
    current_user: CurrentUserDep,
    db: DatabaseDep,
):
    """
    Create a new household and set the current user as owner.
    Only allowed if the user does not already belong to a household.
    """
    if current_user.household_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already belong to a household",
        )

    household = Household(name=body.name)
    db.add(household)
    db.flush()  # get household.id

    current_user.household_id = household.id
    household.owner_id = current_user.id

    db.commit()
    db.refresh(current_user)
    db.refresh(household)

    return household