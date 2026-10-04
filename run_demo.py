from __future__ import annotations
import subprocess
import sys
import time
from pathlib import Path

import httpx
from rich.console import Console
from rich.pretty import pprint

from agent import run_agent
from agent.trace_viewer import render

console = Console()
TASK = (
    "Find the latest invoice from Acme Corp in the invoices folder, "
    "extract the amount and due date, enter it into our internal tracker, "
    "and confirm it's done."
)


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
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mock_company.server:app",
         "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"],
    )
    try:
        wait_for_server("http://127.0.0.1:8000/")
        console.rule("[bold green]TASK")
        console.print(TASK)

        result = run_agent(TASK)

        console.rule("[bold]TRACE")
        pprint([{
            "step": t["step"],
            "tool": t["call"]["tool"],
            "ok": t["obs"]["ok"],
            "retries": max(0, len(t.get("attempts", [])) - 1),
        } for t in result.trace])

        console.rule("[bold]VERIFICATION")
        pprint(result.verification.model_dump() if result.verification else None)

        console.rule("[bold]SUMMARY")
        console.print(result.final_summary)
        console.print(f"\nStatus: [bold]{result.status}[/bold]")

        out_dir = Path("eval_out"); out_dir.mkdir(exist_ok=True)
        out = render(result, str(out_dir / "demo.html"))
        console.print(f"\n[bold]Trace written to:[/bold] {out}")
        return 0 if result.status == "done" else 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:
            server.kill()


if __name__ == "__main__":
    raise SystemExit(main())