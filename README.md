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
# 🥗 Food Management App

A smart household food management system that helps reduce waste, track inventory, and find recipes based on available ingredients.

## Testing

Unit tests run on every push and pull request via GitHub Actions.

| Where to see results | How |
|----------------------|-----|
| **GitHub Actions** | Repo → **Actions** tab → select the **Unit Tests** workflow run. Green ✓ = passed; red ✗ = failed. |
| **Pull requests** | Open a PR → checks appear at the bottom (e.g. "Unit Tests — Success" or "Failure"). |
| **README badge** | Add a status badge so visitors see pass/fail at a glance (see below). |
| **Coverage report** | After a run, open the run → **Artifacts** → download **coverage-html** → unzip and open `index.html` in a browser. |

### Status badge (optional)

Add this to your README (replace `YOUR_USERNAME` and `YOUR_REPO` with your GitHub org/repo):

```markdown
[![Unit Tests](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/unit_tests.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/unit_tests.yml)
```

### Run tests locally

```bash
make test
# or
uv run pytest --cov=app --cov-report=term -v
```

For a one-page summary of what’s covered: `uv run pytest --cov=app --cov-report=term-missing`.
