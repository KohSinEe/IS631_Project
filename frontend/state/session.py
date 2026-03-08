import streamlit as st

SESSION_DEFAULTS = {
    "is_authenticated": False,
    "user": None,
    "household_id": None,
    "tokens": None,
    "inventory": [],
    "inventory_dirty": True,
    "category_filter": "All",
    "sort_by_expiry": True,
    "detected_barcode": None,
    "detected_product_info": None,
    "expiry_toasts_shown": False,
    # Form keys
    "login_email": "",
    "login_password": "",
    "register_email": "",
    "register_password": "",
    "register_name": "",
    "register_household": "",
}


def init_session_state() -> None:
    """Ensure Streamlit session state contains expected keys."""
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session() -> None:
    """Reset authentication-related state."""
    for key, value in SESSION_DEFAULTS.items():
        st.session_state[key] = value
