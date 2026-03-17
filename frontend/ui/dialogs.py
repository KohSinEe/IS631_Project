import streamlit as st
from config.settings import ALLERGEN_OPTIONS
from services.client import APIError, api_request
from services.invitations import (
    create_invite,
    fetch_household_invites,
    fetch_household_members,
)
from services.user import (
    add_allergens,
    delete_allergens,
    delete_household,
    get_my_allergens,
    login_user,
    logout_user,
    register_user,
    update_user,
)
from ui.actions import handle_add_item, handle_quick_actions
from ui.barcode import handle_barcode_scan


def _reset_dialog():
    st.session_state.active_dialog = None


@st.dialog("Sign In", on_dismiss=_reset_dialog)
def sign_in_dialog() -> None:
    with st.form("signin_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        if not email or not password:
            st.error("Email and password are required")
        else:
            try:
                login_user(email, password)
                st.toast("Signed in")
                st.rerun()
            except APIError as err:
                st.error(err.message)


@st.dialog("Sign Up", on_dismiss=_reset_dialog)
def sign_up_dialog() -> None:
    with st.form("signup_form"):
        reg_email = st.text_input("Email", key="register_email")
        reg_password = st.text_input("Password", type="password", key="register_password")
        reg_password_confirm = st.text_input("Confirm Password", type="password", key="register_password_confirm")
        reg_name = st.text_input("Display name", key="register_name")
        submitted = st.form_submit_button("Create account")
    if submitted:
        if not reg_email or not reg_password or not reg_password_confirm:
            st.error("Email, password, and confirmation are required")
        elif reg_password != reg_password_confirm:
            st.error("Passwords do not match")
        else:
            try:
                register_user(
                    reg_email,
                    reg_password,
                    reg_password_confirm,
                    reg_name,
                    None,  # none = household input
                )
                st.success("Account created. Please sign in.")
            except APIError as err:
                st.error(err.message)


@st.dialog("Forget Password", on_dismiss=_reset_dialog)
def reset_password_dialog() -> None:
    with st.form("reset_pw_form"):
        email = st.text_input("Email", key="reset_email")
        new_password = st.text_input("New Password", type="password", key="reset_new_password")
        confirm_password = st.text_input("Confirm New Password", type="password", key="reset_confirm_password")
        submitted = st.form_submit_button("Reset Password")
    if submitted:
        if not email or not new_password or not confirm_password:
            st.error("All fields are required")
        elif new_password != confirm_password:
            st.error("Passwords do not match")
        else:
            try:
                from services.user import reset_password

                reset_password(email, new_password)
                st.success("Password reset successful. Please sign in.")
                st.session_state.show_pw_reset = False
            except APIError as err:
                st.error(err.message)


@st.dialog("You have a fridge invitation!", on_dismiss=_reset_dialog)
def invitation_dialog(invites: list) -> None:
    inv = invites[0]
    role_label = "Co-owner" if inv.get("role") == "co_owner" else "Child"
    fridge_name = inv.get("household_name") or "a fridge"
    st.info(f"You've been invited to join **{fridge_name}** as **{role_label}**.")
    if len(invites) > 1:
        st.caption(f"You have {len(invites)} pending invitation(s) total.")
    if st.button("OK", type="primary", use_container_width=True):
        st.rerun()


def _render_allergen_pills(allergens: list) -> None:
    """Render allergens as badges."""
    if not allergens:
        st.caption("None set")
        return

    # Create two rows of badges
    cols = st.columns(len(allergens) if len(allergens) <= 3 else 3, gap="small")
    for i, allergen in enumerate(allergens):
        with cols[i % len(cols)]:
            st.metric("", allergen, label_visibility="collapsed")


@st.dialog("Profile", on_dismiss=_reset_dialog)
def profile_dialog() -> None:
    user = st.session_state.user or {}
    is_owner = user.get("is_household_owner", False)
    is_co_owner = user.get("household_role") == "co_owner"

    # Profile Header
    header_col1, header_col2 = st.columns([1, 3], gap="medium")
    with header_col1:
        user_name = user.get("name") or user.get("email", "U")
        initials = "".join([word[0].upper() for word in user_name.split()][:2])
        st.markdown(
            f"""
        <div style='
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        '>{initials}</div>
        """,
            unsafe_allow_html=True,
        )

    with header_col2:
        st.markdown(f"## {user_name}")
        st.caption(f"📧 {user.get('email', 'N/A')}")

    st.divider()

    tab_profile, tab_allergen = st.tabs(["Account", "Allergens"])

    with tab_profile:
        st.subheader("Edit Profile")
        with st.form("update_profile_form"):
            name = st.text_input(
                "Display Name",
                value=user.get("name") or "",
                placeholder="Enter your display name",
            )
            _ = st.text_input(
                "Email",
                value=user.get("email") or "",
                disabled=True,
            )

            save = st.form_submit_button("Save Changes", use_container_width=True, type="primary")

        if save:
            if not name.strip():
                st.error("Name cannot be empty")
            else:
                try:
                    update_user(name)
                    st.rerun()
                except Exception:
                    st.error("Failed to update profile. Please try again")

    with tab_allergen:
        try:
            st.session_state.current_allergens = get_my_allergens()
        except Exception:
            st.session_state.current_allergens = []

        st.subheader("My Allergens")
        if st.session_state.current_allergens:
            badges = " ".join(
                f'<span style="' f"background:#FF4B4B22; color:#FF4B4B; border:1px solid #FF48B4B55;" f"padding:2px 10px; border-radius:999px; font-size:0.85rem;" f'">{a}</span>'
                for a in st.session_state.current_allergens
            )
            st.markdown(badges, unsafe_allow_html=True)
        else:
            st.info("You have no allergens set.")

        with st.expander("Add or remove allergens", expanded=False):
            available = [a for a in ALLERGEN_OPTIONS if a not in st.session_state.current_allergens]

            # Add allergens section
            if available:
                st.write("**Add allergens:**")
                to_add = st.multiselect("Select allergens to add", options=available, key="add_allergens_multiselect", label_visibility="collapsed")
                if st.button("Add Selected", key="add_allergens_btn", use_container_width=True, disabled=not to_add):
                    try:
                        add_allergens(to_add)
                        st.session_state.current_allergens += to_add
                        st.rerun()
                    except Exception:
                        st.error("Failed to add allergen. Please try again")
            else:
                st.info("All allergens already added")

            # Remove allergens section
            if st.session_state.current_allergens:
                st.write("**Remove allergens:**")
                to_remove = st.multiselect("Select allergens to remove", options=st.session_state.current_allergens, key="remove_allergens_multiselect", label_visibility="collapsed")
                if st.button("Remove Selected", key="remove_allergens_btn", use_container_width=True, disabled=not to_remove):
                    try:
                        delete_allergens(to_remove)
                        st.session_state.current_allergens = [x for x in st.session_state.current_allergens if x not in to_remove]
                        st.session_state.active_dialog = "user_profile"
                        st.rerun()
                    except Exception:
                        st.error("Failed to remove allergen. Please try again")
            else:
                st.info("No allergens to remove")

        st.divider()

        # Household Allergens (owner/co-owner only)
        st.subheader("Household Allergens")
        if not user.get("household_id"):
            st.info("You are not part of a household.")
        elif is_owner or is_co_owner:
            try:
                household_allergens = api_request("get", "/households/allergens")
                members = fetch_household_members(user["household_id"])
                member_map = {m.get("id"): m.get("name") or m.get("email") for m in members}

                if isinstance(household_allergens, list):
                    has_any = False
                    for entry in household_allergens:
                        allergens = entry.get("allergens", [])
                        if allergens:
                            has_any = True
                            member_name = member_map.get(entry.get("user_id"), f"User {entry.get('user_id')}")
                            st.write(f"**{member_name.title()}**")
                            badges = " ".join(
                                f'<span style="' f"background:#FF4B4B22; color:#FF4B4B; border:1px solid #FF48B4B55;" f"padding:2px 10px; border-radius:999px; font-size:0.85rem;" f'">{a}</span>'
                                for a in allergens
                            )
                            st.markdown(badges, unsafe_allow_html=True)
                    if not has_any:
                        st.info("No household members have allergens set.")
            except Exception as e:
                st.error(f"Failed to load household allergens: {str(e)}")
        else:
            st.warning("You do not have the authority to see household allergens.")


@st.dialog("Logout", on_dismiss=_reset_dialog)
def logout_dialog() -> None:
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Yes", use_container_width=True):
            try:
                logout_user()
            except Exception:
                pass  # Local state is cleared in logout_user; ensure we still close and rerun
            st.rerun()
    with col2:
        if st.button("No", type="secondary", use_container_width=True):
            st.rerun()


@st.dialog("You have a fridge invitation", on_dismiss=_reset_dialog)
def invitation_notification_dialog(invites: list) -> None:
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


@st.dialog("Manage Fridge", on_dismiss=_reset_dialog)
def manage_fridge_dialog() -> None:
    user = st.session_state.get("user") or {}
    household_id = st.session_state.get("household_id")
    is_owner = user.get("is_household_owner", False)

    try:
        members = fetch_household_members(household_id)
    except APIError:
        members = []

    try:
        sent_invites = fetch_household_invites(household_id) if is_owner else []
    except APIError:
        sent_invites = []

    st.markdown("**Fridge Members**")

    if members:
        role_label = {"owner": "Owner", "co_owner": "Co-owner", "child": "Child"}
        role_order = {"owner": 0, "co_owner": 1, "child": 2}
        current_email = user.get("email", "").lower()

        sorted_members = sorted(members, key=lambda m: (role_order.get(m.get("role"), 999), (m.get("name") or m.get("email") or "—").lower()))

        for m in sorted_members:
            member_name = m.get("name") or m.get("email") or "—"
            member_email = m.get("email", "").lower()
            is_current_user = member_email == current_email

            if is_current_user:
                display_name = f"{member_name} (you)"
            else:
                display_name = member_name

            role = role_label.get(m.get("role"), m.get("role", ""))
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"**{display_name}**")
            with col2:
                st.caption(f"_{role}_")
    else:
        st.caption("No members yet.")

    if is_owner:
        st.divider()

        with st.expander("Add Members", expanded=False):
            st.caption("Invite someone by email. They must already have an account.")

            with st.form("manage_fridge_invite_form"):
                email = st.text_input(
                    "Email address",
                    placeholder="friend@example.com",
                    key="manage_invite_email",
                    help="The person must already have an account",
                )
                role = st.selectbox(
                    "Role",
                    options=["co_owner", "child"],
                    format_func=lambda x: "Co-owner" if x == "co_owner" else "Child",
                    key="manage_invite_role",
                    help="Co-owners can manage the fridge. Children have read-only access.",
                )
                submitted = st.form_submit_button("Send invitation", use_container_width=True, type="primary")

            if submitted:
                if not email or "@" not in email:
                    st.error("Please enter a valid email address.")
                else:
                    try:
                        create_invite(household_id, email.strip(), role)
                        st.toast(f"Invitation sent to {email.strip()}")
                        st.rerun()
                    except APIError as e:
                        st.error(getattr(e, "message", str(e)))

        if sent_invites:
            with st.expander("Pending Invitations", expanded=False):
                status_label = {"pending": "Pending", "accepted": "Accepted", "declined": "Declined"}
                role_label_inv = {"co_owner": "Co-owner", "child": "Child"}

                for inv in sent_invites:
                    email = inv.get("invitee_email", "")
                    role = role_label_inv.get(inv.get("role"), inv.get("role", ""))
                    status = status_label.get(inv.get("status"), inv.get("status", ""))

                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.caption(f"**{email}**")
                    with col2:
                        st.caption(f"_{role}_")
                    with col3:
                        status_color = "green" if status == "Accepted" else "orange" if status == "Pending" else "red"
                        st.caption(f":{status_color}[{status}]")

        st.divider()

        st.markdown("**Delete Fridge**")
        st.warning("This action will permanently delete your fridge and all its contents. All members will be removed. This cannot be undone.")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Cancel", type="secondary", use_container_width=True, key="delete_cancel_btn"):
                st.rerun()
        with col2:
            if st.button("Delete fridge", type="primary", use_container_width=True, key="delete_fridge_confirm_btn"):
                try:
                    delete_household(household_id)
                    st.success("Fridge deleted.")
                    st.rerun()
                except APIError as e:
                    st.error(getattr(e, "message", str(e)))


@st.dialog("AddItem", on_dismiss=_reset_dialog)
def add_item_dialog() -> None:
    tab1, tab2, tab3 = st.tabs(["Manual Entry", "Barcode Scan", "Photo Scan"])

    with tab1:
        handle_add_item()
    with tab2:
        handle_barcode_scan()
    with tab3:
        from ui.image_scan import handle_image_scan

        handle_image_scan()


@st.dialog("EditItem", on_dismiss=_reset_dialog)
def edit_item_dialog(sorted_items) -> None:
    handle_quick_actions(sorted_items)
