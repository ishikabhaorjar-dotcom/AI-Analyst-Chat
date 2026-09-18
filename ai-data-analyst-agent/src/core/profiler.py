"""
Builds a structured profile of a DataFrame: shape, missingness, dtypes,
column classification, and candidate target/date columns.

This runs once per upload and its output is cached in session state — every
other agent (planner, EDA, insight) reads this profile instead of
re-inspecting the raw DataFrame, so the "understanding" step happens exactly
once and stays consistent across the whole session.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config import settings


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    role: str                  # "numerical" | "categorical" | "date" | "identifier" | "text"
    missing_count: int
    missing_pct: float
    unique_count: int
    sample_values: list


@dataclass
class DatasetProfile:
    n_rows: int
    n_cols: int
    memory_mb: float
    duplicate_rows: int
    missing_total_pct: float
    numerical_cols: list[str]
    categorical_cols: list[str]
    date_cols: list[str]
    identifier_cols: list[str]
    columns: dict[str, ColumnProfile]
    candidate_targets: list[str] = field(default_factory=list)

    def to_summary_dict(self) -> dict:
        """Compact dict safe to hand to an LLM as context — no raw data, just shape."""
        return {
            "rows": self.n_rows,
            "columns": self.n_cols,
            "duplicate_rows": self.duplicate_rows,
            "missing_pct_overall": round(self.missing_total_pct, 2),
            "numerical_columns": self.numerical_cols,
            "categorical_columns": self.categorical_cols,
            "date_columns": self.date_cols,
            "column_details": {
                name: {
                    "dtype": c.dtype,
                    "role": c.role,
                    "missing_pct": round(c.missing_pct, 2),
                    "unique_count": c.unique_count,
                    "sample_values": c.sample_values,
                }
                for name, c in self.columns.items()
            },
        }


def _detect_role(series: pd.Series, name: str) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"

    # Try to detect date-like strings by column name + parseability, cheaply.
    if series.dtype == object and any(k in name.lower() for k in ("date", "time", "timestamp", "created", "updated")):
        try:
            parsed = pd.to_datetime(series.dropna().head(20), errors="raise")
            if len(parsed) > 0:
                return "date"
        except Exception:
            pass

    if pd.api.types.is_numeric_dtype(series):
        # A numeric column that is actually an identifier (near-unique, no repeats)
        if series.nunique(dropna=True) >= 0.95 * len(series) and len(series) > 20:
            if name.lower() in ("id", "index") or name.lower().endswith(("_id", "id")):
                return "identifier"
        return "numerical"

    if name.lower() in ("id", "index") or name.lower().endswith(("_id", "id")):
        return "identifier"

    return "categorical"


def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    n_rows, n_cols = df.shape
    memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    duplicate_rows = int(df.duplicated().sum())
    missing_total_pct = float(df.isna().mean().mean() * 100)

    columns: dict[str, ColumnProfile] = {}
    numerical, categorical, date_cols, identifiers = [], [], [], []

    for col in df.columns:
        series = df[col]
        role = _detect_role(series, col)
        missing_count = int(series.isna().sum())
        sample = series.dropna().unique()[:5]

        columns[col] = ColumnProfile(
            name=col,
            dtype=str(series.dtype),
            role=role,
            missing_count=missing_count,
            missing_pct=(missing_count / n_rows * 100) if n_rows else 0.0,
            unique_count=int(series.nunique(dropna=True)),
            sample_values=[str(v) for v in sample],
        )

        if role == "numerical":
            numerical.append(col)
        elif role == "categorical":
            categorical.append(col)
        elif role == "date":
            date_cols.append(col)
        elif role == "identifier":
            identifiers.append(col)

    # Candidate targets: numeric columns that aren't identifiers and aren't
    # near-constant — a cheap heuristic, not a claim of statistical significance.
    candidate_targets = [
        c for c in numerical
        if df[c].nunique(dropna=True) > 1 and "id" not in c.lower()
    ][:5]

    return DatasetProfile(
        n_rows=n_rows,
        n_cols=n_cols,
        memory_mb=round(memory_mb, 3),
        duplicate_rows=duplicate_rows,
        missing_total_pct=missing_total_pct,
        numerical_cols=numerical,
        categorical_cols=categorical,
        date_cols=date_cols,
        identifier_cols=identifiers,
        columns=columns,
        candidate_targets=candidate_targets,
    )
