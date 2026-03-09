"""
test_recipe_cook.py -> tests the auto-deduction of ingredients from fridge
when a user cooks an AI-generated recipe.
"""

import pytest

from app.models.item import Item, UnitEnum, CategoryEnum
from app.models.usage_log import ItemUsageLog
from app.services.recipe_cook import cook_recipe, parse_ingredient_line


@pytest.fixture
def egg_item(db, create_test_user):
    item = Item(
        name="egg",
        quantity=6,
        unit=UnitEnum.PIECES,
        category=CategoryEnum.OTHER,
        expiry_date="2026-01-01",
        household_id=create_test_user.household_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def rice_item(db, create_test_user):
    item = Item(
        name="rice",
        quantity=2,
        unit=UnitEnum.G,
        category=CategoryEnum.OTHER,
        expiry_date="2026-01-01",
        household_id=create_test_user.household_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_parse_ingredient_line_simple():
    result = parse_ingredient_line("2 egg")

    assert result["quantity"] == 2
    assert result["name"] == "egg"


def test_cook_recipe_success_deducts_quantity(db, create_test_user, egg_item):
    recipe = {
        "title": "Scrambled Eggs",
        "ingredients": ["2 egg"],
        "missing_ingredients": [],
        "steps": ["Cook eggs"],
    }

    cook_recipe(db, create_test_user.household_id, recipe)

    db.refresh(egg_item)

    assert egg_item.quantity == 4


def test_cook_recipe_creates_usage_log(db, create_test_user, egg_item):
    recipe = {
        "title": "Scrambled Eggs",
        "ingredients": ["2 egg"],
        "missing_ingredients": [],
        "steps": ["Cook eggs"],
    }

    cook_recipe(db, create_test_user.household_id, recipe)

    logs = db.query(ItemUsageLog).all()

    assert len(logs) == 1
    assert logs[0].item_name == "egg"
    assert logs[0].quantity_consumed == 2


def test_cook_recipe_insufficient_quantity_raises(db, create_test_user, egg_item):
    egg_item.quantity = 1
    db.commit()

    recipe = {
        "title": "Scrambled Eggs",
        "ingredients": ["2 egg"],
        "missing_ingredients": [],
        "steps": ["Cook eggs"],
    }

    with pytest.raises(ValueError):
        cook_recipe(db, create_test_user.household_id, recipe)


def test_no_partial_deduction_on_failure(db, create_test_user, egg_item, rice_item):
    recipe = {
        "title": "Egg Rice",
        "ingredients": ["2 egg", "999 rice"],
        "missing_ingredients": [],
        "steps": ["Cook"],
    }

    with pytest.raises(ValueError):
        cook_recipe(db, create_test_user.household_id, recipe)

    db.refresh(egg_item)
    db.refresh(rice_item)

    assert egg_item.quantity == 6
    assert rice_item.quantity == 2
    assert db.query(ItemUsageLog).count() == 0


def test_cook_recipe_missing_item_raises(db, create_test_user, egg_item):
    recipe = {
        "title": "Egg Garlic Fry",
        "ingredients": ["2 egg", "1 garlic"],
        "missing_ingredients": [],
        "steps": ["Cook"],
    }

    with pytest.raises(ValueError, match="Item not found"):
        cook_recipe(db, create_test_user.household_id, recipe)


def test_parse_ingredient_line_invalid_raises():
    with pytest.raises(ValueError, match="Invalid ingredient format"):
        parse_ingredient_line("egg")


# -------------------------
# API endpoint test
# -------------------------
def test_cook_recipe_endpoint(auth_client, db, create_test_user, egg_item):

    payload = {
        "title": "Scrambled Eggs",
        "ingredients": ["2 egg"],
        "missing_ingredients": [],
        "steps": ["Cook eggs"],
    }

    response = auth_client.post("/api/v1/recipes/cook", json=payload)

    assert response.status_code == 200

    db.refresh(egg_item)
    assert egg_item.quantity == 4


def test_parse_ingredient_line_accepts_decimal_whole_number():
    result = parse_ingredient_line("11.0 pieces of Eggs")
    assert result["quantity"] == 11
    assert result["name"] == "egg"


def test_parse_ingredient_line_rejects_fractional_quantity():
    with pytest.raises(ValueError, match="whole number"):
        parse_ingredient_line("1.5 eggs")


def test_cook_recipe_matches_case_insensitively(db, create_test_user):
    item = Item(
        name="Egg",
        quantity=6,
        unit=UnitEnum.PIECES,
        category=CategoryEnum.OTHER,
        expiry_date="2026-01-01",
        household_id=create_test_user.household_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    recipe = {
        "title": "Scrambled Eggs",
        "ingredients": ["2 eggs"],
        "missing_ingredients": [],
        "steps": ["Cook eggs"],
    }

    cook_recipe(db, create_test_user.household_id, recipe)

    db.refresh(item)
    assert item.quantity == 4
