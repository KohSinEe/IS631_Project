"""Household allergen endpoints."""

from fastapi import APIRouter, HTTPException, status
from app.dependencies import DatabaseDep, CurrentUserDep
from app.schemas.user_allergen import UserAllergenResponse
from app.models.user import User

router = APIRouter()


@router.get("/allergens", response_model=list[UserAllergenResponse], status_code=status.HTTP_200_OK)
def get_household_allergens(current_user: CurrentUserDep, db: DatabaseDep):
    """Get allergens for all members in the current user's household."""
    if current_user.household_id is None:
        raise HTTPException(status_code=403, detail="You are not part of a household")

    members = (
        db.query(User)
        .filter(User.household_id == current_user.household_id)
        .all()
    )

    return [
        UserAllergenResponse(
            user_id=member.id,
            allergens=[a.allergen for a in member.allergens],
        )
        for member in members
    ]