"""Unit tests for recipe_gen service (prompt building, normalization, JSON extraction)."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch

from app.services.recipe_gen import (
    _normalize_items,
    _build_prompt,
    _extract_json,
    generate_recipes,
)

# ----- _normalize_items -----


def test_normalize_items_name_only() -> None:
    """Items with only name are normalized to the name."""
    out = _normalize_items([{"name": "egg"}, {"name": "rice"}])
    assert out == ["egg", "rice"]


def test_normalize_items_with_quantity_and_unit() -> None:
    """Quantity and unit are formatted into the string."""
    out = _normalize_items(
        [
            {"name": "egg", "quantity": 6, "unit": "pcs"},
            {"name": "milk", "quantity": 1, "unit": "cup"},
        ]
    )
    assert out == ["6 pcs egg", "1 cup milk"]


def test_normalize_items_quantity_no_unit() -> None:
    """Quantity without unit omits unit."""
    out = _normalize_items([{"name": "egg", "quantity": 2, "unit": ""}])
    assert out == ["2 egg"]


def test_normalize_items_skips_empty_name() -> None:
    """Items with empty or missing name are skipped."""
    out = _normalize_items(
        [
            {"name": "egg"},
            {"name": ""},
            {"name": "   "},
            {"quantity": 1, "unit": "cup"},
        ]
    )
    assert out == ["egg"]


def test_normalize_items_empty_list() -> None:
    """Empty input returns empty list."""
    assert _normalize_items([]) == []


# ----- _build_prompt -----


def test_build_prompt_includes_pantry_and_rules() -> None:
    """Prompt contains pantry lines and max_recipes."""
    prompt = _build_prompt(
        ["egg", "rice"],
        inventory_only=True,
        max_recipes=2,
        preferences=None,
    )
    assert "egg" in prompt
    assert "rice" in prompt
    assert "2 recipes" in prompt or "Provide 2 recipes" in prompt
    assert "missing_ingredients" in prompt
    assert "JSON" in prompt


def test_build_prompt_inventory_only_rules() -> None:
    """When inventory_only=True, prompt says no missing ingredients."""
    prompt = _build_prompt(["egg"], inventory_only=True, max_recipes=1)
    assert "missing_ingredients" in prompt
    assert "empty" in prompt.lower() or "entirely from" in prompt.lower()


def test_build_prompt_with_preferences() -> None:
    """Preferences are serialized into the prompt."""
    prompt = _build_prompt(
        ["egg"], inventory_only=True, max_recipes=1, preferences={"time_minutes_max": 30}
    )
    assert "time_minutes_max" in prompt
    assert "30" in prompt


# ----- _extract_json -----


def test_extract_json_simple() -> None:
    """Extracts a JSON object from plain text."""
    text = 'Here is the result:\n{"recipes": [{"title": "Test"}]}'
    out = _extract_json(text)
    assert out == {"recipes": [{"title": "Test"}]}


def test_extract_json_with_markdown_backticks() -> None:
    """Extracts JSON even when surrounded by markdown."""
    text = '```json\n{"recipes": []}\n```'
    out = _extract_json(text)
    assert out == {"recipes": []}


def test_extract_json_no_object_raises() -> None:
    """Raises ValueError when no JSON object is found."""
    with pytest.raises(ValueError, match="No JSON object"):
        _extract_json("No json here at all")


def test_extract_json_invalid_json_raises() -> None:
    """Invalid JSON inside the match raises."""
    with pytest.raises(json.JSONDecodeError):
        _extract_json('{"recipes": [invalid]}')


# ----- generate_recipes (mocked HTTP) -----


@patch("app.services.recipe_gen.OllamaClient")
def test_generate_recipes_success(mock_client_class) -> None:
    """generate_recipes returns validated recipe dict when Ollama returns valid JSON."""
    raw_json = json.dumps(
        {
            "recipes": [
                {
                    "title": "Test Recipe",
                    "time_minutes": 15,
                    "ingredients": ["a", "b"],
                    "missing_ingredients": [],
                    "steps": ["Step 1", "Step 2"],
                }
            ]
        }
    )
    mock_instance = AsyncMock()
    mock_instance.chat = AsyncMock(return_value=raw_json)
    mock_client_class.return_value = mock_instance

    result = asyncio.run(
        generate_recipes(
            [{"name": "egg", "quantity": 2}],
            model="test-model",
            ollama_host="http://fake:11434",
            inventory_only=True,
            max_recipes=1,
            use_chat_endpoint=True,
        )
    )
    assert "recipes" in result
    assert len(result["recipes"]) == 1
    assert result["recipes"][0]["title"] == "Test Recipe"
    mock_instance.chat.assert_called_once()


def test_generate_recipes_empty_pantry_raises() -> None:
    """Empty pantry items raise ValueError."""
    with pytest.raises(ValueError, match="No pantry items"):
        asyncio.run(generate_recipes([], ollama_host="http://fake:11434"))
