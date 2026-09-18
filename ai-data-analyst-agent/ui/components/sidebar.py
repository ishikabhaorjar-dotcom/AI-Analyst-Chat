import streamlit as st

NAV_ITEMS = [
    ("Dashboard", "🏠"),
    ("Dataset Profile", "🧬"),
    ("AI Analysis", "🔬"),
    ("Ask Your Data", "💬"),
    ("Reports", "📄"),
]


def render_sidebar():
    with st.sidebar:
        st.markdown("### 📊 AI Data Analyst")
        st.caption("Agentic analytics, built with LangGraph")
        st.divider()

        for label, icon in NAV_ITEMS:
            is_active = st.session_state.view == label
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True,
                        type="primary" if is_active else "secondary"):
                st.session_state.view = label
                st.rerun()

        st.divider()
        if st.session_state.get("dataset") is not None:
            st.success(f"Dataset loaded: {st.session_state.get('dataset_name', 'file')}")
        else:
            st.info("No dataset loaded yet.")

        st.divider()
        st.caption("Built with Groq · LangGraph · Pydantic · Streamlit")
