"""
Run with: pytest tests/
These tests cover the deterministic, non-LLM parts of the pipeline —
profiling and the execution sandbox — since those can and should be
verified without hitting the Groq API.
"""
import pandas as pd
import pytest

from src.core.executor import execute_analysis_code
from src.core.loader import load_dataset, validate_file
from src.core.profiler import profile_dataset


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "id": range(1, 21),
        "region": ["North", "South"] * 10,
        "revenue": [100.0 + i for i in range(20)],
        "order_date": pd.date_range("2025-01-01", periods=20, freq="D"),
    })


def test_validate_file_rejects_bad_extension():
    assert validate_file("data.txt", 1000) is not None


def test_validate_file_accepts_csv():
    assert validate_file("data.csv", 1000) is None


def test_load_dataset_csv_roundtrip():
    raw = b"a,b\n1,2\n3,4\n"
    result = load_dataset("sample.csv", raw)
    assert result.success
    assert result.df.shape == (2, 2)


def test_profile_dataset_classifies_columns(sample_df):
    profile = profile_dataset(sample_df)
    assert "revenue" in profile.numerical_cols
    assert "region" in profile.categorical_cols
    assert "order_date" in profile.date_cols
    assert profile.n_rows == 20


def test_executor_runs_simple_code(sample_df):
    result = execute_analysis_code("result = df['revenue'].sum()", sample_df)
    assert result.success
    assert result.result == sample_df["revenue"].sum()


def test_executor_blocks_import(sample_df):
    result = execute_analysis_code("import os\nresult = 1", sample_df)
    assert not result.success


def test_executor_blocks_forbidden_name(sample_df):
    result = execute_analysis_code("result = open('x.txt')", sample_df)
    assert not result.success


def test_executor_requires_result_variable(sample_df):
    result = execute_analysis_code("x = 1 + 1", sample_df)
    assert not result.success
