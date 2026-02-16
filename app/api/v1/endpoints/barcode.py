"""Barcode API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.models import Item
from app.models.item import CategoryEnum, UnitEnum
from app.schemas.item import ItemResponse, Category
from app.services.barcode import barcode_service, BarcodeProduct
from app.core.security import get_current_user

router = APIRouter()


class BarcodeItemCreate(ItemResponse):
    """Schema for item created from barcode."""
    barcode: Optional[str] = None


@router.get("/lookup/{barcode}")
async def lookup_barcode(
    barcode: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Look up product information by barcode.
    
    Returns product details if found, otherwise 404.
    """
    product = await barcode_service.lookup_product(barcode)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No product found for barcode: {barcode}"
        )
    
    return {
        "barcode": product.barcode,
        "name": product.name,
        "category": product.category or "Other",
        "brand": product.brand,
        "image_url": product.image_url,
        "suggested_expiry_days": barcode_service.estimate_expiry_date(product)
    }


@router.post("/add-from-barcode")
async def add_item_from_barcode(
    barcode: str = Query(..., description="Product barcode"),
    quantity: int = Query(1, ge=1, description="Quantity to add"),
    expiry_date: Optional[date] = Query(None, description="Expiry date (auto-estimated if not provided)"),
    category_override: Optional[CategoryEnum] = Query(None, description="Override category if auto-mapping is wrong"),
    household_id: int = Query(None, description="Household ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Scan a barcode and automatically add the product to inventory.
    
    Flow:
    1. Look up product by barcode
    2. Create item in inventory with recognized product info
    3. Return created item
    
    Query parameters:
    - **barcode**: Product barcode/EAN
    - **quantity**: How many to add (default: 1)
    - **expiry_date**: Expiry date (optional - auto-estimated if not provided)
    - **household_id**: Target household ID
    """
    if not household_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="household_id is required"
        )
    
    # Verify user has access to this household
    if current_user.household_id != household_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this household"
        )
    
    # Look up product by barcode
    product = await barcode_service.lookup_product(barcode)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product not found for barcode: {barcode}"
        )
    
    # Determine expiry date
    if not expiry_date:
        expiry_date_str = barcode_service.estimate_expiry_date(product)
        expiry_date = date.fromisoformat(expiry_date_str)
    
    # Map product category to app categories
    category = category_override or map_category(product.category)
    
    # Create item in database
    new_item = Item(
        name=product.name,
        quantity=quantity,
        unit=UnitEnum.PIECES,
        expiry_date=expiry_date.isoformat(),
        category=category,
        household_id=household_id
    )
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return {
        "id": new_item.id,
        "barcode": barcode,
        "name": new_item.name,
        "quantity": new_item.quantity,
        "unit": new_item.unit,
        "expiry_date": new_item.expiry_date,
        "category": new_item.category,
        "message": f"✓ {product.name} added to inventory"
    }


def map_category(open_food_category: Optional[str]) -> CategoryEnum:
    """Map Open Food Facts category to our CategoryEnum."""
    if not open_food_category:
        return CategoryEnum.OTHER

    category_lower = open_food_category.lower()

    category_mapping = {
        "dairy": CategoryEnum.DAIRY,
        "meat": CategoryEnum.MEAT,
        "seafood": CategoryEnum.SEAFOOD,
        "fish": CategoryEnum.SEAFOOD,
        "vegetable": CategoryEnum.VEGETABLES,
        "veg": CategoryEnum.VEGETABLES,
        "fruit": CategoryEnum.FRUITS,
        "beverage": CategoryEnum.BEVERAGES,
        "drink": CategoryEnum.BEVERAGES,
        "condiment": CategoryEnum.CONDIMENTS,
        "sauce": CategoryEnum.CONDIMENTS,
        "frozen": CategoryEnum.FROZEN,
        "leftover": CategoryEnum.LEFTOVERS,
    }

    for key, value in category_mapping.items():
        if key in category_lower:
            return value

    return CategoryEnum.OTHER
