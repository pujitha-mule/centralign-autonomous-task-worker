# CentrAlign Autonomous AI Task Worker

A lightweight autonomous AI task worker that accepts natural-language tasks, creates an execution plan, selects and uses tools, observes results, adapts to failures, verifies outcomes independently, and returns evidence of completion.

Built as a take-home implementation for the **CentrAlign AI Engineering Intern** assignment.

---

## What This Project Demonstrates

The worker is designed around an autonomous execution loop:

**Goal → Understand → Plan → Execute → Observe → Adapt → Verify → Complete**

Given a task such as:

> "Find the latest invoice from Acme Corp in the invoices folder, extract the amount and due date, enter it into our internal tracker, and confirm it's done."

the agent independently:

1. Understands the natural-language objective.
2. Generates a multi-step execution plan.
3. Searches the available files.
4. Reads the relevant invoice.
5. Extracts the required fields from the actual file contents.
6. Uses browser automation to enter the data into the internal tracker.
7. Retries when a transient failure occurs.
8. Verifies the submitted record independently.
9. Produces an execution trace and evidence.
10. Returns a final completion status.

---

## Key Capabilities

### 🧠 Autonomous Planning

The LLM converts the user's objective into an ordered execution plan.

The plan is not hardcoded to a specific invoice or fixed sequence of values. The agent determines what information it needs and which tools are appropriate.

### 🛠️ Tool Use

The worker exposes multiple tools:

| Tool | Purpose |
|---|---|
| `files_list` | Discover files inside the sandbox |
| `files_read` | Read actual file contents |
| `browser_fill_and_submit` | Interact with the internal tracker through a browser |
| `internal_api_get` | Retrieve tracker records for verification |
| `human_ask` | Request clarification or approval when required |

### 🔄 Retry and Recovery

Transient tool failures are handled automatically.

The mock tracker intentionally supports deterministic failure injection so the retry mechanism can be demonstrated reliably.

Example from the demo:

```text
→ step 3 | tool=browser_fill_and_submit
  retried 2 time(s) — final ok=True
  observation ok=True
```

The task continued successfully without requiring manual intervention.

### 🔍 Independent Verification

The worker does not simply assume that a successful tool call means the task is complete.

After submission, the verifier checks evidence from the tracker and confirms that the expected record exists with the correct values.

Example:

```text
VERIFICATION
{
  'verified': True,
  ...
}
```

### 📋 Evidence and Traceability

Each execution produces a structured trace containing:

- Step number
- Selected tool
- Arguments
- Observation
- Success/failure state
- Retry count

The trace can also be rendered as an HTML report for inspection.

---

# Architecture

```text
                    ┌─────────────────────┐
                    │   Natural Language   │
                    │        Task          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Planner        │
                    │  Generate Steps     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Agent Loop       │
                    │ Plan → Act → Observe│
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
       ┌───────────┐     ┌────────────┐    ┌────────────┐
       │   Files   │     │  Browser   │    │ Internal   │
       │   Tools   │     │ Automation │    │    API     │
       └───────────┘     └────────────┘    └────────────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │      Memory         │
                    │ Execution Context   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Verifier       │
                    │ Independent Check   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Evidence + Result   │
                    │       `done`        │
                    └─────────────────────┘
```

---

# Project Structure

```text
centralign-autonomous-task-worker/
│
├── agent/
│   ├── __init__.py
│   ├── llm.py
│   ├── loop.py
│   ├── memory.py
│   ├── planner.py
│   ├── retry.py
│   ├── schemas.py
│   ├── trace_viewer.py
│   ├── verifier.py
│   │
│   └── tools/
│       ├── __init__.py
│       ├── base.py
│       ├── browser.py
│       ├── files.py
│       ├── human.py
│       └── internal_api.py
│
├── mock_company/
│   ├── __init__.py
│   └── server.py
│
├── sandbox/
│   └── invoices/
│       ├── acme_invoice_2024_01.txt
│       ├── acme_invoice_2024_03.txt
│       └── otherco_invoice_2024_02.txt
│
├── tasks/
│   ├── __init__.py
│   ├── evaluate.py
│   └── suite.py
│
├── tests/
│   └── test_smoke.py
│
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── run_demo.py
```

---

# Tech Stack

- **Python**
- **FastAPI** — mock internal company service
- **Playwright** — browser automation
- **OpenAI-compatible LLM API** — planning and agent reasoning
- **Pydantic** — structured data models
- **httpx** — HTTP communication
- **Pytest** — automated tests
- **Rich** — terminal execution output

The implementation intentionally avoids a heavy agent framework so that the planning, execution, retry, memory, tool use, and verification behavior remains explicit and inspectable.

---

# Setup

## Requirements

- Python 3.11+ (64-bit recommended)
- Git
- An OpenAI-compatible LLM API key
- Windows/Linux/macOS

## 1. Clone the repository

```bash
git clone https://github.com/pujitha-mule/centralign-autonomous-task-worker.git
cd centralign-autonomous-task-worker
```

## 2. Create a virtual environment

### Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

Install the browser runtime:

```bash
playwright install chromium
```

## 4. Configure the LLM

Copy the example environment file:

### Windows

```powershell
Copy-Item .env.example .env
```

### macOS/Linux

```bash
cp .env.example .env
```

Then configure the required LLM provider/API credentials in `.env`.

**Never commit `.env` or API keys to Git.**

---

# Running the Demo

Run:

```bash
python run_demo.py
```

The demo starts the mock company service, executes an invoice task, prints the plan and execution trace, performs verification, and writes an HTML trace.

The generated report is:

```text
eval_out/demo.html
```

Open it locally to inspect the execution trace.

---

# Evaluation Suite

Run the complete evaluation:

```bash
python tasks/evaluate.py
```

The evaluation runs two different invoice tasks:

1. Latest Acme Corp invoice
2. OtherCo invoice

The evaluator checks:

- Task completion
- Verification status
- Expected evidence
- Number of execution steps

### Evaluation Result

```text
Success rate: 2/2
```

Both evaluation tasks completed successfully.

---

# Automated Tests

Run:

```bash
pytest -q
```

Current result:

```text
3 passed
```

The smoke tests cover:

- Agent imports
- File-tool sandbox behavior
- Generic invoice field extraction

---

# Example Execution

For the Acme task, the worker discovered the invoice files:

```text
acme_invoice_2024_01.txt
acme_invoice_2024_03.txt
```

It selected the latest invoice and extracted:

```text
Invoice ID: ACME-2024-03
Company: Acme Corp
Amount: 12500.00
Due Date: 2024-04-15
```

It then submitted the information through the browser automation tool.

The mock environment intentionally triggered a transient failure, causing the worker to retry:

```text
retried 2 time(s) — final ok=True
```

The worker subsequently queried the tracker:

```text
{
  'invoice_id': 'ACME-2024-03',
  'company': 'Acme Corp',
  'amount': '12500.00',
  'due_date': '2024-04-15'
}
```

The independent verifier marked the task:

```text
verified: True
```

Final status:

```text
done
```

---

# Design Decisions

## 1. Explicit Agent Loop

Instead of hiding execution behind a framework, the core loop is explicit:

```text
Plan
  ↓
Select Tool
  ↓
Execute
  ↓
Observe
  ↓
Update Context
  ↓
Continue / Retry / Adapt
  ↓
Verify
```

This makes the system easier to inspect, debug, and evaluate.

## 2. Real Tool Execution

The agent does not merely generate a textual answer.

It interacts with:

- Real files in the sandbox
- A running HTTP service
- A Chromium browser through Playwright

This allows the demo to validate actual execution rather than simulated responses.

## 3. Separate Verification

Verification is deliberately separated from task execution.

The agent must provide evidence that the requested state was actually achieved rather than treating the final tool call as proof of completion.

## 4. Deterministic Failure Injection

The mock company service can intentionally fail a submission once.

This provides a reproducible way to demonstrate:

```text
Failure → Retry → Success
```

rather than relying on an unpredictable external failure.

## 5. Generic Extraction

Invoice values are extracted from the actual file contents.

The implementation is not dependent on hardcoded Acme-specific values for the extraction logic, allowing the same extraction mechanism to work with different invoice identifiers, companies, amounts, and dates.

## 6. Human-in-the-Loop Capability

A human interaction tool is available for cases where the agent needs clarification or approval.

The goal is not to force autonomous execution when an important decision cannot safely be inferred.

---

# Reliability Strategy

The worker uses several layers of reliability:

### Tool-level handling

Tool results are represented with explicit success/failure information.

### Retry handling

Transient failures can be retried before the agent decides whether to continue or adapt.

### Execution memory

The worker maintains execution context so later steps can use observations from earlier steps.

### Independent verification

Completion is only accepted when the verifier finds sufficient evidence.

This separates:

```text
"I attempted the action"
```

from:

```text
"The requested outcome actually exists."
```

---

# Limitations

This implementation is intentionally scoped to a controlled demonstration environment.

Current limitations include:

- The browser workflow targets the provided mock tracker rather than arbitrary production websites.
- File access is intentionally restricted to the sandbox.
- The current evaluation tasks are invoice-oriented.
- Human approval is exposed as a tool but the demo does not require a real human escalation.
- The mock company API is local and deterministic rather than a production backend.
- The system does not yet include long-term persistent memory across independent runs.
- Production deployments would require stronger authentication, authorization, secrets management, observability, and sandbox isolation.

---

# Future Improvements

Potential next steps include:

- Persistent task memory across sessions
- More general browser workflows
- Additional API and application integrations
- Richer failure classification
- Exponential backoff and retry policies
- More sophisticated human approval flows
- Persistent execution history
- Authentication and authorization boundaries
- Production-grade observability
- Parallel task execution
- More comprehensive evaluation suites
- Cost and latency tracking
- Stronger action safety policies

---

# Security Notes

- API credentials are loaded through environment variables.
- `.env` is excluded from version control.
- The agent's file access is restricted to the sandbox.
- The browser interaction targets the controlled mock application.
- Production deployment would require additional security controls.

---

# Evaluation Summary

| Capability | Result |
|---|---|
| Natural-language task understanding | ✅ |
| Autonomous planning | ✅ |
| Tool selection | ✅ |
| File interaction | ✅ |
| Browser automation | ✅ |
| Failure recovery | ✅ |
| Retry mechanism | ✅ |
| Execution memory | ✅ |
| Independent verification | ✅ |
| Evidence generation | ✅ |
| Multiple task evaluation | ✅ |
| Automated tests | ✅ |
| Evaluation success rate | **2/2** |
| Smoke tests | **3 passed** |

---

# Repository

**GitHub:**  
https://github.com/pujitha-mule/centralign-autonomous-task-worker

---

## Author

**Pujitha Mule**

B.Tech Computer Science & Engineering — VIT-AP, 2026
