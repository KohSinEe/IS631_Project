"""Mass Stocktake page — inline editing of all inventory items."""

import streamlit as st
import pandas as pd
from datetime import date
from typing import Any, Dict, List

from config.settings import CATEGORY_OPTIONS
from services.client import APIError
from services.inventory import update_inventory_item
from utils.inventory import ensure_inventory_loaded


def render_stocktake() -> None:
    col_back, col_title = st.columns([1, 8])
    with col_back:
        st.markdown("<div style='margin-top: 0.4rem'></div>", unsafe_allow_html=True)
        if st.button("← Back"):
            st.session_state.page = "dashboard"
            st.rerun()
    with col_title:
        st.markdown("## Mass Stocktake")
        st.caption(
            "Edit quantities, categories, and expiry dates directly in the table below. "
            "Press **Save Changes** when done."
        )

    household_id = st.session_state.household_id
    if not household_id:
        st.info("You do not belong to a household yet.")
        return

    ensure_inventory_loaded()
    items: List[Dict[str, Any]] = st.session_state.inventory

    if not items:
        st.info("No items in inventory. Add some items first.")
        return

    st.divider()

    # Build display DataFrame — IDs tracked separately to avoid exposing them
    item_ids = [item["id"] for item in items]
    display_df = pd.DataFrame(
        [
            {
                "Name": item["name"],
                "Quantity": item["quantity"],
                "Unit": item["unit"],
                "Category": item["category"],
                "Expiry Date": date.fromisoformat(item["expiry_date"])
                if item.get("expiry_date")
                else date.today(),
            }
            for item in items
        ]
    )
    original_df = display_df.copy()

    edited_df = st.data_editor(
        display_df,
        column_config={
            "Name": st.column_config.TextColumn("Name", disabled=True),
            "Quantity": st.column_config.NumberColumn("Quantity", min_value=0, step=1),
            "Unit": st.column_config.TextColumn("Unit", disabled=True),
            "Category": st.column_config.SelectboxColumn("Category", options=CATEGORY_OPTIONS),
            "Expiry Date": st.column_config.DateColumn("Expiry Date", min_value=date.today()),
        },
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="stocktake_editor",
    )

    st.markdown("")
    if st.button("Save Changes", type="primary", use_container_width=True):
        # Detect rows that changed in any editable column
        changed_mask = (
            (original_df["Quantity"] != edited_df["Quantity"])
            | (original_df["Category"] != edited_df["Category"])
            | (original_df["Expiry Date"] != edited_df["Expiry Date"])
        )
        changed_indices = original_df.index[changed_mask].tolist()

        if not changed_indices:
            st.info("No changes detected.")
            return

        errors: List[str] = []
        saved = 0

        for i in changed_indices:
            item_id = item_ids[i]
            name = original_df.at[i, "Name"]
            expiry = edited_df.at[i, "Expiry Date"]

            # Normalise expiry to date object (data_editor may return date or string)
            if isinstance(expiry, str):
                try:
                    expiry = date.fromisoformat(expiry)
                except ValueError:
                    errors.append(f"**{name}**: invalid expiry date format")
                    continue

            if expiry < date.today():
                errors.append(f"**{name}**: expiry date cannot be in the past")
                continue

            payload = {
                "quantity": int(edited_df.at[i, "Quantity"]),
                "category": edited_df.at[i, "Category"],
                "expiry_date": expiry.isoformat(),
            }
            try:
                update_inventory_item(item_id, payload)
                saved += 1
            except APIError as err:
                errors.append(f"**{name}**: {err.message}")

        for err in errors:
            st.error(err)

        if saved:
            st.success(f"{saved} item(s) updated successfully.")
            st.session_state.inventory_dirty = True
            st.rerun()
