'''
Request & response models (Pydantic)
'''

from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional, List

## CREATE + READ for account, do not need to include DELETE as nothing to validate
class AccountBase(BaseModel):
    account_email: EmailStr
    name: str

class AccountCreate(AccountBase):
    password: str
    confirm_password: str

class AccountRead(AccountBase):
    account_email: EmailStr

    class Config:
        from_attributes = True

## LOGIN
class LoginRequest(BaseModel):
    account_email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


## CREATE + READ for fridge
class FridgeBase(BaseModel):
    fridge_name: str

class FridgeCreate(FridgeBase):
    pass    # because creating a fridge require the same field as base fridge schema

class FridgeRead(FridgeBase):
    fridge_id: int

    class Config:
        from_attributes = True


## CREATE + READ for user link
class UserLinkBase(BaseModel):
    account_email: EmailStr
    fridge_id: int
    role: str

class UserLinkCreate(UserLinkBase):
    pass    # because creating a user link require the same field as base user link schema

class UserLinkRead(UserLinkBase):
    user_link_id: int

    class Config:
        from_attributes = True


## CREATE + READ + UPDATE for food item

from enum import Enum

class UnitEnum(str, Enum):  # to decide again
    kg = "kg"
    g = "g"
    ml = "ml"
    l = "l"
    pcs = "pcs"


class LocationEnum(str, Enum):  # to decide again
    fridge = "fridge"
    freezer = "freezer"
    pantry = "pantry"
    door = "door"


class CategoryEnum(str, Enum):  # to decide again
    dairy = "dairy"
    meat = "meat"
    vegetable = "vegetable"
    fruit = "fruit"
    beverage = "beverage"
    snack = "snack"
    other = "other"

class FoodItemBase(BaseModel):
    name: str
    quantity: Optional[float] = None   # if provided must be float, but can be empty
    units: Optional[UnitEnum] = None
    expiry_date: Optional[date] = None
    location: Optional[LocationEnum] = None
    category: Optional[CategoryEnum] = None

class FoodItemCreate(FoodItemBase):
    fridge_id: int
    user_link_id: int

class FoodItemRead(FoodItemBase):
    item_id: int
    fridge_id: int
    user_link_id: int

    class Config:
        from_attributes = True