"""
The bridge between "what the user asked" and "an actual number".

Flow: question + dataset profile -> LLM proposes pandas code (PandasCodePlan)
-> executor runs it in the sandbox -> raw result comes back as data, never
as text the LLM was allowed to make up.
"""
from __future__ import annotations

import json

import pandas as pd

from src.core.executor import ExecutionResult, execute_analysis_code
from src.core.profiler import DatasetProfile
from src.llm.client import generate_structured
from src.llm.prompts import PANDAS_CODE_SYSTEM
from src.schemas.models import PandasCodePlan


def answer_with_pandas(question: str, df: pd.DataFrame, profile: DatasetProfile) -> ExecutionResult:
    context = json.dumps(profile.to_summary_dict(), indent=2)
    user_prompt = (
        f"Dataset profile:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Write the pandas code that computes the answer."
    )

    plan = generate_structured(PANDAS_CODE_SYSTEM, user_prompt, PandasCodePlan)
    result = execute_analysis_code(plan.code, df)

    # One repair attempt: if the sandboxed run failed, show the LLM the error
    # and its own code, and ask for a corrected version. This mirrors how a
    # human analyst would debug, and meaningfully lowers the failure rate on
    # slightly-off column names or type mismatches.
    if not result.success:
        repair_prompt = (
            f"{user_prompt}\n\n"
            f"Your previous code:\n{plan.code}\n\n"
            f"It failed with this error:\n{result.error}\n\n"
            "Fix the code."
        )
        repaired_plan = generate_structured(PANDAS_CODE_SYSTEM, repair_prompt, PandasCodePlan)
        result = execute_analysis_code(repaired_plan.code, df)

    return result


def result_to_display_string(result: ExecutionResult, max_rows: int = 20) -> str:
    """Turns an ExecutionResult into a compact string safe to hand back to the LLM for explanation."""
    if not result.success:
        return f"ERROR: {result.error}"
    val = result.result
    if isinstance(val, pd.DataFrame):
        return val.head(max_rows).to_string()
    if isinstance(val, pd.Series):
        return val.head(max_rows).to_string()
    return str(val)
