""" User allergen schema (valiation and response). """

from typing import List
from pydantic import BaseModel, field_validator

from app.models.user_allergen import VALID_ALLERGENS

class UserAllergenBase(BaseModel):
    """Base schema for user allergen data."""
    allergens: List[str] = []

    @field_validator("allergens", mode="before")
    @classmethod
    def validate_allergens(cls, v):
        if not isinstance(v, list):
            raise ValueError("Allergens must be a list of strings")
        invalid = [a for a in v if a not in VALID_ALLERGENS]
        if invalid:
            raise ValueError(f"Invalid allergens: {invalid}. Valid options are: {sorted(VALID_ALLERGENS)}")
        return v

class UserAllergenUpdate(UserAllergenBase):
    """Schema for updating user allergens (same as base)."""
    pass

class UserAllergenResponse(BaseModel):
    """Schema for user allergen response data."""
    user_id: int
    allergens: List[str]

    class Config:
        """Pydantic config."""
        from_attributes = True