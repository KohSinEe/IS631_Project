"""Shared dependencies for FastAPI endpoints."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User

# Type aliases
DatabaseDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_household_id(current_user: User, household_id: Optional[int]) -> int:
    """
    Require a non-None household_id and that the current user has access to it.

    Returns the household_id for use in the rest of the endpoint.
    Raises 400 if household_id is missing, 403 if user cannot access the household.
    """
    if household_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="household_id is required",
        )
    if current_user.household_id != household_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this household",
        )
    return household_id
