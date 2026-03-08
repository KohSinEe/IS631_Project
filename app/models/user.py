"""User model."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import HouseholdRoleEnum


class User(Base):
    """User model - represents a user account."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign keys
    household_id = Column(Integer, ForeignKey("households.id"), nullable=True)
    household_role = Column(Enum(HouseholdRoleEnum), nullable=True)  # CO_OWNER or CHILD; Owner implied by household.owner_id
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    household = relationship(
        "Household",
        back_populates="users",
        primaryjoin="User.household_id == Household.id",
    )

    @property
    def is_household_owner(self) -> bool:
        """True if this user is the owner of their current household (fridge)."""
        return (
            self.household is not None
            and self.household.owner_id is not None
            and self.household.owner_id == self.id
        )

    allergens = relationship("UserAllergen", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"