"""Shared dependencies for FastAPI endpoints."""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User

# Type aliases
DatabaseDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
