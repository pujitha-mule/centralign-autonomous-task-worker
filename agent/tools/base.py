from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from ..schemas import Observation


class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs: Any) -> Observation: ...

    def spec(self) -> dict:
        return {"name": self.name, "description": self.description}