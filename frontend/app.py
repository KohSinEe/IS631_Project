import os

import streamlit as st
from dotenv import load_dotenv
from state.session import init_session_state, reset_dashboard_filters
from styles.theme import CUSTOM_STYLE
from ui.dashboard import ensure_inventory_loaded, render_dashboard
from ui.household_setup import render_household_setup
from ui.public import render_public_view
from ui.recipe import handle_generate_recipe
from ui.stocktake import render_stocktake
from ui.usage import render_usage_overview
from utils.inventory import show_expiry_notifications

# load environment variables from project root.
# prefer a real .env file, but fall back to the example if that's all the user has
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
env_path = os.path.join(root, ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(root, ".env.example")
load_dotenv(env_path)


def main() -> None:
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    if "active_dialog" not in st.session_state:
        st.session_state.active_dialog = None

    st.set_page_config(page_title="Smart Pantry Dashboard", page_icon="🥕", layout="wide")
    st.markdown(CUSTOM_STYLE, unsafe_allow_html=True)
    init_session_state()

    if st.session_state.is_authenticated:
        if not st.session_state.household_id:
            render_household_setup()
        else:
            ensure_inventory_loaded()
            show_expiry_notifications(st.session_state.inventory)

            if st.session_state.page == "dashboard":
                reset_dashboard_filters()
                render_dashboard()
            elif st.session_state.page == "recipe":
                handle_generate_recipe()
            elif st.session_state.page == "stocktake":
                render_stocktake()
            elif st.session_state.page == "usage":
                render_usage_overview()
    else:
        render_public_view()


if __name__ == "__main__":
    main()
