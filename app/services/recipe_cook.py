"""
Allows users to "cook" AI-generated recipes
to auto-deduct ingredients when cooking AI-generated recipes.
"""

import re

from app.models.item import Item
from app.models.usage_log import ItemUsageLog


def normalize_ingredient_name(name: str) -> str:
    """
    Normalize ingredient/item names for matching.

    Examples:
    - "Egg" -> "egg"
    - " Eggs " -> "egg"
    - "tomatoes" -> "tomato"
    - "garlic cloves" -> "garlic clove"
    """
    if not name or not isinstance(name, str):
        return ""

    name = name.strip().lower()
    name = re.sub(r"\s+", " ", name)

    irregulars = {
        "eggs": "egg",
        "tomatoes": "tomato",
        "potatoes": "potato",
        "cloves": "clove",
    }

    if name in irregulars:
        return irregulars[name]

    if name.endswith("ies") and len(name) > 3:
        return name[:-3] + "y"

    if name.endswith("s") and len(name) > 3 and not name.endswith("ss"):
        name = name[:-1]

    return name

def normalize_unit(unit: str) -> str:
    UNIT_CONVERSIONS = {
        "cup": "g",
        "cups": "g",
        "tbsp": "ml",
        "tablespoon": "ml",
        "tsp": "ml",
        "teaspoon": "ml",
        "clove": "pieces",
        "cloves": "pieces",
    }
    
    unit = unit.lower().strip()

    allowed = {"pieces", "ml", "l", "g", "kg"}

    if unit in allowed:
        return unit

    if unit in UNIT_CONVERSIONS:
        return UNIT_CONVERSIONS[unit]

    return "pieces"

def parse_ingredient_line(line: str) -> dict:
    """
    Parse ingredient strings like:
    - "2 egg"
    - "11.0 pieces of Eggs"
    - "1 piece egg"
    - "3 eggs"

    Returns:
    {"quantity": 2, "name": "egg"}
    """
    if not line or not isinstance(line, str):
        raise ValueError("Invalid ingredient format")

    line = line.strip().lower()

    match = re.match(
        r"^\s*(\d+(?:\.\d+)?)\s+"
        r"(?:(pieces?|piece|ml|l|g|kg|tablespoons?|tablespoon|tbsp|tsps?|tsp|teaspoons?|teaspoon|cups?|cup)\s+)?"
        r"(?:of\s+)?"
        r"(.+?)\s*$",
        line,
    )
    if not match:
        raise ValueError("Invalid ingredient format")

    raw_quantity = float(match.group(1))

    # Since Item.quantity is Integer in your DB, only allow whole-number decimals like 11.0
    if not raw_quantity.is_integer():
        raise ValueError("Ingredient quantity must be a whole number")

    quantity = int(raw_quantity)
    name = match.group(3).strip()

    # Remove common trailing measurement words that may still appear in the name
    for suffix in [
        " piece",
        " pieces",
        " clove",
        " cloves",
        " tablespoon",
        " tablespoons",
        " tbsp",
        " tsp",
        " teaspoon",
        " teaspoons",
        " cup",
        " cups",
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()

    name = normalize_ingredient_name(name)

    return {
        "quantity": quantity,
        "name": name,
    }


def find_matching_item(db, household_id: int, ingredient_name: str):
    """
    Find a matching household item using normalized name comparison.
    Handles case-insensitive matching and simple plural normalization.
    """
    items = (
        db.query(Item)
        .filter(Item.household_id == household_id)
        .all()
    )
    normalized_target = normalize_ingredient_name(ingredient_name)

    for item in items:
        if normalize_ingredient_name(item.name) == normalized_target:
            return item

    return None


def cook_recipe(db, household_id: int, recipe: dict):
    """
    Deduct ingredients from a household's fridge inventory
    and create usage logs.
    """
    ingredient_lines = recipe.get("ingredients", [])

    if any(i.strip() for i in recipe.get("missing_ingredients", [])):
        raise ValueError("Recipe cannot be cooked because some ingredients are missing.")

    if not ingredient_lines:
        raise ValueError("Recipe has no ingredients")

    parsed_ingredients = [parse_ingredient_line(line) for line in ingredient_lines]

    items_to_update = []

    # Validate everything first
    for ingredient in parsed_ingredients:
        item = find_matching_item(db, household_id, ingredient["name"])

        if not item:
            raise ValueError(f"Item not found: {ingredient['name']}")

        if item.quantity < ingredient["quantity"]:
            raise ValueError(f"Not enough {ingredient['name']}")

        items_to_update.append((item, ingredient["quantity"]))

    # Apply updates only after validation passes
    for item, qty in items_to_update:
        item.quantity -= qty

        log = ItemUsageLog(
            item_id=item.id,
            item_name=item.name,
            unit=item.unit.value if hasattr(item.unit, "value") else str(item.unit),
            household_id=item.household_id,
            quantity_consumed=qty,
        )
        db.add(log)

    db.commit()

    return {"success": True}