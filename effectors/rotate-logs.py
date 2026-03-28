#!/usr/bin/env python3
"""Truncate cron logs to last 200 lines. Runs weekly via cron."""

from pathlib import Path

LOG_DIR = Path.home() / "logs"
KEEP_LINES = 200

for log in LOG_DIR.glob("*.log"):
    try:
        lines = log.read_text().splitlines()
        if len(lines) > KEEP_LINES:
            log.write_text("\n".join(lines[-KEEP_LINES:]) + "\n")
    except Exception:
        pass
