from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Callable

from .schemas import Observation

RETRYABLE_MARKERS = (
    "timeout", "timed out", "connection", "temporarily",
    "network", "reset", "refused", "503", "unavailable",
)


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 0.5
    retryable: tuple[str, ...] = RETRYABLE_MARKERS
    history: list[dict] = field(default_factory=list)

    def is_retryable(self, obs: Observation) -> bool:
        if obs.ok:
            return False
        err = (obs.error or "").lower()
        return any(marker in err for marker in self.retryable)

    def run(self, call: Callable[[], Observation]) -> tuple[Observation, list[dict]]:
        attempts: list[dict] = []
        last: Observation | None = None
        for attempt in range(1, self.max_attempts + 1):
            obs = call()
            attempts.append({"attempt": attempt, "ok": obs.ok, "error": obs.error})
            last = obs
            if obs.ok or not self.is_retryable(obs):
                break
            delay = self.base_delay * (2 ** (attempt - 1))
            time.sleep(delay)
        self.history.extend(attempts)
        assert last is not None
        return last, attempts