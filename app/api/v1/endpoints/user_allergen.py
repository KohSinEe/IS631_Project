"""User allergen endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import DatabaseDep, CurrentUserDep
from app.schemas.user_allergen import UserAllergenUpdate, UserAllergenResponse
from app.models.user_allergen import UserAllergen
from app.models.user import User

router = APIRouter()


@router.get("/me/allergens", response_model=UserAllergenResponse, status_code=status.HTTP_200_OK)
def get_allergens(current_user: CurrentUserDep, db: DatabaseDep):
    """Get allergens for the current user."""
    allergens = db.query(UserAllergen).filter(UserAllergen.user_id == current_user.id).all()
    return UserAllergenResponse(
        user_id=current_user.id,
        allergens=[a.allergen for a in allergens],
    )


@router.delete("/me/allergens", response_model=UserAllergenResponse, status_code=status.HTTP_200_OK)
def delete_allergens(
    payload: UserAllergenUpdate,
    current_user: CurrentUserDep,
    db: DatabaseDep,
):
    """Remove specific allergens from the current user's list."""
    db.query(UserAllergen).filter(
        UserAllergen.user_id == current_user.id, UserAllergen.allergen.in_(payload.allergens)
    ).delete()
    db.commit()

    remaining = db.query(UserAllergen).filter(UserAllergen.user_id == current_user.id).all()
    return UserAllergenResponse(
        user_id=current_user.id,
        allergens=[a.allergen for a in remaining],
    )


@router.post("/me/allergens", response_model=UserAllergenResponse, status_code=status.HTTP_200_OK)
def add_allergens(
    payload: UserAllergenUpdate,
    current_user: CurrentUserDep,
    db: DatabaseDep,
):
    """Add allergens to the current user's list."""
    existing = db.query(UserAllergen).filter(UserAllergen.user_id == current_user.id).all()
    existing_set = {a.allergen for a in existing}

    # Only insert allergens that don't already exist
    new_allergens = [
        UserAllergen(user_id=current_user.id, allergen=a)
        for a in payload.allergens
        if a not in existing_set
    ]
    db.add_all(new_allergens)
    db.commit()

    all_allergens = list(existing_set | {a.allergen for a in new_allergens})
    return UserAllergenResponse(
        user_id=current_user.id,
        allergens=all_allergens,
    )
