from typing import Optional, Any, Dict
import streamlit as st
from services.client import APIError, api_request, get_api_client
from state.session import reset_session


def register_user(
    email: str, password: str, name: Optional[str], household_name: Optional[str]
) -> Dict[str, Any]:
    payload = {
        "email": email,
        "password": password,
        "name": name or None,
        "household_name": household_name or None,
    }
    return api_request("post", "/auth/register", json=payload)  # type: ignore[return-value]


def login_user(email: str, password: str) -> None:
    data = {"username": email, "password": password}
    api_request("post", "/auth/login", data=data)
    profile = api_request("get", "/users/me")

    if not isinstance(profile, dict):
        raise APIError("Unexpected profile payload")

    st.session_state.is_authenticated = True
    st.session_state.user = profile
    st.session_state.household_id = profile.get("household_id")
    st.session_state.inventory_dirty = True


def logout_user() -> None:
    try:
        api_request("post", "/auth/logout")
    except APIError:
        pass

    client = get_api_client()
    client.cookies.clear()
    reset_session()


def get_current_user() -> None:
    profile = api_request("get", "/users/me")

    if profile:
        st.session_state.is_authenticated = True
        st.session_state.user = profile
        st.session_state.household_id = profile.get("household_id")
        st.session_state.inventory_dirty = True


def update_user(name: str) -> None:
    data = {"name": name}
    try:
        response = api_request("put", "/users/me", json=data)
        st.session_state.user = response

    except APIError as e:
        st.error(f"Failed to update profile: {e}")
        raise
