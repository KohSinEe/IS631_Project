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
    # Household setup: show invitation dialog only once per page load
    "household_setup_invitation_shown": False,
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


def reset_active_dialog() -> None:
    st.session_state.active_dialog = None


def reset_dashboard_filters() -> None:
    st.session_state.category_filter = "All"
    st.session_state.sort_by_expiry = True


def mark_inventory_dirty(rerun: bool = False) -> None:
    st.session_state.inventory_dirty = True
    if rerun:
        st.rerun()
