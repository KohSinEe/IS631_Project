from sqlalchemy import Column, Integer, String, Float
from database import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, unique=True, index=True)
    quantity = Column(Float)
    storage_type = Column(String)
    expiry_days = Column(Integer)
