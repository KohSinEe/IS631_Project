from datetime import date, timedelta
from typing import Any, Dict, List

import streamlit as st
from config.settings import (
    CATEGORY_OPTIONS,
    EXPIRY_ALERT_DAYS,
)
from services.client import APIError
from services.invitations import (
    accept_invitation,
    decline_invitation,
    fetch_my_invitations,
)
from services.user import (
    get_current_user,
)
from state.session import mark_inventory_dirty, reset_active_dialog
from ui.dialogs import (
    add_item_dialog,
    edit_item_dialog,
    invitation_notification_dialog,
    logout_dialog,
    manage_fridge_dialog,
    profile_dialog,
)
from utils.inventory import (
    ensure_inventory_loaded,
    filter_inventory,
    parse_expiry,
    summarize_inventory,
)
from utils.presentation import format_role, get_error_message, safe_html_text, user_display_name


def render_header() -> None:
    user = st.session_state.user or {}
    household_id = user.get("household_id")

    header_left, header_right = st.columns([8, 2])

    with header_left:
        name = safe_html_text(user_display_name(user))
        st.markdown(
            f"""
            <div class="dashboard-welcome">
            <h1>Welcome back, {name}</h1>
            <h3>Your fridge at a glance</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with header_right:
        st.markdown("<div style='margin-top: 1.5rem'></div>", unsafe_allow_html=True)

        with st.popover("Account"):
            if (
                st.button("Profile", key="header_profile_btn", use_container_width=True)
                or st.session_state.active_dialog == "user_profile"
            ):
                st.session_state.active_dialog = "user_profile"
                profile_dialog()
            if household_id and (
                st.button("Manage Fridge", key="manage_fridge_button", use_container_width=True)
                or st.session_state.active_dialog == "manage_fridge"
            ):
                st.session_state.active_dialog = "manage_fridge"
                manage_fridge_dialog()
            if (
                st.button(
                    "Sign out", key="header_signout_btn", type="secondary", use_container_width=True
                )
                or st.session_state.active_dialog == "logout"
            ):
                st.session_state.active_dialog = "logout"
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

    st.markdown("### Inventory Overview")
    st.dataframe(rows, width="stretch", hide_index=True)
    return working


def render_dashboard() -> None:
    user = st.session_state.get("user") or {}

    ensure_inventory_loaded()

    render_header()

    if "flash_success" in st.session_state:
        st.success(st.session_state.flash_success)
        del st.session_state.flash_success

    # Pending invitations: fetch early so we can open at most one dialog per run
    try:
        raw = fetch_my_invitations()
        pending = [x for x in (raw or []) if isinstance(x, dict)]
    except APIError:
        pending = []
    if not pending:
        st.session_state.invitation_popup_dismissed = False  # Reset so next invite shows popup
    if "invitation_popup_dismissed" not in st.session_state:
        st.session_state.invitation_popup_dismissed = False

    if pending and not st.session_state.invitation_popup_dismissed:
        invitation_notification_dialog(pending)

    if pending:
        st.markdown("### Pending invitations")
        for inv in pending:
            role_label = format_role(inv.get("role"))
            inviter = inv.get("inviter_name") or "Someone"
            inv_id = inv.get("id")
            if inv_id is None:
                continue
            st.write(
                f"**{inv.get('household_name', 'Fridge')}** — {inviter} invited you as **{role_label}**."
            )
            col1, col2, _ = st.columns([1, 1, 4])
            with col1:
                if st.button("Accept", key=f"accept_inv_{inv_id}"):
                    reset_active_dialog()  # Avoid opening "Invite to fridge" after accept
                    try:
                        accept_invitation(inv_id)
                        get_current_user()
                        st.success("You joined the fridge!")
                        mark_inventory_dirty(rerun=True)
                    except APIError as e:
                        st.error(get_error_message(e))
            with col2:
                if st.button("Decline", key=f"decline_inv_{inv_id}", type="secondary"):
                    try:
                        decline_invitation(inv_id)
                        st.rerun()
                    except APIError as e:
                        st.error(get_error_message(e))
        st.divider()

    action_cols = st.columns([1, 1, 1])
    render_metric("Items tracked", len(st.session_state.inventory), action_cols[0], "green")
    summary = summarize_inventory(st.session_state.inventory)
    render_metric("Expiring soon", summary["expiring"], action_cols[1], "orange")
    render_metric("Expired", summary["overdue"], action_cols[2], "red")

    st.space()

    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("Stocktake", use_container_width=True):
            reset_active_dialog()
            st.session_state.page = "stocktake"
            st.rerun()
    with nav_col2:
        if st.button("Usage Overview", use_container_width=True):
            reset_active_dialog()
            st.session_state.page = "usage"
            st.rerun()

    st.divider()

    household_id = st.session_state.household_id
    if not household_id:
        if not pending:
            st.info(
                "You do not belong to a fridge yet. Get invited by an owner, or create an account with a household name."
            )
        ensure_inventory_loaded()
        return

    if user.get("household_role") != "child":
        add_item_col, edit_item_col = st.columns([1, 1])

        with add_item_col:
            if st.button("Add Item", use_container_width=True):
                st.session_state.active_dialog = "add_item"
                add_item_dialog()
        with edit_item_col:
            if (
                st.button("Edit Items", use_container_width=True)
                or st.session_state.active_dialog == "edit_item"
            ):
                st.session_state.active_dialog = "edit_item"
                edit_item_dialog(st.session_state.filtered_inventory)
    else:
        if (
            st.button("Edit Items", use_container_width=True)
            or st.session_state.active_dialog == "edit_item"
        ):
            st.session_state.active_dialog = "edit_item"
            edit_item_dialog(st.session_state.filtered_inventory)

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

    st.divider()

    st.markdown("### Help Me Generate A Recipe")

    inventory_only = not st.toggle(
        "Consider ingredients outside my fridge",
        value=False,
        key="inventory_only_toggle",
        help="When on, the AI may suggest recipes that need extra ingredients not in your fridge.",
    )
    st.session_state.inventory_only = inventory_only

    if user.get("household_id"):
        cooking_for = st.radio(
            "Who are you cooking for?",
            options=["myself", "household"],
            format_func=lambda x: "Myself" if x == "myself" else "My Household",
            horizontal=True,
            key="cooking_for_radio",
        )
        st.session_state.use_household_allergens = cooking_for == "household"
    else:
        st.session_state.use_household_allergens = False

    if st.button("✨ Generate Recipe ✨", use_container_width=True):
        st.session_state.page = "recipe"

    ensure_inventory_loaded()
