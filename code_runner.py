"""Run pasted Python on the Railway server (subprocess)."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
USER_CODE_FILE = ROOT / "user_code.py"
DEFAULT_TIMEOUT = 60


def save_user_code(source: str) -> Path:
    USER_CODE_FILE.write_text(source, encoding="utf-8")
    return USER_CODE_FILE


def run_python_code(source: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    """Execute source in a subprocess; return (exit_code, stdout, stderr)."""
    save_user_code(source)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(source)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT),
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Timed out after {timeout} seconds."
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
