#!/usr/bin/env python3
"""interoceptor.py — Notification hook. Logs background task completions."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / "logs" / "notification-log.jsonl"

try:
    data = json.load(sys.stdin)
    entry = json.dumps(
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "type": data.get("type", "unknown"),
            "message": data.get("message", ""),
            "tool": data.get("tool_name", ""),
        }
    )
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(entry + "\n")
except Exception:
    pass
