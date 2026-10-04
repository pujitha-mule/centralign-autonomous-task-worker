from __future__ import annotations
from typing import Any
from .base import Tool
from ..schemas import Observation


class HumanAskTool(Tool):
    name = "human_ask"
    description = (
        "Ask the human for clarification or approval when the agent cannot "
        "safely proceed (destructive action, ambiguity)."
    )

    def run(self, question: str, **_: Any) -> Observation:
        print(f"\n[AGENT ASKS HUMAN] {question}")
        answer = input("Your answer: ").strip()
        return Observation(ok=True, output={"answer": answer})