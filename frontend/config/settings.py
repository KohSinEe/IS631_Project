import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
EXPIRY_ALERT_DAYS = int(os.getenv("EXPIRY_ALERT_DAYS", "5"))
USAGE_DEFAULT_DAYS = int(os.getenv("USAGE_DEFAULT_DAYS", "30"))

CATEGORY_OPTIONS = [
    "Dairy",
    "Meat",
    "Seafood",
    "Vegetables",
    "Fruits",
    "Beverages",
    "Condiments",
    "Leftovers",
    "Frozen",
    "Other",
]
UNIT_OPTIONS = ["pieces", "mL", "L", "g", "kg"]

CATEGORY_DEFAULT_EXPIRY_DAYS: dict[str, int] = {
    "Dairy": 14,
    "Meat": 3,
    "Seafood": 3,
    "Vegetables": 7,
    "Fruits": 7,
    "Beverages": 365,
    "Condiments": 180,
    "Leftovers": 3,
    "Frozen": 180,
    "Other": 30,
}

# optional Google Vision key for photo-based food recognition
VISION_API_KEY = os.getenv("VISION_API_KEY")

# make sure this matches models.VALID_ALLERGENS in app/models/user_allergen.py
ALLERGEN_OPTIONS = [
    "PEANUTS",
    "SHELLFISH",
    "MILK",
    "EGGS",
    "FISH",
    "TREE_NUTS",
    "WHEAT",
    "SOY",
    "SESAME",
]

ROLE_DISPLAY_NAMES = {
    "owner": "Owner",
    "co_owner": "Co-owner",
    "child": "Child",
}

INVITATION_STATUS_DISPLAY = {
    "pending": "Pending",
    "accepted": "Accepted",
    "declined": "Declined",
}
