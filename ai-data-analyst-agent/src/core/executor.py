"""
Executes LLM-generated pandas code against the user's DataFrame.

This is the single most safety-sensitive module in the project: an LLM writes
a string of Python, and we run it. Never `eval`/`exec` LLM output against the
real global namespace. Everything here is deliberately restrictive:

  * only a fixed set of builtins is exposed
  * only `pd`, `np`, and the dataframe (as `df`) are in scope
  * the generated snippet MUST assign its answer to a variable named `result`
  * a wall-clock timeout kills runaway code (e.g. an accidental infinite loop)
  * exceptions are caught and returned as data, never raised into the UI

This is what stands between "the LLM writes code" and "arbitrary code
execution" — treat any change here as a security change, not a refactor.
"""
from __future__ import annotations

import ast
import multiprocessing as mp
import traceback
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import pandas as pd

TIMEOUT_SECONDS = 8

# Only names an analysis snippet legitimately needs. No `os`, `sys`, `subprocess`,
# `open`, `__import__`, `eval`, `exec`, or network access of any kind.
SAFE_BUILTINS = {
    "len": len, "range": range, "sum": sum, "min": min, "max": max,
    "sorted": sorted, "abs": abs, "round": round, "list": list, "dict": dict,
    "set": set, "tuple": tuple, "str": str, "int": int, "float": float,
    "bool": bool, "enumerate": enumerate, "zip": zip, "any": any, "all": all,
    "isinstance": isinstance,
}

FORBIDDEN_NODE_TYPES = (ast.Import, ast.ImportFrom)
FORBIDDEN_NAMES = {
    "os", "sys", "subprocess", "shutil", "socket", "requests", "urllib",
    "open", "eval", "exec", "compile", "__import__", "globals", "locals",
    "getattr", "setattr", "delattr", "vars", "input", "exit", "quit",
}


@dataclass
class ExecutionResult:
    success: bool
    result: Any = None
    result_type: Optional[str] = None   # "dataframe" | "series" | "scalar" | "other"
    error: Optional[str] = None
    code: str = ""


def _static_check(code: str) -> Optional[str]:
    """Reject obviously unsafe code before it ever runs."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Generated code has a syntax error: {e}"

    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODE_TYPES):
            return "Generated code attempted an import, which is not allowed."
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return f"Generated code referenced a forbidden name: '{node.id}'."
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return "Generated code attempted to access a dunder attribute."

    if "result" not in code:
        return "Generated code did not assign to a variable named 'result'."

    return None


def _run_in_subprocess(code: str, df: pd.DataFrame, queue: mp.Queue) -> None:
    local_scope = {"df": df, "pd": pd, "np": np}
    global_scope = {"__builtins__": SAFE_BUILTINS}
    try:
        exec(code, global_scope, local_scope)  # noqa: S102 — sandboxed on purpose, see module docstring
        result = local_scope.get("result", None)
        queue.put(("ok", result))
    except Exception:
        queue.put(("error", traceback.format_exc(limit=2)))


def execute_analysis_code(code: str, df: pd.DataFrame) -> ExecutionResult:
    """
    Runs `code` against `df` in an isolated subprocess with a hard timeout.
    `code` must set a variable called `result`.
    """
    static_error = _static_check(code)
    if static_error:
        return ExecutionResult(success=False, error=static_error, code=code)

    queue: mp.Queue = mp.Queue()
    proc = mp.Process(target=_run_in_subprocess, args=(code, df, queue))
    proc.start()
    proc.join(TIMEOUT_SECONDS)

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return ExecutionResult(success=False, error=f"Execution exceeded {TIMEOUT_SECONDS}s and was stopped.", code=code)

    if queue.empty():
        return ExecutionResult(success=False, error="Execution ended without producing a result.", code=code)

    status, payload = queue.get()
    if status == "error":
        return ExecutionResult(success=False, error=payload, code=code)

    result = payload
    if isinstance(result, pd.DataFrame):
        rtype = "dataframe"
    elif isinstance(result, pd.Series):
        rtype = "series"
    elif isinstance(result, (int, float, str, bool, np.integer, np.floating)):
        rtype = "scalar"
    else:
        rtype = "other"

    return ExecutionResult(success=True, result=result, result_type=rtype, code=code)
