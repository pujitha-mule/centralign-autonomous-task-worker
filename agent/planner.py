from __future__ import annotations
import json
from .llm import LLM
from .schemas import Plan, PlanStep

SYSTEM = """You are a planning module for an autonomous AI worker.

Given a natural-language task, produce a plan as JSON:
{"goal": "...", "steps": [{"step_id": 1, "intent": "...", "tool_hint": "..."}]}

Rules:
- Steps are high-level intents, not micro-actions.
- Never hardcode file names, invoice IDs, amounts, or dates. Those must be
  discovered at runtime by reading files and observations.
- tool_hint suggests a tool family (files, browser, internal_api, human_ask),
  not a guarantee.
- If the task names a company, plan to discover the right file at runtime.
"""


def plan(task: str, llm: LLM) -> Plan:
    raw = llm.chat(SYSTEM, f"Task: {task}", json_mode=True)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return Plan(goal=task, steps=[PlanStep(step_id=1, intent=task)])
    return Plan(**data)