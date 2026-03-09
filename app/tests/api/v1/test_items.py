from datetime import date, timedelta

import pytest
from app.config import settings
from fastapi.testclient import TestClient
from app.models import User, Household, Item
from app.models.item import CategoryEnum, UnitEnum


def _item_payload(name: str = "Milk", **kwargs) -> dict:
    # Use a future expiry so validation passes regardless of run date (CI or local)
    future_expiry = (date.today() + timedelta(days=30)).isoformat()
    defaults = {
        "name": name,
        "quantity": 1,
        "unit": "kg",
        "expiry_date": future_expiry,
        "category": "Dairy",
    }
    defaults.update(kwargs)
    return defaults


# ----- List items -----


def test_list_items_empty(auth_client: TestClient, create_test_user: User) -> None:
    # sets up a test user and their household (no items)
    household_id = create_test_user.household_id
    r = auth_client.get(f"{settings.API_V1_STR}/items", params={"household_id": household_id})
    assert r.status_code == 200
    assert len(r.json()) == 0


def test_list_items_requires_household_id(auth_client: TestClient) -> None:
    # tests that the API returns a 400 error if the household_id is not provided
    r = auth_client.get(f"{settings.API_V1_STR}/items")
    assert r.status_code == 400
    assert "household_id" in r.json().get("detail", "").lower()


def test_list_items_denied_for_other_household(
    auth_client: TestClient, create_test_user: User
) -> None:
    # tests that the API returns a 403 error if the household_id is not the same as the test user's household_id
    other_household_id = 99999
    r = auth_client.get(f"{settings.API_V1_STR}/items", params={"household_id": other_household_id})
    assert r.status_code == 403
    assert "access denied" in r.json().get("detail", "").lower()


def test_list_items_with_results(auth_client: TestClient, create_test_user: User, db) -> None:
    # tests that the API returns a 200 status code and the correct number of items
    from app.database import get_db

    household_id = create_test_user.household_id
    item = Item(
        name="Bread",
        quantity=2,
        unit=UnitEnum.PIECES,
        expiry_date="2026-04-01",
        category=CategoryEnum.OTHER,
        household_id=household_id,
    )
    db.add(item)
    db.commit()

    r = auth_client.get(f"{settings.API_V1_STR}/items", params={"household_id": household_id})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["name"] == "Bread"


def test_list_items_filter_by_category(auth_client: TestClient, create_test_user: User, db) -> None:
    # tests that the API returns a 200 status code and the correct number of items filtered by category
    household_id = create_test_user.household_id
    for name, cat in [("Milk", CategoryEnum.DAIRY), ("Apple", CategoryEnum.FRUITS)]:
        db.add(
            Item(
                name=name,
                quantity=1,
                unit=UnitEnum.PIECES,
                expiry_date="2026-05-01",
                category=cat,
                household_id=household_id,
            )
        )
    db.commit()

    r = auth_client.get(
        f"{settings.API_V1_STR}/items", params={"household_id": household_id, "category": "Dairy"}
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["category"] == "Dairy"


def test_list_items_sort_by_expiry(auth_client: TestClient, create_test_user: User, db) -> None:
    # tests that the API returns a 200 status code and the correct number of items sorted by expiry date
    household_id = create_test_user.household_id
    for name, exp in [("First", "2026-06-01"), ("Second", "2026-05-01")]:
        db.add(
            Item(
                name=name,
                quantity=1,
                unit=UnitEnum.PIECES,
                expiry_date=exp,
                category=CategoryEnum.OTHER,
                household_id=household_id,
            )
        )
    db.commit()

    r = auth_client.get(
        f"{settings.API_V1_STR}/items",
        params={"household_id": household_id, "sort_by_expiry": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["expiry_date"] == "2026-05-01"
    assert data[1]["expiry_date"] == "2026-06-01"


# ----- Create item -----


def test_create_item(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 201 status code and the correct item data
    household_id = create_test_user.household_id
    data = _item_payload()

    r = auth_client.post(
        f"{settings.API_V1_STR}/items", params={"household_id": household_id}, json=data
    )
    assert r.status_code == 201

    item = r.json()
    assert len(item) == 9
    assert item["name"] == "Milk"
    assert item["quantity"] == 1
    assert item["unit"] == "kg"
    assert item["expiry_date"] == data["expiry_date"]
    assert item["category"] == "Dairy"


def test_create_item_requires_household_id(auth_client: TestClient) -> None:
    # tests that the API returns a 400 error if the household_id is not provided
    r = auth_client.post(f"{settings.API_V1_STR}/items", json=_item_payload())
    assert r.status_code == 400


def test_create_item_denied_for_other_household(
    auth_client: TestClient, create_test_user: User
) -> None:
    # tests that the API returns a 403 error if the household_id is not the same as the test user's household_id
    r = auth_client.post(
        f"{settings.API_V1_STR}/items",
        params={"household_id": 99999},
        json=_item_payload(),
    )
    assert r.status_code == 403


def test_create_item_rejects_past_expiry(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 422 error if the expiry date is in the past
    past = (date.today() - timedelta(days=1)).isoformat()
    r = auth_client.post(
        f"{settings.API_V1_STR}/items",
        params={"household_id": create_test_user.household_id},
        json=_item_payload(expiry_date=past),
    )
    assert r.status_code == 422


# ----- Get item -----


def test_get_item(auth_client: TestClient, create_test_user: User, db) -> None:
    # tests that the API returns a 200 status code and the correct item data
    household_id = create_test_user.household_id
    item = Item(
        name="Eggs",
        quantity=6,
        unit=UnitEnum.PIECES,
        expiry_date="2026-03-15",
        category=CategoryEnum.DAIRY,
        household_id=household_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    r = auth_client.get(
        f"{settings.API_V1_STR}/items/{item.id}", params={"household_id": household_id}
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Eggs"
    assert r.json()["quantity"] == 6


def test_get_item_404(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 404 error if the item id is not found
    r = auth_client.get(
        f"{settings.API_V1_STR}/items/99999", params={"household_id": create_test_user.household_id}
    )
    assert r.status_code == 404


def test_get_item_403_other_household(auth_client: TestClient, create_test_user: User, db) -> None:
    # tests that the API returns a 403 error if the household_id is not the same as the test user's household_id
    other = Household(name="Other")
    db.add(other)
    db.commit()
    db.refresh(other)
    item = Item(
        name="X",
        quantity=1,
        unit=UnitEnum.PIECES,
        expiry_date="2026-06-01",
        category=CategoryEnum.OTHER,
        household_id=other.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    r = auth_client.get(f"{settings.API_V1_STR}/items/{item.id}", params={"household_id": other.id})
    assert r.status_code == 403


# ----- Update item -----


def test_update_item(auth_client: TestClient, create_test_user: User, db) -> None:
    # tests that the API returns a 200 status code and the correct item data
    household_id = create_test_user.household_id
    item = Item(
        name="Old",
        quantity=1,
        unit=UnitEnum.PIECES,
        expiry_date="2026-04-01",
        category=CategoryEnum.OTHER,
        household_id=household_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    r = auth_client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        params={"household_id": household_id},
        json={"name": "Updated", "quantity": 5},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Updated"
    assert data["quantity"] == 5


def test_update_item_404(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 404 error if the item id is not found
    r = auth_client.put(
        f"{settings.API_V1_STR}/items/99999",
        params={"household_id": create_test_user.household_id},
        json={"name": "X"},
    )
    assert r.status_code == 404


# ----- Delete item -----


def test_delete_item(auth_client: TestClient, create_test_user: User, db) -> None:
    # tests that the API returns a 204 status code and the item is deleted
    household_id = create_test_user.household_id
    item = Item(
        name="ToDelete",
        quantity=1,
        unit=UnitEnum.PIECES,
        expiry_date="2026-04-01",
        category=CategoryEnum.OTHER,
        household_id=household_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    r = auth_client.delete(
        f"{settings.API_V1_STR}/items/{item.id}", params={"household_id": household_id}
    )
    assert r.status_code == 204

    r2 = auth_client.get(
        f"{settings.API_V1_STR}/items/{item.id}", params={"household_id": household_id}
    )
    assert r2.status_code == 404


def test_delete_item_404(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 404 error if the item id is not found
    r = auth_client.delete(
        f"{settings.API_V1_STR}/items/99999", params={"household_id": create_test_user.household_id}
    )
    assert r.status_code == 404


# ----- Adjust quantity -----


def test_adjust_quantity_increase(auth_client: TestClient, create_test_user: User, db) -> None:
    # tests that the API returns a 200 status code and the correct item data
    household_id = create_test_user.household_id
    item = Item(
        name="Qty",
        quantity=10,
        unit=UnitEnum.PIECES,
        expiry_date="2026-04-01",
        category=CategoryEnum.OTHER,
        household_id=household_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    r = auth_client.patch(
        f"{settings.API_V1_STR}/items/{item.id}/quantity",
        params={"household_id": household_id},
        json={"change": 5},
    )
    assert r.status_code == 200
    assert r.json()["quantity"] == 15


def test_adjust_quantity_decrease(auth_client: TestClient, create_test_user: User, db) -> None:
    # tests that the API returns a 200 status code and the correct item data
    household_id = create_test_user.household_id
    item = Item(
        name="Qty",
        quantity=10,
        unit=UnitEnum.PIECES,
        expiry_date="2026-04-01",
        category=CategoryEnum.OTHER,
        household_id=household_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    r = auth_client.patch(
        f"{settings.API_V1_STR}/items/{item.id}/quantity",
        params={"household_id": household_id},
        json={"change": -3},
    )
    assert r.status_code == 200
    assert r.json()["quantity"] == 7


def test_adjust_quantity_rejects_negative_result(
    auth_client: TestClient, create_test_user: User, db
) -> None:
    # tests that the API returns a 400 error if the quantity is negative
    household_id = create_test_user.household_id
    item = Item(
        name="Qty",
        quantity=2,
        unit=UnitEnum.PIECES,
        expiry_date="2026-04-01",
        category=CategoryEnum.OTHER,
        household_id=household_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    r = auth_client.patch(
        f"{settings.API_V1_STR}/items/{item.id}/quantity",
        params={"household_id": household_id},
        json={"change": -10},
    )
    assert r.status_code == 400
    assert "negative" in r.json().get("detail", "").lower()


def test_adjust_quantity_404(auth_client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 404 error if the item id is not found
    r = auth_client.patch(
        f"{settings.API_V1_STR}/items/99999/quantity",
        params={"household_id": create_test_user.household_id},
        json={"change": 1},
    )
    assert r.status_code == 404


# ----- Auth -----


def test_list_items_unauthorized(client: TestClient, create_test_user: User) -> None:
    # tests that the API returns a 401 error if the user is not authenticated
    """No auth cookie -> 401."""
    r = client.get(
        f"{settings.API_V1_STR}/items", params={"household_id": create_test_user.household_id}
    )
    assert r.status_code == 401
