
from pydantic import BaseModel
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Date, DECIMAL, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class Account(Base):
    __tablename__ = 'accounts'

    account_email = Column(String(255), primary_key=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)

    user_links = relationship(
        "UserLink", 
        back_populates="account"
        # cascade="all, delete" # do we need this
    )

class Fridge(Base):
    __tablename__ = "fridges"

    fridge_id = Column(Integer, primary_key=True, autoincrement=True)
    fridge_name = Column(String(255), nullable=False)

    user_links = relationship(
        "UserLink", 
        back_populates="fridge"
        # cascade="all, delete" # do we need this
    )
    
    food_items = relationship(
        "FoodItem", 
        back_populates="fridge"
        # cascade="all, delete" # do we need this
    )

class UserLink(Base):
    __tablename__ = "user_links"

    user_link_id = Column(Integer, primary_key=True, autoincrement=True)
    account_email = Column(
        Integer,
        ForeignKey("accounts.account_email", ondelete="CASCADE"),
        nullable=False
    )
    fridge_id = Column(
        Integer,
        ForeignKey("fridges.fridge_id", ondelete="CASCADE"),
        nullable=False
    )
    role = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("account_email", "fridge_id", name="uq_user_fridge"), # no same user and role to same fridge
    )

    account = relationship("Account", back_populates="user_links")
    fridge = relationship("Fridge", back_populates="user_links")
    food_items = relationship(
        "FoodItem",
        back_populates="user_link",
        cascade="all, delete"
    )

class FoodItem(Base):
    __tablename__ = "food_items"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    fridge_id = Column(
        Integer,
        ForeignKey("fridges.fridge_id", ondelete="CASCADE"),
        nullable=False
    )
    user_link_id = Column(
        Integer,
        ForeignKey("user_links.user_link_id", ondelete="CASCADE"),
        nullable=False
    )

    name = Column(String(255), nullable=False)
    quantity = Column(DECIMAL(10, 2))
    units = Column(String(50))
    expiry_date = Column(Date)
    location = Column(String(100))
    category = Column(String(100))

    fridge = relationship("Fridge", back_populates="food_items")
    user_link = relationship("UserLink", back_populates="food_items")