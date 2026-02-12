from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.models.model import Account
from app.schema import AccountCreate, AccountRead, LoginRequest, TokenResponse
import re

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

SECRET_KEY = "IS631G3n3r4t3dS3cr3tK3yF0rJWTT0k3n"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter(prefix="/accounts", tags=["Accounts"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def validate_password(password: str) -> None:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 characters.")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Password must contain at least one letter.")

    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one number.")

    if not re.search(r"[^\w\s]", password):
        raise ValueError("Password must contain at least one symbol.")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post(
        "/", 
        response_model=AccountRead, 
        status_code=status.HTTP_201_CREATED,
        summary="Create Account",
        description=(
                "*Create a new user account using email and password.*\n\n"
                "**Requirements:**\n"
                "- Email must be unique\n"
                "- Password must be at least **8 characters** long\n"
                "- Password must contain **at least one letter, one number, and one symbol**\n"
                "- Password is **securely hashed** before storage\n\n"
                "**Acceptance Criteria for S/N 22:**\n"
                "- AC1: Users should NOT be able to proceeed if email format is wrong, and system should display error message\n"
                "- AC2: Users should NOT be able to proceed if passwords do not match, and system should display error message\n"
                "- AC3: Users should NOT be able to proceed when signing up with existing emails\n"
                "- AC4: Password is stored hashed (not plaintext)\n"
                "- AC5: Users should be able to proceed when valid email and passwords are submitted, and gets redirected to dashboard.\n\n"
                "**Acceptance Criteria for S/N 24:**\n"
                "- AC1: User should NOT be able to proceed when password are too weak, with appropriate error message\n"
                "- AC2: User should be able to proceed with sign up  when password meats requirement\n"
        )
    )

def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        validate_password(payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Duplicate email (AC3)
    existing = db.query(Account).filter(
        Account.account_email == payload.account_email.lower()
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_account = Account(
        account_email=payload.account_email.lower(),
        name=payload.name,
        password_hash=hash_password(payload.password),
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account


@router.post(
        "/login", 
        response_model=TokenResponse,
        summary="Login",
        description=
            "*Authenticate user using email and password and return a JWT access token.*\n\n"
            "**Acceptance Criteria for S/N 25:**\n"
            "- AC1: Users should NOT be able to log in if email does not exist \n"
            "- AC2: Users should NOT be able to log in if email and password does not match\n"
            "- AC3: System should generate a valid token upon successful login, and users should be redirected to dashboard\n\n"
            "**Acceptance Criteria for S/N 26:**\n"
            "- AC1: When user clicks logout, the session token should be invalidated and user should be redirected to log in page.\n\n"
            "**Acceptance Criteria for S/N 27:**\n"
            "- AC1: When users opens app, user is automatically logged in and redirected to dashboard given a valid saved session token."
    )

def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # check email exists
    user = db.query(Account).filter(
        Account.account_email == payload.account_email.lower()
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # verify password
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # create JWT token
    access_token = create_access_token(
        data={"sub": user.account_email}
    )

    # return token
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }