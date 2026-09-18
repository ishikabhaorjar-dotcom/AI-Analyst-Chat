"""
Pydantic models the LLM's structured responses are validated against.
If the model's JSON doesn't fit these shapes, `llm.client.generate_structured`
retries automatically — the UI layer only ever sees valid, typed objects.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

AnalysisType = Literal["profile_question", "calculation", "visualization", "general_insight"]


class AnalysisPlan(BaseModel):
    """Output of the Planner node."""
    analysis_type: AnalysisType
    reasoning: str = Field(description="One sentence on why this classification was chosen")
    relevant_columns: list[str] = Field(default_factory=list)
    needs_visualization: bool = False


class PandasCodePlan(BaseModel):
    """What the LLM proposes to compute, before execution."""
    code: str = Field(description="A pandas snippet using `df`, assigning to `result`")
    explanation: str = Field(description="One sentence describing what this code calculates")


class AnalysisResponse(BaseModel):
    """Final structured answer returned to the UI for a user question."""
    question: str
    analysis_type: AnalysisType
    calculation: Optional[str] = None
    result: str
    insights: list[str] = Field(default_factory=list)
    visualization: Optional[str] = None
    confidence: Literal["high", "medium", "low"] = "high"


class ChartSpec(BaseModel):
    """What the Visualization tool should draw."""
    chart_type: Literal["bar", "line", "scatter", "histogram", "box", "heatmap", "pie"]
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    title: str
    reasoning: str = Field(description="Why this chart type fits this data/question")


class Insight(BaseModel):
    title: str
    detail: str
    severity: Literal["info", "positive", "warning"] = "info"


class InsightBundle(BaseModel):
    insights: list[Insight]
