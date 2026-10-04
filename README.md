# CentrAlign AI — Autonomous Task Worker

An autonomous AI task worker that accepts a natural-language goal, creates an execution plan, uses tools to perform actions, observes results, adapts to failures, retries when appropriate, and independently verifies the final outcome.

The project was built as a take-home submission for the CentrAlign AI Engineering Intern role.

---

## Live Demo

**Live application:** `YOUR_RENDER_URL`

The deployed application provides a live interface for submitting natural-language tasks to the autonomous worker. The agent plans the task, selects and executes the required tools, observes their results, handles recoverable failures, and independently verifies the final outcome.

### Endpoints

- `GET /` — Interactive web interface for submitting tasks
- `POST /run` — Executes a task and returns the execution trace, result, and verification evidence
- `GET /healthz` — Health check for the deployed service

### Verified Live Execution

The deployed application was successfully tested with the Acme invoice task:

```text
#1 files_list                 OK
#2 files_read                 OK
#3 browser_fill_and_submit    OK
#4 internal_api_get           OK

VERIFIED
status: done
```

The agent successfully located the latest invoice, extracted the amount and due date, submitted the information to the internal tracker, and independently verified that the expected data was recorded.

---

## What I Built

The system implements an explicit autonomous execution loop:

```text
Goal
 ↓
Understand
 ↓
Plan
 ↓
Execute
 ↓
Observe
 ↓
Adapt / Retry
 ↓
Verify
 ↓
Complete
```

The agent receives a natural-language task such as:

> Find the latest invoice from Acme Corp in the invoices folder, extract the amount and due date, enter it into our internal tracker, and confirm it's done.

Instead of following a fixed invoice-specific sequence, the LLM generates a plan and selects available tools during execution.

The system then:

1. Locates the relevant file.
2. Reads the file contents.
3. Extracts the required values at runtime.
4. Submits the information through browser automation.
5. Observes the result.
6. Retries when a transient action fails.
7. Queries the tracker independently.
8. Verifies that the expected data was actually recorded.
9. Returns a final status and execution evidence.

---


## Key Features

### 1. Natural-Language Task Execution

The worker accepts a high-level task rather than requiring the user to specify individual tool calls.

### 2. Dynamic Planning

The LLM generates an execution plan based on the task and available tools.

### 3. Tool-Based Execution

The agent can use controlled tools for:

- File listing
- File reading
- Browser interaction
- Internal API access
- Human escalation when required

### 4. Observation-Driven Execution

After each tool call, the agent receives an observation containing the result of the action.

The next action is determined using the current execution state rather than blindly following a predetermined script.

### 5. Retry and Adaptation

Transient failures can trigger retries.

For example, during the reliability demonstration, the browser submission failed temporarily and the agent retried the action before continuing.

Example:

```text
browser_fill_and_submit
retry
browser_fill_and_submit → success
```

### 6. Independent Verification

The system does not treat successful execution as sufficient evidence of completion.

After submitting an invoice, it performs an independent tracker lookup and verifies the recorded invoice ID, company, amount, and due date.

Example:

```text
Execution:
Submit to tracker

Verification:
Tracker GET → expected invoice data

Result:
VERIFIED
```

### 7. Execution Trace

The worker records the actions, observations, attempts, and verification information so that the result can be inspected rather than treated as a black box.

---

# Architecture

```text
                         Natural Language Task
                                  |
                                  v
                         +------------------+
                         |      Planner     |
                         |       LLM        |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         |    Agent Loop    |
                         |                  |
                         | Execute          |
                         | Observe          |
                         | Adapt / Retry    |
                         +--------+---------+
                                  |
              +-------------------+-------------------+
              |                   |                   |
              v                   v                   v
        File Tools          Browser Tool       Internal API
              |                   |                   |
              +-------------------+-------------------+
                                  |
                                  v
                         +------------------+
                         |     Memory       |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         |    Verifier      |
                         | Independent      |
                         | outcome check    |
                         +--------+---------+
                                  |
                                  v
                         VERIFIED / FAILED
```

---

## Core Execution Loop

The central agent loop follows this pattern:

```text
1. Understand the task
2. Generate a plan
3. Select the next tool
4. Execute the tool
5. Observe the result
6. Decide whether the result satisfies the current step
7. Retry or adapt if necessary
8. Continue until the plan is complete
9. Independently verify the final outcome
10. Return completion status and evidence
```

This loop is implemented explicitly rather than delegated to a heavy autonomous-agent framework.

---

# Tools

| Tool | Purpose |
|---|---|
| `files_list` | Locate relevant files in the sandbox |
| `files_read` | Read file contents and extract task data |
| `browser_fill_and_submit` | Enter data into the internal tracker through browser automation |
| `internal_api_get` | Retrieve tracker state for verification |
| `human_ask` | Provide a mechanism for human intervention when required |

---

# Project Structure

```text
centralign-autonomous-task-worker/
│
├── agent/
│   ├── loop.py
│   ├── memory.py
│   ├── verifier.py
│   ├── trace_viewer.py
│   │
│   └── tools/
│       ├── files.py
│       ├── browser.py
│       ├── internal_api.py
│       └── human.py
│
├── mock_company/
│   └── server.py
│
├── sandbox/
│   └── invoices/
│       ├── acme_invoice_2024_03.txt
│       └── otherco_invoice_2024_02.txt
│
├── tasks/
│   └── evaluate.py
│
├── tests/
│   └── test_smoke.py
│
├── app.py
├── run_demo.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── render.yaml
├── .env.example
└── README.md
```

---

# Technology Stack

### Language

- Python

### AI / LLM

- OpenAI-compatible LLM API
- Groq API
- `openai/gpt-oss-120b`

### Backend

- FastAPI
- Uvicorn
- Pydantic

### Browser Automation

- Playwright
- Chromium

### HTTP / APIs

- httpx

### Testing

- pytest

### Utilities

- python-dotenv
- Rich

### Deployment

- Docker
- Render

---

# Setup

## 1. Clone the repository

```bash
git clone https://github.com/pujitha-mule/centralign-autonomous-task-worker.git
cd centralign-autonomous-task-worker
```

## 2. Create a virtual environment

Python 3.11 is recommended.

### Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Install Playwright Chromium

```bash
playwright install chromium
```

## 5. Configure environment variables

Create a `.env` file based on `.env.example`.

Example:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=YOUR_API_KEY
OPENAI_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
MAX_STEPS=15
```

Never commit `.env` or API keys to GitHub.

---

# Run Locally

Run the demonstration:

```bash
python run_demo.py
```

The demonstration starts the mock company tracker and executes the autonomous worker against the invoice task.

---

# Evaluation

The evaluation suite tests the worker against multiple invoice-processing tasks.

Run:

```bash
python tasks/evaluate.py
```

Expected result:

```text
Success rate: 2/2
```

The two evaluated tasks cover:

### Acme Corp

```text
Invoice: ACME-2024-03
Amount: 12,500.00
Due Date: 2024-04-15
```

### OtherCo

```text
Invoice: OTHER-2024-02
Amount: 3,100.00
Due Date: 2024-03-01
```

Both tasks completed successfully and were independently verified.

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

The tests cover basic system functionality including imports, sandbox safety, and generic invoice extraction behavior.

---

# Reliability Demonstration

The worker includes retry handling for transient tool failures.

A reliability demonstration intentionally introduces a temporary browser submission failure.

The worker observes the failure, retries the action, and continues when the retry succeeds.

Example:

```text
browser_fill_and_submit
  ↓
temporary failure
  ↓
retry
  ↓
browser_fill_and_submit
  ↓
success
```

Example output:

```text
retried 2 time(s) — final ok=True
```

This demonstrates that the worker does not immediately fail when a tool action encounters a recoverable error.

---

# Independent Verification

Verification is intentionally separated from the action that performs the task.

For an invoice submission:

```text
1. Read invoice
2. Extract invoice data
3. Submit invoice
4. Query tracker independently
5. Compare observed tracker state
6. Mark task VERIFIED
```

Example verification evidence:

```text
Read file:
invoices/acme_invoice_2024_03.txt

Submitted to tracker:
ACME-2024-03

Tracker GET:
ACME-2024-03
Acme Corp
12,500.00
2024-04-15

Result:
VERIFIED
```

This reduces the risk of treating an attempted action as proof that the intended outcome actually occurred.

---

# Live Deployment

The application is deployed as a Docker-based FastAPI service on Render.

The Docker image uses the official Playwright Python image so that Chromium and its required system dependencies are available at runtime.

The deployment exposes:

```text
GET /
GET /healthz
POST /run
```

The web UI allows a recruiter or evaluator to submit a task directly to the deployed autonomous worker.

---

# Demo

The recommended demonstration shows:

1. Project architecture
2. Core autonomous loop
3. Local execution
4. Retry behavior
5. Evaluation result
6. Automated tests
7. Live Render deployment
8. Independent verification

The live demo demonstrates the same agent running through the deployed FastAPI service.

---

# What Is Genuinely Autonomous?

The following components are determined dynamically at runtime:

- Natural-language task interpretation
- Plan generation
- Tool selection
- Runtime extraction of invoice information
- Progression based on tool observations
- Retry decisions
- Completion decision
- Independent verification reasoning

For example, the invoice amount and due date are read from the actual invoice file rather than embedded into the agent's execution logic.

---

# What Is Hard-Coded or Manually Configured?

The current demonstration environment intentionally controls:

- Available tools
- Sandbox directory
- Mock internal tracker
- Evaluation data
- Browser target
- Available LLM configuration
- Runtime environment variables

The evaluation tasks and mock company data are predefined.

However, the core execution flow is not hard-coded to the specific invoice values.

---

# Design Decisions

## Explicit Agent Loop

The core reasoning loop is implemented directly rather than relying on a large agent framework.

This makes the execution flow easier to inspect, debug, and modify.

## Tool Abstraction

Tools expose structured inputs and outputs so the agent can reason over observations instead of manipulating implementation details directly.

## Independent Verification

Verification is deliberately separated from execution so that the system has evidence that the desired state was actually reached.

## Controlled Environment

The project uses a sandbox and mock tracker to demonstrate autonomous behavior without requiring unauthorized access to real external systems.

## Evidence-Oriented Execution

The worker records execution information so the final result can be inspected and explained.

---

# Limitations

The current implementation operates in a controlled demonstration environment with a mock tracker and a relatively narrow invoice-processing workflow.

The current evaluation does not cover the full range of failures and integrations that an autonomous worker would encounter in production.

Additional production requirements would include:

- Stronger authentication
- Secure tool permissions
- Browser isolation
- Sandboxing
- Persistent long-term memory
- Better failure classification
- More comprehensive observability
- Broader evaluation coverage
- Cost and latency monitoring
- Human approval for sensitive actions

---

# Security Considerations

- API credentials are supplied through environment variables.
- `.env` is excluded from Git.
- The system uses sandbox data and a mock internal tracker.
- No confidential company data is included.
- No unauthorized third-party systems are accessed.
- Production deployment would require stronger authentication, authorization, isolation, and rate limiting.

---

# What I Would Build Next

With another two weeks, I would focus on:

### 1. Persistent Memory

Add durable memory across tasks so the worker can retain useful context between executions.

### 2. Broader Tool Integrations

Add additional safe browser/API/file tools and support more task categories.

### 3. Better Failure Handling

Introduce structured failure classification, exponential backoff, and more targeted retry strategies.

### 4. Human Approval

Add human approval gates before sensitive or irreversible actions.

### 5. Broader Evaluation

Create a larger evaluation suite covering:

- Tool failures
- Missing files
- Incorrect data
- API failures
- Browser failures
- Ambiguous tasks
- Verification failures

### 6. Observability

Track:

- Execution latency
- Tool usage
- Retry count
- Token/cost usage
- Success rate
- Failure categories

---

# AI Coding Assistance Disclosure

AI coding assistance was used during development for implementation support, debugging, code refinement, and documentation.

The final system was reviewed, tested, and understood by the author.

The core autonomous loop, tools, retry behavior, verification logic, evaluation setup, and deployment configuration are included in this repository and can be explained or modified during a technical interview.

---

# Submission

**GitHub Repository**

https://github.com/pujitha-mule/centralign-autonomous-task-worker

**Live Demo**

`YOUR_RENDER_URL`

**Demo Video**

`YOUR_DEMO_VIDEO_URL`

---

# Final Evaluation Summary

| Criterion | Implementation |
|---|---|
| Natural-language task input | Yes |
| Dynamic planning | Yes |
| Tool selection | Yes |
| File interaction | Yes |
| Browser automation | Yes |
| API interaction | Yes |
| Observation loop | Yes |
| Retry / adaptation | Yes |
| Independent verification | Yes |
| Execution trace | Yes |
| Multiple evaluation tasks | Yes |
| Evaluation success | 2/2 |
| Automated tests | 3 passed |
| Cloud deployment | Render |
| Docker deployment | Yes |
| AI coding assistance disclosed | Yes |

---

## Result

The project demonstrates a working autonomous task worker that can:

```text
Understand
    ↓
Plan
    ↓
Use tools
    ↓
Observe
    ↓
Adapt / Retry
    ↓
Verify independently
    ↓
Complete with evidence
```

The same worker is available locally and through the deployed FastAPI application.
```

