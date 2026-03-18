from typing import Any, Dict, Optional

import streamlit as st
from services.client import APIError, api_request, get_api_client
from state.adapter import get_user, set_household_id, set_inventory_dirty, set_user
from state.session import reset_session


def register_user(
    email: str,
    password: str,
    password_confirm: str,
    name: Optional[str],
    household_name: Optional[str],
) -> Dict[str, Any]:
    payload = {
        "email": email,
        "password": password,
        "password_confirm": password_confirm,
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
    set_user(profile)
    set_household_id(profile.get("household_id"))
    set_inventory_dirty(True)


def logout_user() -> None:
    try:
        api_request("post", "/auth/logout")
    except Exception:
        # Always clear local state even if server request fails (e.g. network, 401)
        pass

    try:
        client = get_api_client()
        client.cookies.clear()
    except Exception:
        pass
    reset_session()


def get_current_user() -> None:
    profile = api_request("get", "/users/me")

    if isinstance(profile, dict):
        st.session_state.is_authenticated = True
        set_user(profile)
        set_household_id(profile.get("household_id"))
        set_inventory_dirty(True)


def update_user(name: str) -> None:
    data = {"name": name}
    try:
        response = api_request("put", "/users/me", json=data)
        st.session_state.user = response

    except APIError as e:
        st.error(f"Failed to update profile: {e}")
        raise


def reset_password(email: str, new_password: str) -> None:
    payload = {"email": email, "new_password": new_password}
    try:
        response = api_request("post", "/users/reset-password", json=payload)
        print(f"Password reset response: {response}")
        if not response or (isinstance(response, dict) and response.get("message") != "Password reset successful"):
            st.error("Password reset failed. Please check your email and try again.")
        else:
            st.success("Password reset successful. Please sign in.")
    except APIError as e:
        st.error(f"Failed to reset password: {e}")
        print(f"APIError: {e}")
    except APIError as e:
        st.error(f"Failed to reset password: {e}")
        raise


def delete_household(household_id: int) -> None:
    """Delete the current user's fridge (household) and all its contents. Owner only."""
    api_request("delete", f"/households/{household_id}")
    set_household_id(None)
    st.session_state.inventory = []
    set_inventory_dirty(True)
    user = get_user()
    if user:
        user["household_id"] = None
        user["is_household_owner"] = False
        set_user(user)


def create_household(name: str) -> Dict[str, Any]:
    result = api_request("post", "/households", json={"name": name})
    if isinstance(result, dict):
        set_household_id(result.get("id"))
        user = get_user()
        if user:
            user["household_id"] = result.get("id")
            user["is_household_owner"] = True
            set_user(user)
    return result


# Allergens related:


def get_my_allergens() -> list:
    result = api_request("get", "/users/me/allergens")
    return result.get("allergens", []) if isinstance(result, dict) else []


def add_allergens(allergens: list) -> list:
    result = api_request("post", "/users/me/allergens", json={"allergens": allergens})
    return result.get("allergens", []) if isinstance(result, dict) else []


def delete_allergens(allergens: list) -> list:
    result = api_request("delete", "/users/me/allergens", json={"allergens": allergens})
    return result.get("allergens", []) if isinstance(result, dict) else []
