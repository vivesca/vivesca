#!/usr/bin/env python3
"""Oghma daemon health check — logs state changes, auto-restarts daemon if needed.

Checks:
1. Is the daemon process running? (launchctl)
2. Is the last extraction recent? (<18h — overnight gap is naturally 8-12h)
3. Is the binary path valid? (symlink target exists)

Run via cron every 2h. Logs on state changes only. No TG alerts — check ~/logs/oghma-health.log.
"""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

STATE_FILE = Path.home() / ".oghma" / "health-state.json"
DB_PATH = Path.home() / ".oghma" / "oghma.db"
BINARY_PATH = Path.home() / ".local" / "bin" / "oghma"
STALENESS_THRESHOLD_HOURS = 18  # Overnight gap (end-of-day → morning session) is naturally 8-12h


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_alert": None, "last_status": "ok"}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state))


PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / "com.oghma.daemon.plist"


def check_daemon_running() -> bool:
    try:
        r = subprocess.run(
            ["launchctl", "list", "com.oghma.daemon"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.returncode == 0 and "PID" in r.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def restart_daemon() -> bool:
    """Auto-restart the Oghma daemon via launchctl."""
    try:
        subprocess.run(
            ["launchctl", "unload", str(PLIST_PATH)],
            capture_output=True, timeout=10,
        )
        r = subprocess.run(
            ["launchctl", "load", str(PLIST_PATH)],
            capture_output=True, timeout=10,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_binary_valid() -> bool:
    return BINARY_PATH.exists() and os.access(BINARY_PATH, os.X_OK)


def check_extraction_fresh() -> tuple[bool, str]:
    if not DB_PATH.exists():
        return False, "DB missing"
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT MAX(created_at) FROM memories")
        row = cur.fetchone()
        conn.close()
        if not row or not row[0]:
            return False, "no memories"
        # DB timestamps are UTC — compare against UTC
        last_ts = datetime.fromisoformat(row[0])
        age = datetime.now(tz=__import__('zoneinfo').ZoneInfo('UTC')).replace(tzinfo=None) - last_ts
        hours = age.total_seconds() / 3600
        if hours > STALENESS_THRESHOLD_HOURS:
            return False, f"last extraction {hours:.1f}h ago"
        return True, f"fresh ({hours:.1f}h)"
    except Exception as e:
        return False, str(e)


def main():
    state = load_state()
    issues = []

    if not check_binary_valid():
        issues.append("binary missing/broken (symlink stale after uv install?)")

    if not check_daemon_running():
        issues.append("daemon not running")

    fresh, detail = check_extraction_fresh()
    if not fresh:
        issues.append(f"extraction stale: {detail}")

    current_status = "failing" if issues else "ok"
    prev_status = state.get("last_status", "ok")

    # Auto-heal: only attempt restart if binary exists (otherwise it's a pointless loop)
    if current_status == "failing":
        if check_binary_valid():
            restart_daemon()
        # Log only on state change, not every cycle
        if prev_status == "ok":
            print(f"UNHEALTHY: {'; '.join(issues)}")
    elif prev_status == "failing":
        print(f"OK: recovered — {detail}")

    save_state({"last_alert": datetime.now().isoformat(), "last_status": current_status})


if __name__ == "__main__":
    main()
