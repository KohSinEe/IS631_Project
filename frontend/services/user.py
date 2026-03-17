from typing import Any, Dict, Optional

import streamlit as st
from services.client import APIError, api_request, get_api_client
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


def confirm_signup(email: str, confirmation_code: str) -> None:
    payload = {"email": email, "confirmation_code": confirmation_code}
    api_request("post", "/auth/confirm-signup", json=payload)


def resend_signup_code(email: str) -> None:
    payload = {"email": email}
    api_request("post", "/auth/resend-confirmation", json=payload)


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


def change_password(current_password: str, new_password: str) -> None:
    payload = {
        "current_password": current_password,
        "new_password": new_password,
    }
    api_request("put", "/users/me/password", json=payload)


def reset_password(email: str, new_password: str) -> None:
    payload = {"email": email, "new_password": new_password}
    try:
        response = api_request("post", "/users/reset-password", json=payload)
        print(f"Password reset response: {response}")
        if not response or (
            isinstance(response, dict) and response.get("message") != "Password reset successful"
        ):
            st.error("Password reset failed. Please check your email and try again.")
        else:
            st.success("Password reset successful. Please sign in.")
    except APIError as e:
        st.error(f"Failed to reset password: {e}")
        print(f"APIError: {e}")
    except APIError as e:
        st.error(f"Failed to reset password: {e}")
        raise


def request_password_reset(email: str, new_password: Optional[str] = None) -> None:
    payload = {"email": email}
    try:
        api_request("post", "/users/reset-password/request", json=payload)
    except APIError as err:
        # Local auth mode has no verification-code step.
        if err.status_code == 400:
            if new_password:
                reset_password(email, new_password)
                return
            raise APIError(
                "Local auth mode does not use verification codes. Enter a new password and click Reset Password.",
                err.status_code,
            )
        raise


def confirm_password_reset(email: str, confirmation_code: str, new_password: str) -> None:
    payload = {
        "email": email,
        "confirmation_code": confirmation_code,
        "new_password": new_password,
    }

    try:
        api_request("post", "/users/reset-password/confirm", json=payload)
    except APIError as err:
        # Backward compatibility for local-auth mode.
        if err.status_code == 400:
            reset_password(email, new_password)
            return
        raise


def delete_household(household_id: int) -> None:
    """Delete the current user's fridge (household) and all its contents. Owner only."""
    api_request("delete", f"/households/{household_id}")
    st.session_state.household_id = None
    st.session_state.inventory = []
    st.session_state.inventory_dirty = True
    if st.session_state.user and isinstance(st.session_state.user, dict):
        st.session_state.user["household_id"] = None
        st.session_state.user["is_household_owner"] = False


def create_household(name: str) -> Dict[str, Any]:
    result = api_request("post", "/households", json={"name": name})
    if isinstance(result, dict):
        st.session_state.household_id = result.get("id")
        if st.session_state.user:
            st.session_state.user["household_id"] = result.get("id")
            st.session_state.user["is_household_owner"] = True
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
