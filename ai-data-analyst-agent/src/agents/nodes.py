"""
Each function is one LangGraph node: reads AgentState, does one job, returns
the partial state update. Keeping nodes single-purpose is what makes the
graph in graph.py legible instead of one giant function.
"""
from __future__ import annotations

import json

from src.agents.state import AgentState
from src.core.executor import execute_analysis_code
from src.llm.client import generate_structured, generate_text
from src.llm.prompts import INSIGHT_SYSTEM, PANDAS_CODE_SYSTEM, PLANNER_SYSTEM
from src.schemas.models import AnalysisPlan, PandasCodePlan


def _log(state: AgentState, message: str) -> list[str]:
    log = list(state.get("status_log", []))
    log.append(message)
    return log


def planner_node(state: AgentState) -> dict:
    profile_summary = json.dumps(state["profile"].to_summary_dict(), indent=2)
    user_prompt = f"Dataset profile:\n{profile_summary}\n\nUser question: {state['question']}"

    plan: AnalysisPlan = generate_structured(PLANNER_SYSTEM, user_prompt, AnalysisPlan)

    return {
        "analysis_type": plan.analysis_type,
        "relevant_columns": plan.relevant_columns,
        "status_log": _log(state, f"Planner classified request as '{plan.analysis_type}'"),
    }


def pandas_execution_node(state: AgentState) -> dict:
    """Only runs when analysis_type == 'calculation'."""
    profile_summary = json.dumps(state["profile"].to_summary_dict(), indent=2)
    user_prompt = (
        f"Dataset profile:\n{profile_summary}\n\n"
        f"Question: {state['question']}\n\nWrite the pandas code that computes the answer."
    )

    code_plan: PandasCodePlan = generate_structured(PANDAS_CODE_SYSTEM, user_prompt, PandasCodePlan)
    exec_result = execute_analysis_code(code_plan.code, state["df"])

    if not exec_result.success:
        repair_prompt = (
            f"{user_prompt}\n\nYour code:\n{code_plan.code}\n\n"
            f"It failed with:\n{exec_result.error}\n\nFix it."
        )
        repaired: PandasCodePlan = generate_structured(PANDAS_CODE_SYSTEM, repair_prompt, PandasCodePlan)
        exec_result = execute_analysis_code(repaired.code, state["df"])
        code_used = repaired.code
    else:
        code_used = code_plan.code

    log_msg = ("Python analysis completed" if exec_result.success
               else f"Python analysis failed: {exec_result.error}")

    return {
        "pandas_code": code_used,
        "raw_result": exec_result.result,
        "raw_result_type": exec_result.result_type,
        "execution_error": exec_result.error,
        "status_log": _log(state, log_msg),
    }


def insight_node(state: AgentState) -> dict:
    """Turns a raw computed result (or profile-level info) into a plain-language answer."""
    import pandas as pd  # local import keeps this node's dependency obvious

    raw = state.get("raw_result")
    if isinstance(raw, (pd.DataFrame, pd.Series)):
        result_str = raw.head(20).to_string()
    elif raw is not None:
        result_str = str(raw)
    else:
        result_str = "No calculation was needed for this question."

    profile_summary = json.dumps(state["profile"].to_summary_dict(), indent=2)
    user_prompt = (
        f"Question: {state['question']}\n\n"
        f"Computed result:\n{result_str}\n\n"
        f"Dataset context:\n{profile_summary}\n\n"
        "Explain this result in plain business language."
    )

    if state.get("execution_error"):
        answer = (
            "I wasn't able to compute an exact answer for this — "
            f"the analysis step failed ({state['execution_error']}). "
            "Try rephrasing the question or checking the column names involved."
        )
        confidence = "low"
    else:
        answer = generate_text(INSIGHT_SYSTEM, user_prompt)
        confidence = "high" if not state.get("execution_error") else "medium"

    return {
        "final_answer": answer,
        "insights": [answer],
        "confidence": confidence,
        "status_log": _log(state, "Insight generated"),
    }
