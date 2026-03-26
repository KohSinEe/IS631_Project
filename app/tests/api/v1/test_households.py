"""Tests for household (fridge) endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.config import settings
from app.models import User, Household
from app.core.security import get_password_hash


def test_delete_household_as_owner_success(
    auth_client: TestClient, create_test_user: User, db: Session
) -> None:
    """Owner can delete their fridge; household and items are removed."""
    household_id = create_test_user.household_id
    assert household_id is not None
    r = auth_client.delete(f"{settings.API_V1_STR}/households/{household_id}")
    assert r.status_code == 204
    household = db.query(Household).filter(Household.id == household_id).first()
    assert household is None


def test_delete_household_as_non_owner_forbidden(
    client: TestClient, create_test_user: User, db: Session
) -> None:
    """Non-owner member cannot delete the fridge."""
    household_id = create_test_user.household_id
    other = User(
        email="other@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        household_id=household_id,
    )
    db.add(other)
    db.commit()
    db.refresh(other)
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "other@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    access_token = r.cookies.get("access_token")
    if access_token:
        client.cookies["access_token"] = access_token
    r2 = client.delete(f"{settings.API_V1_STR}/households/{household_id}")
    assert r2.status_code == 403
    assert "owner" in (r2.json().get("detail") or "").lower()


def test_delete_household_other_household_forbidden(
    auth_client: TestClient, create_test_user: User
) -> None:
    """Delete returns 403 when trying to delete another household."""
    # create_test_user's household_id is e.g. 1; 99999 is not theirs
    r = auth_client.delete(f"{settings.API_V1_STR}/households/99999")
    assert r.status_code == 403


def test_create_household_success(client: TestClient, db: Session) -> None:
    """User without a household can create one."""
    user = User(
        email="newuser@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        household_id=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # login
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "newuser@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200

    access_token = r.cookies.get("access_token")
    if access_token:
        client.cookies["access_token"] = access_token

    r2 = client.post(
        f"{settings.API_V1_STR}/households",
        json={"name": "My Fridge"},
    )

    assert r2.status_code == 201
    data = r2.json()

    assert data["name"] == "My Fridge"
    assert "id" in data

    db.refresh(user)
    assert user.household_id == data["id"]


def test_create_household_when_user_already_in_one(auth_client: TestClient) -> None:
    """User already in a household cannot create another."""
    r = auth_client.post(
        f"{settings.API_V1_STR}/households",
        json={"name": "Another Fridge"},
    )

    assert r.status_code == 400
    assert "already belong to a household" in r.json()["detail"].lower()
