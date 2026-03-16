import streamlit as st
from config.settings import ALLERGEN_OPTIONS
from services.client import APIError, api_request
from services.invitations import create_invite, fetch_household_members
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
        st.session_state.invitation_popup_dismissed = True
        st.rerun()


@st.dialog("Profile", on_dismiss=_reset_dialog)
def profile_dialog() -> None:
    user = st.session_state.user or {}
    is_owner = user.get("is_household_owner", False)
    is_co_owner = user.get("household_role") == "co_owner"

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

    st.divider()

    # My Allergens section (always visible in profile)
    try:
        current_allergens = get_my_allergens()
    except Exception:
        current_allergens = []

    with st.expander("**My Allergens**", expanded=True):
        if current_allergens:
            st.write("You are currently allergic to:")
            st.write(", ".join(current_allergens))
        else:
            st.info("No allergens set.")

        if "show_allergen_edit" not in st.session_state:
            st.session_state.show_allergen_edit = False

        if st.button("Edit My Allergens", key="profile_edit_allergens_btn", use_container_width=True):
            st.session_state.show_allergen_edit = not st.session_state.show_allergen_edit

        if st.session_state.show_allergen_edit:
            available = [a for a in ALLERGEN_OPTIONS if a not in current_allergens]
            removable = current_allergens

            if available:
                st.write("**Add allergens:**")
                to_add = []
                cols = st.columns(3)
                for i, allergen in enumerate(available):
                    with cols[i % 3]:
                        if st.checkbox(allergen, key=f"add_{allergen}"):
                            to_add.append(allergen)
                if st.button("Add selected", key="add_allergens_btn"):
                    if to_add:
                        try:
                            add_allergens(to_add)
                            st.success(f"Added: {', '.join(to_add)}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                    else:
                        st.warning("No allergens selected")

            if removable:
                st.write("**Remove allergens:**")
                to_remove = []
                cols = st.columns(3)
                for i, allergen in enumerate(removable):
                    with cols[i % 3]:
                        if st.checkbox(allergen, key=f"remove_{allergen}"):
                            to_remove.append(allergen)
                if st.button("Remove selected", key="remove_allergens_btn"):
                    if to_remove:
                        try:
                            delete_allergens(to_remove)
                            st.success(f"Removed: {', '.join(to_remove)}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                    else:
                        st.warning("No allergens selected")

    st.divider()

    # Household Allergens (owner/co-owner only)
    with st.expander("**Household Allergens**", expanded=True):
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
                            name = member_map.get(entry.get("user_id"), f"User {entry.get('user_id')}")
                            st.write(f"**{name.title()}**: {', '.join(allergens)}")
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


@st.dialog("Invite to fridge", on_dismiss=_reset_dialog)
def invite_user_dialog() -> None:
    household_id = st.session_state.get("household_id")

    # Show success + OK when we just sent an invite (so user can acknowledge)
    if st.session_state.get("invite_sent_to"):
        email = st.session_state.invite_sent_to
        st.success(f"Invitation sent to **{email}**. They can accept or decline from their dashboard.")
        if st.button("OK", type="primary", use_container_width=True):
            st.session_state.invite_sent_to = None
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


@st.dialog("You have a fridge invitation", on_dismiss=_reset_dialog)
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


@st.dialog("Delete fridge", on_dismiss=_reset_dialog)
def delete_fridge_dialog() -> None:
    household_id = st.session_state.get("household_id")

    st.warning("This will permanently delete your fridge and all its contents. " "All members will be removed from the fridge. This cannot be undone.")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Cancel", type="secondary", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("Delete my fridge", type="primary", use_container_width=True):
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
