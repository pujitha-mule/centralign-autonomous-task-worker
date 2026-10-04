from __future__ import annotations
import os
from typing import Any
import httpx
from .base import Tool
from ..schemas import Observation

BASE = os.getenv("INTERNAL_API_URL", "http://127.0.0.1:8000")


class InternalApiGetTool(Tool):
    name = "internal_api_get"
    description = "GET an invoice record from the internal tracker by invoice_id."

    def run(self, invoice_id: str, **_: Any) -> Observation:
        try:
            r = httpx.get(f"{BASE}/invoices/{invoice_id}", timeout=5)
            if r.status_code == 404:
                return Observation(ok=False, error=f"Not found: {invoice_id}")
            r.raise_for_status()
            return Observation(ok=True, output=r.json())
        except Exception as e:
            return Observation(ok=False, error=str(e))