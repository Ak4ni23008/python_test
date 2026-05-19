"""
Railway backend — paste code in browser, click Run, executes HERE in the cloud.

Run locally:  python -m uvicorn server:app --host 0.0.0.0 --port 8080
Railway:      uvicorn server:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import os
import socket
from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse

from code_runner import run_python_code
from github_push import push_file

app = FastAPI(title="Cloud Code Runner")

ROOT = Path(__file__).resolve().parent
USER_CODE_FILE = ROOT / "user_code.py"

DEFAULT_CODE = USER_CODE_FILE.read_text(encoding="utf-8") if USER_CODE_FILE.exists() else (
    "for i in range(1, 11):\n    print(i)\n"
)

HOSTNAME = socket.gethostname()
IS_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))


def _page_html(code: str, output: str = "", error: str = "", gh_msg: str = "") -> str:
    esc = (
        lambda s: s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    where = "☁️ Railway cloud" if IS_RAILWAY else f"💻 This machine ({HOSTNAME})"
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"/>
<title>Cloud Code Runner</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; background: #0f172a; color: #e2e8f0; }}
  h1 {{ margin-bottom: 0.25rem; }}
  .badge {{ display: inline-block; padding: 0.35rem 0.75rem; border-radius: 8px; background: #1e293b; margin-bottom: 1rem; font-size: 0.9rem; }}
  textarea {{ width: 100%; height: 280px; font-family: ui-monospace, monospace; font-size: 14px; padding: 12px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #f1f5f9; box-sizing: border-box; }}
  button {{ margin-top: 12px; margin-right: 8px; padding: 10px 20px; font-size: 16px; border: none; border-radius: 8px; cursor: pointer; }}
  .run {{ background: #2563eb; color: white; }}
  .save {{ background: #475569; color: white; }}
  pre {{ background: #1e293b; padding: 16px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; border: 1px solid #334155; }}
  .ok {{ color: #4ade80; }} .err {{ color: #f87171; }} .info {{ color: #93c5fd; }}
  .hint {{ color: #94a3b8; font-size: 0.9rem; margin-top: 1rem; }}
</style></head><body>
<h1>☁️ Cloud Code Runner</h1>
<p class="badge">Running on: <strong>{esc(where)}</strong></p>
<p class="hint">Use your <strong>Railway public URL</strong> (not localhost) to run in the cloud.</p>
<form method="post" action="/run">
  <label for="code"><strong>Python code</strong></label><br/>
  <textarea id="code" name="code">{esc(code)}</textarea><br/>
  <button type="submit" class="run">▶ Run in cloud</button>
  <button type="submit" formaction="/save" class="save">Save to GitHub</button>
</form>
{"<h3>Output</h3><pre class='ok'>" + esc(output) + "</pre>" if output else ""}
{"<h3>Errors</h3><pre class='err'>" + esc(error) + "</pre>" if error else ""}
{"<p class='info'>" + esc(gh_msg) + "</p>" if gh_msg else ""}
</body></html>"""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return HTMLResponse(_page_html(DEFAULT_CODE))


@app.post("/run", response_class=HTMLResponse)
def run_code(code: str = Form(...)) -> HTMLResponse:
    exit_code, stdout, stderr = run_python_code(code)
    USER_CODE_FILE.write_text(code, encoding="utf-8")
    err = stderr
    if exit_code != 0 and not err:
        err = f"Exit code {exit_code}"
    return HTMLResponse(_page_html(code, output=stdout, error=err))


@app.post("/save", response_class=HTMLResponse)
def save_code(code: str = Form(...)) -> HTMLResponse:
    result = push_file(code, message="Save from Cloud Code Runner")
    if result.get("ok"):
        msg = f"Saved to GitHub: {result.get('html_url', result.get('path', ''))}"
    else:
        msg = f"GitHub error: {result.get('error', 'unknown')}"
    return HTMLResponse(_page_html(code, gh_msg=msg))


@app.post("/api/run")
async def api_run(payload: dict) -> JSONResponse:
    """Remote run — local Streamlit can call this."""
    code = payload.get("code", "")
    if not code.strip():
        return JSONResponse({"ok": False, "error": "No code provided"}, status_code=400)
    exit_code, stdout, stderr = run_python_code(code)
    return JSONResponse({
        "ok": exit_code == 0,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "host": HOSTNAME,
        "railway": IS_RAILWAY,
    })
