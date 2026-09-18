"""
Wires the nodes in nodes.py into a LangGraph StateGraph.

Flow:
    planner -> (route) -> pandas_execution -> insight -> END
                       -> insight (skip pandas for profile/general questions) -> END

The router is the Planner Agent's decision made concrete: only questions
classified as "calculation" pay the cost of code generation + sandboxed
execution. Everything else goes straight to the insight step, which already
knows how to answer from the dataset profile alone.
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents.nodes import insight_node, pandas_execution_node, planner_node
from src.agents.state import AgentState


def _route_after_planner(state: AgentState) -> str:
    if state.get("analysis_type") == "calculation":
        return "pandas_execution"
    return "insight"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("pandas_execution", pandas_execution_node)
    graph.add_node("insight", insight_node)

    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", _route_after_planner, {
        "pandas_execution": "pandas_execution",
        "insight": "insight",
    })
    graph.add_edge("pandas_execution", "insight")
    graph.add_edge("insight", END)

    return graph.compile()


_compiled_graph = None


def get_agent():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_agent(question: str, df, profile) -> dict:
    """Convenience entry point used by the UI layer."""
    agent = get_agent()
    initial_state: AgentState = {
        "question": question,
        "df": df,
        "profile": profile,
        "status_log": ["Dataset loaded", "Dataset profile generated"],
    }
    return agent.invoke(initial_state)
