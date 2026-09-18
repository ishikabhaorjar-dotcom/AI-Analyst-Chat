"""
Turns a ChartSpec (chosen by the LLM or by eda_tool heuristics) into an
actual interactive Plotly figure. Kept separate from chart *selection* logic
so the rendering code stays simple and testable on its own.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.schemas.models import ChartSpec

TEMPLATE = "plotly_white"


def build_chart(df: pd.DataFrame, spec: ChartSpec) -> Optional[go.Figure]:
    try:
        if spec.chart_type == "bar":
            fig = px.bar(df, x=spec.x_column, y=spec.y_column, color=spec.color_column,
                        title=spec.title, template=TEMPLATE)
        elif spec.chart_type == "line":
            fig = px.line(df, x=spec.x_column, y=spec.y_column, color=spec.color_column,
                         title=spec.title, template=TEMPLATE, markers=True)
        elif spec.chart_type == "scatter":
            fig = px.scatter(df, x=spec.x_column, y=spec.y_column, color=spec.color_column,
                             title=spec.title, template=TEMPLATE)
        elif spec.chart_type == "histogram":
            fig = px.histogram(df, x=spec.x_column, color=spec.color_column,
                               title=spec.title, template=TEMPLATE)
        elif spec.chart_type == "box":
            fig = px.box(df, x=spec.x_column, y=spec.y_column, color=spec.color_column,
                        title=spec.title, template=TEMPLATE)
        elif spec.chart_type == "pie":
            fig = px.pie(df, names=spec.x_column, values=spec.y_column,
                        title=spec.title, template=TEMPLATE)
        elif spec.chart_type == "heatmap":
            fig = px.imshow(df, text_auto=".2f", title=spec.title, template=TEMPLATE,
                           color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
        else:
            return None

        fig.update_layout(
            margin=dict(l=10, r=10, t=50, b=10),
            font=dict(family="Inter, sans-serif", size=13),
            title_font_size=16,
        )
        return fig
    except Exception:
        return None


def correlation_heatmap(corr_df: pd.DataFrame, title: str = "Correlation Heatmap") -> go.Figure:
    fig = px.imshow(corr_df, text_auto=".2f", title=title, template=TEMPLATE,
                    color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    return fig


def distribution_chart(df: pd.DataFrame, column: str) -> go.Figure:
    fig = px.histogram(df, x=column, title=f"Distribution of {column}", template=TEMPLATE,
                       marginal="box")
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    return fig


def category_bar_chart(series: pd.Series, title: str) -> go.Figure:
    fig = px.bar(x=series.index.astype(str), y=series.values, title=title, template=TEMPLATE,
                labels={"x": series.index.name or "Category", "y": "Count"})
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    return fig


def trend_line_chart(trend_df: pd.DataFrame, date_col: str, value_col: str, title: str) -> go.Figure:
    fig = px.line(trend_df, x=date_col, y=value_col, title=title, template=TEMPLATE, markers=True)
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    return fig
