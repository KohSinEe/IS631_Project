"""Tests for users API endpoints."""

from app.config import settings
from fastapi.testclient import TestClient
from app.models import User


# ----- Get current user (GET /me) -----


def test_get_me(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 200 status code and the correct user data
    """Authenticated user can get their profile."""
    r = auth_client.get(f"{settings.API_V1_STR}/users/me")
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == create_test_user.email
    assert data["id"] == create_test_user.id
    assert data["household_id"] == create_test_user.household_id
    assert data["is_active"] is True
    assert "hashed_password" not in data


def test_get_me_unauthorized(client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 401 error if the user is not authenticated
    """Without auth cookie, GET /me returns 401."""
    r = client.get(f"{settings.API_V1_STR}/users/me")
    assert r.status_code == 401


# ----- Update current user (PUT /me) -----


def test_update_me(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 200 status code and the correct user data
    """Authenticated user can update their name."""
    r = auth_client.put(
        f"{settings.API_V1_STR}/users/me",
        json={"name": "Updated Name"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Updated Name"
    assert data["email"] == create_test_user.email


def test_update_me_partial(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 200 status code and the correct user data
    """Partial update only changes provided fields."""
    r = auth_client.put(
        f"{settings.API_V1_STR}/users/me",
        json={"name": "New Name"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"


def test_update_me_unauthorized(client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 401 error if the user is not authenticated
    """Without auth, PUT /me returns 401."""
    r = client.put(
        f"{settings.API_V1_STR}/users/me",
        json={"name": "Hacker"},
    )
    assert r.status_code == 401


# ----- Change password (PUT /me/password) -----


def test_change_password_success(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 200 status code and the correct user data
    """User can change password with correct current password."""
    r = auth_client.put(
        f"{settings.API_V1_STR}/users/me/password",
        json={
            "current_password": "password123",
            "new_password": "newpassword456",
        },
    )
    assert r.status_code == 200
    assert "message" in r.json()

    # New password works at login
    login_r = auth_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test@example.com", "password": "newpassword456"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_r.status_code == 200


def test_change_password_wrong_current(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 400 error if the current password is incorrect
    """Wrong current password returns 400."""
    r = auth_client.put(
        f"{settings.API_V1_STR}/users/me/password",
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
        },
    )
    assert r.status_code == 400
    assert "current password" in r.json().get("detail", "").lower()


def test_change_password_same_as_current(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 400 error if the new password is the same as the current password
    """New password same as current returns 400."""
    r = auth_client.put(
        f"{settings.API_V1_STR}/users/me/password",
        json={
            "current_password": "password123",
            "new_password": "password123",
        },
    )
    assert r.status_code == 400
    assert "different" in r.json().get("detail", "").lower()


def test_change_password_unauthorized(client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 401 error if the user is not authenticated
    """Without auth, PUT /me/password returns 401."""
    r = client.put(
        f"{settings.API_V1_STR}/users/me/password",
        json={
            "current_password": "password123",
            "new_password": "newpassword456",
        },
    )
    assert r.status_code == 401


# ----- Delete current user (DELETE /me) -----


def test_delete_me(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 204 status code and the user is deleted
    """Authenticated user can delete their account."""
    r = auth_client.delete(f"{settings.API_V1_STR}/users/me")
    assert r.status_code == 204

    # Same cookie can no longer access /me (user is gone)
    r2 = auth_client.get(f"{settings.API_V1_STR}/users/me")
    assert r2.status_code == 401


def test_delete_me_unauthorized(client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 401 error if the user is not authenticated
    """Without auth, DELETE /me returns 401."""
    r = client.delete(f"{settings.API_V1_STR}/users/me")
    assert r.status_code == 401
