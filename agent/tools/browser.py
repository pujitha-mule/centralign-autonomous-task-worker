from __future__ import annotations
import os
from typing import Any
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from .base import Tool
from ..schemas import Observation

BASE = os.getenv("INTERNAL_API_URL", "http://127.0.0.1:8000")


class _BrowserSession:
    _instance: "_BrowserSession | None" = None

    def __init__(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    @classmethod
    def get(cls) -> "_BrowserSession":
        if cls._instance is None:
            cls._instance = _BrowserSession()
        return cls._instance

    def close(self):
        try:
            self.browser.close()
            self.pw.stop()
        finally:
            _BrowserSession._instance = None


class BrowserOpenTool(Tool):
    name = "browser_open"
    description = "Open a URL in the headless browser."

    def run(self, url: str, **_: Any) -> Observation:
        try:
            page = _BrowserSession.get().page
            page.goto(url, wait_until="networkidle", timeout=15000)
            return Observation(ok=True, output={"url": url, "title": page.title()})
        except PWTimeout as e:
            return Observation(ok=False, error=f"timeout: {e}")
        except Exception as e:
            return Observation(ok=False, error=str(e))


class BrowserFillAndSubmitTool(Tool):
    name = "browser_fill_and_submit"
    description = (
        "Fill the new-invoice form on the internal tracker and submit it. "
        "Args: invoice_id, company, amount, due_date."
    )

    def run(self, invoice_id: str, company: str, amount: str,
            due_date: str, **_: Any) -> Observation:
        try:
            page = _BrowserSession.get().page
            page.goto(f"{BASE}/new", wait_until="networkidle", timeout=15000)
            page.fill("input[name=invoice_id]", invoice_id)
            page.fill("input[name=company]", company)
            page.fill("input[name=amount]", amount)
            page.fill("input[name=due_date]", due_date)
            page.click("button[type=submit]")
            page.wait_for_load_state("networkidle", timeout=15000)
            body = page.inner_text("body").lower()
            if "temporarily unavailable" in body or "error" in body:
                return Observation(ok=False, error="temporarily unavailable (503)")
            if "saved" not in body and invoice_id.lower() not in body:
                return Observation(
                    ok=False,
                    error="Submit did not confirm success.",
                    output={"body_snippet": body[:300]},
                )
            return Observation(ok=True, output={"submitted": invoice_id})
        except Exception as e:
            return Observation(ok=False, error=str(e))