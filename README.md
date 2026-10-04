# CentrAlign AI — Autonomous Task Worker (Intern Submission)

A narrow but **genuinely autonomous** AI worker that completes a real
end-to-end business task using a computer:

> "Find the latest invoice from Acme Corp in the invoices folder, extract the
> amount and due date, enter it into our internal tracker, and confirm it's done."

It plans, selects tools, executes real actions (filesystem, headless Chromium,
HTTP), observes results, retries failures, verifies the outcome, and returns
a summary with evidence.

## Core loop

```
Goal → Understand → Plan → Execute → Observe → Adapt → Verify → Complete
```

Implemented as a ReAct loop in `agent/loop.py`:

1. Plan (`planner.py`) turns the NL task into high-level steps.
2. Reason + Act — an LLM decides the next tool call from full observations.
3. Observe — the tool returns `Observation(ok, output, error)`.
4. Adapt — facts stored in `Memory`; the loop advances the plan step.
5. Retry — explicit retry policy (`retry.py`) with exponential backoff.
6. Verify — separate verifier (`verifier.py`) checks the outcome.
7. Summarize — concise summary + evidence.

## Architecture

```
             ┌──────────────┐
   task ───▶ │   Planner    │
             └──────┬───────┘
                    ▼
        ┌────────────────────────┐
        │      Agent Loop        │
        │  Reason → Tool Call    │
        │     → Observe → Adapt  │
        └──────┬─────────────────┘
               ▼
   ┌──────────────────────────────────┐
   │ Tools                            │
   │  files_list / files_read         │
   │  browser_open / browser_fill_... │
   │  internal_api_get                │
   │  human_ask                       │
   └──────┬───────────────────────────┘
          ▼
   ┌──────────────┐   ┌────────────────┐
   │  Verifier    │──▶│ Summary+Evidence│
   └──────────────┘   └────────────────┘
```

## Design decisions

- **No agent framework.** Raw loop keeps every decision explicit and debuggable.
- **No hardcoded answers.** The LLM reads the actual invoice file and extracts
  `invoice_id`, `company`, `amount`, `due_date` from its text. Adding a new
  invoice file requires no code changes.
- **Groq by default.** Free, no credit card. Groq is OpenAI-compatible, so
  the same code works with OpenAI, OpenRouter, or any compatible endpoint by
  changing `OPENAI_BASE_URL` in `.env`.
- **Real tools, sandboxed.** Playwright drives real Chromium; the internal
  tracker is a small FastAPI mock. No real credentials or third parties.
- **Typed boundaries.** Pydantic schemas for plans, tool calls, observations,
  verification.
- **Separate verifier.** Verification is a distinct step, not the agent
  grading itself.
- **Explicit retries.** `agent/retry.py` with exponential backoff.
- **Deterministic failure injection.** `FAIL_ONCE_ID` env var makes the mock
  tracker return 503 once for a specific invoice id, so reliability is
  demonstrated live, not claimed.

## Setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Edit `.env`:
- Get a free Groq key at **console.groq.com/keys** (no credit card).
- Set `OPENAI_API_KEY=gsk_...`.

## Run

```bash
python run_demo.py
```

The mock server starts automatically.

## Reliability demo (deterministic)

With `FAIL_ONCE_ID=ACME-2024-03` in `.env`, the tracker returns 503 on the
first submit for that invoice id and succeeds afterwards. `agent/retry.py`
detects the retryable error, backs off, and retries. Every attempt is
recorded in the trace and visible in the HTML viewer.

## Generalization

`tasks/suite.py` defines two tasks (Acme + OtherCo). The agent code is
identical for both. The company, invoice id, amount, and due date are all
extracted from the file text at runtime.

```bash
python tasks/evaluate.py
```

## Trace viewer

`agent/trace_viewer.py` renders any `AgentRun` to a self-contained HTML file.

```bash
python run_demo.py
# then open eval_out/demo.html
```

## Tests

```bash
pytest -q
```

## Known limitations

- The heuristic step scorer is a placeholder; production would use an
  LLM-as-judge or learned reward.
- Long-term memory is a JSON file; production would use a vector store keyed
  by organization.
- The browser tool assumes a specific form layout; generalization comes from
  swapping tools, not from the agent learning arbitrary DOMs.
- No policy layer for allowed domains/URLs.
- The mock LLM fallback uses regex parsing of observations; it exercises the
  loop but is not a substitute for a real model.

## What I'd build next

- LLM-as-judge step scoring and a proper evaluation suite with metrics.
- Vector-store company memory keyed by organization.
- Declarative tool registry / connectors so new workflows are config, not code.
- CI job that runs `tasks/evaluate.py` and fails on regression.
- Human-approval UI on top of the trace viewer with replay + approval actions.

## Assumptions

- The internal tracker is a sandboxed mock; no real company systems.
- Invoices are plain text in `sandbox/invoices/`.
- Submitting a record requires no approval for this demo; `human_ask` exists
  for cases where it does.

## Models / APIs / components

- Python 3.11+
- FastAPI + Uvicorn (mock internal system)
- Playwright (Chromium) for real browser automation
- httpx, pydantic, rich, pytest
- LLM: Groq via OpenAI-compatible SDK (default), or `mock` offline fallback