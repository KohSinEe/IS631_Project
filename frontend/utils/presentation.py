import ast
from html import escape
from typing import Any, Mapping, Optional

import streamlit as st
from config.settings import INVITATION_STATUS_DISPLAY, ROLE_DISPLAY_NAMES


def format_role(role: Optional[str]) -> str:
    if not role:
        return "Unknown"
    return ROLE_DISPLAY_NAMES.get(role, role.replace("_", " ").title())


def format_invitation_status(status: Optional[str]) -> str:
    if not status:
        return "Unknown"
    return INVITATION_STATUS_DISPLAY.get(status, status.replace("_", " ").title())


def get_error_message(err: Exception) -> str:
    return str(getattr(err, "message", str(err)))


def parse_signup_error(err: Exception) -> str:
    err_msg = []
    err = ast.literal_eval(err.message)
    for e in err:
        type = e["loc"][-1].title()
        msg = e["msg"].split(":")[-1].strip()
        if type != "Password_Confirm":
            err_msg.append(f"{type}: {msg}")
    return err_msg


def user_display_name(user: Optional[Mapping[str, Any]], fallback: str = "there") -> str:
    if not user:
        return fallback
    name = user.get("name") if isinstance(user, Mapping) else None
    email = user.get("email") if isinstance(user, Mapping) else None
    return str(name or email or fallback)


def render_allergen_badges(allergens: list[str]) -> None:
    if not allergens:
        st.caption("None set")
        return
    badge_style = "background:#FF4B4B22; color:#FF4B4B; border:1px solid #FF4B4B55;" "padding:2px 10px; border-radius:999px; font-size:0.85rem;"
    badges = " ".join(f'<span style="{badge_style}">{escape(str(a))}</span>' for a in allergens)
    st.markdown(badges, unsafe_allow_html=True)


def safe_html_text(value: str) -> str:
    return escape(value)
