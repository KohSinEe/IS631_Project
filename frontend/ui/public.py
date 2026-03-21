import streamlit as st
from ui.dialogs import (
    reset_password_dialog,
    sign_in_dialog,
    sign_up_dialog,
    sign_up_verification_form,
)


def render_public_view() -> None:
    if "show_sign_in_form" not in st.session_state:
        st.session_state.show_sign_in_form = False
    if "sign_in_form_data" not in st.session_state:
        st.session_state.sign_in_form_data = {"email": "", "password": ""}

    if st.session_state.get("show_sign_up_verification"):
        sign_up_verification_form()
        return

    st.markdown(
        "<div class='landing-hero'>" "<h1>🥕 FridgeBuddy</h1>" "<p class='landing-tagline'>Stop guessing. Start managing.</p>" "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        if st.button("Sign In", key="landing_signin", use_container_width=True) or st.session_state.active_dialog == "sign_in":
            st.session_state.active_dialog = "sign_in"
            sign_in_dialog()
        if st.button("Sign Up", key="landing_signup", use_container_width=True) or st.session_state.active_dialog == "sign_up":
            st.session_state.active_dialog = "sign_up"
            sign_up_dialog()
        if st.button("Forgot Password?", key="landing_forgotpw", use_container_width=True) or st.session_state.active_dialog == "forget_pw":
            st.session_state.active_dialog = "forget_pw"
            reset_password_dialog()
