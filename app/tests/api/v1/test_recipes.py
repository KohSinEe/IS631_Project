"""Tests for recipes API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch

from app.config import settings
from fastapi.testclient import TestClient


FAKE_RECIPE_RESPONSE = {
    "recipes": [
        {
            "title": "Scrambled Eggs",
            "time_minutes": 10,
            "ingredients": ["egg", "butter", "salt"],
            "missing_ingredients": [],
            "steps": ["Beat eggs", "Cook in pan", "Serve"],
            "reason": None,
        }
    ]
}


@patch("app.api.v1.endpoints.recipes.generate_recipes", new_callable=AsyncMock)
def test_recipes_generate_success(mock_generate: AsyncMock, client: TestClient) -> None:
    """POST /recipes/generate returns recipes when Ollama is available (mocked)."""
    mock_generate.return_value = FAKE_RECIPE_RESPONSE

    r = client.post(
        f"{settings.API_V1_STR}/recipes/generate",
        json={
            "items": [
                {"name": "egg", "quantity": 6, "unit": "pcs"},
                {"name": "butter", "quantity": 1, "unit": "tbsp"},
            ],
            "inventory_only": True,
            "max_recipes": 1,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "recipes" in data
    assert len(data["recipes"]) == 1
    assert data["recipes"][0]["title"] == "Scrambled Eggs"
    assert data["recipes"][0]["time_minutes"] == 10
    mock_generate.assert_called_once()


@patch("app.api.v1.endpoints.recipes.generate_recipes", new_callable=AsyncMock)
def test_recipes_generate_calls_with_params(mock_generate: AsyncMock, client: TestClient) -> None:
    """Generate is called with request params and defaults."""
    mock_generate.return_value = FAKE_RECIPE_RESPONSE

    client.post(
        f"{settings.API_V1_STR}/recipes/generate",
        json={
            "items": [{"name": "rice"}],
            "inventory_only": False,
            "max_recipes": 2,
            "preferences": {"time_minutes_max": 30},
        },
    )
    call_kwargs = mock_generate.call_args[1]
    assert call_kwargs["inventory_only"] is False
    assert call_kwargs["max_recipes"] == 2
    assert call_kwargs["preferences"] == {"time_minutes_max": 30}
    assert len(call_kwargs["pantry_items"]) == 1
    assert call_kwargs["pantry_items"][0]["name"] == "rice"


def test_recipes_generate_empty_items_validation(client: TestClient) -> None:
    """Empty items list is rejected by service with 400."""
    r = client.post(
        f"{settings.API_V1_STR}/recipes/generate",
        json={"items": [], "inventory_only": True, "max_recipes": 1},
    )
    assert r.status_code == 400
    assert "pantry" in r.json().get("detail", "").lower()


@patch("app.api.v1.endpoints.recipes.generate_recipes", new_callable=AsyncMock)
def test_recipes_generate_service_error(mock_generate: AsyncMock, client: TestClient) -> None:
    """When generate_recipes raises, API returns 500."""
    mock_generate.side_effect = ValueError("Ollama unavailable")

    r = client.post(
        f"{settings.API_V1_STR}/recipes/generate",
        json={"items": [{"name": "egg"}], "inventory_only": True, "max_recipes": 1},
    )
    assert r.status_code == 500
