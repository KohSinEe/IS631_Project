"""Barcode API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import Item
from app.models.item import CategoryEnum, UnitEnum
from app.schemas.item import ItemResponse, Category
from app.services.barcode import barcode_service, BarcodeProduct
from app.core.security import get_current_user

router = APIRouter()


class BarcodeProductResponse(BaseModel):
    """Product information returned from barcode lookup."""

    barcode: str
    name: str
    category: str
    brand: Optional[str] = None
    image_url: Optional[str] = None
    suggested_expiry_days: str = Field(..., description="Auto-estimated expiry date (ISO format)")


class BarcodeItemResponse(ItemResponse):
    """Item created from barcode scan."""

    barcode: str = Field(..., description="Original barcode scanned")


@router.get("/lookup/{barcode}", response_model=BarcodeProductResponse)
async def lookup_barcode(
    barcode: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)
) -> BarcodeProductResponse:
    """
    Look up product information by barcode.

    Returns product details if found, otherwise 404.
    """
    product = await barcode_service.lookup_product(barcode)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No product found for barcode: {barcode}"
        )

    return BarcodeProductResponse(
        barcode=product.barcode,
        name=product.name,
        category=product.category or "Other",
        brand=product.brand,
        image_url=product.image_url,
        suggested_expiry_days=barcode_service.estimate_expiry_date(product),
    )


@router.post(
    "/add-from-barcode", status_code=status.HTTP_201_CREATED, response_model=BarcodeItemResponse
)
async def add_item_from_barcode(
    barcode: str = Query(..., description="Product barcode"),
    quantity: int = Query(1, ge=1, description="Quantity to add"),
    expiry_date: Optional[date] = Query(
        None, description="Expiry date (auto-estimated if not provided)"
    ),
    category_override: Optional[CategoryEnum] = Query(
        None, description="Override category if auto-mapping is wrong"
    ),
    household_id: int = Query(None, description="Household ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> BarcodeItemResponse:
    """
    Scan a barcode and automatically add the product to inventory.

    Flow:
    1. Look up product by barcode
    2. Create item in inventory with recognized product info
    3. Return created item with 201 Created status

    Query parameters:
    - **barcode**: Product barcode/EAN
    - **quantity**: How many to add (default: 1)
    - **expiry_date**: Expiry date (optional - auto-estimated if not provided)
    - **category_override**: Override auto-detected category if needed
    - **household_id**: Target household ID (required)
    """
    if not household_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="household_id is required"
        )

    # Verify user has access to this household
    if current_user.household_id != household_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this household"
        )

    # Look up product by barcode
    product = await barcode_service.lookup_product(barcode)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product not found for barcode: {barcode}",
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
        household_id=household_id,
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return BarcodeItemResponse.model_validate({**new_item.__dict__, "barcode": barcode})


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
