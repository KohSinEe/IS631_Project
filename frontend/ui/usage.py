import csv
import io
from datetime import date, timedelta
from typing import Any, Dict, List

import streamlit as st
from services.client import APIError
from services.usage import fetch_usage_summary


def render_usage_overview() -> None:
    col_back, col_title = st.columns([1, 8])
    with col_back:
        st.markdown("<div style='margin-top: 0.4rem'></div>", unsafe_allow_html=True)
        if st.button("← Back"):
            st.session_state.page = "dashboard"
            st.rerun()
    with col_title:
        st.markdown("## Usage Overview")
        st.caption("Understand your household's consumption patterns over a selected period.")

    household_id = st.session_state.household_id
    if not household_id:
        st.info("You do not belong to a household yet.")
        return

    st.divider()

    # Date range picker — default: last 30 days
    today = date.today()
    default_from = today - timedelta(days=30)

    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From", value=default_from, max_value=today, format="DD/MM/YYYY")
    with col2:
        to_date = st.date_input("To", value=today, max_value=today, format="DD/MM/YYYY")

    if from_date > to_date:
        st.error("'From' date must be on or before the 'To' date.")
        return

    try:
        data: Dict[str, Any] = fetch_usage_summary(from_date, to_date)
    except APIError as err:
        st.error(f"Failed to load usage data: {err.message}")
        return

    logs: List[Dict[str, Any]] = data.get("logs", [])
    most_used: List[Dict[str, Any]] = data.get("most_used", [])
    least_used: List[Dict[str, Any]] = data.get("least_used", [])

    st.divider()

    # Summary metrics
    total_consumed = sum(entry["total_consumed"] for entry in logs)
    top_item = most_used[0]["item_name"] if most_used else "—"
    bottom_item = least_used[0]["item_name"] if least_used else "—"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Consumed", total_consumed)
    with col2:
        st.metric("Most Used", top_item)
    with col3:
        st.metric("Least Used", bottom_item)

    st.divider()

    if not logs:
        st.info(
            "No consumption recorded in this period. Quantity decreases via 'Quick Actions' are tracked here."
        )
        return

    # Consumption table
    st.markdown("### Consumption by Item")
    table_rows = [
        {
            "Item": entry["item_name"],
            "Unit": entry["unit"],
            "Total Consumed": entry["total_consumed"],
            "Last Used": entry["last_consumed"][:10] if entry.get("last_consumed") else "—",
        }
        for entry in logs
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    # CSV export — built from the same table_rows as displayed (AC3)
    st.divider()
    csv_buf = io.StringIO()
    writer = csv.DictWriter(csv_buf, fieldnames=["Item", "Unit", "Total Consumed", "Last Used"])
    writer.writeheader()
    writer.writerows(table_rows)

    filename = f"usage_{from_date}_{to_date}.csv"
    st.download_button(
        label="Export as CSV",
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )
