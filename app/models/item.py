"""Item model for household inventory."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import date

from app.database import Base


class CategoryEnum(str, PyEnum):
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


class UnitEnum(str, PyEnum):
    """Unit of measurement enumeration."""
    PIECES = "pieces"
    ML = "mL"
    L = "L"
    G = "g"
    KG = "kg"


class Item(Base):
    """Item model - represents a food item in a household's inventory."""
    
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit = Column(Enum(UnitEnum), nullable=False, default=UnitEnum.PIECES)
    expiry_date = Column(String, nullable=False)  # Stored as ISO format string (YYYY-MM-DD)
    category = Column(Enum(CategoryEnum), nullable=False)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    household = relationship("Household", back_populates="items")
    
    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}', household_id={self.household_id})>"
