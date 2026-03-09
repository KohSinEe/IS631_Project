from services.client import APIError, api_request


def generate_recipe(items, max_recipes, inventory_only, preferences, use_household_allergens=True):
    data = {
        "items": items,
        "max_recipes": max_recipes,
        "inventory_only": inventory_only,
        "preferences": preferences,
        "use_household_allergens": use_household_allergens,
    }

    try:
        recipes = api_request("post", "/recipes", json=data, timeout=120)
        return recipes
    except APIError:
        raise


def cook_recipe(recipe):
    try:
        result = api_request("post", "/recipes/cook", json=recipe, timeout=30)
        return result
    except APIError:
        raise
