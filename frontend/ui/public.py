import streamlit as st
from ui.dialogs import reset_password_dialog
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
        confirmation_code = st.text_input(
            "Verification Code (from email)", key="reset_confirmation_code"
        )
        new_password = st.text_input("New Password", type="password", key="reset_new_password")
        confirm_password = st.text_input(
            "Confirm New Password", type="password", key="reset_confirm_password"
        )
        send_code = st.form_submit_button("Send Verification Code")
        submitted = st.form_submit_button("Reset Password")

    if send_code:
        if not email:
            st.error("Email is required")
        else:
            try:
                from services.user import request_password_reset

                local_fallback_password = None
                if new_password and confirm_password and new_password == confirm_password:
                    local_fallback_password = new_password

                request_password_reset(email, local_fallback_password)
                if local_fallback_password:
                    st.success("Password reset successful. Please sign in.")
                else:
                    st.success("Verification code sent. Check your email.")
            except APIError as err:
                st.error(err.message)

    if submitted:
        if not email or not confirmation_code or not new_password or not confirm_password:
            st.error("All fields are required")
        elif new_password != confirm_password:
            st.error("Passwords do not match")
        else:
            try:
                from services.user import confirm_password_reset

                confirm_password_reset(email, confirmation_code, new_password)
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
        reg_household = st.text_input("Household name (optional)", key="register_household")
        submitted = st.form_submit_button("Create account")
    if submitted:
        if not reg_email or not reg_password or not reg_password_confirm:
            st.error("Email, password, and confirmation are required")
        elif reg_password != reg_password_confirm:
            st.error("Passwords do not match")
        else:
            try:
                register_user(
                    reg_email, reg_password, reg_password_confirm, reg_name, reg_household
                )
                st.session_state.verification_email = reg_email
                st.session_state.show_sign_up_form = False
                st.session_state.show_sign_up_verification = True
                st.rerun()
            except APIError as err:
                st.error(err.message)


@st.dialog("Verify Account")
def sign_up_verification_form() -> None:
    st.markdown("<h3 style='text-align: center;'>Verify Account</h3>", unsafe_allow_html=True)
    email = st.session_state.get("verification_email") or st.session_state.get("register_email", "")
    with st.form("verify_signup_form"):
        st.text_input("Email", value=email, key="verification_email", disabled=bool(email))
        code = st.text_input("Verification Code", key="verification_code")
        resend = st.form_submit_button("Resend Code")
        verify = st.form_submit_button("Verify Account")

    if resend:
        if not email:
            st.error("Email is required")
        else:
            try:
                from services.user import resend_signup_code

                resend_signup_code(email)
                st.success("Verification code sent.")
            except APIError as err:
                # Local mode does not require verification.
                if err.status_code == 400:
                    st.session_state.active_dialog = None
                    st.session_state.show_sign_up_verification = False
                    st.success("Account created. Please sign in.")
                    st.rerun()
                else:
                    st.error(err.message)

    if verify:
        if not email or not code:
            st.error("Email and verification code are required")
        else:
            try:
                from services.user import confirm_signup

                confirm_signup(email, code)
                st.session_state.active_dialog = None
                st.session_state.show_sign_up_verification = False
                st.success("Account verified. Please sign in.")
                st.rerun()
            except APIError as err:
                if err.status_code == 400:
                    st.session_state.active_dialog = None
                    st.session_state.show_sign_up_verification = False
                    st.success("Account created. Please sign in.")
                    st.rerun()
                else:
                    st.error(err.message)


def render_public_view() -> None:
    if "show_sign_in_form" not in st.session_state:
        st.session_state.show_sign_in_form = False
    if "sign_in_form_data" not in st.session_state:
        st.session_state.sign_in_form_data = {"email": "", "password": ""}

    # Show verification dialog immediately after signup
    if st.session_state.get("show_sign_up_verification"):
        sign_up_verification_form()
        return

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
        if (
            st.button("Sign In", key="landing_signin", use_container_width=True)
            or st.session_state.active_dialog == "sign_in"
        ):
            st.session_state.active_dialog = "sign_in"
            sign_in_dialog()
        if (
            st.button("Sign Up", key="landing_signup", use_container_width=True)
            or st.session_state.active_dialog == "sign_up"
        ):
            st.session_state.active_dialog = "sign_up"
            sign_up_dialog()
        if (
            st.button("Forgot Password?", key="landing_forgotpw", use_container_width=True)
            or st.session_state.active_dialog == "forget_pw"
        ):
            st.session_state.active_dialog = "forget_pw"
            reset_password_dialog()
