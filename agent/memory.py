from __future__ import annotations
import json
import os
from typing import Any

STORE = os.path.join(os.path.dirname(__file__), "..", "memory_store.json")


class Memory:
    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self.trace: list[dict[str, Any]] = []
        self.facts: dict[str, Any] = {}
        self._load()

    def add_step(self, thought: str, tool_call: dict, observation: dict) -> None:
        self.trace.append({
            "thought": thought,
            "tool_call": tool_call,
            "observation": observation,
        })

    def remember(self, key: str, value: Any, *, persist: bool = False) -> None:
        self.facts[key] = value
        if persist:
            self._save()

    def recall(self, key: str, default: Any = None) -> Any:
        return self.facts.get(key, default)

    def as_context(self, last_n: int = 5) -> str:
        lines = [f"Namespace: {self.namespace}", "Known facts:"]
        for k, v in self.facts.items():
            lines.append(f"  - {k}: {str(v)[:200]}")
        lines.append("Recent steps:")
        for step in self.trace[-last_n:]:
            tc = step["tool_call"]
            obs = step["observation"]
            lines.append(
                f"  - tool={tc.get('tool')} args={tc.get('args')} "
                f"ok={obs.get('ok')} out={str(obs.get('output'))[:200]}"
            )
        return "\n".join(lines)

    def _load(self) -> None:
        if not os.path.exists(STORE):
            return
        try:
            with open(STORE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.facts = data.get(self.namespace, {})
        except Exception:
            self.facts = {}

    def _save(self) -> None:
        data: dict[str, Any] = {}
        if os.path.exists(STORE):
            try:
                with open(STORE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data[self.namespace] = self.facts
        with open(STORE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)