import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
EXPIRY_ALERT_DAYS = int(os.getenv("EXPIRY_ALERT_DAYS", "5"))

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
