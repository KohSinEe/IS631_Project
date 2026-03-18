import streamlit as st
from services.client import APIError
from services.invitations import accept_invitation, decline_invitation, fetch_my_invitations
from services.user import create_household
from ui.dialogs import invitation_dialog, logout_dialog
from utils.presentation import format_role


def _render_create_household() -> None:
    st.subheader("🏠 Create your Fridge")
    st.write("Set up a household to start managing your fridge. You'll be the owner.")

    with st.form("create_household_form"):
        name = st.text_input("Household name", placeholder="e.g. Group 3's Fridge")
        submitted = st.form_submit_button("Create Household", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Please enter a household name.")
        else:
            try:
                create_household(name.strip())
                st.success("Household created! Taking you to your dashboard...")
                st.rerun()
            except APIError as err:
                st.error(err.message)


def _render_pending_invitations(invitations: list) -> None:
    st.subheader("📬 Pending Invitations")

    if not invitations:
        st.info("You have no pending invitations right now.")
        return

    st.write("You've been invited to join a household. Accept one to skip creating your own.")

    for inv in invitations:
        household_name = inv.get("household_name") or f"Household #{inv.get('household_id')}"
        inviter = inv.get("inviter_name") or inv.get("inviter_email") or "Someone"
        role = format_role(inv.get("role"))
        inv_id = inv.get("id")

        with st.container(border=True):
            st.markdown(f"**{household_name}**")
            st.caption(f"Invited by {inviter} · Role: {role}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Accept", key=f"accept_{inv_id}", use_container_width=True):
                    try:
                        accept_invitation(inv_id)
                        from services.user import get_current_user

                        get_current_user()
                        st.toast("Invitation accepted!")
                        st.rerun()
                    except APIError as err:
                        st.error(err.message)
            with col2:
                if st.button("❌ Decline", key=f"decline_{inv_id}", use_container_width=True):
                    try:
                        decline_invitation(inv_id)
                        st.toast("Invitation declined.")
                        st.rerun()
                    except APIError as err:
                        st.error(err.message)


def render_household_setup() -> None:
    st.markdown(
        "<div style='text-align: center; padding: 2rem 0 1rem;'>"
        "<h1>🥕 Welcome to FridgeBuddy!</h1>"
        "<p style='color: gray;'>You're almost set up. Create a household or accept invitations to get started.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Fetch invitations once
    try:
        invitations = fetch_my_invitations()
        pending = [x for x in (invitations or []) if isinstance(x, dict)]
    except Exception:
        pending = []

    if pending and not st.session_state.household_setup_invitation_shown:
        st.session_state.household_setup_invitation_shown = True
        invitation_dialog(pending)

    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        _render_create_household()
        st.divider()
        _render_pending_invitations(pending)
        st.divider()
        if st.button("Sign out", use_container_width=True) or st.session_state.active_dialog == "logout":
            st.session_state.active_dialog = "logout"
            logout_dialog()
