"""Household (fridge) management endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.dependencies import DatabaseDep, CurrentUserDep
from app.models.household import Household
from app.models.user import User


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
        {User.household_id: None}
    )
    # Delete household (items are cascade-deleted)
    db.delete(household)
    db.commit()

    return None
