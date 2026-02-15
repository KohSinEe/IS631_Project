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
        name = str(it.get("name", "")).strip()
        if not name:
            continue
        qty = it.get("quantity", None)
        unit = str(it.get("unit", "")).strip()
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
) -> str:
    prefs_text = (
        f"\nUser preferences (optional): {json.dumps(preferences)}\n" if preferences else ""
    )

    rules = [
        "- Return ONLY valid JSON. No markdown. No backticks. No commentary.",
        "- Output must match the schema shown.",
        f"- Provide {max_recipes} recipes.",
        "- Use pantry items as much as possible.",
    ]
    if inventory_only:
        rules.append(
            "- Do NOT include any missing ingredients. missing_ingredients must be an empty list."
        )
        rules.append("- If a recipe would require missing ingredients, do not output it.")
    else:
        rules.append(
            "- If an ingredient is not available in pantry items, list it in missing_ingredients."
        )

    schema = {
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
        "You are a helpful cooking assistant.\n"
        "Given the following pantry items, generate practical home-cooking recipes.\n"
        f"Pantry items: {pantry_lines}\n"
        f"{prefs_text}\n"
        "JSON schema (example shape):\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        "Rules:\n" + "\n".join(rules) + "\n\nReturn JSON only."
    )


def _extract_json(text: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output.")
    return json.loads(match.group(0))


class OllamaClient:
    def __init__(self, host: str, api_key: Optional[str] = None):
        self.host = host.rstrip("/")
        self.api_base = f"{self.host}/api"
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async def chat(self, model: str, messages: List[Dict[str, str]]) -> str:
        url = f"{self.api_base}/chat"
        payload = {"model": model, "messages": messages, "stream": False}
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, json=payload, headers=self.headers)
            r.raise_for_status()
            data = r.json()
        return data.get("message", {}).get("content", "")

    async def generate(self, model: str, prompt: str) -> str:
        url = f"{self.api_base}/generate"
        payload = {"model": model, "prompt": prompt, "stream": False}
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, json=payload, headers=self.headers)
            r.raise_for_status()
            data = r.json()
        return data.get("response", "")


async def generate_recipes(
    pantry_items: List[Dict[str, Any]],
    *,
    model: str = "mistral-large-3:675b-cloud",
    ollama_host: Optional[str] = None,
    inventory_only: bool = True,
    max_recipes: int = 3,
    preferences: Optional[Dict[str, Any]] = None,
    use_chat_endpoint: bool = True,
) -> Dict[str, Any]:
    pantry_lines = _normalize_items(pantry_items)
    if not pantry_lines:
        raise ValueError("No pantry items provided.")

    if ollama_host is None:
        ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    print("OLLAMA_HOST:", ollama_host)
    api_key = os.getenv("OLLAMA_API_KEY")

    prompt = _build_prompt(
        pantry_lines,
        inventory_only=inventory_only,
        max_recipes=max_recipes,
        preferences=preferences,
    )

    client = OllamaClient(ollama_host, api_key=api_key)

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
    validated = RecipeResponse.model_validate(parsed)
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
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "mistral-large-3"))
    parser.add_argument("--ollama-host", default=os.getenv("OLLAMA_HOST", "http://ollama:11434"))
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
