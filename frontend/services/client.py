from typing import Optional, Any
import requests
import streamlit as st
from config.settings import API_BASE_URL


class APIError(Exception):
    """Raised when the backend returns an error response."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_api_client() -> requests.Session:
    """Return a per-user API client that stores cookies between calls."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = requests.Session()
    return st.session_state.api_client


def api_request(method: str, path: str, **kwargs) -> Optional[Any]:
    """Wrap requests to the FastAPI backend with unified error handling."""
    session = get_api_client()
    url = f"{API_BASE_URL}{path}"
    timeout = kwargs.pop("timeout", 15)

    try:
        response = session.request(method, url, timeout=timeout, **kwargs)
    except requests.RequestException as exc:
        raise APIError("Network error while reaching the API") from exc

    if response.status_code >= 400:
        detail: Any = None
        try:
            payload = response.json()
            detail = payload.get("detail") if isinstance(payload, dict) else payload
        except ValueError:
            detail = response.text
        message = detail or "Request failed"
        raise APIError(str(message), response.status_code)

    if response.status_code == 204 or not response.content:
        return None

    try:
        return response.json()
    except ValueError:
        return response.text
