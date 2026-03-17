"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import DatabaseDep
from app.config import settings
from app.schemas.auth import Token, ConfirmSignUpRequest, ResendSignUpCodeRequest
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.models.household import Household
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.core.cognito import (
    cognito_sign_up,
    cognito_confirm_sign_up,
    cognito_resend_sign_up_code,
    cognito_login,
    cognito_global_sign_out,
    verify_cognito_token,
)

router = APIRouter()


@router.post("/confirm-signup")
def confirm_signup(payload: ConfirmSignUpRequest):
    """Confirm a newly registered Cognito user with verification code."""
    if not settings.is_cognito_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup confirmation is only required in Cognito mode",
        )

    cognito_confirm_sign_up(payload.email, payload.confirmation_code)
    return {"message": "Account verified. You can now sign in."}


@router.post("/resend-confirmation")
def resend_confirmation(payload: ResendSignUpCodeRequest):
    """Resend Cognito sign-up verification code."""
    if not settings.is_cognito_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup confirmation is only required in Cognito mode",
        )

    cognito_resend_sign_up_code(payload.email)
    return {"message": "Verification code sent"}


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

    # Create household if provided
    household_id = None
    if user_in.household_name:
        household = Household(name=user_in.household_name)
        db.add(household)
        db.flush()  # Get the ID without committing
        household_id = household.id

    cognito_sub = None
    if settings.is_cognito_enabled:
        cognito_result = cognito_sign_up(user_in.email, user_in.password, user_in.name)
        cognito_sub = cognito_result.get("UserSub")

    # Create user (use only password, password_confirm is validated by schema)
    user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
        cognito_sub=cognito_sub,
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
    if settings.is_cognito_enabled:
        token_data = cognito_login(form_data.username, form_data.password)
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token", "")
        id_token = token_data["id_token"]
        id_claims = verify_cognito_token(id_token, token_use="id")

        cognito_sub = id_claims.get("sub")
        email = id_claims.get("email") or form_data.username
        name = id_claims.get("name")

        user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
        if user is None:
            user = db.query(User).filter(User.email == email).first()

        if user is None:
            user = User(
                email=email,
                name=name,
                cognito_sub=cognito_sub,
                hashed_password=get_password_hash(form_data.password),
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            if not user.cognito_sub and cognito_sub:
                user.cognito_sub = cognito_sub
            if name and not user.name:
                user.name = name
            db.commit()
    else:
        # Find user (username field of OAuth2 form is used for email)
        user = db.query(User).filter(User.email == form_data.username).first()

        # Verify user and password
        if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
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
def logout(request: Request, response: Response):
    """
    Logout by clearing the authentication cookies.
    """
    if settings.is_cognito_enabled:
        auth_header = request.headers.get("Authorization", "")
        access_token = ""
        if auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ", 1)[1].strip()
        if not access_token:
            access_token = request.cookies.get("access_token", "")
        cognito_global_sign_out(access_token)

    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Successfully logged out"}
