"""Tests for Cognito-backed auth and password flows."""

from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.models import User
from app.core.security import get_current_user
from app.api.v1.endpoints import auth as auth_endpoints
from app.api.v1.endpoints import users as users_endpoints


@pytest.fixture()
def cognito_mode() -> Generator[None, None, None]:
    """Temporarily force Cognito mode for tests in this module."""
    original = settings.AUTH_PROVIDER
    settings.AUTH_PROVIDER = "cognito"
    yield
    settings.AUTH_PROVIDER = original


def test_confirm_signup_cognito_calls_helper(client: TestClient, cognito_mode, monkeypatch) -> None:
    calls = {}

    def _fake_confirm(email: str, code: str) -> None:
        calls["email"] = email
        calls["code"] = code

    monkeypatch.setattr(auth_endpoints, "cognito_confirm_sign_up", _fake_confirm)

    r = client.post(
        f"{settings.API_V1_STR}/auth/confirm-signup",
        json={"email": "verify@example.com", "confirmation_code": "123456"},
    )

    assert r.status_code == 200
    assert calls == {"email": "verify@example.com", "code": "123456"}


def test_resend_confirmation_cognito_calls_helper(client: TestClient, cognito_mode, monkeypatch) -> None:
    calls = {}

    def _fake_resend(email: str) -> None:
        calls["email"] = email

    monkeypatch.setattr(auth_endpoints, "cognito_resend_sign_up_code", _fake_resend)

    r = client.post(
        f"{settings.API_V1_STR}/auth/resend-confirmation",
        json={"email": "verify@example.com"},
    )

    assert r.status_code == 200
    assert calls == {"email": "verify@example.com"}


def test_register_cognito_sets_cognito_sub(client: TestClient, db, cognito_mode, monkeypatch) -> None:
    monkeypatch.setattr(
        auth_endpoints,
        "cognito_sign_up",
        lambda email, password, name: {"UserSub": "sub-abc-123"},
    )

    r = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "cognito-new@example.com",
            "password": "Secure_12",
            "password_confirm": "Secure_12",
            "name": "Cognito User",
        },
    )

    assert r.status_code == 201
    user = db.query(User).filter(User.email == "cognito-new@example.com").first()
    assert user is not None
    assert user.cognito_sub == "sub-abc-123"


def test_login_cognito_creates_local_user(client: TestClient, db, cognito_mode, monkeypatch) -> None:
    monkeypatch.setattr(
        auth_endpoints,
        "cognito_login",
        lambda email, password: {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "id_token": "id-token",
            "token_type": "bearer",
        },
    )
    monkeypatch.setattr(
        auth_endpoints,
        "verify_cognito_token",
        lambda token, token_use="id": {
            "sub": "sub-login-1",
            "email": "new-login@example.com",
            "name": "Login User",
        },
    )

    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "new-login@example.com", "password": "Password_1"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert r.status_code == 200
    assert "access_token" in r.cookies
    assert "refresh_token" in r.cookies

    user = db.query(User).filter(User.email == "new-login@example.com").first()
    assert user is not None
    assert user.cognito_sub == "sub-login-1"


def test_change_password_cognito_calls_helper(
    client: TestClient,
    create_test_user: User,
    cognito_mode,
    monkeypatch,
) -> None:
    calls = {}

    def _fake_change(token: str, current_password: str, new_password: str) -> None:
        calls["token"] = token
        calls["current_password"] = current_password
        calls["new_password"] = new_password

    monkeypatch.setattr(users_endpoints, "cognito_change_password", _fake_change)
    app.dependency_overrides[get_current_user] = lambda: create_test_user

    try:
        r = client.put(
            f"{settings.API_V1_STR}/users/me/password",
            json={"current_password": "oldpass123", "new_password": "newpass456"},
            headers={"Authorization": "Bearer token-xyz"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert r.status_code == 200
    assert calls == {
        "token": "token-xyz",
        "current_password": "oldpass123",
        "new_password": "newpass456",
    }


def test_reset_password_request_cognito_calls_helper(client: TestClient, cognito_mode, monkeypatch) -> None:
    calls = {}

    def _fake_start(email: str) -> None:
        calls["email"] = email

    monkeypatch.setattr(users_endpoints, "cognito_forgot_password_start", _fake_start)

    r = client.post(
        f"{settings.API_V1_STR}/users/reset-password/request",
        json={"email": "forgot@example.com"},
    )

    assert r.status_code == 200
    assert calls == {"email": "forgot@example.com"}


def test_reset_password_confirm_cognito_calls_helper(client: TestClient, cognito_mode, monkeypatch) -> None:
    calls = {}

    def _fake_confirm(email: str, confirmation_code: str, new_password: str) -> None:
        calls["email"] = email
        calls["confirmation_code"] = confirmation_code
        calls["new_password"] = new_password

    monkeypatch.setattr(users_endpoints, "cognito_forgot_password_confirm", _fake_confirm)

    r = client.post(
        f"{settings.API_V1_STR}/users/reset-password/confirm",
        json={
            "email": "forgot@example.com",
            "confirmation_code": "654321",
            "new_password": "Secure_12",
        },
    )

    assert r.status_code == 200
    assert calls == {
        "email": "forgot@example.com",
        "confirmation_code": "654321",
        "new_password": "Secure_12",
    }
