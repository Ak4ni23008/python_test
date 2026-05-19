"""
Railway trading app — Backtest, Live Trading, Custom Code.

Run: uvicorn server:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import io
import os
import uuid
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, time as dtime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from backtest_20min import BacktestConfig, backtest
from code_runner import run_python_code
from github_push import push_file
from live_trade_0920_0921 import LiveConfig, YES_BANK_SECURITY_ID, run_once
from web_ui import esc, page

app = FastAPI(title="Trading App")

ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
DEFAULT_CSV = ROOT / "yesbank_5m.csv"
USER_CODE_FILE = ROOT / "user_code.py"
IST = ZoneInfo("Asia/Kolkata")

DEFAULT_CODE = (
    USER_CODE_FILE.read_text(encoding="utf-8")
    if USER_CODE_FILE.exists()
    else "for i in range(1, 11):\n    print(i)\n"
)


def _capture_output(fn) -> tuple[str, str, int]:
    out = io.StringIO()
    err = io.StringIO()
    code = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = fn()
            if code is None:
                code = 0
    except Exception as exc:
        err.write(str(exc))
        code = 1
    return out.getvalue(), err.getvalue(), int(code)


def _parse_hhmm(s: str) -> dtime:
    hh, mm = s.strip().split(":")
    return dtime(int(hh), int(mm))


def _dhan_status() -> str:
    cid = os.getenv("DHAN_CLIENT_ID", "")
    tok = os.getenv("DHAN_ACCESS_TOKEN", "")
    if cid and tok:
        return f"Dhan keys configured (client …{cid[-4:]})"
    return "Dhan keys NOT set — add DHAN_CLIENT_ID & DHAN_ACCESS_TOKEN in Railway Variables"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    body = """
<div class="card">
  <p>All modules run on <strong>Railway cloud</strong> when you click Run.</p>
  <div class="metrics">
    <div class="metric"><b>Backtesting</b><span>Test strategy on CSV data</span></div>
    <div class="metric"><b>Live Trading</b><span>Dhan orders (Yes Bank)</span></div>
    <div class="metric"><b>Custom Code</b><span>Paste & run Python</span></div>
  </div>
  <p class="hint">""" + esc(_dhan_status()) + """</p>
</div>
"""
    return HTMLResponse(page("Dashboard", "/", body))


@app.get("/backtest", response_class=HTMLResponse)
def backtest_form() -> HTMLResponse:
    return HTMLResponse(page("Backtesting", "/backtest", backtest_form_body()))


@app.post("/backtest/run", response_class=HTMLResponse)
async def backtest_run(
    entry_mode: str = Form("buy_0915_sell_0935"),
    quantity: int = Form(1),
    hold_minutes: int = Form(20),
    brokerage: float = Form(20.0),
    slippage: float = Form(5.0),
    price_field: str = Form("open"),
    csv_file: UploadFile | None = File(None),
) -> HTMLResponse:
    csv_path = DEFAULT_CSV
    if csv_file and csv_file.filename:
        dest = UPLOAD_DIR / f"{uuid.uuid4().hex}_{csv_file.filename}"
        content = await csv_file.read()
        dest.write_bytes(content)
        csv_path = dest

    cfg = BacktestConfig(
        csv_path=str(csv_path),
        entry_mode=entry_mode,  # type: ignore[arg-type]
        entry_price=price_field,  # type: ignore[arg-type]
        exit_price=price_field,  # type: ignore[arg-type]
        hold_minutes=hold_minutes,
        quantity=quantity,
        brokerage_per_trade=brokerage,
        slippage_bps=slippage,
    )

    try:
        trades, stats = backtest(cfg)
        lines = ["=== STATS ==="]
        for k, v in stats.items():
            lines.append(f"{k}: {v}")
        lines.append("\n=== LAST 10 TRADES ===")
        if len(trades):
            lines.append(trades.tail(10).to_string(index=False))
        else:
            lines.append("No trades.")
        output = "\n".join(lines)
        return HTMLResponse(page("Backtesting", "/backtest", backtest_form_body(), output=output))
    except Exception as exc:
        return HTMLResponse(page("Backtesting", "/backtest", backtest_form_body(), error=str(exc)))


def backtest_form_body() -> str:
    return f"""
<form method="post" action="/backtest/run" enctype="multipart/form-data" class="card">
  <p class="hint">Upload OHLC CSV or use demo <code>{esc(DEFAULT_CSV.name)}</code></p>
  <label>CSV file (optional)</label>
  <input type="file" name="csv_file" accept=".csv"/>
  <div class="row">
    <div><label>Entry mode</label>
      <select name="entry_mode">
        <option value="buy_0915_sell_0935">Buy 09:15 → Sell 09:35</option>
        <option value="first_bar_each_day">First bar each day</option>
        <option value="every_bar">Every bar</option>
      </select></div>
    <div><label>Quantity</label><input type="number" name="quantity" value="1" min="1"/></div>
  </div>
  <div class="row">
    <div><label>Hold minutes</label><input type="number" name="hold_minutes" value="20"/></div>
    <div><label>Brokerage</label><input type="number" name="brokerage" value="20" step="0.01"/></div>
  </div>
  <div class="row">
    <div><label>Slippage (bps)</label><input type="number" name="slippage" value="5"/></div>
    <div><label>Price field</label>
      <select name="price_field"><option value="open">open</option><option value="close">close</option></select></div>
  </div>
  <button type="submit" class="primary">▶ Run Backtest</button>
</form>"""


@app.get("/live", response_class=HTMLResponse)
def live_form() -> HTMLResponse:
    body = f"""
<form method="post" action="/live/run" class="card">
  <p class="warn" style="padding:0.75rem;border-radius:8px;background:#451a03;">
    ⚠ Live trading places real orders when Dry Run is OFF. Test with Dry Run first.
  </p>
  <p class="hint">{esc(_dhan_status())}</p>
  <div class="row">
    <div><label>Quantity</label><input type="number" name="quantity" value="1" min="1"/></div>
    <div><label>Security ID (Yes Bank default)</label>
      <input type="text" name="security_id" value="{YES_BANK_SECURITY_ID}"/></div>
  </div>
  <div class="row">
    <div><label>Buy time (HH:MM IST)</label><input type="text" name="buy_time" value="11:55"/></div>
    <div><label>Sell time (HH:MM IST)</label><input type="text" name="sell_time" value="11:56"/></div>
  </div>
  <label class="check"><input type="checkbox" name="dry_run" value="1" checked/> Dry Run (no real orders)</label>
  <label class="check"><input type="checkbox" name="instant" value="1" checked/>
    Instant test (buy/sell in ~5 sec — for cloud testing)</label>
  <button type="submit" class="primary">▶ Run Live Strategy</button>
</form>
"""
    return HTMLResponse(page("Live Trading", "/live", body))


@app.post("/live/run", response_class=HTMLResponse)
def live_run(
    quantity: int = Form(1),
    security_id: str = Form(YES_BANK_SECURITY_ID),
    buy_time: str = Form("11:55"),
    sell_time: str = Form("11:56"),
    dry_run: str | None = Form(None),
    instant: str | None = Form(None),
) -> HTMLResponse:
    is_dry = dry_run == "1"
    is_instant = instant == "1"

    if is_instant:
        now = datetime.now(tz=IST)
        buy_t = (now + timedelta(seconds=2)).time().replace(microsecond=0)
        sell_t = (now + timedelta(seconds=5)).time().replace(microsecond=0)
    else:
        buy_t = _parse_hhmm(buy_time)
        sell_t = _parse_hhmm(sell_time)

    cfg = LiveConfig(
        security_id=security_id.strip(),
        quantity=quantity,
        buy_time=buy_t,
        sell_time=sell_t,
        dry_run=is_dry,
    )

    stdout, stderr, code = _capture_output(lambda: run_once(cfg))
    output = stdout or "(no output)"
    error = stderr if code != 0 else ""
    info = "Dry run — no real money." if is_dry else "REAL ORDERS were attempted."

    live_body = f"""
<form method="post" action="/live/run" class="card">
  <div class="row">
    <div><label>Quantity</label><input type="number" name="quantity" value="{quantity}"/></div>
    <div><label>Security ID</label><input type="text" name="security_id" value="{esc(security_id)}"/></div>
  </div>
  <div class="row">
    <div><label>Buy time</label><input type="text" name="buy_time" value="{esc(buy_time)}"/></div>
    <div><label>Sell time</label><input type="text" name="sell_time" value="{esc(sell_time)}"/></div>
  </div>
  <label class="check"><input type="checkbox" name="dry_run" value="1" {"checked" if is_dry else ""}/> Dry Run</label>
  <label class="check"><input type="checkbox" name="instant" value="1" {"checked" if is_instant else ""}/> Instant test</label>
  <button type="submit" class="primary">▶ Run Live Strategy</button>
</form>"""

    return HTMLResponse(page("Live Trading", "/live", live_body, output=output, error=error, info=info))


@app.get("/code", response_class=HTMLResponse)
def code_form() -> HTMLResponse:
    body = f"""
<form method="post" action="/code/run" class="card">
  <label>Python code</label>
  <textarea name="code">{esc(DEFAULT_CODE)}</textarea>
  <button type="submit" class="primary">▶ Run in cloud</button>
  <button type="submit" formaction="/code/save" class="secondary">Save to GitHub</button>
</form>
"""
    return HTMLResponse(page("Custom Code", "/code", body))


@app.post("/code/run", response_class=HTMLResponse)
def code_run(code: str = Form(...)) -> HTMLResponse:
    exit_code, stdout, stderr = run_python_code(code)
    USER_CODE_FILE.write_text(code, encoding="utf-8")
    body = f"""
<form method="post" action="/code/run" class="card">
  <textarea name="code">{esc(code)}</textarea>
  <button type="submit" class="primary">▶ Run in cloud</button>
  <button type="submit" formaction="/code/save" class="secondary">Save to GitHub</button>
</form>"""
    err = stderr or (f"Exit code {exit_code}" if exit_code != 0 else "")
    return HTMLResponse(page("Custom Code", "/code", body, output=stdout, error=err))


@app.post("/code/save", response_class=HTMLResponse)
def code_save(code: str = Form(...)) -> HTMLResponse:
    result = push_file(code, message="Save from Trading App")
    body = f"""
<form method="post" action="/code/run" class="card">
  <textarea name="code">{esc(code)}</textarea>
  <button type="submit" class="primary">▶ Run in cloud</button>
  <button type="submit" formaction="/code/save" class="secondary">Save to GitHub</button>
</form>"""
    if result.get("ok"):
        info = f"Saved: {result.get('html_url', result.get('path', ''))}"
    else:
        info = f"GitHub error: {result.get('error', 'unknown')}"
    return HTMLResponse(page("Custom Code", "/code", body, info=info))


@app.post("/api/run")
async def api_run(payload: dict) -> JSONResponse:
    code = payload.get("code", "")
    if not code.strip():
        return JSONResponse({"ok": False, "error": "No code"}, status_code=400)
    exit_code, stdout, stderr = run_python_code(code)
    return JSONResponse({"ok": exit_code == 0, "stdout": stdout, "stderr": stderr})
