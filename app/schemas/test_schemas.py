"""Tests for Pydantic schemas (validation, serialization)."""

from datetime import date, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserUpdate, PasswordChange, UserResponse
from app.schemas.auth import Token
from app.schemas.item import (
    Category,
    UnitType,
    ItemCreate,
    ItemUpdate,
    ItemQuantityChange,
)
from app.schemas.recipes import PantryItem, Recipe, RecipeGenerateRequest, RecipeGenerateResponse


# ----- User schemas -----


def test_user_create_valid() -> None:
    """UserCreate accepts valid email, password, optional name and household."""
    u = UserCreate(email="user@example.com", password="Password_123", name="Test", household_name="Home")
    assert u.email == "user@example.com"
    assert u.password == "Password_123"
    assert u.name == "Test"
    assert u.household_name == "Home"


def test_user_create_password_too_short() -> None:
    """UserCreate rejects password under 8 characters."""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(email="u@x.com", password="short")
    assert "password" in str(exc_info.value).lower() or "8" in str(exc_info.value)


def test_user_create_password_too_long() -> None:
    """UserCreate rejects password over 72 characters."""
    with pytest.raises(ValidationError):
        UserCreate(email="u@x.com", password="a" * 73)


def test_user_create_invalid_email() -> None:
    """UserCreate rejects invalid email format."""
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="valid_pass123")


def test_user_update_partial() -> None:
    """UserUpdate accepts optional name only."""
    u = UserUpdate(name="New Name")
    assert u.name == "New Name"
    u2 = UserUpdate()
    assert u2.name is None


def test_password_change_valid() -> None:
    """PasswordChange accepts current and new password (8+ chars)."""
    p = PasswordChange(current_password="Oldpass_123", new_password="Newpass_456")
    assert p.current_password == "Oldpass_123"
    assert p.new_password == "Newpass_456"


def test_password_change_new_too_short() -> None:
    """PasswordChange rejects new_password under 8 characters."""
    with pytest.raises(ValidationError):
        PasswordChange(current_password="Oldpass_123", new_password="short")


# ----- Auth schemas -----


def test_token_schema() -> None:
    """Token has access_token, refresh_token, default token_type."""
    t = Token(access_token="abc", refresh_token="xyz")
    assert t.access_token == "abc"
    assert t.refresh_token == "xyz"
    assert t.token_type == "bearer"


# ----- Item schemas -----


def test_item_create_valid() -> None:
    """ItemCreate accepts valid name, quantity, unit, expiry, category."""
    future = (date.today() + timedelta(days=7)).isoformat()
    item = ItemCreate(
        name="Milk",
        quantity=2,
        unit=UnitType.L,
        expiry_date=future,
        category=Category.DAIRY,
    )
    assert item.name == "Milk"
    assert item.quantity == 2
    assert item.unit == UnitType.L
    assert item.category == Category.DAIRY


def test_item_create_name_empty() -> None:
    """ItemCreate rejects empty name."""
    future = (date.today() + timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError):
        ItemCreate(
            name="",
            quantity=1,
            unit=UnitType.PIECES,
            expiry_date=future,
            category=Category.OTHER,
        )


def test_item_create_quantity_negative() -> None:
    """ItemCreate rejects negative quantity."""
    future = (date.today() + timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError):
        ItemCreate(
            name="Egg",
            quantity=-1,
            unit=UnitType.PIECES,
            expiry_date=future,
            category=Category.DAIRY,
        )


def test_item_create_expiry_in_past() -> None:
    """ItemCreate rejects expiry_date in the past."""
    past = (date.today() - timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError) as exc_info:
        ItemCreate(
            name="Egg",
            quantity=1,
            unit=UnitType.PIECES,
            expiry_date=past,
            category=Category.DAIRY,
        )
    assert "expiry" in str(exc_info.value).lower() or "past" in str(exc_info.value).lower()


def test_item_update_partial() -> None:
    """ItemUpdate accepts optional fields; expiry in past rejected."""
    u = ItemUpdate(name="Updated", quantity=5)
    assert u.name == "Updated"
    assert u.quantity == 5
    assert u.expiry_date is None

    past = (date.today() - timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError):
        ItemUpdate(expiry_date=past)


def test_item_quantity_change() -> None:
    """ItemQuantityChange accepts any integer change."""
    q = ItemQuantityChange(change=3)
    assert q.change == 3
    q2 = ItemQuantityChange(change=-2)
    assert q2.change == -2


# ----- Recipe schemas -----


def test_pantry_item() -> None:
    """PantryItem accepts name; quantity and unit optional."""
    p = PantryItem(name="egg")
    assert p.name == "egg"
    assert p.quantity is None
    assert p.unit is None
    p2 = PantryItem(name="milk", quantity=1.5, unit="L")
    assert p2.quantity == 1.5
    assert p2.unit == "L"


def test_recipe_valid() -> None:
    """Recipe accepts title, time_minutes in range, ingredients, steps."""
    r = Recipe(
        title="Scrambled Eggs",
        time_minutes=10,
        ingredients=["egg", "butter"],
        steps=["Beat eggs", "Cook"],
    )
    assert r.title == "Scrambled Eggs"
    assert r.time_minutes == 10
    assert r.missing_ingredients == []
    assert r.reason is None


def test_recipe_time_minutes_bounds() -> None:
    """Recipe rejects time_minutes outside 1–600."""
    with pytest.raises(ValidationError):
        Recipe(title="X", time_minutes=0, ingredients=["a"], steps=["b"])
    with pytest.raises(ValidationError):
        Recipe(title="X", time_minutes=601, ingredients=["a"], steps=["b"])


def test_recipe_generate_request() -> None:
    """RecipeGenerateRequest accepts items list and optional flags."""
    req = RecipeGenerateRequest(
        items=[PantryItem(name="egg")],
        inventory_only=True,
        max_recipes=2,
        preferences={"time_max": 30},
    )
    assert len(req.items) == 1
    assert req.items[0].name == "egg"
    assert req.inventory_only is True
    assert req.max_recipes == 2
    assert req.preferences == {"time_max": 30}


def test_recipe_generate_request_defaults() -> None:
    """RecipeGenerateRequest has defaults for inventory_only, max_recipes, preferences."""
    req = RecipeGenerateRequest(items=[PantryItem(name="rice")])
    assert req.inventory_only is True
    assert req.max_recipes == 3
    assert req.preferences is None


def test_recipe_generate_response() -> None:
    """RecipeGenerateResponse holds list of Recipe."""
    r = Recipe(
        title="Test",
        time_minutes=15,
        ingredients=["a"],
        steps=["step"],
    )
    res = RecipeGenerateResponse(recipes=[r])
    assert len(res.recipes) == 1
    assert res.recipes[0].title == "Test"
