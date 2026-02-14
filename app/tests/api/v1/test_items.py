from app.config import settings
from fastapi.testclient import TestClient
from app.models import User


def test_list_items_empty(auth_client: TestClient, create_test_user: User) -> None:
    household_id = create_test_user.household_id

    r = auth_client.get(f"{settings.API_V1_STR}/items", params={"household_id": household_id})

    assert r.status_code == 200
    assert len(r.json()) == 0


def test_create_item(auth_client: TestClient, create_test_user: User) -> None:
    household_id = create_test_user.household_id
    data = {
        "name": "Milk",
        "quantity": 1,
        "unit": "kg",
        "expiry_date": "2026-03-01",
        "category": "Dairy",
    }

    r = auth_client.post(
        f"{settings.API_V1_STR}/items", params={"household_id": household_id}, json=data
    )
    assert r.status_code == 201

    item = r.json()
    assert len(item) == 9
    assert item["name"] == "Milk"
    assert item["quantity"] == 1
    assert item["unit"] == "kg"
    assert item["expiry_date"] == "2026-03-01"
    assert item["category"] == "Dairy"
