from datetime import date, timedelta
from typing import Any, Dict, List

import streamlit as st
from config.settings import CATEGORY_DEFAULT_EXPIRY_DAYS, CATEGORY_OPTIONS, UNIT_OPTIONS
from services.client import APIError
from services.inventory import (
    adjust_inventory_quantity,
    create_inventory_item,
    delete_inventory_item,
)


def handle_add_item() -> None:
    category = st.selectbox("Category", options=CATEGORY_OPTIONS, key="create_category")

    days = CATEGORY_DEFAULT_EXPIRY_DAYS.get(category, 30)

    with st.form("add_item_form"):
        st.subheader("Add to pantry")
        name = st.text_input("Item", key="create_name")
        quantity = st.number_input("Quantity", min_value=0, step=1, value=1, key="create_quantity")
        unit = st.selectbox("Unit", options=UNIT_OPTIONS, key="create_unit")
        expiry = st.date_input(
            "Expiry Date",
            value=None,
            min_value=date.today(),
            format="DD/MM/YYYY",
            key="create_expiry",
            help=f"Leave blank to auto-estimate for {category} ({days} days).",
        )
        submitted = st.form_submit_button("Save item")

    if submitted:
        if not name:
            st.error("Item name is required")
            return
        if expiry is None:
            expiry = date.today() + timedelta(days=days)
        data = {
            "name": name,
            "quantity": int(quantity),
            "unit": unit,
            "expiry_date": expiry.isoformat(),
            "category": category,
        }
        try:
            create_inventory_item(data)
            st.success("Item added")
            st.session_state.inventory_dirty = True
            st.rerun()
        except APIError as err:
            st.error(err.message)


def handle_quick_actions(items: List[Dict[str, Any]]) -> None:
    st.subheader("Quick actions")
    if not items:
        st.info("Inventory is empty")
        return

    option_map = {f"#{item['id']} · {item['name']} ({item['quantity']} {item['unit']})": item["id"] for item in items}
    labels = list(option_map.keys())

    with st.form("quantity_form"):
        selected = st.selectbox("Select item", labels, key="adjust_target")
        change = st.number_input("Adjust quantity", min_value=-100, max_value=100, value=1, step=1, key="adjust_delta")
        submitted = st.form_submit_button("Apply change")
    if submitted:
        try:
            adjust_inventory_quantity(option_map[selected], int(change))
            st.success("Quantity updated")
            st.session_state.inventory_dirty = True
            st.rerun()
        except APIError as err:
            st.error(err.message)

    with st.form("delete_form"):
        target = st.selectbox("Remove item", labels, key="delete_target")
        confirm = st.checkbox("Yes, delete this item", key="delete_confirm")
        submitted = st.form_submit_button("Delete item")
    if submitted:
        if not confirm:
            st.warning("Please confirm deletion")
        else:
            try:
                delete_inventory_item(option_map[target])
                st.success("Item deleted")
                st.session_state.inventory_dirty = True
                st.rerun()
            except APIError as err:
                st.error(err.message)
