import pandas as pd
import streamlit as st

from config import settings
from src.agents.graph import run_agent
from ui.components.agent_status import render_agent_status

SUGGESTED_QUESTIONS = [
    "Give me three important insights from this dataset",
    "Which column has the most missing values?",
    "Show me a summary of the numerical columns",
]


def render():
    if st.session_state.dataset is None:
        st.warning("Upload a dataset from the Dashboard first.")
        return

    if not settings.GROQ_API_KEY:
        st.error("GROQ_API_KEY is not set. Add it to your .env file to enable the AI agent.")
        return

    st.subheader("Ask Your Data")

    cols = st.columns(len(SUGGESTED_QUESTIONS))
    for i, q in enumerate(SUGGESTED_QUESTIONS):
        if cols[i].button(q, key=f"suggested_{i}", use_container_width=True):
            st.session_state.pending_question = q

    question = st.chat_input("Ask anything about your dataset...")
    if st.session_state.get("pending_question"):
        question = st.session_state.pop("pending_question")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner("Agent is analyzing your data..."):
            try:
                result_state = run_agent(question, st.session_state.dataset, st.session_state.profile)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result_state.get("final_answer", "I couldn't produce an answer."),
                    "status_log": result_state.get("status_log", []),
                    "raw_result": result_state.get("raw_result"),
                    "raw_result_type": result_state.get("raw_result_type"),
                    "pandas_code": result_state.get("pandas_code"),
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Something went wrong while analyzing this: {e}",
                    "status_log": [],
                })

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="qa-question">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="qa-answer">{msg["content"]}</div>', unsafe_allow_html=True)

            raw = msg.get("raw_result")
            if isinstance(raw, pd.DataFrame):
                st.dataframe(raw.head(20), use_container_width=True)
            elif isinstance(raw, pd.Series):
                st.dataframe(raw.head(20), use_container_width=True)

            if msg.get("pandas_code"):
                with st.expander("View generated code"):
                    st.code(msg["pandas_code"], language="python")

            render_agent_status(msg.get("status_log", []))
            st.divider()
