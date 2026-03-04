from fastapi.testclient import TestClient
from app.config import settings

VALID = ['PEANUTS', 'SHELLFISH', 'MILK']


# Household allergen tests

def test_get_household_allergens_auth(client: TestClient) -> None:
    """Unauthenticated users cannot view household allergens."""
    r = client.get(f"{settings.API_V1_STR}/households/allergens")
    assert r.status_code == 401

def test_get_household_allergens_empty(auth_client: TestClient, create_test_user) -> None:
    """Returns all household members with empty allergen lists if none set."""
    r = auth_client.get(f"{settings.API_V1_STR}/households/allergens")
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, list)
    assert any(m["user_id"] == create_test_user.id for m in data)
    assert all(m["allergens"] == [] for m in data)

def test_get_household_allergens_with_data(auth_client: TestClient, create_test_user) -> None:
    """Returns correct allergens for each household member."""
    auth_client.put(
        f"{settings.API_V1_STR}/users/me/allergens",
        json={"allergens": VALID}
    )

    r = auth_client.get(f"{settings.API_V1_STR}/households/allergens")
    assert r.status_code == 200

    data = r.json()
    member = next(m for m in data if m["user_id"] == create_test_user.id)
    assert set(member["allergens"]) == set(VALID)


def test_get_household_allergens_outside_household(client: TestClient, db) -> None:
    """Users outside the household cannot view allergens."""
    # Create a second user with no household
    from app.models import User
    from app.core.security import get_password_hash
    outsider = User(
        email="outsider@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        household_id=None,
    )
    db.add(outsider)
    db.commit()

    client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "outsider@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    r = client.get(f"{settings.API_V1_STR}/households/allergens")
    assert r.status_code == 403