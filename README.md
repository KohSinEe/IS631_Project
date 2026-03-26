# 🥗 FridgeBuddy

A smart household food management system that helps reduce waste, track inventory, and find recipes based on available ingredients.

Stop wasting. Start managing.

![Python](https://img.shields.io/badge/python-3.11-blue)
![UV](https://img.shields.io/badge/uv-latest-blueviolet)
![FastAPI](https://img.shields.io/badge/FastAPI-0.129.0-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.54.0-orange)

![UnitTest](https://github.com/KohSinEe/IS631_Project/actions/workflows/unit_tests.yml/badge.svg)

## Quick Start
1. Install dependencies
```bash
make install
```
2. Setup database and environment
```bash
make setup
```
3. Initialise the backend server
```bash
make run
```
4. Initialise the frontend interface
```bash
make st
```

## Prerequisites
- Python 3.11.*
- UV Package Manager
- Ollama

## API Endpoints
List of available API endpoints can be found at http://localhost:8000/docs

## Testing

Unit tests run on every push and pull request via GitHub Actions.

| Where to see results | How |
|----------------------|-----|
| **GitHub Actions** | Repo → **Actions** tab → select the **Unit Tests** workflow run. Green ✓ = passed; red ✗ = failed. |
| **Pull requests** | Open a PR → checks appear at the bottom (e.g. "Unit Tests — Success" or "Failure"). |
| **README badge** | Add a status badge so visitors see pass/fail at a glance (see below). |
| **Coverage report** | After a run, open the run → **Artifacts** → download **coverage-html** → unzip and open `index.html` in a browser. |

### Run tests locally

```bash
make test
```

For a one-page summary of what’s covered: `uv run pytest --cov=app --cov-report=term-missing`.

## Recipe Generator

`recipe` endpoint available for generating recipe suggestions from a list of pantry items. It accepts a JSON list of pantry items and returns JSON-compatible recipe outputs. Recipe generation is done using the `llama3.2:3b` model provisioned through Ollama.

### Quick notes
- Input: list of pantry item dicts (each with at least a `name`, optional `quantity` and `unit`).
- Output: dict matching a `recipes` list of recipe objects (title, time, ingredients, steps, etc.).

Sample request input if testing through swagger ui/terminal:
```json
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
## Recipe Cooking & Inventory Auto-Deduction

FridgeBuddy allows users to cook AI-generated recipes and automatically update household inventory.

When a recipe is cooked, the system:

- Parses the ingredient list from the generated recipe
- Normalizes ingredient names for matching with fridge items
- Validates that sufficient quantities exist in the inventory
- Deducts the used quantities from the household fridge
- Records ingredient usage in the `item_usage_logs` table

This ensures that the household inventory remains accurate after recipes are prepared.

### Example

Before cooking:

```text
Eggs: 6 pieces
Butter: 100 g
```

Recipe ingredients:

```text
4 pieces egg
30 g butter
```

After cooking:

```text
Eggs: 2 pieces
Butter: 70 g
```

Ingredient usage is also logged for tracking consumption.

Deployment