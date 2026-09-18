import pandas as pd
import streamlit as st

from ui.components.metrics import render_overview_metrics


def render():
    if st.session_state.dataset is None:
        st.warning("Upload a dataset from the Dashboard first.")
        return

    df = st.session_state.dataset
    profile = st.session_state.profile

    st.subheader("Dataset Profile")
    render_overview_metrics(profile)

    st.markdown("#### Column Details")
    rows = []
    for name, col in profile.columns.items():
        rows.append({
            "Column": name,
            "Type": col.dtype,
            "Role": col.role,
            "Missing %": round(col.missing_pct, 2),
            "Unique Values": col.unique_count,
            "Sample": ", ".join(col.sample_values[:3]),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("#### Column Groups")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Numerical", len(profile.numerical_cols))
    c2.metric("Categorical", len(profile.categorical_cols))
    c3.metric("Date", len(profile.date_cols))
    c4.metric("Identifier", len(profile.identifier_cols))

    st.markdown("#### Raw Data Preview")
    st.dataframe(df.head(50), use_container_width=True)
