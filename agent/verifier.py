from __future__ import annotations
import json
from .llm import LLM
from .schemas import VerificationResult

SYSTEM = """You are a verification module.

Given the original task and observed evidence, decide whether the requested
outcome was actually achieved. Respond as JSON:
{"verified": true|false, "evidence": ["..."], "reason": "..."}

Be conservative: if evidence does not show the outcome persisted in the target
system, verified must be false."""


def verify(task: str, evidence: list[str], llm: LLM) -> VerificationResult:
    user = f"Task: {task}\nEvidence:\n" + "\n".join(f"- {e}" for e in evidence)
    raw = llm.chat(SYSTEM, user, json_mode=True)
    try:
        return VerificationResult(**json.loads(raw))
    except Exception:
        return VerificationResult(verified=False, reason="Verifier parse failure.")