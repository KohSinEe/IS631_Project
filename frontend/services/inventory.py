from typing import Any, Dict, List
import streamlit as st
from services.client import api_request


def fetch_inventory() -> List[Dict[str, Any]]:
    household_id = st.session_state.household_id
    if not household_id:
        return []
    params = {"household_id": household_id}
    result = api_request("get", "/items", params=params)
    return result if isinstance(result, list) else []


def create_inventory_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
    params = {"household_id": st.session_state.household_id}
    return api_request("post", "/items", params=params, json=item_data)


def adjust_inventory_quantity(item_id: int, change: int) -> Dict[str, Any]:
    params = {"household_id": st.session_state.household_id}
    payload = {"change": change}
    return api_request("patch", f"/items/{item_id}/quantity", params=params, json=payload)


def update_inventory_item(item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
    params = {"household_id": st.session_state.household_id}
    return api_request("put", f"/items/{item_id}", params=params, json=item_data)


def delete_inventory_item(item_id: int) -> None:
    params = {"household_id": st.session_state.household_id}
    api_request("delete", f"/items/{item_id}", params=params)
