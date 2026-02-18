from sqlalchemy.orm import Session
from models import Inventory

def add_item(db: Session, item_name: str, quantity: float, storage_type: str, expiry_days: int):
    existing_item = db.query(Inventory).filter(Inventory.item_name == item_name).first()
    if existing_item:
        existing_item.quantity = quantity
        existing_item.storage_type = storage_type
        existing_item.expiry_days = expiry_days
    else:
        new_item = Inventory(
            item_name=item_name,
            quantity=quantity,
            storage_type=storage_type,
            expiry_days=expiry_days
        )
        db.add(new_item)
    db.commit()
