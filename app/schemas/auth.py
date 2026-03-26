"""Authentication schemas."""

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ConfirmSignUpRequest(BaseModel):
    """Confirm a Cognito sign-up using an email code."""

    email: EmailStr
    confirmation_code: str = Field(..., min_length=1, max_length=20)


class ResendSignUpCodeRequest(BaseModel):
    """Request Cognito to resend sign-up verification code."""

    email: EmailStr
