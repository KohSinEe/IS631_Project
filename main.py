"""
FridgeBuddy - A household food inventory management application
Helps households live more and waste less by simplifying food management
"""

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import date, datetime
from enum import Enum
import asyncpg
from contextlib import asynccontextmanager
import asyncio
import logging

import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fridgebuddy:fridgebuddy123@localhost:5432/fridgebuddy"
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Category(str, Enum):
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

class UserRole(str, Enum):
    OWNER = "Owner"
    CO_OWNER = "Co-Owner"
    CHILD = "Child"

class UnitType(str, Enum):
    PIECES = "pieces"
    ML = "mL"
    L = "L"
    G = "g"
    KG = "kg"

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    quantity: int = Field(..., ge=0, description="Quantity of the item")
    unit: UnitType = Field(default=UnitType.PIECES, description="Unit of measurement")
    expiry_date: date = Field(..., description="Expiry date of the item")
    category: Category = Field(..., description="Category of the item")
    
    @field_validator('expiry_date')
    @classmethod
    def validate_expiry_date(cls, v):
        if v < date.today():
            raise ValueError('Expiry date cannot be in the past')
        return v

class ItemCreate(ItemBase):
    """Schema for creating a new item - all fields mandatory"""
    pass

class ItemUpdate(BaseModel):
    """Schema for updating an item - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    quantity: Optional[int] = Field(None, ge=0)
    unit: Optional[UnitType] = None
    expiry_date: Optional[date] = None
    category: Optional[Category] = None
    
    @field_validator('expiry_date')
    @classmethod
    def validate_expiry_date(cls, v):
        if v is not None and v < date.today():
            raise ValueError('Expiry date cannot be in the past')
        return v

class ItemQuantityChange(BaseModel):
    """Schema for incrementing/decrementing quantity"""
    change: int = Field(..., description="Amount to change (positive to increase, negative to decrease)")

class ItemResponse(BaseModel):
    id: int
    name: str
    quantity: int
    unit: UnitType
    expiry_date: date
    category: Category
    created_at: datetime
    updated_at: datetime

class DeleteConfirmation(BaseModel):
    """Schema for delete confirmation"""
    confirm: bool = Field(..., description="Must be true to confirm deletion")

class MessageResponse(BaseModel):
    message: str
    item_id: Optional[int] = None

pool: Optional[asyncpg.Pool] = None

async def get_db():
    """Get a database connection from the pool"""
    async with pool.acquire() as connection:
        yield connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for database connection pool"""
    global pool

    max_retries = 5
    retry_delay = 2  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Attempting to connect to database (attempt {attempt}/{max_retries})...")
            pool = await asyncpg.create_pool(DATABASE_URL, timeout=5)
            logging.info("Successfully connected to database")
            break
        except (ConnectionRefusedError, OSError, asyncpg.PostgresError) as e:
            if attempt == max_retries:
                logging.error(f"Failed to connect to database after {max_retries} attempts")
                raise
            logging.warning(f"Database connection failed: {e}. Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff

    yield
    await pool.close()

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="FridgeBuddy API",
    description="Help households live more and waste less by simplifying food management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API Endpoints
# ============================================================================

# --- User Story 1: Add New Items ---
# As a Owner or Co-Owner, I want to add new items with quantity, expiry date 
# and category so that I can track what is in my fridge.

@app.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Inventory Management"],
    summary="Add a new item to inventory"
)
async def create_item(
    item: ItemCreate,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Add a new item to the fridge inventory.
    
    **Requirements:**
    - All fields (name, quantity, expiry_date, category) are mandatory
    - Quantity must be non-negative
    - Expiry date must not be in the past
    - Category must be from the predefined list
    
    **Acceptance Criteria:**
    - AC1: User should be able to move on with item appearing in list when all fields are populated correctly
    - AC2: User should NOT be able to continue when there are empty fields
    - AC3: Invalid field values should be flagged to user
    """
    query = """
        INSERT INTO items (name, quantity, unit, expiry_date, category)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, name, quantity, unit, expiry_date, category, created_at, updated_at
    """
    row = await db.fetchrow(
        query,
        item.name,
        item.quantity,
        item.unit.value,
        item.expiry_date,
        item.category.value
    )
    return ItemResponse(**dict(row))


# --- User Story 2: Edit Item Details ---
# As a Owner or Co-Owner, I want to edit an item's existing details 
# so that I can correct erroneous entries.

@app.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    tags=["Inventory Management"],
    summary="Edit an existing item"
)
async def update_item(
    item_id: int,
    item: ItemUpdate,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Edit an existing item's details.
    
    **Requirements:**
    - All fields should be made editable
    - Quick +/- buttons for fast increase/decrease of item quantities
    
    **Acceptance Criteria:**
    - AC1: All fields are editable
    - AC2: Upon completion, user should be able to see updated values in their list
    """
    # First check if item exists
    existing = await db.fetchrow("SELECT * FROM items WHERE id = $1", item_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    # Build dynamic update query
    updates = []
    values = []
    param_count = 1
    
    if item.name is not None:
        updates.append(f"name = ${param_count}")
        values.append(item.name)
        param_count += 1
    if item.quantity is not None:
        updates.append(f"quantity = ${param_count}")
        values.append(item.quantity)
        param_count += 1
    if item.unit is not None:
        updates.append(f"unit = ${param_count}")
        values.append(item.unit.value)
        param_count += 1
    if item.expiry_date is not None:
        updates.append(f"expiry_date = ${param_count}")
        values.append(item.expiry_date)
        param_count += 1
    if item.category is not None:
        updates.append(f"category = ${param_count}")
        values.append(item.category.value)
        param_count += 1
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )
    
    updates.append("updated_at = NOW()")
    values.append(item_id)
    
    query = f"""
        UPDATE items 
        SET {', '.join(updates)}
        WHERE id = ${param_count}
        RETURNING id, name, quantity, unit, expiry_date, category, created_at, updated_at
    """
    
    row = await db.fetchrow(query, *values)
    return ItemResponse(**dict(row))


# --- User Story 3: Increase/Decrease Quantity ---
# As a Owner or Co-Owner, I want to increase or decrease existing item's quantity 
# so that I can update the stock after a grocery run.

@app.patch(
    "/items/{item_id}/quantity",
    response_model=Union[ItemResponse, MessageResponse],
    tags=["Inventory Management"],
    summary="Adjust item quantity"
)
async def adjust_quantity(
    item_id: int,
    change: ItemQuantityChange,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Increase or decrease an item's quantity.

    **Requirements:**
    - Quick +/- buttons for fast increase/decrease of item quantities
    - Buttons can be pressed multiple times for multiple increase/decrease
    - Item should be automatically deleted when quantity reaches 0

    **Acceptance Criteria:**
    - AC1: Upon completion, user should be able to see updated values in their list
    - AC2: When value is zero, item should be removed from list
    - AC3: User should be flagged when values turn negative

    **Returns:**
    - ItemResponse: Updated item details (if quantity > 0)
    - MessageResponse: Deletion confirmation (if quantity = 0)
    """
    # Get current item
    existing = await db.fetchrow("SELECT * FROM items WHERE id = $1", item_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    new_quantity = existing['quantity'] + change.change

    # AC3: Flag negative values
    if new_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quantity cannot be negative. Current: {existing['quantity']}, Change: {change.change}"
        )

    # AC2: Auto-delete when quantity reaches 0
    if new_quantity == 0:
        await db.execute("DELETE FROM items WHERE id = $1", item_id)
        return MessageResponse(
            message=f"Item '{existing['name']}' removed from inventory (quantity reached 0)",
            item_id=item_id
        )

    # Update quantity
    query = """
        UPDATE items
        SET quantity = $1, updated_at = NOW()
        WHERE id = $2
        RETURNING id, name, quantity, unit, expiry_date, category, created_at, updated_at
    """
    row = await db.fetchrow(query, new_quantity, item_id)
    return ItemResponse(**dict(row))


# --- User Story 4: View All Items ---
# As a Owner or Co-Owner or Child, I want to view all items with so that
# I know what is in my fridge.

@app.get(
    "/items",
    response_model=List[ItemResponse],
    tags=["Inventory Management"],
    summary="View all items in inventory"
)
async def get_all_items(
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Get all items in the fridge inventory.

    **Requirements:**
    - Items should show quantity, expiry date and category
    - Items should appear as a list

    **Acceptance Criteria:**
    - AC1: Items should appear as a list with quantity, expiry and category
    """
    query = """
        SELECT id, name, quantity, unit, expiry_date, category, created_at, updated_at
        FROM items
        ORDER BY expiry_date ASC, name ASC
    """
    rows = await db.fetch(query)
    return [ItemResponse(**dict(row)) for row in rows]


# --- User Story 6: Search Items ---
# As a Owner or Co-Owner or Child, I want to search for items by typing
# an item's name.

@app.get(
    "/items/search",
    response_model=List[ItemResponse],
    tags=["Inventory Management"],
    summary="Search items by name"
)
async def search_items(
    q: str = Query(..., min_length=1, description="Search query"),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Search for items by name.

    **Requirements:**
    - Search should be case-insensitive
    - Search should support partial matches

    **Acceptance Criteria:**
    - AC1: Relevant items should pop up with partial search (e.g. apple appears when user types "app")
    - AC2: Search should still work regardless of capitalisation
    - AC3: Flag should appear if there are no items found
    """
    query = """
        SELECT id, name, quantity, unit, expiry_date, category, created_at, updated_at
        FROM items
        WHERE LOWER(name) LIKE LOWER($1)
        ORDER BY expiry_date ASC, name ASC
    """
    search_pattern = f"%{q}%"
    rows = await db.fetch(query, search_pattern)

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No items found matching '{q}'"
        )

    return [ItemResponse(**dict(row)) for row in rows]


# --- Expiry Tracking & Alerts ---
# As a Owner or Co-Owner, I want to see a visual indicator for items
# expiring soon so that I can prioritize using them before they spoil.

@app.get(
    "/items/expiring-soon",
    response_model=List[ItemResponse],
    tags=["Expiry Tracking & Alerts"],
    summary="Get items expiring within specified days"
)
async def get_expiring_items(
    days: int = Query(default=5, ge=1, le=30, description="Number of days to check (default: 5)"),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Get items that are expiring within the specified number of days.

    **Requirements:**
    - Visual indicator should appear for items expiring in <= 5 days
    - Visual indicator should appear as a red badge to catch attention

    **Acceptance Criteria:**
    - AC1: Items not expiring in <= 5 days should NOT have visual indicator
    - AC2: Items expiring in <= 5 days should have visual indicator
    - AC3: Expiry status should update automatically without manual update
    """
    query = """
        SELECT id, name, quantity, unit, expiry_date, category, created_at, updated_at
        FROM items
        WHERE expiry_date <= CURRENT_DATE + make_interval(days => $1)
        ORDER BY expiry_date ASC
    """
    rows = await db.fetch(query, days)
    return [ItemResponse(**dict(row)) for row in rows]


# --- User Story 5: Filter by Category ---
# As a Owner or Co-Owner or Child, I want to filter my view according to
# the defined categories to find things faster.

@app.get(
    "/items/category/{category}",
    response_model=List[ItemResponse],
    tags=["Inventory Management"],
    summary="Filter items by category"
)
async def get_items_by_category(
    category: Category,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Filter items by category.

    **Requirements:**
    - Items within category should be arranged with expiry item at the top

    **Acceptance Criteria:**
    - AC1: Only items belonging to selected category should appear
    - AC2: Users should be able to clear filter (use GET /items endpoint)
    """
    query = """
        SELECT id, name, quantity, unit, expiry_date, category, created_at, updated_at
        FROM items
        WHERE category = $1
        ORDER BY expiry_date ASC, name ASC
    """
    rows = await db.fetch(query, category.value)
    return [ItemResponse(**dict(row)) for row in rows]


# --- User Story 7: Delete Item ---
# As a Owner or Co-Owner, I want to delete item regardless of existing quantity.

@app.delete(
    "/items/{item_id}",
    response_model=MessageResponse,
    tags=["Inventory Management"],
    summary="Delete an item"
)
async def delete_item(
    item_id: int,
    confirmation: DeleteConfirmation,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Delete an item from inventory.
    
    **Requirements:**
    - Delete should require a second step confirmation
    
    **Acceptance Criteria:**
    - AC1: When user presses delete, a confirmation prompt should appear
    - AC2: Upon user's confirmation, item should no longer be seen on the list
    """
    # AC1: Require confirmation
    if not confirmation.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion not confirmed. Set 'confirm' to true to delete."
        )
    
    # Check if item exists
    existing = await db.fetchrow("SELECT name FROM items WHERE id = $1", item_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    # Delete the item
    await db.execute("DELETE FROM items WHERE id = $1", item_id)
    
    return MessageResponse(
        message=f"Item '{existing['name']}' has been deleted successfully",
        item_id=item_id
    )


# --- Additional Utility Endpoints ---

@app.get(
    "/categories",
    response_model=List[str],
    tags=["Utilities"],
    summary="Get all available categories"
)
async def get_categories():
    """Get list of all available categories for dropdown selection"""
    return [category.value for category in Category]


@app.get(
    "/units",
    response_model=List[str],
    tags=["Utilities"],
    summary="Get all available units"
)
async def get_units():
    """Get list of all available units for dropdown selection"""
    return [unit.value for unit in UnitType]


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)