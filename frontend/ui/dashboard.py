import streamlit as st
from typing import Any, Dict, List
from datetime import date, timedelta

from config.settings import EXPIRY_ALERT_DAYS, CATEGORY_OPTIONS, UNIT_OPTIONS
from utils.inventory import (
    parse_expiry,
    summarize_inventory,
    ensure_inventory_loaded,
    filter_inventory,
)
from services.user import logout_user, update_user
from services.client import APIError
from services.inventory import create_inventory_item
from ui.actions import handle_quick_actions
from ui.barcode import handle_barcode_scan
from ui.image_scan import handle_image_scan  # new photo recognition UI
from ui.recipe import handle_generate_recipe


@st.dialog("Profile")
def profile_dialog() -> None:
    user = st.session_state.user or {}

    with st.form("update_profile_form"):
        name = st.text_input(
            "Username",
            value=user.get("name") or "",
            placeholder="Enter your display name",
        )
        _ = st.text_input(
            "Email",
            value=user.get("email") or "",
            disabled=True,
        )

        save = st.form_submit_button("Save", use_container_width=True)

    if save:
        if not name.strip():
            st.error("Name cannot be empty")
        else:
            try:
                update_user(name)
                st.success("Profile updated successfully")
            except Exception as e:
                st.error("Failed to update profile. Please try again")
                st.error(e)


@st.dialog("Logout")
def logout_dialog() -> None:
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Yes", use_container_width=True):
            logout_user()
            st.session_state.show_logout_dialog = False
            st.rerun()
    with col2:
        if st.button("No", type="secondary", use_container_width=True):
            st.session_state.show_logout_dialog = False
            st.rerun()


def render_header() -> None:
    user = st.session_state.user or {}
    if "show_profile_dialog" not in st.session_state:
        st.session_state.show_profile_dialog = False
    if "show_logout_dialog" not in st.session_state:
        st.session_state.show_logout_dialog = False

    header_left, header_right = st.columns([10, 1])

    with header_left:
        st.markdown(
            f"""
            <h1>Welcome back, {user.get('name') or user.get('email')}</h1>
            <h3>Your fridge at a glance...</h3>
            """,
            unsafe_allow_html=True,
        )

    with header_right:
        st.markdown("<div style='margin-top: 1.5rem'></div>", unsafe_allow_html=True)

        with st.popover("Account"):
            if st.button("Profile", use_container_width=True):
                st.session_state.show_profile_dialog = True
                if st.session_state.show_profile_dialog:
                    profile_dialog()
            if st.button("Sign out", type="secondary", use_container_width=True):
                st.session_state.show_logout_dialog = True
                if st.session_state.show_logout_dialog:
                    logout_dialog()


def render_metric(
    label: str, value: Any, column: st.delta_generator.DeltaGenerator, color: str
) -> None:
    color_class = {
        "blue": "",
        "green": "metric-green",
        "orange": "metric-orange",
        "red": "metric-red",
    }.get(color, "")

    with column:
        st.markdown(
            f"""
            <div class="metric-card {color_class}">
                <h3>{label}</h3>
                <p>{value}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_expiry_alerts(summary: Dict[str, Any]) -> None:
    expiring_items = summary.get("expiring_items", [])
    if not expiring_items:
        return

    st.warning("Watch these items before they go bad:")
    for item in expiring_items:
        expiry = item["expiry"].strftime("%b %d")
        st.write(f"• {item['name']} — {item['quantity']} {item['unit']} by {expiry}")


def render_inventory_table(
    items: List[Dict[str, Any]], sort_by_expiry: bool
) -> List[Dict[str, Any]]:
    working = items.copy()
    if sort_by_expiry:
        working.sort(
            key=lambda entry: (
                parse_expiry(entry["expiry_date"]) if entry.get("expiry_date") else date.max
            )
        )

    rows: List[Dict[str, Any]] = []
    soon_cutoff = date.today() + timedelta(days=EXPIRY_ALERT_DAYS)
    for item in working:
        expiry_raw = item.get("expiry_date")
        if not expiry_raw:
            continue
        expiry = parse_expiry(expiry_raw)
        status = "Fresh"
        if expiry < date.today():
            status = "Expired"
        elif expiry <= soon_cutoff:
            status = "Expiring soon"
        rows.append(
            {
                "Item": item.get("name"),
                "Quantity": f"{item.get('quantity')} {item.get('unit')}",
                "Category": item.get("category"),
                "Expiry": expiry.strftime("%b %d, %Y"),
                "Status": status,
            }
        )

    if not rows:
        st.info("No items to display yet.")
        return working

    st.markdown("### Inventory overview")
    st.dataframe(rows, use_container_width=True, hide_index=True)
    return working


def handle_add_item() -> None:
    with st.form("add_item_form"):
        st.subheader("Add to pantry")
        name = st.text_input("Item", key="create_name")
        quantity = st.number_input("Quantity", min_value=0, step=1, value=1, key="create_quantity")
        unit = st.selectbox("Unit", options=UNIT_OPTIONS, key="create_unit")
        expiry = st.date_input(
            "Expiry Date", min_value=date.today(), format="DD/MM/YYYY", key="create_expiry"
        )
        category = st.selectbox("Category", options=CATEGORY_OPTIONS, key="create_category")
        submitted = st.form_submit_button("Save item")

    if submitted:
        if not name:
            st.error("Item name is required")
            return
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


@st.dialog("AddItem")
def add_item_dialog() -> None:
    tab1, tab2, tab3 = st.tabs(["Manual Entry", "Barcode Scan", "Photo Scan"])

    with tab1:
        handle_add_item()
    with tab2:
        handle_barcode_scan()
    with tab3:
        from ui.image_scan import handle_image_scan
        handle_image_scan()


@st.dialog("EditItem")
def edit_item_dialog(sorted_items) -> None:
    handle_quick_actions(sorted_items)


def render_dashboard() -> None:
    if "show_add_item_dialog" not in st.session_state:
        st.session_state.show_add_item_dialog = False
    if "show_edit_item_dialog" not in st.session_state:
        st.session_state.show_edit_item_dialog = False

    render_header()
    action_cols = st.columns([1, 1, 1])
    render_metric("Items tracked", len(st.session_state.inventory), action_cols[0], "green")
    summary = summarize_inventory(st.session_state.inventory)
    render_metric("Expiring soon", summary["expiring"], action_cols[1], "orange")
    render_metric("Expired", summary["overdue"], action_cols[2], "red")

    household_id = st.session_state.household_id
    if not household_id:
        st.info(
            "You do not belong to a household yet. Ask an admin to assign you before managing items."
        )
        return

    st.divider()

    add_item_col, edit_item_col = st.columns([1, 1])

    if "category_filter" not in st.session_state:
        st.session_state.category_filter = "All"

    filter_options = ["All"] + CATEGORY_OPTIONS
    _ = st.selectbox("Filter by category", filter_options, key="category_filter")
    _ = st.toggle("Sort by expiry date", key="sort_by_expiry")

    st.session_state.filtered_inventory = filter_inventory(
        st.session_state.inventory, st.session_state.category_filter
    )
    st.session_state.filtered_inventory = render_inventory_table(
        st.session_state.filtered_inventory, st.session_state.sort_by_expiry
    )

    with add_item_col:
        if st.button("Add Item", use_container_width=True):
            st.session_state.show_add_item_dialog = True
            if st.session_state.show_add_item_dialog:
                add_item_dialog()
    with edit_item_col:
        if st.button("Edit Items", use_container_width=True):
            st.session_state.show_edit_item_dialog = True
            if st.session_state.show_edit_item_dialog:
                edit_item_dialog(st.session_state.filtered_inventory)

    nav_col1, nav_col2, nav_col3 = st.columns(3)
    with nav_col1:
        if st.button("✨ Generate Recipe ✨", use_container_width=True):
            st.session_state.page = "recipe"
    with nav_col2:
        if st.button("Stocktake", use_container_width=True):
            st.session_state.page = "stocktake"
    with nav_col3:
        if st.button("Usage Overview", use_container_width=True):
            st.session_state.page = "usage"

    ensure_inventory_loaded()
