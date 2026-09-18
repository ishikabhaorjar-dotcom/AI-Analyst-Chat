"""
Rule-based automated EDA. Deliberately NOT LLM-driven for the calculations
themselves — an LLM deciding which columns to correlate is unnecessary risk
and latency when plain pandas heuristics do it deterministically. The LLM is
reserved for interpreting these results in eda's insight step, not computing them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config import settings
from src.core.profiler import DatasetProfile


@dataclass
class EDAResult:
    correlations: pd.DataFrame | None = None
    top_correlated_pairs: list[tuple[str, str, float]] = field(default_factory=list)
    outlier_summary: dict[str, int] = field(default_factory=dict)
    missing_by_column: dict[str, float] = field(default_factory=dict)
    category_distributions: dict[str, pd.Series] = field(default_factory=dict)
    numeric_summary: pd.DataFrame | None = None
    time_trend: pd.DataFrame | None = None


def run_automated_eda(df: pd.DataFrame, profile: DatasetProfile) -> EDAResult:
    result = EDAResult()

    # Missing values by column (only columns that actually have any)
    result.missing_by_column = {
        c: round(p.missing_pct, 2) for c, p in profile.columns.items() if p.missing_count > 0
    }

    # Correlation analysis — needs at least 2 numeric columns
    if len(profile.numerical_cols) >= 2:
        corr = df[profile.numerical_cols].corr(numeric_only=True)
        result.correlations = corr
        pairs = []
        cols = corr.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr.iloc[i, j]
                if pd.notna(val):
                    pairs.append((cols[i], cols[j], round(float(val), 3)))
        pairs.sort(key=lambda p: abs(p[2]), reverse=True)
        result.top_correlated_pairs = pairs[:5]

    # Outlier detection via z-score, per numeric column
    for col in profile.numerical_cols:
        series = df[col].dropna()
        if len(series) < 10 or series.std(ddof=0) == 0:
            continue
        z = (series - series.mean()) / series.std(ddof=0)
        n_outliers = int((z.abs() > settings.OUTLIER_Z_THRESHOLD).sum())
        if n_outliers > 0:
            result.outlier_summary[col] = n_outliers

    # Category distributions for low-cardinality categorical columns
    for col in profile.categorical_cols:
        nunique = df[col].nunique(dropna=True)
        if 0 < nunique <= settings.HIGH_CARDINALITY_THRESHOLD:
            result.category_distributions[col] = df[col].value_counts().head(10)

    # Descriptive stats for numeric columns
    if profile.numerical_cols:
        result.numeric_summary = df[profile.numerical_cols].describe().T

    # Simple time trend if a date column and at least one numeric column exist
    if profile.date_cols and profile.numerical_cols:
        date_col = profile.date_cols[0]
        metric_col = profile.numerical_cols[0]
        try:
            temp = df[[date_col, metric_col]].copy()
            temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
            temp = temp.dropna(subset=[date_col])
            if not temp.empty:
                trend = temp.set_index(date_col).resample("ME")[metric_col].sum().reset_index()
                result.time_trend = trend
        except Exception:
            pass  # trend is a bonus, not critical — fail silently rather than break EDA

    return result
