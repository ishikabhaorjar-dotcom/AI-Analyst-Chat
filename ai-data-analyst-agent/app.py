import streamlit as st

from config import settings
from ui.components.sidebar import render_sidebar
from ui.views import analysis, ask, dashboard, profile, reports

st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css():
    css_path = settings.BASE_DIR / "ui" / "styles" / "custom.css"
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def init_session_state():
    defaults = {
        "dataset": None,
        "dataset_name": None,
        "profile": None,
        "eda": None,
        "messages": [],
        "view": "Dashboard",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def main():
    init_session_state()
    load_css()
    render_sidebar()

    view = st.session_state.view
    if view == "Dashboard":
        dashboard.render()
    elif view == "Dataset Profile":
        profile.render()
    elif view == "AI Analysis":
        analysis.render()
    elif view == "Ask Your Data":
        ask.render()
    elif view == "Reports":
        reports.render()


if __name__ == "__main__":
    main()
