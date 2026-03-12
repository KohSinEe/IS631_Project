"""Household setup landing page - shown after login if user has no household."""

import streamlit as st
from services.user import create_household, logout_user
from services.invitations import fetch_my_invitations, accept_invitation, decline_invitation
from services.client import APIError


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

@st.dialog("You have a fridge invitation!")
def _invitation_popup(invites: list) -> None:
    inv = invites[0]
    role_label = "Co-owner" if inv.get("role") == "co_owner" else "Child"
    fridge_name = inv.get("household_name") or "a fridge"
    st.info(f"You've been invited to join **{fridge_name}** as **{role_label}**.")
    if len(invites) > 1:
        st.caption(f"You have {len(invites)} pending invitation(s) total.")
    if st.button("OK", type="primary", use_container_width=True):
        st.session_state.invitation_popup_dismissed = True
        st.rerun()


@st.dialog("Sign out")
def _logout_dialog() -> None:
    st.write("Are you sure you want to sign out?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes", use_container_width=True):
            logout_user()
            st.rerun()
    with col2:
        if st.button("No", type="secondary", use_container_width=True):
            st.session_state.show_household_logout_dialog = False
            st.rerun()


def _render_pending_invitations(invitations: list) -> None:
    st.subheader("📬 Pending Invitations")

    if not invitations:
        st.info("You have no pending invitations right now.")
        return

    st.write("You've been invited to join a household. Accept one to skip creating your own.")

    for inv in invitations:
        household_name = inv.get("household_name") or f"Household #{inv.get('household_id')}"
        inviter = inv.get("inviter_name") or inv.get("inviter_email") or "Someone"
        role = inv.get("role", "member").replace("_", " ").title()
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

    if not pending:
        st.session_state.invitation_popup_dismissed = False
    if "invitation_popup_dismissed" not in st.session_state:
        st.session_state.invitation_popup_dismissed = False

    if pending and not st.session_state.invitation_popup_dismissed:
        _invitation_popup(pending)

    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        _render_create_household()
        st.divider()
        _render_pending_invitations(pending)
        st.divider()
        if st.button("Sign out", use_container_width=True):
            st.session_state.show_household_logout_dialog = True
        if st.session_state.get("show_household_logout_dialog"):
            _logout_dialog()