import streamlit as st

from styles.theme import CUSTOM_STYLE
from state.session import init_session_state
from ui.public import render_public_view
from ui.dashboard import render_dashboard, ensure_inventory_loaded
from ui.recipe import handle_generate_recipe


def main() -> None:
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"

    st.set_page_config(page_title="Smart Pantry Dashboard", page_icon="🥕", layout="wide")
    st.markdown(CUSTOM_STYLE, unsafe_allow_html=True)
    init_session_state()

    if st.session_state.is_authenticated:
        if st.session_state.page == "dashboard":
            st.session_state.category_filter = "All"
            ensure_inventory_loaded()
            render_dashboard()
        elif st.session_state.page == "recipe":
            handle_generate_recipe()
    else:
        render_public_view()


if __name__ == "__main__":
    main()
