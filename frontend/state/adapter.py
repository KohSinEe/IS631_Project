from typing import Any, Dict, Optional

import streamlit as st


def get_household_id() -> Optional[int]:
    return st.session_state.get("household_id")


def set_household_id(household_id: Optional[int]) -> None:
    st.session_state.household_id = household_id


def get_user() -> Optional[Dict[str, Any]]:
    user = st.session_state.get("user")
    return user if isinstance(user, dict) else None


def set_user(user: Optional[Dict[str, Any]]) -> None:
    st.session_state.user = user


def set_inventory_dirty(value: bool = True) -> None:
    st.session_state.inventory_dirty = value
