"""Shared HTML layout for the Railway trading app."""

from __future__ import annotations

import os
import socket

HOSTNAME = socket.gethostname()
IS_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def where_label() -> str:
    return "☁️ Railway cloud" if IS_RAILWAY else f"💻 {HOSTNAME}"


CSS = """
  body { font-family: system-ui, sans-serif; max-width: 980px; margin: 0 auto; padding: 1rem 1.25rem 2rem;
         background: #0f172a; color: #e2e8f0; }
  h1 { margin: 0 0 0.25rem; font-size: 1.75rem; }
  h2 { margin-top: 0; color: #94a3b8; font-size: 1rem; font-weight: 500; }
  nav { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0 1.5rem; }
  nav a { color: #93c5fd; text-decoration: none; padding: 0.4rem 0.75rem; border-radius: 8px;
          background: #1e293b; border: 1px solid #334155; font-size: 0.9rem; }
  nav a:hover, nav a.active { background: #2563eb; color: white; border-color: #2563eb; }
  .badge { display: inline-block; padding: 0.35rem 0.75rem; border-radius: 8px; background: #1e293b;
           margin-bottom: 0.5rem; font-size: 0.85rem; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; }
  label { display: block; margin: 0.75rem 0 0.25rem; font-size: 0.9rem; color: #cbd5e1; }
  input[type=text], input[type=number], select, textarea {
    width: 100%; box-sizing: border-box; padding: 0.5rem 0.65rem; border-radius: 8px;
    border: 1px solid #475569; background: #0f172a; color: #f1f5f9; font-size: 0.95rem; }
  textarea { font-family: ui-monospace, monospace; min-height: 200px; }
  input[type=file] { margin-top: 0.25rem; color: #cbd5e1; }
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  @media (max-width: 640px) { .row { grid-template-columns: 1fr; } }
  button, .btn { margin-top: 1rem; margin-right: 0.5rem; padding: 0.65rem 1.25rem; font-size: 0.95rem;
                 border: none; border-radius: 8px; cursor: pointer; }
  .primary { background: #2563eb; color: white; }
  .secondary { background: #475569; color: white; }
  .warn { background: #b45309; color: white; }
  pre.out { background: #0f172a; padding: 1rem; border-radius: 8px; overflow-x: auto;
            white-space: pre-wrap; border: 1px solid #334155; color: #4ade80; font-size: 0.85rem; }
  pre.err { color: #f87171; }
  .info { color: #93c5fd; font-size: 0.9rem; }
  .hint { color: #64748b; font-size: 0.85rem; margin-top: 0.5rem; }
  .metrics { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 0.75rem; }
  .metric { background: #0f172a; padding: 0.75rem; border-radius: 8px; border: 1px solid #334155; }
  .metric b { display: block; font-size: 1.1rem; color: #4ade80; }
  .metric span { font-size: 0.75rem; color: #94a3b8; }
  input[type=checkbox] { width: auto; margin-right: 0.5rem; }
  .check { display: flex; align-items: center; margin-top: 0.75rem; }
  .tabs-bar { display: flex; gap: 0.35rem; margin-bottom: 1rem; }
  .tab-btn { padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #334155; background: #1e293b;
             color: #94a3b8; cursor: pointer; font-size: 0.9rem; margin-top: 0; }
  .tab-btn.active { background: #2563eb; color: white; border-color: #2563eb; }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }
  textarea.code-editor { min-height: 320px; }
"""

TAB_SCRIPT = """
<script>
document.querySelectorAll('.tabs-bar').forEach(function(bar) {
  var panels = bar.parentElement.querySelectorAll('.tab-panel');
  bar.querySelectorAll('.tab-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var tab = btn.getAttribute('data-tab');
      bar.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
      panels.forEach(function(p) { p.classList.remove('active'); });
      btn.classList.add('active');
      var panel = bar.parentElement.querySelector('#tab-' + tab);
      if (panel) panel.classList.add('active');
    });
  });
});
</script>
"""


def module_tabs(
    form_html: str,
    code_html: str,
    *,
    active: str = "form",
) -> str:
    form_active = "active" if active == "form" else ""
    code_active = "active" if active == "code" else ""
    form_btn = "active" if active == "form" else ""
    code_btn = "active" if active == "code" else ""
    html = f"""
<div class="card" style="padding-top:0.75rem;">
  <div class="tabs-bar">
    <button type="button" class="tab-btn {form_btn}" data-tab="form">📋 Form</button>
    <button type="button" class="tab-btn {code_btn}" data-tab="code">⌨️ Write Code</button>
  </div>
  <div id="tab-form" class="tab-panel {form_active}">{form_html}</div>
  <div id="tab-code" class="tab-panel {code_active}">{code_html}</div>
</div>
{TAB_SCRIPT}"""
    return html


def nav(active: str) -> str:
    links = [
        ("/", "Home"),
        ("/backtest", "Backtesting"),
        ("/live", "Live Trading"),
        ("/code", "Custom Code"),
    ]
    parts = []
    for href, label in links:
        cls = ' class="active"' if href == active else ""
        parts.append(f'<a href="{href}"{cls}>{label}</a>')
    return "<nav>" + "".join(parts) + "</nav>"


def page(title: str, active: str, body: str, output: str = "", error: str = "", info: str = "") -> str:
    out_block = f"<h3>Output</h3><pre class='out'>{esc(output)}</pre>" if output else ""
    err_block = f"<h3>Error</h3><pre class='out err'>{esc(error)}</pre>" if error else ""
    info_block = f"<p class='info'>{esc(info)}</p>" if info else ""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>{esc(title)}</title>
<style>{CSS}</style></head><body>
<h1>📈 Trading App</h1>
<h2>{esc(title)}</h2>
<p class="badge">Running on: <strong>{esc(where_label())}</strong></p>
{nav(active)}
{body}
{out_block}{err_block}{info_block}
</body></html>"""
