"""Items API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.database import get_db
from app.models import Item
from app.models.usage_log import ItemUsageLog
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse, ItemQuantityChange, Category
from app.core.security import get_current_user
from app.utils.expiry import get_default_expiry_for_category

router = APIRouter()


def get_item_or_404(item_id: int, household_id: int, db: Session) -> Item:
    """Helper function to get an item or raise 404."""
    item = db.query(Item).filter(Item.id == item_id, Item.household_id == household_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.get("", response_model=List[ItemResponse])
def list_items(
    household_id: int = Query(None, description="Household ID"),
    category: Category = Query(None, description="Filter by category"),
    sort_by_expiry: bool = Query(False, description="Sort by expiry date (ascending)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    List all items in a household.

    - **household_id**: The household to list items for
    - **category**: Optional category filter
    - **sort_by_expiry**: Sort results by expiry date
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

    query = db.query(Item).filter(Item.household_id == household_id)

    if category:
        query = query.filter(Item.category == category)

    items = query.all()

    if sort_by_expiry:
        items = sorted(items, key=lambda x: x.expiry_date)

    return items


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item: ItemCreate,
    household_id: int = Query(None, description="Household ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create a new item in a household's inventory.

    - **name**: Item name
    - **quantity**: Quantity of the item
    - **unit**: Unit of measurement
    - **expiry_date**: Expiry date (YYYY-MM-DD)
    - **category**: Category of the item
    - **household_id**: The household to add the item to
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

    db_item = Item(
        name=item.name,
        quantity=item.quantity,
        unit=item.unit,
        expiry_date=(
            item.expiry_date or get_default_expiry_for_category(item.category.value)
        ).isoformat(),
        category=item.category,
        household_id=household_id,
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    household_id: int = Query(None, description="Household ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a specific item by ID."""
    if not household_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="household_id is required"
        )

    # Verify user has access to this household
    if current_user.household_id != household_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this household"
        )

    item = get_item_or_404(item_id, household_id, db)
    return item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item_update: ItemUpdate,
    household_id: int = Query(None, description="Household ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an item."""
    if not household_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="household_id is required"
        )

    # Verify user has access to this household
    if current_user.household_id != household_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this household"
        )

    db_item = get_item_or_404(item_id, household_id, db)

    # Update only provided fields
    update_data = item_update.model_dump(exclude_unset=True)

    if "expiry_date" in update_data and update_data["expiry_date"] is not None:
        update_data["expiry_date"] = update_data["expiry_date"].isoformat()

    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    household_id: int = Query(None, description="Household ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an item."""
    if not household_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="household_id is required"
        )

    # Verify user has access to this household
    if current_user.household_id != household_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this household"
        )

    db_item = get_item_or_404(item_id, household_id, db)
    db.delete(db_item)
    db.commit()


@router.patch("/{item_id}/quantity", response_model=ItemResponse)
def adjust_item_quantity(
    item_id: int,
    quantity_change: ItemQuantityChange,
    household_id: int = Query(None, description="Household ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Adjust an item's quantity by adding or removing a specific amount.

    - **change**: Positive number to increase, negative to decrease quantity
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

    db_item = get_item_or_404(item_id, household_id, db)

    new_quantity = db_item.quantity + quantity_change.change
    if new_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity cannot be negative"
        )

    db_item.quantity = new_quantity
    db.add(db_item)

    if quantity_change.change < 0:
        log = ItemUsageLog(
            item_id=db_item.id,
            item_name=db_item.name,
            unit=db_item.unit.value,
            household_id=db_item.household_id,
            quantity_consumed=abs(quantity_change.change),
        )
        db.add(log)

    db.commit()
    db.refresh(db_item)

    return db_item
