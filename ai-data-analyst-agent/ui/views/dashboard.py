import streamlit as st

from config import settings
from src.core.loader import load_dataset
from src.core.profiler import profile_dataset
from src.tools.eda_tool import run_automated_eda
from ui.components.metrics import render_insight_card, render_overview_metrics


def _handle_upload(uploaded_file):
    raw_bytes = uploaded_file.getvalue()
    result = load_dataset(uploaded_file.name, raw_bytes)

    if not result.success and result.error == "MULTIPLE_SHEETS":
        st.warning("This Excel file has multiple sheets. Choose one:")
        sheet = st.selectbox("Sheet", result.sheet_names, key="sheet_picker")
        if st.button("Load selected sheet"):
            result = load_dataset(uploaded_file.name, raw_bytes, sheet_name=sheet)
        else:
            return

    if not result.success:
        st.error(result.error)
        return

    st.session_state.dataset = result.df
    st.session_state.dataset_name = uploaded_file.name
    st.session_state.profile = profile_dataset(result.df)
    st.session_state.eda = run_automated_eda(result.df, st.session_state.profile)
    st.session_state.messages = []
    st.success(f"Loaded **{uploaded_file.name}** — {result.df.shape[0]:,} rows × {result.df.shape[1]} columns")
    st.rerun()


def render():
    st.markdown(
        f"""<div class="app-hero">
                <h1>🤖 {settings.APP_TITLE}</h1>
                <p>{settings.APP_TAGLINE}</p>
            </div>""",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        _handle_upload(uploaded_file)

    if st.session_state.dataset is None:
        st.info("👆 Upload a dataset to get started, or try the bundled sample below.")
        if st.button("Load sample sales dataset"):
            sample_path = settings.SAMPLE_DIR / "sample_sales.csv"
            with open(sample_path, "rb") as f:
                raw = f.read()
            result = load_dataset("sample_sales.csv", raw)
            st.session_state.dataset = result.df
            st.session_state.dataset_name = "sample_sales.csv"
            st.session_state.profile = profile_dataset(result.df)
            st.session_state.eda = run_automated_eda(result.df, st.session_state.profile)
            st.rerun()
        return

    profile = st.session_state.profile
    eda = st.session_state.eda

    st.subheader("Dataset Overview")
    render_overview_metrics(profile)

    st.subheader("AI Generated Insights")
    shown = 0
    if eda.top_correlated_pairs:
        a, b, v = eda.top_correlated_pairs[0]
        direction = "positive" if v > 0 else "negative"
        render_insight_card(
            f"**{a}** and **{b}** show a strong {direction} relationship (correlation {v:+.2f}).",
            "positive" if abs(v) > 0.5 else "info",
        )
        shown += 1
    if eda.outlier_summary:
        top_col = max(eda.outlier_summary, key=eda.outlier_summary.get)
        render_insight_card(
            f"**{eda.outlier_summary[top_col]} unusual values** detected in **{top_col}** — worth a closer look.",
            "warning",
        )
        shown += 1
    if profile.duplicate_rows > 0:
        render_insight_card(f"**{profile.duplicate_rows} duplicate rows** were found in this dataset.", "warning")
        shown += 1
    if eda.missing_by_column:
        worst = max(eda.missing_by_column, key=eda.missing_by_column.get)
        render_insight_card(
            f"**{worst}** has the highest missing-value rate at **{eda.missing_by_column[worst]}%**.", "warning",
        )
        shown += 1
    if shown == 0:
        render_insight_card("Dataset looks clean — no major data quality issues detected.", "positive")

    st.divider()
    st.caption("Use the sidebar to explore the dataset profile, run automated analysis, or ask questions directly.")
