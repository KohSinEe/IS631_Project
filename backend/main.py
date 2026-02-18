# backend/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import your database setup
from database import Base, engine, SessionLocal, get_db
from crud import add_item

# Create tables on startup
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(title="Fridge Buddy Inventory API")

# Allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # use your frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"]
)

# Pydantic model for inventory item
class InventoryItem(BaseModel):
    item_name: str
    quantity: float
    storage_type: str
    expiry_days: int

# Endpoint to add inventory items
@app.post("/add_item/")
async def add_inventory_item(item: InventoryItem, db: Session = Depends(get_db)):
    try:
        add_item(db, item.item_name, item.quantity, item.storage_type, item.expiry_days)
        return JSONResponse({"message": f"{item.item_name} added/updated successfully."})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
