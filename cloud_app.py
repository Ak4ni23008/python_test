"""
Local Streamlit UI — Run calls your Railway server (not this laptop).

Set before running:
  $env:CLOUD_RUNNER_URL = "https://your-app.up.railway.app"
"""

from __future__ import annotations

import os
import socket

import requests
import streamlit as st

from code_runner import USER_CODE_FILE, run_python_code
from github_push import push_file

DEFAULT_CODE = '''for i in range(1, 11):
    print(i)
'''

if USER_CODE_FILE.exists():
    try:
        saved = USER_CODE_FILE.read_text(encoding="utf-8")
        if saved.strip():
            DEFAULT_CODE = saved
    except OSError:
        pass

CLOUD_URL = os.getenv("CLOUD_RUNNER_URL", "").strip().rstrip("/")
LOCAL_HOST = socket.gethostname()

st.set_page_config(page_title="Cloud Code Runner", page_icon="☁️", layout="wide")

st.title("☁️ Cloud Code Runner (local UI)")

if CLOUD_URL:
    st.success(f"Cloud server: `{CLOUD_URL}` — Run will execute **on Railway**")
else:
    st.error(
        "**CLOUD_RUNNER_URL not set** — Run only works on your laptop right now.\n\n"
        "Set your Railway URL:\n"
        "`$env:CLOUD_RUNNER_URL = \"https://your-app.up.railway.app\"`"
    )
    st.info("Or open your **Railway public URL** directly in the browser (no Streamlit needed).")

st.caption(f"This page is on: **{LOCAL_HOST}** (your PC)")

code = st.text_area("Python code", value=DEFAULT_CODE, height=360)

col1, col2 = st.columns(2)
with col1:
    run_clicked = st.button("▶ Run on Railway", type="primary", use_container_width=True)
with col2:
    save_clicked = st.button("Save to GitHub", use_container_width=True)

st.markdown("---")

if run_clicked:
    if not CLOUD_URL:
        st.warning("Running locally instead (no cloud URL set)…")
        exit_code, stdout, stderr = run_python_code(code)
        st.code(stdout or "(no output)")
        if stderr:
            st.error(stderr)
    else:
        with st.spinner(f"Calling Railway at {CLOUD_URL}…"):
            try:
                resp = requests.post(
                    f"{CLOUD_URL}/api/run",
                    json={"code": code},
                    timeout=120,
                )
                data = resp.json()
                st.success(f"Ran on Railway host: `{data.get('host', '?')}`")
                st.code(data.get("stdout") or "(no output)")
                if data.get("stderr"):
                    st.error(data["stderr"])
            except requests.RequestException as exc:
                st.error(f"Could not reach Railway: {exc}")
                st.info("Check Railway deploy is **Active** (not Stopping). Open Railway URL in browser instead.")

if save_clicked:
    result = push_file(code, message="Save from local Cloud Runner")
    if result.get("ok"):
        st.success(f"Pushed: {result.get('html_url', '')}")
    else:
        st.error(result.get("error", "Push failed"))
