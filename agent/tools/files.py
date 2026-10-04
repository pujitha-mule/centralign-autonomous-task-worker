from __future__ import annotations
import os
from typing import Any
from .base import Tool
from ..schemas import Observation

SANDBOX = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sandbox"))


def _safe(path: str) -> str:
    full = os.path.abspath(os.path.join(SANDBOX, path))
    if not full.startswith(SANDBOX):
        raise PermissionError("Path escapes sandbox")
    return full


class FilesListTool(Tool):
    name = "files_list"
    description = "List files in the sandbox under a path, optional substring pattern."

    def run(self, path: str = "", pattern: str = "", **_: Any) -> Observation:
        try:
            target = _safe(path)
            if not os.path.isdir(target):
                return Observation(ok=False, error=f"Not a directory: {path}")
            matches = sorted(
                f for f in os.listdir(target) if pattern.lower() in f.lower()
            )
            return Observation(ok=True, output={"path": path, "files": matches})
        except Exception as e:
            return Observation(ok=False, error=str(e))


class FilesReadTool(Tool):
    name = "files_read"
    description = "Read a UTF-8 text file from the sandbox."

    def run(self, path: str, **_: Any) -> Observation:
        try:
            with open(_safe(path), "r", encoding="utf-8") as f:
                return Observation(ok=True, output={"path": path, "content": f.read()})
        except Exception as e:
            return Observation(ok=False, error=str(e))