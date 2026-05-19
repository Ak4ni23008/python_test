"""
Your logic runs HERE — on the Railway server when someone clicks Run in the browser.

Replace this function later with Dhan trading code (use env vars for CLIENT_ID / TOKEN).
"""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def run() -> str:
  """
  Called from cloud_app.py when the user clicks Run.
  Return text to show on the webpage; print() also goes to Railway deploy logs.
  """
  lines: list[str] = []
  now = datetime.now(tz=IST).strftime("%Y-%m-%d %H:%M:%S IST")
  lines.append(f"Started at {now}")
  lines.append("")
  lines.append("Numbers 1 to 10:")

  for i in range(1, 11):
    print(i, flush=True)
    lines.append(str(i))

  # Later: read Dhan keys from Railway Variables (not from your laptop)
  client_id = os.getenv("DHAN_CLIENT_ID", "")
  if client_id:
    lines.append("")
    lines.append(f"Dhan CLIENT_ID is set (ends with …{client_id[-4:]})")
  else:
    lines.append("")
    lines.append("Dhan CLIENT_ID not set yet — add DHAN_CLIENT_ID in Railway Variables when ready.")

  lines.append("")
  lines.append("Finished OK.")
  return "\n".join(lines)
