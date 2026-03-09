'''
allows users to "cook" AI-generated recipes
for auto-deduct ingredients when cooking AI-generated recipe
'''

import re

from app.models.item import Item
from app.models.usage_log import ItemUsageLog


def parse_ingredient_line(line: str) -> dict:
    """
    Parse a simple ingredient string like '2 egg'
    into {'quantity': 2, 'name': 'egg'}.
    """
    if not line or not isinstance(line, str):
        raise ValueError("Invalid ingredient format")

    match = re.match(r"^\s*(\d+)\s+(.+?)\s*$", line)
    if not match:
        raise ValueError("Invalid ingredient format")

    quantity = int(match.group(1))
    name = match.group(2).strip().lower()

    return {
        "quantity": quantity,
        "name": name,
    }


def cook_recipe(db, household_id: int, recipe: dict):
    """
    Deduct ingredients from a household's fridge inventory
    and create usage logs.
    """
    ingredient_lines = recipe.get("ingredients", [])
    if not ingredient_lines:
        raise ValueError("Recipe has no ingredients")

    parsed_ingredients = [parse_ingredient_line(line) for line in ingredient_lines]

    items_to_update = []

    # Validate everything first
    for ingredient in parsed_ingredients:
        item = (
            db.query(Item)
            .filter(
                Item.household_id == household_id,
                Item.name.ilike(ingredient["name"])
            )
            .first()
        )

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