from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    step_id: int
    intent: str = Field(..., description="What this step should accomplish")
    tool_hint: Optional[str] = None


class Plan(BaseModel):
    goal: str
    steps: list[PlanStep]


class ToolCall(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""


class Observation(BaseModel):
    ok: bool
    output: Any = None
    error: Optional[str] = None


class VerificationResult(BaseModel):
    verified: bool
    evidence: list[str] = Field(default_factory=list)
    reason: str = ""


class AgentRun(BaseModel):
    task: str
    plan: Optional[Plan] = None
    trace: list[dict] = Field(default_factory=list)
    final_summary: str = ""
    verification: Optional[VerificationResult] = None
    status: Literal["running", "done", "failed", "needs_human"] = "running"