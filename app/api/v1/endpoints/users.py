"""User management endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.dependencies import DatabaseDep, CurrentUserDep
from app.schemas.user import UserResponse, UserUpdate, PasswordChange
from app.core.security import verify_password, get_password_hash
from app.models.user import User


router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: CurrentUserDep):
    """
    Get current user profile.
    
    Requires authentication.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: CurrentUserDep,
    db: DatabaseDep
):
    """
    Update current user profile.
    
    - **name**: New display name
    """
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.put("/me/password", status_code=status.HTTP_200_OK)
def change_password(
    password_change: PasswordChange,
    current_user: CurrentUserDep,
    db: DatabaseDep
):
    """
    Change current user's password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 characters)
    """
    # Verify current password
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Check if new password is different
    if password_change.current_password == password_change.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    current_user: CurrentUserDep,
    db: DatabaseDep
):
    """
    Delete current user account.
    
    This action is irreversible!
    """
    db.delete(current_user)
    db.commit()
    
    return None


