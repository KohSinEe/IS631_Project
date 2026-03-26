"""AWS Cognito helpers for auth flows and token verification."""

from __future__ import annotations

import base64
import hashlib
import hmac
import importlib
from functools import lru_cache
from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import settings


def _ensure_cognito_config() -> None:
    missing = []
    if not settings.AWS_REGION:
        missing.append("AWS_REGION")
    if not settings.COGNITO_USER_POOL_ID:
        missing.append("COGNITO_USER_POOL_ID")
    if not settings.COGNITO_APP_CLIENT_ID:
        missing.append("COGNITO_APP_CLIENT_ID")

    if missing:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Missing Cognito config: {', '.join(missing)}",
        )


@lru_cache(maxsize=1)
def _cognito_client():
    _ensure_cognito_config()
    try:
        boto3 = importlib.import_module("boto3")
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="boto3 is required for Cognito auth",
        ) from exc

    return boto3.client("cognito-idp", region_name=settings.AWS_REGION)


def _secret_hash(username: str) -> Optional[str]:
    if not settings.COGNITO_APP_CLIENT_SECRET:
        return None

    digest = hmac.new(
        settings.COGNITO_APP_CLIENT_SECRET.encode("utf-8"),
        f"{username}{settings.COGNITO_APP_CLIENT_ID}".encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


def cognito_sign_up(email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
    client = _cognito_client()

    user_attributes = [{"Name": "email", "Value": email}]
    if name:
        user_attributes.append({"Name": "name", "Value": name})

    request: Dict[str, Any] = {
        "ClientId": settings.COGNITO_APP_CLIENT_ID,
        "Username": email,
        "Password": password,
        "UserAttributes": user_attributes,
    }

    secret_hash = _secret_hash(email)
    if secret_hash:
        request["SecretHash"] = secret_hash

    try:
        return client.sign_up(**request)
    except Exception as exc:
        message = getattr(exc, "response", {}).get("Error", {}).get("Message", str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc


def cognito_confirm_sign_up(email: str, confirmation_code: str) -> None:
    client = _cognito_client()

    request: Dict[str, Any] = {
        "ClientId": settings.COGNITO_APP_CLIENT_ID,
        "Username": email,
        "ConfirmationCode": confirmation_code,
    }
    secret_hash = _secret_hash(email)
    if secret_hash:
        request["SecretHash"] = secret_hash

    try:
        client.confirm_sign_up(**request)
    except Exception as exc:
        message = (
            getattr(exc, "response", {})
            .get("Error", {})
            .get("Message", "Sign-up confirmation failed")
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc


def cognito_resend_sign_up_code(email: str) -> None:
    client = _cognito_client()

    request: Dict[str, Any] = {
        "ClientId": settings.COGNITO_APP_CLIENT_ID,
        "Username": email,
    }
    secret_hash = _secret_hash(email)
    if secret_hash:
        request["SecretHash"] = secret_hash

    try:
        client.resend_confirmation_code(**request)
    except Exception as exc:
        message = (
            getattr(exc, "response", {})
            .get("Error", {})
            .get("Message", "Failed to resend verification code")
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc


def cognito_login(email: str, password: str) -> Dict[str, str]:
    client = _cognito_client()

    auth_parameters = {
        "USERNAME": email,
        "PASSWORD": password,
    }
    secret_hash = _secret_hash(email)
    if secret_hash:
        auth_parameters["SECRET_HASH"] = secret_hash

    configured_flow = (settings.COGNITO_AUTH_FLOW or "USER_PASSWORD_AUTH").strip().upper()

    def _initiate_user_password() -> Dict[str, Any]:
        return client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters=auth_parameters,
            ClientId=settings.COGNITO_APP_CLIENT_ID,
        )

    def _initiate_admin_user_password() -> Dict[str, Any]:
        return client.admin_initiate_auth(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            ClientId=settings.COGNITO_APP_CLIENT_ID,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters=auth_parameters,
        )

    try:
        if configured_flow == "ADMIN_USER_PASSWORD_AUTH":
            response = _initiate_admin_user_password()
        else:
            response = _initiate_user_password()
    except Exception as exc:
        message = getattr(exc, "response", {}).get("Error", {}).get("Message", "Login failed")

        # Common misconfiguration: app client has USER_PASSWORD_AUTH disabled.
        if (
            configured_flow == "USER_PASSWORD_AUTH"
            and "USER_PASSWORD_AUTH flow not enabled" in message
        ):
            try:
                response = _initiate_admin_user_password()
            except Exception as fallback_exc:
                fallback_msg = (
                    getattr(fallback_exc, "response", {})
                    .get("Error", {})
                    .get("Message", "Login failed")
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail=fallback_msg
                ) from fallback_exc
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from exc

    auth_result = response.get("AuthenticationResult") or {}
    access_token = auth_result.get("AccessToken")
    refresh_token = auth_result.get("RefreshToken")
    id_token = auth_result.get("IdToken")

    if not access_token or not id_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Cognito auth response"
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token or "",
        "id_token": id_token,
        "token_type": "bearer",
    }


def cognito_global_sign_out(access_token: str) -> None:
    client = _cognito_client()
    if not access_token:
        return

    try:
        client.global_sign_out(AccessToken=access_token)
    except Exception:
        # Best effort sign out. Client cookies are still cleared by backend.
        return


def cognito_change_password(
    access_token: str, previous_password: str, proposed_password: str
) -> None:
    client = _cognito_client()
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    try:
        client.change_password(
            AccessToken=access_token,
            PreviousPassword=previous_password,
            ProposedPassword=proposed_password,
        )
    except Exception as exc:
        message = (
            getattr(exc, "response", {}).get("Error", {}).get("Message", "Password change failed")
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc


def cognito_forgot_password_start(email: str) -> None:
    client = _cognito_client()

    request: Dict[str, Any] = {
        "ClientId": settings.COGNITO_APP_CLIENT_ID,
        "Username": email,
    }
    secret_hash = _secret_hash(email)
    if secret_hash:
        request["SecretHash"] = secret_hash

    try:
        client.forgot_password(**request)
    except Exception as exc:
        message = (
            getattr(exc, "response", {})
            .get("Error", {})
            .get("Message", "Password reset request failed")
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc


def cognito_forgot_password_confirm(email: str, confirmation_code: str, new_password: str) -> None:
    client = _cognito_client()

    request: Dict[str, Any] = {
        "ClientId": settings.COGNITO_APP_CLIENT_ID,
        "Username": email,
        "ConfirmationCode": confirmation_code,
        "Password": new_password,
    }
    secret_hash = _secret_hash(email)
    if secret_hash:
        request["SecretHash"] = secret_hash

    try:
        client.confirm_forgot_password(**request)
    except Exception as exc:
        message = (
            getattr(exc, "response", {})
            .get("Error", {})
            .get("Message", "Password reset confirmation failed")
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc


@lru_cache(maxsize=1)
def _fetch_jwks() -> Dict[str, Any]:
    _ensure_cognito_config()
    response = requests.get(settings.cognito_jwks_url, timeout=10)
    response.raise_for_status()
    return response.json()


def verify_cognito_token(token: str, token_use: str = "access") -> Dict[str, Any]:
    _ensure_cognito_config()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    try:
        headers = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header"
        ) from exc

    kid = headers.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token key id")

    jwks = _fetch_jwks()
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown token signing key"
        )

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=settings.cognito_issuer,
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc

    actual_token_use = claims.get("token_use")
    if actual_token_use != token_use:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unexpected token use")

    if token_use == "id":
        if claims.get("aud") != settings.COGNITO_APP_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token audience"
            )
    else:
        if claims.get("client_id") != settings.COGNITO_APP_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token client id"
            )

    return claims
