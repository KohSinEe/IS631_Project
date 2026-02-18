from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from database import create_inventory_table, add_item

app = FastAPI(title="Fridge Buddy Inventory API")

# Allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # specify frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"]
)

# Create table on startup
create_inventory_table()

# Pydantic model for a single inventory item
class InventoryItem(BaseModel):
    item_name: str
    quantity: float
    storage_type: str
    expiry_days: int

@app.post("/add_item/")
async def add_inventory_item(item: InventoryItem):
    try:
        add_item(item.item_name, item.quantity, item.storage_type, item.expiry_days)
        return JSONResponse({"message": f"{item.item_name} added/updated successfully."})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
