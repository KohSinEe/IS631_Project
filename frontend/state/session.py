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
    # Public view: do not auto-open sign-in/sign-up dialogs after logout
    "show_sign_in_form": False,
    "show_sign_up_form": False,
    "show_pw_reset": False,
    # Dashboard dialogs: reset on logout so profile doesn't open on next login
    "show_household_setup": False,
    "show_profile_dialog": False,
    "show_logout_dialog": False,
    "show_invite_dialog": False,
    "show_delete_fridge_dialog": False,
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
