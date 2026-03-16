"""Schemas for item-related requests and responses."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
from enum import Enum


class Category(str, Enum):
    """Item category enumeration."""

    DAIRY = "Dairy"
    MEAT = "Meat"
    SEAFOOD = "Seafood"
    VEGETABLES = "Vegetables"
    FRUITS = "Fruits"
    BEVERAGES = "Beverages"
    CONDIMENTS = "Condiments"
    LEFTOVERS = "Leftovers"
    FROZEN = "Frozen"
    OTHER = "Other"


class UnitType(str, Enum):
    """Unit of measurement enumeration."""

    PIECES = "pieces"
    ML = "mL"
    L = "L"
    G = "g"
    KG = "kg"


class ItemBase(BaseModel):
    """Base schema for item data."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    quantity: int = Field(..., ge=0, description="Quantity of the item")
    unit: UnitType = Field(default=UnitType.PIECES, description="Unit of measurement")
    expiry_date: date = Field(..., description="Expiry date of the item")
    category: Category = Field(..., description="Category of the item")

    @field_validator("expiry_date")
    @classmethod
    def validate_expiry_date(cls, v):
        if v is not None and v < date.today():
            raise ValueError("Expiry date cannot be in the past")
        return v


class ItemCreate(ItemBase):
    """Schema for creating a new item. expiry_date is optional and auto-filled if blank."""

    expiry_date: Optional[date] = Field(
        None, description="Expiry date; auto-estimated from category if not provided"
    )


class ItemUpdate(BaseModel):
    """Schema for updating an item (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    quantity: Optional[int] = Field(None, ge=0)
    unit: Optional[UnitType] = None
    expiry_date: Optional[date] = None
    category: Optional[Category] = None

    @field_validator("expiry_date")
    @classmethod
    def validate_expiry_date(cls, v):
        if v is not None and v < date.today():
            raise ValueError("Expiry date cannot be in the past")
        return v


class ItemQuantityChange(BaseModel):
    """Schema for incrementing/decrementing item quantity."""

    change: int = Field(
        ..., description="Amount to change (positive to increase, negative to decrease)"
    )


class ItemResponse(BaseModel):
    """Schema for item response data."""

    id: int
    name: str
    quantity: int
    unit: UnitType
    expiry_date: date
    category: Category
    household_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True
