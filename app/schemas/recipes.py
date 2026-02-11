from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PantryItem(BaseModel):
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None

class Recipe(BaseModel):
    title: str
    time_minutes: int = Field(ge=1, le=600)
    ingredients: List[str]
    missing_ingredients: List[str] = []
    steps: List[str]
    reason: Optional[str] = None

class RecipeGenerateRequest(BaseModel):
    items: List[PantryItem]
    inventory_only: bool = True
    max_recipes: int = 3
    preferences: Optional[Dict[str, Any]] = None

class RecipeGenerateResponse(BaseModel):
    recipes: List[Recipe]
