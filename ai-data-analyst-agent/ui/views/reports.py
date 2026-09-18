import streamlit as st

from src.reports.generator import generate_pdf_report


def _default_recommendations(profile, eda) -> list[str]:
    recs = []
    if profile.duplicate_rows > 0:
        recs.append(f"Investigate and remove {profile.duplicate_rows} duplicate records before further analysis.")
    if eda.missing_by_column:
        worst = max(eda.missing_by_column, key=eda.missing_by_column.get)
        recs.append(f"Address missing data in '{worst}' ({eda.missing_by_column[worst]}%) — consider imputation or exclusion.")
    if eda.outlier_summary:
        col = max(eda.outlier_summary, key=eda.outlier_summary.get)
        recs.append(f"Review outliers in '{col}' to confirm they are valid data points, not entry errors.")
    if eda.top_correlated_pairs:
        a, b, _ = eda.top_correlated_pairs[0]
        recs.append(f"Explore the relationship between '{a}' and '{b}' further for potential business drivers.")
    if not recs:
        recs.append("Dataset quality is strong — proceed to deeper modeling or segmentation analysis.")
    return recs


def render():
    if st.session_state.dataset is None:
        st.warning("Upload a dataset from the Dashboard first.")
        return

    st.subheader("AI-Generated Report")
    st.caption("Compiles the dataset profile, automated EDA, and any insights from your Q&A session into a PDF.")

    profile = st.session_state.profile
    eda = st.session_state.eda

    insights_from_chat = [
        m["content"] for m in st.session_state.get("messages", []) if m["role"] == "assistant"
    ]

    recommendations = _default_recommendations(profile, eda)

    with st.expander("Preview recommendations included in the report"):
        for r in recommendations:
            st.write(f"• {r}")

    if st.button("📄 Generate AI Report", type="primary"):
        with st.spinner("Compiling report..."):
            pdf_bytes = generate_pdf_report(
                profile=profile,
                eda=eda,
                insights=insights_from_chat,
                recommendations=recommendations,
                dataset_name=st.session_state.get("dataset_name", "dataset"),
            )
        st.success("Report ready.")
        st.download_button(
            "⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name=f"{st.session_state.get('dataset_name', 'dataset').split('.')[0]}_analysis_report.pdf",
            mime="application/pdf",
        )
