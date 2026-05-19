"""
Cloud Code Runner — paste Python, click Run:
  1. Runs on Railway server (immediate)
  2. Pushes to GitHub (saves code; Railway redeploys from repo)
"""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from code_runner import USER_CODE_FILE, run_python_code
from github_push import push_file

IST = ZoneInfo("Asia/Kolkata")

DEFAULT_CODE = '''# Your code runs on Railway — not on your laptop
for i in range(1, 11):
    print(i)
'''

st.set_page_config(
    page_title="Cloud Code Runner",
    page_icon="☁️",
    layout="wide",
)

st.title("☁️ Cloud Code Runner")
st.caption("Paste code → **Run** → executes on Railway + saves to GitHub")

if USER_CODE_FILE.exists():
    try:
        saved = USER_CODE_FILE.read_text(encoding="utf-8")
        if saved.strip():
            DEFAULT_CODE = saved
    except OSError:
        pass

code = st.text_area(
    "Python code",
    value=DEFAULT_CODE,
    height=360,
    help="Edit and click Run. Output appears below.",
)

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    run_clicked = st.button("▶ Run in cloud", type="primary", use_container_width=True)
with col2:
    push_only = st.button("Push to GitHub only", use_container_width=True)

github_ok = bool(os.getenv("GITHUB_TOKEN", "").strip())
with col3:
    if github_ok:
        st.success("GitHub token configured")
    else:
        st.warning("Add `GITHUB_TOKEN` in Railway Variables to push to GitHub")

st.markdown("---")

if run_clicked or push_only:
    steps: list[str] = []

    if run_clicked:
        with st.spinner("Step 1/2 — Running on Railway server…"):
            exit_code, stdout, stderr = run_python_code(code)
            steps.append("Ran on Railway server")

        st.subheader("Output")
        if stdout:
            st.code(stdout, language="text")
        if stderr:
            st.subheader("Errors")
            st.code(stderr, language="text")

        if exit_code == 0:
            st.success(f"Finished (exit code {exit_code})")
        else:
            st.error(f"Finished with exit code {exit_code}")

    if run_clicked or push_only:
        with st.spinner("Step 2/2 — Pushing to GitHub…"):
            ts = datetime.now(tz=IST).strftime("%Y-%m-%d %H:%M:%S IST")
            result = push_file(
                code,
                message=f"Cloud Runner update {ts}",
            )

        if result.get("ok"):
            st.success("Pushed to GitHub")
            if result.get("html_url"):
                st.markdown(f"[View commit]({result['html_url']})")
            st.caption(
                f"Repo: `{result.get('repo')}` · branch: `{result.get('branch')}` · "
                f"file: `{result.get('path')}`"
            )
            st.info(
                "Railway will redeploy from GitHub in the background (usually 1–3 min). "
                "Your code already ran on the server above."
            )
        else:
            st.error(result.get("error", "GitHub push failed"))
