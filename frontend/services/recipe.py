from services.client import APIError, api_request


def generate_recipe(items, max_recipes, inventory_only, preferences):
    data = {
        "items": items,
        "max_recipes": max_recipes,
        "inventory_only": inventory_only,
        "preferences": preferences,
    }

    try:
        recipes = api_request("post", "/recipes/generate", json=data)
        return recipes
    except APIError:
        raise
