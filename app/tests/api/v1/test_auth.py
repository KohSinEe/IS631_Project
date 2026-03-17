"""Tests for authentication API endpoints."""

from app.config import settings
from fastapi.testclient import TestClient
from app.models import User

# ----- Register -----


def test_register_success(client: TestClient, db) -> None:
    """New user can register with email and password."""
    r = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "Secure_12",
            "password_confirm": "Secure_12",
            "name": "New User",
            "household_name": "New User Household",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    assert data["is_active"] is True
    assert data["household_id"] is not None
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_without_household_success(client: TestClient, db) -> None:
    """New user can register without providing a household name."""
    r = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "nohouse@example.com",
            "password": "Secure_12",
            "password_confirm": "Secure_12",
            "name": "No House",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "nohouse@example.com"
    assert data["household_id"] is None


def test_register_duplicate_email(client: TestClient, create_test_user: User) -> None:
    """Duplicate email returns 400."""
    r = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "test@example.com",
            "password": "Another_1",
            "password_confirm": "Another_1",
            "name": "Duplicate",
            "household_name": "Dup Household",
        },
    )
    assert r.status_code == 400
    assert "already registered" in r.json().get("detail", "").lower()


def test_register_password_too_short(client: TestClient, db) -> None:
    """Password under 8 characters returns 422."""
    r = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "short@example.com",
            "password": "short",
            "name": "Short",
        },
    )
    assert r.status_code == 422


def test_register_invalid_email(client: TestClient, db) -> None:
    """Invalid email format returns 422."""
    r = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": "not-an-email",
            "password": "validpass123",
            "name": "Bad",
        },
    )
    assert r.status_code == 422


# ----- Login -----


def test_login_success(client: TestClient, create_test_user: User) -> None:
    """Valid credentials return 200 and set cookies."""
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "refresh_token" in data
    assert "access_token" in r.cookies
    assert "refresh_token" in r.cookies


def test_login_wrong_password(client: TestClient, create_test_user: User) -> None:
    """Wrong password returns 401."""
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401
    assert "incorrect" in r.json().get("detail", "").lower()


def test_login_nonexistent_user(client: TestClient, db) -> None:
    """Unknown email returns 401."""
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "nobody@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401


def test_login_inactive_user(client: TestClient, db) -> None:
    """Inactive user gets 403."""
    from app.models import User, Household
    from app.core.security import get_password_hash

    household = Household(name="Inactive Household")
    db.add(household)
    db.commit()
    db.refresh(household)
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=False,
        household_id=household.id,
    )
    db.add(user)
    db.commit()

    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "inactive@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 403
    assert "inactive" in r.json().get("detail", "").lower()


# ----- Logout -----


def test_logout(client: TestClient, create_test_user: User) -> None:
    """Logout clears cookies and returns 200."""
    login_r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_r.status_code == 200

    r = client.post(f"{settings.API_V1_STR}/auth/logout")
    assert r.status_code == 200
    assert "message" in r.json()
    # Cookies should be cleared (empty or max_age=0)
    assert r.cookies.get("access_token") in (None, "")
