"""
The state object passed between every LangGraph node. Each node reads what
it needs and writes its own piece back — nothing is mutated implicitly, so
the trace of `status_log` doubles as a readable record of what the agent did.
"""
from __future__ import annotations

from typing import Any, Optional, TypedDict

import pandas as pd

from src.core.profiler import DatasetProfile


class AgentState(TypedDict, total=False):
    question: str
    df: pd.DataFrame
    profile: DatasetProfile

    analysis_type: str
    relevant_columns: list[str]

    pandas_code: Optional[str]
    raw_result: Any
    raw_result_type: Optional[str]
    execution_error: Optional[str]

    chart_spec: Optional[dict]

    final_answer: str
    insights: list[str]
    confidence: str

    status_log: list[str]   # human-readable trace, shown in the UI as "agent status"
