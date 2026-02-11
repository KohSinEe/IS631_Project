# recipegen

`recipegen` is a small module for generating recipe suggestions from a list of pantry items. It accepts pantry item data and returns JSON-compatible recipe output following a simple recipe schema.

Purpose:
- Provide an async `generate_recipes` entrypoint that consumes pantry items and produces validated recipe data for use in a larger pantry/meal-planning app.

Status:
- Work-in-progress. Implementation may be under `recipegen` (script or package) in this repository; the module is intended to be imported and used from an async context (e.g., FastAPI route).

Quick notes:
- Input: list of pantry item dicts (each with at least a `name`, optional `quantity` and `unit`).
- Output: dict matching a `recipes` list of recipe objects (title, time, ingredients, steps, etc.).
- Dependencies are managed in `requirements.txt`.
