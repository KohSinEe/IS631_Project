import streamlit as st
from services.user import login_user, register_user
from services.client import APIError


@st.dialog("Sign In")
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


def reset_password_form() -> None:
    st.markdown("<h3 style='text-align: center;'>Reset Password</h3>", unsafe_allow_html=True)
    with st.form("reset_pw_form"):
        email = st.text_input("Email", key="reset_email")
        new_password = st.text_input("New Password", type="password", key="reset_new_password")
        confirm_password = st.text_input(
            "Confirm New Password", type="password", key="reset_confirm_password"
        )
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


@st.dialog("Sign Up")
def sign_up_dialog() -> None:
    with st.form("signup_form"):
        reg_email = st.text_input("Email", key="register_email")
        reg_password = st.text_input("Password", type="password", key="register_password")
        reg_password_confirm = st.text_input(
            "Confirm Password", type="password", key="register_password_confirm"
        )
        reg_name = st.text_input("Display name", key="register_name")
        # reg_household = st.text_input("Household name (optional)", key="register_household") -  no longer required
        submitted = st.form_submit_button("Create account")
    if submitted:
        if not reg_email or not reg_password or not reg_password_confirm:
            st.error("Email, password, and confirmation are required")
        elif reg_password != reg_password_confirm:
            st.error("Passwords do not match")
        else:
            try:
                register_user(
                    reg_email, reg_password, reg_password_confirm, reg_name #, reg_household
                )
                st.success("Account created. Please sign in.")
            except APIError as err:
                st.error(err.message)


def render_public_view() -> None:
    if "show_sign_in_form" not in st.session_state:
        st.session_state.show_sign_in_form = False
    if "sign_in_form_data" not in st.session_state:
        st.session_state.sign_in_form_data = {"email": "", "password": ""}

    st.markdown(
        "<div class='landing-hero'>"
        "<h1>🥕 FridgeBuddy</h1>"
        "<p class='landing-tagline'>Stop guessing. Start managing.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        # Only allow one dialog or form at a time
        if st.button("Sign In", key="landing_signin", use_container_width=True):
            st.session_state.show_sign_in_form = True
            st.session_state.show_sign_up_form = False
            st.session_state.show_pw_reset = False
        if st.button("Sign Up", key="landing_signup", use_container_width=True):
            st.session_state.show_sign_up_form = True
            st.session_state.show_sign_in_form = False
            st.session_state.show_pw_reset = False
        if st.button("Forgot Password?", key="landing_forgotpw", use_container_width=True):
            st.session_state.show_pw_reset = True
            st.session_state.show_sign_in_form = False
            st.session_state.show_sign_up_form = False

        # Only show one dialog or form at a time
        if st.session_state.get("show_sign_in_form"):
            sign_in_dialog()
        elif st.session_state.get("show_sign_up_form"):
            sign_up_dialog()
        elif st.session_state.get("show_pw_reset"):
            reset_password_form()
