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
from services.user import logout_user, update_user, delete_household, get_current_user
from services.client import APIError
from services.inventory import create_inventory_item
from services.invitations import (
    fetch_my_invitations,
    fetch_household_members,
    fetch_household_invites,
    create_invite,
    accept_invitation,
    decline_invitation,
)
from ui.actions import handle_quick_actions
from ui.barcode import handle_barcode_scan
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
            try:
                logout_user()
            except Exception:
                pass  # Local state is cleared in logout_user; ensure we still close and rerun
            st.session_state.show_logout_dialog = False
            st.rerun()
    with col2:
        if st.button("No", type="secondary", use_container_width=True):
            st.session_state.show_logout_dialog = False
            st.rerun()


@st.dialog("Invite to fridge")
def invite_user_dialog(household_id: int) -> None:
    # Show success + OK when we just sent an invite (so user can acknowledge)
    if st.session_state.get("invite_sent_to"):
        email = st.session_state.invite_sent_to
        st.success(f"Invitation sent to **{email}**. They can accept or decline from their dashboard.")
        if st.button("OK", type="primary", use_container_width=True):
            st.session_state.invite_sent_to = None
            st.session_state.show_invite_dialog = False
            st.rerun()
        return

    st.caption("Invite someone by email. They must already have an account.")
    with st.form("invite_user_form"):
        email = st.text_input("Email", placeholder="friend@example.com", key="invite_email")
        role = st.selectbox(
            "Role",
            options=["co_owner", "child"],
            format_func=lambda x: "Co-owner" if x == "co_owner" else "Child",
            key="invite_role",
        )
        submitted = st.form_submit_button("Send invite")
    if submitted:
        if not email or "@" not in email:
            st.error("Please enter a valid email.")
        else:
            try:
                create_invite(household_id, email.strip(), role)
                st.session_state.invite_sent_to = email.strip()
                st.rerun()
            except APIError as e:
                st.error(getattr(e, "message", str(e)))


@st.dialog("You have a fridge invitation")
def invitation_notification_dialog(invites: list) -> None:
    """Pop-up to notify the user they have pending invitation(s)."""
    invites = [i for i in (invites or []) if isinstance(i, dict)]
    if not invites:
        return
    inv = invites[0]
    role_label = "Co-owner" if inv.get("role") == "co_owner" else "Child"
    fridge_name = inv.get("household_name") or "a fridge"
    st.info(f"You've been invited to join **{fridge_name}** as **{role_label}**.")
    if len(invites) > 1:
        st.caption(f"You have {len(invites)} pending invitation(s).")
    if st.button("OK", type="primary", use_container_width=True):
        st.session_state.invitation_popup_dismissed = True
        st.rerun()


@st.dialog("Delete fridge")
def delete_fridge_dialog(household_id: int) -> None:
    st.warning(
        "This will permanently delete your fridge and all its contents. "
        "All members will be removed from the fridge. This cannot be undone."
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Cancel", type="secondary", use_container_width=True):
            st.session_state.show_delete_fridge_dialog = False
            st.rerun()
    with col2:
        if st.button("Delete my fridge", type="primary", use_container_width=True):
            try:
                delete_household(household_id)
                st.session_state.show_delete_fridge_dialog = False
                st.success("Fridge deleted.")
                st.rerun()
            except APIError as e:
                st.error(getattr(e, "message", str(e)))


def render_header() -> None:
    user = st.session_state.user or {}
    if "show_profile_dialog" not in st.session_state:
        st.session_state.show_profile_dialog = False
    if "show_logout_dialog" not in st.session_state:
        st.session_state.show_logout_dialog = False
    if "show_delete_fridge_dialog" not in st.session_state:
        st.session_state.show_delete_fridge_dialog = False
    if "show_invite_dialog" not in st.session_state:
        st.session_state.show_invite_dialog = False

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
            if (
                user.get("household_id")
                and user.get("is_household_owner")
                and st.button("Invite to fridge", use_container_width=True)
            ):
                st.session_state.show_invite_dialog = True
            if (
                user.get("household_id")
                and user.get("is_household_owner")
                and st.button("Delete fridge", use_container_width=True)
            ):
                st.session_state.show_delete_fridge_dialog = True
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
    tab1, tab2 = st.tabs(["Manual Entry", "Barcode Scan"])

    with tab1:
        handle_add_item()
    with tab2:
        handle_barcode_scan()


@st.dialog("EditItem")
def edit_item_dialog(sorted_items) -> None:
    handle_quick_actions(sorted_items)


def render_dashboard() -> None:
    if "show_add_item_dialog" not in st.session_state:
        st.session_state.show_add_item_dialog = False
    if "show_edit_item_dialog" not in st.session_state:
        st.session_state.show_edit_item_dialog = False

    render_header()

    # Show invite dialog when triggered from Account popover
    if st.session_state.get("show_invite_dialog") and st.session_state.get("household_id"):
        invite_user_dialog(st.session_state.household_id)
    # Show delete-fridge confirmation dialog when triggered (e.g. from Account popover)
    if st.session_state.get("show_delete_fridge_dialog") and st.session_state.get("household_id"):
        delete_fridge_dialog(st.session_state.household_id)

    # Pending invitations (for users not in a household, or at top for everyone)
    try:
        raw = fetch_my_invitations()
        pending = [x for x in (raw or []) if isinstance(x, dict)]
    except Exception:
        pending = []
    if not pending:
        st.session_state.invitation_popup_dismissed = False  # Reset so next invite shows popup
    if pending:
        # Pop-up notification for invitee (show once until they click OK)
        if "invitation_popup_dismissed" not in st.session_state:
            st.session_state.invitation_popup_dismissed = False
        if not st.session_state.invitation_popup_dismissed:
            invitation_notification_dialog(pending)
        st.markdown("### Pending invitations")
        for inv in pending:
            role_label = "Co-owner" if inv.get("role") == "co_owner" else "Child"
            inviter = inv.get("inviter_name") or "Someone"
            inv_id = inv.get("id")
            if inv_id is None:
                continue
            st.write(f"**{inv.get('household_name', 'Fridge')}** — {inviter} invited you as **{role_label}**.")
            col1, col2, _ = st.columns([1, 1, 4])
            with col1:
                if st.button("Accept", key=f"accept_inv_{inv_id}"):
                    try:
                        accept_invitation(inv_id)
                        get_current_user()
                        st.session_state.inventory_dirty = True
                        st.success("You joined the fridge!")
                        st.rerun()
                    except APIError as e:
                        st.error(getattr(e, "message", str(e)))
            with col2:
                if st.button("Decline", key=f"decline_inv_{inv_id}", type="secondary"):
                    try:
                        decline_invitation(inv_id)
                        st.rerun()
                    except APIError as e:
                        st.error(getattr(e, "message", str(e)))
        st.divider()

    action_cols = st.columns([1, 1, 1])
    render_metric("Items tracked", len(st.session_state.inventory), action_cols[0], "green")
    summary = summarize_inventory(st.session_state.inventory)
    render_metric("Expiring soon", summary["expiring"], action_cols[1], "orange")
    render_metric("Expired", summary["overdue"], action_cols[2], "red")

    household_id = st.session_state.household_id
    if not household_id:
        if not pending:
            st.info(
                "You do not belong to a fridge yet. Get invited by an owner, or create an account with a household name."
            )
        ensure_inventory_loaded()
        return

    # Fridge members and their roles
    try:
        members = fetch_household_members(household_id)
    except APIError:
        members = []
    if members:
        role_label = {"owner": "Owner", "co_owner": "Co-owner", "child": "Child"}
        st.markdown("### Fridge members")
        for m in members:
            name = m.get("name") or m.get("email") or "—"
            role = role_label.get(m.get("role"), m.get("role", ""))
            st.caption(f"**{name}** — {role}")
        st.divider()

    # Owner: invitation status (accepted / declined / pending) so they see when someone responds
    user = st.session_state.user or {}
    if user.get("is_household_owner"):
        try:
            sent_invites = fetch_household_invites(household_id)
        except APIError:
            sent_invites = []
        if sent_invites:
            status_label = {"pending": "Pending", "accepted": "Accepted", "declined": "Declined"}
            role_label_inv = {"co_owner": "Co-owner", "child": "Child"}
            with st.expander("Invitation status (shared fridge)"):
                st.caption("You’ll see here when someone accepts or declines your invite.")
                for inv in sent_invites:
                    email = inv.get("invitee_email", "")
                    role = role_label_inv.get(inv.get("role"), inv.get("role", ""))
                    status = status_label.get(inv.get("status"), inv.get("status", ""))
                    st.caption(f"**{email}** — {role} — *{status}*")
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

    if st.button("✨ Generate Recipe ✨", use_container_width=True):
        st.session_state.page = "recipe"

    ensure_inventory_loaded()
