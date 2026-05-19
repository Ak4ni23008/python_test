"""
Web UI: click Run → job.run() executes on the Railway server (cloud), not on your laptop.

Deploy this once to Railway. After that, only push to Git when you change job.py code.
"""

from __future__ import annotations

import streamlit as st

from job import run

st.set_page_config(
  page_title="Cloud Runner",
  page_icon="☁️",
  layout="centered",
)

st.title("☁️ Cloud Runner")
st.caption("Click **Run** — code runs on Railway, not on your PC.")

col1, col2 = st.columns(2)
with col1:
  run_clicked = st.button("▶ Run", type="primary", use_container_width=True)
with col2:
  st.caption("No git push needed per run.")

st.markdown("---")

if run_clicked:
  with st.spinner("Running in the cloud…"):
    try:
      output = run()
      st.success("Completed on Railway server")
      st.text_area("Output", value=output, height=320)
    except Exception as exc:
      st.error(f"Failed: {exc}")

st.markdown(
  """
**How it works**
1. This page stays online on Railway (one-time deploy).
2. Each **Run** click runs `job.py` on the server.
3. Change code → `git push` once → Railway redeploys → click Run again.

Later: put `CLIENT_ID` and `ACCESS_TOKEN` in Railway **Variables**, then edit `job.py`.
"""
)
