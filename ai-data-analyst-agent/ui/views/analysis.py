import streamlit as st

from src.tools import viz_tool


def render():
    if st.session_state.dataset is None:
        st.warning("Upload a dataset from the Dashboard first.")
        return

    df = st.session_state.dataset
    profile = st.session_state.profile
    eda = st.session_state.eda

    st.subheader("Automated Exploratory Analysis")

    if eda.correlations is not None:
        st.markdown("#### Correlation Analysis")
        fig = viz_tool.correlation_heatmap(eda.correlations)
        st.plotly_chart(fig, use_container_width=True)
        if eda.top_correlated_pairs:
            with st.expander("Strongest relationships"):
                for a, b, v in eda.top_correlated_pairs:
                    st.write(f"**{a}** ↔ **{b}**: {v:+.2f}")
    else:
        st.caption("Correlation analysis needs at least two numerical columns.")

    if profile.numerical_cols:
        st.markdown("#### Distributions")
        col = st.selectbox("Numerical column", profile.numerical_cols, key="dist_col")
        st.plotly_chart(viz_tool.distribution_chart(df, col), use_container_width=True)

    if eda.category_distributions:
        st.markdown("#### Category Breakdown")
        cat_col = st.selectbox("Categorical column", list(eda.category_distributions.keys()), key="cat_col")
        st.plotly_chart(
            viz_tool.category_bar_chart(eda.category_distributions[cat_col], f"Top values — {cat_col}"),
            use_container_width=True,
        )

    if eda.time_trend is not None:
        st.markdown("#### Trend Over Time")
        trend = eda.time_trend
        date_col, value_col = trend.columns[0], trend.columns[1]
        st.plotly_chart(
            viz_tool.trend_line_chart(trend, date_col, value_col, f"{value_col} over time"),
            use_container_width=True,
        )

    if eda.numeric_summary is not None:
        st.markdown("#### Descriptive Statistics")
        st.dataframe(eda.numeric_summary.round(2), use_container_width=True)

    if eda.outlier_summary:
        st.markdown("#### Outlier Summary")
        for col, count in eda.outlier_summary.items():
            st.write(f"⚠️ **{col}**: {count} potential outliers (|z-score| > 3)")
