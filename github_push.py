"""Push user_code.py to GitHub via API (no git CLI needed on Railway)."""

from __future__ import annotations

import base64
import os
from typing import Any

import requests

DEFAULT_REPO = "Ak4ni23008/python_test"
DEFAULT_BRANCH = "main"
DEFAULT_PATH = "user_code.py"


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def push_file(
    content: str,
    *,
    path: str = DEFAULT_PATH,
    message: str = "Update code from Cloud Runner",
    token: str | None = None,
    repo: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    token = (token or os.getenv("GITHUB_TOKEN", "")).strip()
    repo = (repo or os.getenv("GITHUB_REPO", DEFAULT_REPO)).strip()
    branch = (branch or os.getenv("GITHUB_BRANCH", DEFAULT_BRANCH)).strip()

    if not token:
        return {
            "ok": False,
            "error": "GITHUB_TOKEN not set. Add it in Railway → Variables.",
        }

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    hdrs = _headers(token)

    sha: str | None = None
    get_resp = requests.get(url, headers=hdrs, params={"ref": branch}, timeout=30)
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
    elif get_resp.status_code not in (404,):
        return {
            "ok": False,
            "error": f"GitHub read failed ({get_resp.status_code}): {get_resp.text[:300]}",
        }

    body: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha

    put_resp = requests.put(url, headers=hdrs, json=body, timeout=30)
    if put_resp.status_code not in (200, 201):
        return {
            "ok": False,
            "error": f"GitHub push failed ({put_resp.status_code}): {put_resp.text[:300]}",
        }

    data = put_resp.json()
    return {
        "ok": True,
        "commit_sha": data.get("commit", {}).get("sha", ""),
        "html_url": data.get("commit", {}).get("html_url", ""),
        "repo": repo,
        "branch": branch,
        "path": path,
    }
