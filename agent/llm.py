"""
Provider-agnostic LLM wrapper.

Providers: openai (also used for Groq / any OpenAI-compatible endpoint) | mock
Default:   openai with OPENAI_BASE_URL pointing at Groq (free, no card).

The 'mock' provider is a *generic offline fallback*: it does NOT hardcode
company names, invoice ids, amounts, or dates. It reasons over the actual
observations the loop passes in (file listings, file contents) using generic
regex heuristics, so the same code path handles any invoice file.
"""
from __future__ import annotations
import json
import os
import re
from typing import Any

from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")


class LLM:
    def __init__(self):
        self.provider = PROVIDER

    def chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        if self.provider == "openai":
            return self._openai_compatible(system, user, json_mode)
        return self._mock(system, user, json_mode)

    # ---------- OpenAI-compatible provider (Groq by default) ----------
    def _openai_compatible(self, system: str, user: str, json_mode: bool) -> str:
        """
        Works with OpenAI *and* any OpenAI-compatible endpoint (Groq,
        OpenRouter, Gemini compat, etc.). The base URL is read from
        OPENAI_BASE_URL; the key from OPENAI_API_KEY.
        """
        from openai import OpenAI

        client = OpenAI(
            base_url=BASE_URL,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        kwargs: dict[str, Any] = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    # ---------- generic offline fallback (no task-specific hardcoding) ----------
    def _mock(self, system: str, user: str, json_mode: bool) -> str:
        s = system.lower()
        if "produce a plan" in s or "planning" in s:
            return self._mock_plan(user)
        if "decide the next tool call" in s:
            return self._mock_next_tool_call(user)
        if "verify" in s:
            return self._mock_verify(user)
        if "summarize" in s:
            return "Task complete: requested action was performed and verified."
        return "{}"

    def _mock_plan(self, user: str) -> str:
        return json.dumps({
            "goal": "Complete the invoice task end-to-end.",
            "steps": [
                {"step_id": 1, "intent": "list candidate invoice files",
                 "tool_hint": "files"},
                {"step_id": 2, "intent": "read the matching invoice and extract fields",
                 "tool_hint": "files"},
                {"step_id": 3, "intent": "open the internal tracker",
                 "tool_hint": "browser"},
                {"step_id": 4, "intent": "enter extracted fields and submit",
                 "tool_hint": "browser"},
                {"step_id": 5, "intent": "verify the record exists via the API",
                 "tool_hint": "internal_api"},
            ],
        })

    def _mock_next_tool_call(self, user: str) -> str:
        step_match = re.search(r"current_step:\s*(\d+)", user)
        step = int(step_match.group(1)) if step_match else 1

        files = self._parse_files(user)
        content = self._parse_invoice_content(user)

        if not files:
            return json.dumps({
                "tool": "files_list",
                "args": {"path": "invoices", "pattern": ""},
                "reason": "No file listing yet; list invoice files.",
            })

        if not content:
            candidate = self._pick_best_candidate(files, user)
            return json.dumps({
                "tool": "files_read",
                "args": {"path": f"invoices/{candidate}"},
                "reason": f"Read candidate invoice {candidate}.",
            })

        fields = self._extract_fields(content)
        if step <= 3:
            return json.dumps({
                "tool": "browser_open",
                "args": {"url": "http://127.0.0.1:8000/"},
                "reason": "Open the internal tracker UI.",
            })
        if step == 4:
            return json.dumps({
                "tool": "browser_fill_and_submit",
                "args": fields,
                "reason": "Submit extracted invoice fields.",
            })
        if step >= 5:
            return json.dumps({
                "tool": "internal_api_get",
                "args": {"invoice_id": fields["invoice_id"]},
                "reason": "Verify the record via the API.",
            })
        return json.dumps({"tool": "finish", "args": {}, "reason": "Done."})

    # ---------- generic parsers over observations ----------
    def _parse_files(self, user: str) -> list[str]:
        m = re.search(r'"files":\s*\[(.*?)\]', user)
        if not m:
            return []
        return [x.strip().strip('"') for x in m.group(1).split(",") if x.strip()]

    def _parse_invoice_content(self, user: str) -> str:
        m = re.search(r'"content":\s*"(.*?)"(?=,\s*"|\})', user, re.DOTALL)
        if m:
            return m.group(1)
        m = re.search(r'"content":\s*"(.*?)"\s*\}', user, re.DOTALL)
        return m.group(1) if m else ""

    def _pick_best_candidate(self, files: list[str], user: str) -> str:
        task_lower = user.lower()
        tokens = set(re.findall(r"[a-z]+", task_lower))
        scored: list[tuple[int, str]] = []
        for f in files:
            f_lower = f.lower()
            score = sum(1 for tok in tokens if tok and tok in f_lower and len(tok) > 2)
            scored.append((score, f))
        scored.sort(key=lambda t: (-t[0], t[1]))
        if scored and scored[0][0] > 0:
            candidates = [f for s, f in scored if s == scored[0][0]]
        else:
            candidates = [f for _, f in scored]

        def date_key(name: str) -> str:
            m = re.search(r"(\d{4})[_-](\d{2})", name)
            return f"{m.group(1)}{m.group(2)}" if m else "000000"
        candidates.sort(key=date_key, reverse=True)
        return candidates[0] if candidates else files[0]

    def _extract_fields(self, content: str) -> dict:
        content = content.replace("\\n", "\n")
        inv = re.search(r"INVOICE\s+([A-Z0-9\-]+)", content)
        amount = re.search(r"Amount:\s*([\d,]+\.\d{2})", content)
        due = re.search(r"Due Date:\s*([\d\-]+)", content)
        vendor = re.search(r"Vendor:\s*(.+)", content)
        return {
            "invoice_id": inv.group(1) if inv else "UNKNOWN",
            "company": vendor.group(1).strip() if vendor else "Unknown",
            "amount": amount.group(1).replace(",", "") if amount else "0.00",
            "due_date": due.group(1) if due else "1970-01-01",
        }

    def _mock_verify(self, user: str) -> str:
        if "Tracker GET" in user and '"invoice_id"' in user:
            return json.dumps({
                "verified": True,
                "evidence": ["Tracker API GET returned the submitted record."],
                "reason": "Record persisted in the internal system.",
            })
        return json.dumps({
            "verified": False,
            "evidence": [],
            "reason": "No persisted record observed.",
        })