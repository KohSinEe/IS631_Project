import streamlit as st

from styles.theme import CUSTOM_STYLE
from state.session import init_session_state
from ui.public import render_public_view
from ui.dashboard import render_dashboard, ensure_inventory_loaded


def main() -> None:
    st.set_page_config(page_title="Smart Pantry Dashboard", page_icon="🥕", layout="wide")
    st.markdown(CUSTOM_STYLE, unsafe_allow_html=True)
    init_session_state()

    if st.session_state.is_authenticated:
        ensure_inventory_loaded()
        render_dashboard()
    else:
        render_public_view()


if __name__ == "__main__":
    main()
