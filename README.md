# recipe generator

`recipe generator` is a small module for generating recipe suggestions from a list of pantry items. It accepts pantry item data and returns JSON-compatible recipe output following a simple recipe schema. currently a stand-alone module and not integrated with the rest of the app.

Purpose:
- Provide an async `generate_recipes` entrypoint that consumes pantry items and produces validated recipe data for use in a larger pantry/meal-planning app.

Status:
- Work-in-progress. Module is intended to be imported and used from an async context (e.g., FastAPI route).

Quick notes:
- Input: list of pantry item dicts (each with at least a `name`, optional `quantity` and `unit`).
- Output: dict matching a `recipes` list of recipe objects (title, time, ingredients, steps, etc.).
- Dependencies are managed in `requirements.txt`.

Sample request input if testing through swagger ui/terminal:
```
{
  "items": [
    {"name": "egg", "quantity": 6, "unit": "pcs"},
    {"name": "rice", "quantity": 2, "unit": "cups"},
    {"name": "soy sauce", "quantity": 1, "unit": "tbsp"}
  ],
  "inventory_only": false,
  "max_recipes": 2
}
```