import json
import subprocess
import sys
import time
from pathlib import Path

import httpx
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import run_agent, LLM

from agent.trace_viewer import render
from tasks.suite import TASKS

console = Console()
OUT_DIR = Path("eval_out")


def wait_for_server(url: str, timeout: float = 10.0) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            httpx.get(url, timeout=1)
            return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError("Mock server did not start")


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mock_company.server:app",
         "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"],
    )
    results = []
    try:
        wait_for_server("http://127.0.0.1:8000/")
        llm = LLM()
        for spec in TASKS:
            console.rule(f"[bold]TASK: {spec.name}")
            run = run_agent(spec.instruction, llm=llm, namespace=spec.namespace)

            evidence_blob = json.dumps(
                [t["obs"]["output"] for t in run.trace if t["obs"].get("ok")],
                default=str,
            )
            evidence_ok = spec.expected_evidence in evidence_blob
            success = bool(run.verification and run.verification.verified and evidence_ok)

            html_path = OUT_DIR / f"{spec.name}.html"
            render(run, str(html_path))

            results.append({
                "task": spec.name,
                "status": run.status,
                "verified": bool(run.verification and run.verification.verified),
                "evidence_ok": evidence_ok,
                "success": success,
                "html": str(html_path),
                "steps": len(run.trace),
            })

        table = Table(title="Evaluation Results")
        for col in ("task", "status", "verified", "evidence_ok", "success", "steps"):
            table.add_column(col)
        for r in results:
            table.add_row(
                r["task"], r["status"], str(r["verified"]),
                str(r["evidence_ok"]), str(r["success"]), str(r["steps"]),
            )
        console.print(table)

        passed = sum(1 for r in results if r["success"])
        console.print(f"\n[bold]Success rate: {passed}/{len(results)}[/bold]")
        with open(OUT_DIR / "results.json", "w") as f:
            json.dump(results, f, indent=2)
        return 0 if passed == len(results) else 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:
            server.kill()


if __name__ == "__main__":
    raise SystemExit(main())