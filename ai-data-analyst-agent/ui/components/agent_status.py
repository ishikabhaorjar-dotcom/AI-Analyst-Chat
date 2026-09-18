import streamlit as st


def render_agent_status(steps: list[str]):
    """Renders the agent's step-by-step trace so the app visibly feels like an agent at work."""
    if not steps:
        return
    with st.expander("🤖 Agent activity", expanded=False):
        for step in steps:
            st.markdown(f'<div class="agent-step">{step}</div>', unsafe_allow_html=True)
