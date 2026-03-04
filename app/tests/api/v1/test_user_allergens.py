from fastapi.testclient import TestClient
from app.config import settings

VALID = ['PEANUTS', 'SHELLFISH', 'MILK']

def test_get_allergens_auth(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me/allergens")
    assert r.status_code == 401

def test_get_allergens_empty(auth_client: TestClient, create_test_user) -> None:
    r = auth_client.get(f"{settings.API_V1_STR}/users/me/allergens")
    assert r.status_code == 200
    
    data = r.json()
    assert data["user_id"] == create_test_user.id
    assert data["allergens"] == []


def test_put_allergens(auth_client: TestClient, create_test_user) -> None:
    r = auth_client.put(
        f"{settings.API_V1_STR}/users/me/allergens",
        json={"allergens": VALID}
    )
    assert r.status_code == 200
    
    data = r.json()
    assert data["user_id"] == create_test_user.id
    assert set(data["allergens"]) == set(VALID)


def test_get_allergens(auth_client: TestClient, create_test_user) -> None:
    
    r = auth_client.put(
        f"{settings.API_V1_STR}/users/me/allergens",
        json={"allergens": VALID}
    )

    r = auth_client.get(f"{settings.API_V1_STR}/users/me/allergens")
    assert r.status_code == 200
    
    data = r.json()
    assert data["user_id"] == create_test_user.id
    assert set(data["allergens"]) == set(VALID)



def test_put_allergens_invalid(auth_client: TestClient) -> None:
    r = auth_client.put(
        f"{settings.API_V1_STR}/users/me/allergens",
        json={"allergens": ["INVALID_ALLERGEN"]}
    )
    assert r.status_code == 422

def test_put_allergens_empty(auth_client: TestClient, create_test_user) -> None:
    r = auth_client.put(
        f"{settings.API_V1_STR}/users/me/allergens",
        json={"allergens": []}
    )
    assert r.status_code == 200
    
    data = r.json()
    assert data["user_id"] == create_test_user.id
    assert data["allergens"] == []
