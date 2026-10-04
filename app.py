"""
Web wrapper around the autonomous agent.

Exposes:
- GET  /          → minimal HTML UI
- POST /run       → run the agent on a task; returns full trace + verification JSON
- GET  /healthz   → health check

Uses the same run_agent as run_demo.py — no logic is duplicated.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from agent import run_agent


app = FastAPI(title="CentrAlign AI — Autonomous Task Worker")

INTERNAL_API_URL = os.getenv(
    "INTERNAL_API_URL",
    "http://127.0.0.1:8000",
)

_mock_proc: subprocess.Popen | None = None


def _mock_alive() -> bool:
    try:
        response = httpx.get(f"{INTERNAL_API_URL}/", timeout=1)
        return response.status_code < 500
    except Exception:
        return False


def _start_mock_if_needed() -> None:
    global _mock_proc

    if _mock_alive():
        return

    _mock_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "mock_company.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--log-level",
            "warning",
        ]
    )

    for _ in range(40):
        if _mock_alive():
            return
        time.sleep(0.25)

    raise RuntimeError("Mock company server did not start")


@app.on_event("startup")
def _on_startup() -> None:
    _start_mock_if_needed()


class RunRequest(BaseModel):
    task: str = Field(..., min_length=4, max_length=800)


@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "internal_api": INTERNAL_API_URL,
        "mock_alive": _mock_alive(),
    }


@app.post("/run")
def run(req: RunRequest):
    try:
        result = run_agent(req.task)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent crashed: {e}",
        )

    return JSONResponse(
        {
            "task": result.task,
            "status": result.status,
            "plan": result.plan.model_dump() if result.plan else None,
            "trace": result.trace,
            "verification": (
                result.verification.model_dump()
                if result.verification
                else None
            ),
            "summary": result.final_summary,
        }
    )


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML


INDEX_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>CentrAlign AI — Autonomous Task Worker</title>

<style>
  body {
    font-family: -apple-system, Segoe UI, Roboto, sans-serif;
    background: #0f1115;
    color: #e6e6e6;
    margin: 0;
    padding: 28px;
  }

  h1 {
    font-size: 20px;
    margin: 0 0 4px;
  }

  .sub {
    color: #9aa4b2;
    margin-bottom: 20px;
  }

  textarea {
    width: 100%;
    max-width: 760px;
    height: 80px;
    padding: 10px;
    background: #161a20;
    color: #e6e6e6;
    border: 1px solid #23262d;
    border-radius: 8px;
    font-size: 14px;
  }

  button {
    margin-top: 10px;
    padding: 10px 18px;
    border: none;
    border-radius: 8px;
    background: #2b6cb0;
    color: #fff;
    font-weight: 600;
    cursor: pointer;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  pre {
    background: #0b0d11;
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 12px;
    color: #cfd6e4;
    max-width: 960px;
  }

  .ok {
    color: #5ddc8b;
    font-weight: 600;
  }

  .fail {
    color: #ff6b6b;
    font-weight: 600;
  }

  .chip {
    background: #23262d;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    color: #9aa4b2;
    margin-left: 6px;
  }
</style>
</head>

<body>

<h1>CentrAlign AI — Autonomous Task Worker</h1>

<div class="sub">
  Submit a task. The agent plans, executes, observes, retries, verifies.
</div>

<textarea id="task">Find the latest invoice from Acme Corp in the invoices folder, extract the amount and due date, enter it into our internal tracker, and confirm it's done.</textarea>

<br>

<button id="go" onclick="runIt()">Run agent</button>

<div id="out"></div>

<script>

async function runIt() {

  const btn = document.getElementById('go');
  const out = document.getElementById('out');

  btn.disabled = true;

  out.innerHTML = '<pre>Running…</pre>';

  try {

    const r = await fetch('/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        task: document.getElementById('task').value
      })
    });

    const data = await r.json();

    const steps = (data.trace || []).map(t => {

      const retries = Math.max(
        0,
        (t.attempts || []).length - 1
      );

      const cls = t.obs.ok ? 'ok' : 'fail';
      const txt = t.obs.ok ? 'OK' : 'FAIL';

      const badge = retries
        ? `<span class="chip">retries: ${retries}</span>`
        : '';

      return `#${t.step}  ${t.call.tool}  <span class="${cls}">${txt}</span>${badge}`;

    }).join('\\n');

    const v = data.verification || {};

    const vCls = v.verified ? 'ok' : 'fail';
    const vTxt = v.verified
      ? 'VERIFIED'
      : 'NOT VERIFIED';

    out.innerHTML = `
      <pre>${steps}</pre>

      <pre>
verification:
<span class="${vCls}">${vTxt}</span>

${JSON.stringify(v, null, 2)}
      </pre>

      <pre>
summary: ${data.summary}
status: ${data.status}
      </pre>
    `;

  } catch (e) {

    out.innerHTML =
      `<pre class="fail">Error: ${e}</pre>`;

  } finally {

    btn.disabled = false;

  }
}

</script>

</body>
</html>
"""