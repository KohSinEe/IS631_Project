"""Household schemas."""

from pydantic import BaseModel


class HouseholdCreate(BaseModel):
    name: str


class HouseholdResponse(BaseModel):
    id: int
    name: str
    owner_id: int

    model_config = {"from_attributes": True}
