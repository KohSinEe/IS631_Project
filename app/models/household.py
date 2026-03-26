"""Household model."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class Household(Base):
    """Household model - represents a family or group of users (fridge)."""

    __tablename__ = "households"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship(
        "User",
        back_populates="household",
        primaryjoin="Household.id == User.household_id",
    )
    items = relationship("Item", back_populates="household", cascade="all, delete-orphan")
    owner = relationship("User", foreign_keys=[owner_id])

    def __repr__(self):
        return f"<Household(id={self.id}, name='{self.name}')>"
