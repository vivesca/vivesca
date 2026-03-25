#!/usr/bin/env python3
"""Anabolism stop guard — prevents the model from stopping during INTERACTIVE anabolism sessions.

Safety net for when Terry says "anabolism" and walks away (supply-driven build).
Uses ~/tmp/.anabolism-guard-active as the signal file.
"""

import json
import subprocess
import sys
from pathlib import Path

GUARD_LOCK = Path.home() / "tmp" / ".anabolism-guard-active"


def get_budget_status() -> str:
    try:
        result = subprocess.run(
            ["respirometry-cached", "--budget"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip().lower() or "unknown"
    except Exception:
        return "unknown"


def main():
    hook_input = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}

    if hook_input.get("stop_hook_active", False):
        return

    if not GUARD_LOCK.exists():
        return

    budget = get_budget_status()

    if budget == "green":
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        "[ANABOLISM GUARD] Budget GREEN, interactive anabolism active. "
                        "Keep dispatching. Read ~/tmp/anabolism-session.md."
                    ),
                }
            )
        )
    elif budget == "yellow":
        print(
            json.dumps(
                {
                    "reason": (
                        "[ANABOLISM GUARD] Budget YELLOW. Finish current wave, "
                        "write report, then stop."
                    )
                }
            )
        )


if __name__ == "__main__":
    main()
