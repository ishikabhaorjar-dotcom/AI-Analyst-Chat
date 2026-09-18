import streamlit as st

from src.utils.helpers import format_number


def render_metric_card(label: str, value: str):
    st.markdown(
        f"""<div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def render_overview_metrics(profile):
    cols = st.columns(4)
    with cols[0]:
        render_metric_card("Rows", format_number(profile.n_rows))
    with cols[1]:
        render_metric_card("Columns", str(profile.n_cols))
    with cols[2]:
        render_metric_card("Missing", f"{profile.missing_total_pct:.1f}%")
    with cols[3]:
        render_metric_card("Duplicates", str(profile.duplicate_rows))


def render_insight_card(text: str, severity: str = "info"):
    icon = {"info": "📊", "positive": "📈", "warning": "⚠️"}.get(severity, "📊")
    st.markdown(
        f"""<div class="insight-card {severity if severity != 'info' else ''}">
                {icon} {text}
            </div>""",
        unsafe_allow_html=True,
    )
