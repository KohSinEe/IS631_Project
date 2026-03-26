from datetime import date, timedelta

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

_DEFAULT_DAYS = 30


def get_default_expiry_for_category(category: str) -> date:
    """Return the estimated expiry date for the given category."""
    days = CATEGORY_DEFAULT_EXPIRY_DAYS.get(category, _DEFAULT_DAYS)

    return date.today() + timedelta(days=days)
