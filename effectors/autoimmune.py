#!/usr/bin/env python3
from __future__ import annotations

"""
PreToolUse hook — meta-spiral guard.

Prevents productive-feeling meta-work (garden posts via sarcio) from
displacing deadline work. If 3+ sarcio invocations in this session AND
no Praxis.md items due within 7 days have been completed, blocks further
sarcio calls.

State: ~/.claude/meta-spiral-state.json
Input: PreToolUse JSON on stdin (tool_input.skill, session_id)
Output: JSON with hookSpecificOutput.permissionDecision = "deny" to block.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

from metabolon.locus import praxis

STATE_FILE = Path.home() / ".claude" / "meta-spiral-state.json"
PRAXIS_FILE = praxis
LOG_FILE = Path.home() / "logs" / "hook-fire-log.jsonl"
THRESHOLD = 3


def log_fire(reason: str) -> None:
    try:
        entry = json.dumps(
            {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "hook": "meta-spiral-guard",
                "rule": reason[:80],
            }
        )
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a") as f:
            f.write(entry + "\n")
    except OSError:
        pass


def deny(reason: str) -> None:
    log_fire(reason)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state: dict) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state))
    except OSError:
        pass


def has_open_items_due_within_days(days: int = 7) -> bool:
    """Parse Praxis.md for incomplete items with due: dates within N days of today."""
    if not PRAXIS_FILE.exists():
        return False

    today = datetime.now().date()
    horizon = today + timedelta(days=days)
    due_pattern = re.compile(r"`due:(\d{4}-\d{2}-\d{2})`")

    try:
        for line in PRAXIS_FILE.read_text(encoding="utf-8").splitlines():
            # Only incomplete items: starts with "- [ ]"
            stripped = line.strip()
            if not stripped.startswith("- [ ]"):
                continue
            m = due_pattern.search(stripped)
            if not m:
                continue
            try:
                due_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
            except ValueError:
                continue
            if due_date <= horizon:
                return True
    except OSError:
        pass

    return False


def main():
    parser = argparse.ArgumentParser(description="PreToolUse hook — meta-spiral guard. Blocks excessive sarcio calls when deadline work is pending.")
    parser.parse_args()

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Only care about sarcio skill invocations
    skill_name = data.get("tool_input", {}).get("skill", "")
    if not skill_name.startswith("sarcio"):
        sys.exit(0)

    session_id = data.get("session_id", "")
    if not session_id:
        sys.exit(0)

    # Load and update state
    state = load_state()

    # Reset counter on new session
    if state.get("session_id") != session_id:
        state = {"session_id": session_id, "sarcio_count": 0}

    state["sarcio_count"] = state.get("sarcio_count", 0) + 1
    save_state(state)

    # Below threshold — allow
    if state["sarcio_count"] < THRESHOLD:
        sys.exit(0)

    # At or above threshold — check for deadline items
    if has_open_items_due_within_days(7):
        deny(
            f"[meta-spiral] Blocked: {state['sarcio_count']} garden posts this session "
            f"with open Praxis.md items due within 7 days. "
            f"Finish a deadline item before publishing more. "
            f"Run: grep 'due:' ~/epigenome/chromatin/Praxis.md to see what's urgent."
        )

    # No deadline items due soon — allow freely
    sys.exit(0)


if __name__ == "__main__":
    main()
