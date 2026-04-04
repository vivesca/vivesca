#!/usr/bin/env python3
"""
respirometry-autolog — logs Claude Code usage every 30 minutes.
Runs as a UserPromptSubmit hook. Checks staleness of last log entry
and skips if <30 min old. Runs respirometry log silently in background.

On the FIRST prompt of a session, always fires immediately (token is
freshest at session start). Uses a random session_id to detect new sessions.

Hook context: runs inside CC session where Keychain token is valid.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

STATE_FILE = Path.home() / ".local/share/respirometry/autolog-state.json"
INTERVAL_SEC = 1800  # 30 minutes


def main():
    now = time.time()
    state = {}
    is_new_session = True

    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError, OSError:
            state = {}

    # Detect new session: no session_id in state means first prompt
    current_session_id = state.get("session_id")
    if current_session_id:
        is_new_session = False
        # Existing session — check interval
        last = state.get("last_log", 0)
        if now - last < INTERVAL_SEC:
            sys.exit(0)

    # New session: generate session_id and always fire
    if is_new_session:
        state["session_id"] = str(uuid.uuid4())

    # Run respirometry log silently — don't block the hook
    try:
        subprocess.Popen(
            ["respirometry", "log", "--note", "autolog"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        sys.exit(0)  # respirometry not installed, skip silently

    # Update state
    state["last_log"] = now
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))


if __name__ == "__main__":
    main()
