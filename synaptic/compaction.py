#!/usr/bin/env python3
"""compaction.py — consolidated PreCompact hook.

Replaces: consolidation.js, consolidation-log.py
"""

from __future__ import annotations

import contextlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()

# Repo root: hooks → claude → vivesca
_VIVESCA_ROOT = Path(__file__).resolve().parent.parent.parent

REPOS = [
    ("vivesca", _VIVESCA_ROOT),
    ("skills", HOME / "skills"),
]


def mod_auto_flush():
    """Auto-commit + push dirty repos before compaction."""
    msgs = []
    for name, path in REPOS:
        try:
            r = subprocess.run(
                ["git", "-C", str(path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if not r.stdout.strip():
                continue
            count = len([line for line in r.stdout.strip().split("\n") if line.strip()])
            subprocess.run(
                f'git -C "{path}" add -A && git -C "{path}" commit -m "chore: pre-compact auto-flush"',
                shell=True,
                capture_output=True,
                timeout=10,
            )
            with contextlib.suppress(Exception):
                subprocess.run(["git", "-C", str(path), "push"], capture_output=True, timeout=15)
            msgs.append(f"auto-committed+pushed {name} ({count} file{'s' if count > 1 else ''})")
        except Exception:
            pass
    if msgs:
        print(f"[PreCompact] {'; '.join(msgs)}", file=sys.stderr)


def mod_log_compaction(data):
    """Log compaction to daily note."""
    custom = data.get("custom_instructions", "")
    ts = datetime.now().strftime("%H:%M")
    daily = HOME / "notes" / "Daily" / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    if daily.exists():
        with daily.open("a") as f:
            f.write(f"\n**Compact ({ts}):** {custom or 'auto'}\n")


def main():
    data = {}
    with contextlib.suppress(Exception):
        data = json.load(sys.stdin)

    with contextlib.suppress(Exception):
        mod_auto_flush()
    with contextlib.suppress(Exception):
        mod_log_compaction(data)


if __name__ == "__main__":
    main()
