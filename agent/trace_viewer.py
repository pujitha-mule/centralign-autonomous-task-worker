from __future__ import annotations
import html
import json
from .schemas import AgentRun

TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8">
<title>Agent Trace — {task}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif;
         background:#0f1115; color:#e6e6e6; margin:0; padding:24px; }}
  h1 {{ font-size:18px; margin:0 0 4px; }}
  .task {{ color:#9aa4b2; margin-bottom:20px; }}
  .step {{ border:1px solid #23262d; border-radius:10px;
           padding:14px 16px; margin-bottom:12px; background:#161a20; }}
  .step-header {{ display:flex; justify-content:space-between; align-items:center; }}
  .tool {{ font-weight:600; color:#7cc4ff; }}
  .ok {{ color:#5ddc8b; font-weight:600; }}
  .fail {{ color:#ff6b6b; font-weight:600; }}
  .reason {{ color:#9aa4b2; font-size:13px; margin:6px 0; }}
  pre {{ background:#0b0d11; padding:10px; border-radius:6px;
         overflow-x:auto; font-size:12px; color:#cfd6e4; }}
  .badge {{ background:#23262d; padding:2px 8px; border-radius:999px;
            font-size:11px; color:#9aa4b2; margin-left:6px; }}
  .verified {{ background:#12351f; border-color:#1f6f3f; }}
  .not-verified {{ background:#3a1414; border-color:#7a2626; }}
</style></head><body>
  <h1>Agent Trace</h1>
  <div class="task">{task}</div>
  {steps}
  <div class="step {verify_class}">
    <div class="step-header">
      <span class="tool">VERIFICATION</span>
      <span class="{verify_ok}">{verify_text}</span>
    </div>
    <pre>{verify_body}</pre>
  </div>
</body></html>
"""


def render(run: AgentRun, out_path: str) -> str:
    steps_html = []
    for t in run.trace:
        call = t["call"]; obs = t["obs"]
        attempts = t.get("attempts", [])
        retry_badge = (
            f'<span class="badge">retries: {len(attempts) - 1}</span>'
            if len(attempts) > 1 else ""
        )
        status_cls = "ok" if obs.get("ok") else "fail"
        status_txt = "OK" if obs.get("ok") else "FAIL"
        body = {
            "args": call.get("args"),
            "observation": obs.get("output") if obs.get("ok") else obs.get("error"),
            "attempts": attempts,
        }
        steps_html.append(f"""
        <div class="step">
          <div class="step-header">
            <span class="tool">#{t['step']} {call['tool']}</span>
            <span class="{status_cls}">{status_txt}{retry_badge}</span>
          </div>
          <div class="reason">{html.escape(call.get('reason', ''))}</div>
          <pre>{html.escape(json.dumps(body, indent=2))}</pre>
        </div>""")

    v = run.verification
    verify_ok = "ok" if (v and v.verified) else "fail"
    verify_text = "VERIFIED" if (v and v.verified) else "NOT VERIFIED"
    verify_class = "verified" if (v and v.verified) else "not-verified"
    verify_body = json.dumps(v.model_dump() if v else {}, indent=2)

    html_out = TEMPLATE.format(
        task=html.escape(run.task),
        steps="\n".join(steps_html),
        verify_ok=verify_ok,
        verify_text=verify_text,
        verify_class=verify_class,
        verify_body=html.escape(verify_body),
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)
    return out_path