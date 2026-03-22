from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field, ValidationError


class Recipe(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    time_minutes: int = Field(ge=1, le=600)
    ingredients: List[str] = Field(min_length=1)
    missing_ingredients: List[str] = Field(default_factory=list)
    steps: List[str] = Field(min_length=1)
    reason: Optional[str] = None


class RecipeResponse(BaseModel):
    recipes: List[Recipe] = Field(min_length=1, max_length=8)


def _normalize_items(items: List[Dict[str, Any]]) -> List[str]:
    norm: List[str] = []
    for it in items:
        name = str(it.get("name", "")).strip().lower()
        if not name:
            continue

        if name.endswith("s") and len(name) > 3 and not name.endswith("ss"):
            name = name[:-1]

        qty = it.get("quantity", None)
        unit = str(it.get("unit", "")).strip().lower()

        if isinstance(qty, float) and qty.is_integer():
            qty = int(qty)

        if qty is None or qty == "":
            norm.append(name)
        else:
            norm.append(f"{qty} {unit} {name}".strip() if unit else f"{qty} {name}")
    return norm


def _build_prompt(
    pantry_lines: List[str],
    *,
    inventory_only: bool,
    max_recipes: int,
    preferences: Optional[Dict[str, Any]] = None,
    allergens: Optional[List[str]] = None,
) -> str:

    ALLOWED_UNITS = ["pieces", "ml", "l", "g", "kg"]

    prefs_text = (
        f"\nUser preferences (optional): {json.dumps(preferences)}\n" if preferences else ""
    )

    allergen_text = f"\nAllergens to avoid: {', '.join(allergens)}\n" if allergens else ""

    rules = [
        "Return ONLY valid JSON. No markdown or explanation.",
        f"Provide {max_recipes} recipes.",
        "Use only whole-number quantities in 'ingredients'.",
        "Format ingredients as '<whole number> <ingredient name>' or '<whole number> <unit> <ingredient name>'.",
        f"Allowed units are ONLY: {', '.join(ALLOWED_UNITS)}.",
        "Do not use vague terms like 'to taste' or fractions.",
        "Ingredient names should match pantry items closely.",
    ]
    if inventory_only:
        rules += [
            "Use ONLY the provided pantry items.",
            "Missing_ingredients must be an empty list.",
        ]
    else:
        rules += [
            "Minimize missing_ingredients.",
            "Only include essential missing items.",
        ]
    if allergens:
        rules += [
            f"Do NOT include allergens: {', '.join(allergens)} in any part of the recipe.",
            f"- If a recipe would normally use {', '.join(allergens)}, find a safe substitute or skip that recipe entirely.",
            "This is a food safety requirement. Ignoring allergens could harm people.",
        ]

    schema_hint = {
        "recipes": [
            {
                "title": "string",
                "time_minutes": 30,
                "ingredients": ["string", "..."],
                "missing_ingredients": ["string", "..."],
                "steps": ["string", "..."],
                "reason": "string (optional)",
            }
        ]
    }
    return (
        "You are a cooking assistant.\n"
        f"Pantry: {pantry_lines}\n"
        f"{allergen_text}"
        f"{prefs_text}\n"
        "Output format:\n"
        f"{schema_hint}\n\n"
        "Rules:\n- " + "\n- ".join(rules)
    )


def _extract_json(text: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output.")
    return json.loads(match.group(0))


class OllamaClient:
    def __init__(self, host: str, api_key: Optional[str] = None, timeout_seconds: int = 300):
        self.host = host.rstrip("/")
        self.api_base = f"{self.host}/api"
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.timeout_seconds = 300

    async def chat(self, model: str, messages: List[Dict[str, str]]) -> str:
        url = f"{self.api_base}/chat"
        payload = {"model": model, "messages": messages, "stream": False}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                r = await client.post(url, json=payload, headers=self.headers)
                r.raise_for_status()
                data = r.json()
        except httpx.ConnectError as exc:
            raise ValueError(f"Cannot connect to recipe model service at {self.host}.") from exc
        except httpx.TimeoutException as exc:
            raise ValueError(
                f"Timed out while contacting recipe model service at {self.host} after {self.timeout_seconds} seconds."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ValueError(
                f"Recipe model service returned HTTP {exc.response.status_code}."
            ) from exc
        return data.get("message", {}).get("content", "")

    async def generate(self, model: str, prompt: str) -> str:
        url = f"{self.api_base}/generate"
        payload = {"model": model, "prompt": prompt, "stream": False}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                r = await client.post(url, json=payload, headers=self.headers)
                r.raise_for_status()
                data = r.json()
        except httpx.ConnectError as exc:
            raise ValueError(f"Cannot connect to recipe model service at {self.host}.") from exc
        except httpx.TimeoutException as exc:
            raise ValueError(
                f"Timed out while contacting recipe model service at {self.host} after {self.timeout_seconds} seconds."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ValueError(
                f"Recipe model service returned HTTP {exc.response.status_code}."
            ) from exc
        return data.get("response", "")


async def generate_recipes(
    pantry_items: List[Dict[str, Any]],
    *,
    model: str = "llama3.2:3b",
    ollama_host: Optional[str] = None,
    inventory_only: bool = True,
    max_recipes: int = 3,
    preferences: Optional[Dict[str, Any]] = None,
    use_chat_endpoint: bool = True,
    allergens: Optional[List[str]] = None,
) -> Dict[str, Any]:
    pantry_lines = _normalize_items(pantry_items)
    if not pantry_lines:
        raise ValueError("No pantry items provided.")

    if ollama_host is None:
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    api_key = os.getenv("OLLAMA_API_KEY")
    timeout_seconds = 300

    prompt = _build_prompt(
        pantry_lines,
        inventory_only=inventory_only,
        max_recipes=max_recipes,
        preferences=preferences,
        allergens=allergens,
    )

    client = OllamaClient(ollama_host, api_key=api_key, timeout_seconds=timeout_seconds)

    if use_chat_endpoint:
        raw = await client.chat(
            model=model,
            messages=[
                {"role": "system", "content": "Return JSON only. Follow the schema exactly."},
                {"role": "user", "content": prompt},
            ],
        )
    else:
        raw = await client.generate(model=model, prompt=prompt)

    parsed = _extract_json(raw)
    try:
        validated = RecipeResponse.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError("Recipe model returned invalid response format.") from exc
    return validated.model_dump()


async def _smoke_test(model: str, ollama_host: str) -> None:
    sample_items = [
        {"name": "egg", "quantity": 6, "unit": "pcs"},
        {"name": "rice", "quantity": 2, "unit": "cups"},
        {"name": "soy sauce", "quantity": 1, "unit": "tbsp"},
        {"name": "garlic", "quantity": 3, "unit": "cloves"},
    ]
    result = await generate_recipes(
        sample_items,
        model=model,
        ollama_host=ollama_host,
        inventory_only=False,
        max_recipes=3,
        preferences={"time_minutes_max": 30},
        use_chat_endpoint=True,
    )
    print(json.dumps(result, indent=2))


def main():
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "llama3.2:3b"))
    parser.add_argument("--ollama-host", default=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    args = parser.parse_args()

    if args.smoke_test:
        import asyncio

        try:
            asyncio.run(_smoke_test(args.model, args.ollama_host))
        except ValidationError as ve:
            print("Model output did not match schema:")
            print(ve)
            raise
    else:
        print("Nothing to do. Use --smoke-test.")


if __name__ == "__main__":
    main()
