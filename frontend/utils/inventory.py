import streamlit as st
from services.inventory import fetch_inventory
from typing import Any, Dict, List
from datetime import date, datetime, timedelta

from config.settings import EXPIRY_ALERT_DAYS


def parse_expiry(raw_value: str) -> date:
    """Convert ISO strings from the API to date objects."""
    dt_value = datetime.fromisoformat(raw_value)
    return dt_value.date()


def ensure_inventory_loaded() -> None:
    if not st.session_state.is_authenticated or not st.session_state.household_id:
        st.session_state.inventory = []
        st.session_state.inventory_dirty = False
        return

    if st.session_state.inventory_dirty:
        st.session_state.inventory = fetch_inventory()
        st.session_state.inventory_dirty = False


def filter_inventory(items: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    if category == "All":
        return items
    return [item for item in items if item.get("category") == category]


def summarize_inventory(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    today = date.today()
    soon_cutoff = today + timedelta(days=EXPIRY_ALERT_DAYS)

    expiring = []
    overdue = 0
    for item in items:
        expiry_raw = item.get("expiry_date")
        if not expiry_raw:
            continue
        expiry = parse_expiry(expiry_raw)
        if expiry < today:
            overdue += 1
        elif expiry <= soon_cutoff:
            expiring.append(
                {
                    "name": item.get("name"),
                    "expiry": expiry,
                    "quantity": item.get("quantity"),
                    "unit": item.get("unit"),
                }
            )

    return {
        "total": len(items),
        "expiring": len(expiring),
        "overdue": overdue,
        "expiring_items": expiring,
    }


# helpers for expiry suggestions ------------------------------------------------
# these are arbitrary defaults used by the photo scan UI; more sophisticated
# logic could be added later (e.g. based on category stored on the backend).
CATEGORY_EXPIRY_DAYS = {
    "dairy": 7,
    "fruit": 14,
    "vegetable": 21,
    "spice": 180,
    "grain": 180,
    "meat": 7,
}

# some common foods we might encounter in photo labels
FOOD_TO_CATEGORY = {
    "milk": "dairy",
    "cheese": "dairy",
    "yogurt": "dairy",
    "ginger": "vegetable",
    "potato": "vegetable",
    "banana": "fruit",
    "orange": "fruit",
    "onion": "vegetable",
    "noodles": "grain",
    "chicken": "meat",
    "beef": "meat",
}


def suggest_expiry_for_name(name: str, purchase: date) -> date:
    """Return a default expiry date based on the food name."""
    if not name:
        return purchase
    n = name.lower().strip()
    cat = FOOD_TO_CATEGORY.get(n)
    days = CATEGORY_EXPIRY_DAYS.get(cat, 7)
    return purchase + timedelta(days=days)
