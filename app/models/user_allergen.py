"""User allergen model. """

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

VALID_ALLERGENS = {
    "PEANUTS",
    "SHELLFISH",
    "MILK",
    "EGGS",
    "FISH",
    "TREE_NUTS",
    "WHEAT",
    "SOY",
    "SESAME",
}

class UserAllergen(Base):
    """ Stores allergens for a user. One row per allergen. User may have multiple allergens. """
    
    __tablename__ = "user_allergens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    allergen = Column(String(150), nullable=False)
    
    user = relationship("User", back_populates="allergens")

    def __repr__(self):
        return f"<UserAllergen(user_id={self.user_id}, allergen='{self.allergen}')>"
