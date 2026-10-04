from __future__ import annotations
import json
import os
from typing import Any
from rich.console import Console

from .llm import LLM
from .memory import Memory
from .planner import plan as make_plan
from .verifier import verify as run_verify
from .schemas import AgentRun, Observation, ToolCall
from .tools import default_tools
from .retry import RetryPolicy

console = Console()
MAX_STEPS = int(os.getenv("MAX_STEPS", "15"))

REACT_SYSTEM = """You are the reasoning core of an autonomous AI worker.

You are given:
- the user's task,
- a high-level plan,
- the current plan step index,
- known facts,
- recent observations (full JSON payloads, including file listings and file
  contents).

Decide the NEXT tool call. Respond ONLY as JSON:
{{"tool": "<tool_name>", "args": {{}}, "reason": "<short why>"}}

Available tools:
{tools}

Rules:
- Read the actual contents before deciding to submit anything.
- Extract fields from the file contents; do not invent values.
- If the last observation failed, choose a reasonable alternative or retry.
- Call "finish" only when the plan's last step is satisfied.
- Call "human_ask" if the task is ambiguous or requires approval.
"""


def _tools_block(tools) -> str:
    return "\n".join(f"- {t.name}: {t.description}" for t in tools)


def _score_step(obs: Observation, call: ToolCall, plan_step: Any) -> float:
    if not obs.ok:
        return 0.0
    if plan_step and call.tool.startswith(plan_step.tool_hint or ""):
        return 1.0
    return 0.6


def run_agent(
    task: str,
    llm: LLM | None = None,
    namespace: str = "demo-company",
) -> AgentRun:
    llm = llm or LLM()
    tools = default_tools()
    tool_map = {t.name: t for t in tools}
    memory = Memory(namespace=namespace)
    retry = RetryPolicy()

    run = AgentRun(task=task)
    run.plan = make_plan(task, llm)

    console.rule("[bold]PLAN")
    for s in run.plan.steps:
        console.print(
            f"  {s.step_id}. {s.intent}  [dim]({s.tool_hint})[/dim]"
        )

    plan_by_id = {s.step_id: s for s in run.plan.steps}
    current_step = run.plan.steps[0].step_id if run.plan.steps else 1

    for step_i in range(1, MAX_STEPS + 1):
        recent = []

        for t in memory.trace[-4:]:
            recent.append({
                "tool": t["tool_call"].get("tool"),
                "args": t["tool_call"].get("args"),
                "ok": t["observation"].get("ok"),
                "output": t["observation"].get("output"),
                "error": t["observation"].get("error"),
            })

        react_system = REACT_SYSTEM.format(
            tools=_tools_block(tools)
        )

        user = (
            f"task: {task}\n"
            f"current_step: {current_step}\n"
            f"known_facts: {json.dumps(memory.facts, default=str)}\n"
            f"recent_observations: {json.dumps(recent, default=str)}\n"
            "Decide the next tool call."
        )

        raw = llm.chat(
            react_system,
            user,
            json_mode=True,
        )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            console.print(
                "[red]Invalid JSON from LLM, retrying once…[/red]"
            )
            raw = llm.chat(
                react_system,
                user + "\nReturn valid JSON.",
                json_mode=True,
            )
            data = json.loads(raw)

        call = ToolCall(**data)

        if call.tool == "finish":
            console.print("[green]Agent signalled finish.[/green]")
            run.status = "done"
            break

        tool = tool_map.get(call.tool)

        if tool is None:
            obs = Observation(
                ok=False,
                error=f"Unknown tool: {call.tool}",
            )
            attempts = [{
                "attempt": 1,
                "ok": False,
                "error": obs.error,
            }]
        else:
            console.print(
                f"\n[cyan]→ step {step_i} | "
                f"tool={call.tool} args={call.args}[/cyan]"
            )

            def _invoke():
                try:
                    return tool.run(**call.args)
                except Exception as e:
                    return Observation(
                        ok=False,
                        error=f"Tool crashed: {e}",
                    )

            obs, attempts = retry.run(_invoke)

            if len(attempts) > 1:
                console.print(
                    f"[yellow]  retried {len(attempts)} time(s) — "
                    f"final ok={obs.ok}[/yellow]"
                )

            console.print(
                f"[dim]  observation ok={obs.ok} "
                f"out={str(obs.output)[:160]}[/dim]"
            )

        memory.add_step(
            call.reason,
            call.model_dump(),
            obs.model_dump(),
        )

        run.trace.append({
            "step": step_i,
            "call": call.model_dump(),
            "obs": obs.model_dump(),
            "attempts": attempts,
            "plan_step": current_step,
        })

        if call.tool == "files_read" and obs.ok and obs.output:
            content = obs.output.get("content", "")
            memory.remember(
                "last_invoice_content",
                content[:500],
            )

        if call.tool == "internal_api_get" and obs.ok:
            memory.remember(
                "verified_record",
                obs.output,
                persist=True,
            )

        if call.tool == "browser_fill_and_submit" and obs.ok:
            memory.remember(
                "last_submitted",
                obs.output,
                persist=True,
            )

        if obs.ok:
            score = _score_step(
                obs,
                call,
                plan_by_id.get(current_step),
            )

            run.trace[-1]["step_score"] = score

            next_ids = [
                s.step_id
                for s in run.plan.steps
                if s.step_id > current_step
            ]

            if score >= 0.6 and next_ids:
                current_step = next_ids[0]
                console.print(
                    f"[dim]  advanced to plan step "
                    f"{current_step}[/dim]"
                )

        if call.tool == "human_ask":
            run.status = "needs_human"

    evidence = _collect_evidence(run)

    verification = run_verify(
        task,
        evidence,
        llm,
    )

    run.verification = verification

    run.final_summary = llm.chat(
        "Summarize the completed task briefly.",
        f"task: {task}\nevidence: {evidence}",
    )

    if verification.verified and run.status == "running":
        run.status = "done"

    return run


def _collect_evidence(run: AgentRun) -> list[str]:
    ev: list[str] = []

    for t in run.trace:
        call = t["call"]
        obs = t["obs"]

        if not obs.get("ok"):
            continue

        if call["tool"] == "files_read":
            ev.append(
                f"Read file: {obs['output'].get('path')}"
            )

        elif call["tool"] == "browser_fill_and_submit":
            ev.append(
                f"Submitted to tracker: {obs['output']}"
            )

        elif call["tool"] == "internal_api_get":
            ev.append(
                f"Tracker GET: {obs['output']}"
            )

    return ev