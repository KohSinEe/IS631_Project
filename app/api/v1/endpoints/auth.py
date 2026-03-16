"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import DatabaseDep
from app.config import settings
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.models.household import Household
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: DatabaseDep):
    """
    Register a new user.

    - **email**: Valid email address
    - **password**: At least 8 characters
    - **name**: Optional display name
    - **household_name**: Optional household name (creates new household) - Feature removed, household creation is now separate endpoint. Users can be created without household and join later.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create user (use only password, password_confirm is validated by schema)
    user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
        household_id=None,
        is_active=True,
    )

    db.add(user)
    db.flush()  # Get user.id

    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login(
    response: Response,
    db: DatabaseDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Login with email and password.

    Sets secure HTTP-only cookie with access token.
    Returns access token and refresh token for frontend use if needed.
    """
    # Find user (username field of OAuth2 form is used for email)
    user = db.query(User).filter(User.email == form_data.username).first()

    # Verify user and password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    # Set secure HTTP-only cookie with access token
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,  # Prevents JavaScript access (XSS protection)
        secure=settings.COOKIE_SECURE,  # Allow HTTP cookies during local development
        samesite="lax",  # CSRF protection
        path="/",
    )

    # Optionally set refresh token cookie (can use for auto-refresh)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
    )

    # Return OAuth2-compatible token response (for any frontend that needs tokens)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@router.post("/logout")
def logout(response: Response):
    """
    Logout by clearing the authentication cookies.
    """
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Successfully logged out"}
