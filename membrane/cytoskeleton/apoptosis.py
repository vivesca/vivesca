#!/usr/bin/env python3
"""apoptosis.py — StopFailure hook handler.

Fires when a turn ends due to an API error (rate limit, auth, server).
Logs to ~/logs/stop-failures.jsonl for observability.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
LOG_FILE = HOME / "logs" / "stop-failures.jsonl"


def classify(error: dict) -> str:
    """Classify the error into a category."""
    code = str(error.get("code", "")).lower()
    message = str(error.get("message", "")).lower()
    combined = code + " " + message

    if "rate_limit" in combined or "rate limit" in combined or "429" in combined:
        return "rate_limit"
    if "auth" in combined or "permission" in combined or "401" in combined or "403" in combined:
        return "auth_failure"
    if "server" in combined or "500" in combined or "502" in combined or "503" in combined:
        return "server_error"
    return "unknown"


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    error = data.get("error", {}) or {}
    stop_reason = str(data.get("stopReason", ""))[:200]
    category = classify(error)

    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "category": category,
        "reason": stop_reason,
        "error_code": error.get("code", ""),
    }

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a") as logfile:
            logfile.write(json.dumps(entry) + "\n")
    except OSError:
        pass

    labels = {
        "rate_limit": "Rate limited",
        "auth_failure": "Auth failure",
        "server_error": "Server error",
        "unknown": "API error",
    }
    print(f"[apoptosis] {labels[category]}: {stop_reason[:100]}")


if __name__ == "__main__":
    main()
