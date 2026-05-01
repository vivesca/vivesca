#!/usr/bin/env python3
"""compaction.py — consolidated PreCompact hook.

Replaces: consolidation.js, consolidation-log.py
"""

from __future__ import annotations

import contextlib
import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

HOME = Path.home()
FLUSH_QUEUE = HOME / "germline" / "loci" / "flush-queue.jsonl"

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


def mod_queue_memory_flush(data):
    """Queue a Hermes-style memory flush for async processing.

    Inspired by Hermes Agent's pre-compression flush primitive: before context
    compacts, give the model one chance to extract durable substance (preferences,
    corrections, recurring patterns, env facts) into MEMORY.md / marks. Compaction
    transcripts persist on disk, so we queue the flush rather than block compaction.

    Source: Manthan Gupta, "Hermes Agent's Memory System" (2026-04), translated
    via 宝玉: https://x.com/dotey/status/2049534755729707205
    Note: ~/epigenome/chromatin/euchromatin/hermes-memory-architecture-2026-04.md

    Processed by: ~/germline/effectors/flush_processor.py (cron).
    """
    transcript = data.get("transcript_path") or data.get("transcript")
    session_id = data.get("session_id") or str(uuid.uuid4())
    trigger = data.get("trigger") or data.get("hook_event_name", "unknown")
    if not transcript:
        return
    entry = {
        "queued_at": datetime.now().isoformat(timespec="seconds"),
        "session_id": session_id,
        "transcript_path": str(transcript),
        "trigger": trigger,
        "status": "pending",
    }
    FLUSH_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with FLUSH_QUEUE.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[PreCompact] queued memory flush for session {session_id[:8]}", file=sys.stderr)


def main():
    data = {}
    with contextlib.suppress(Exception):
        data = json.load(sys.stdin)

    with contextlib.suppress(Exception):
        mod_auto_flush()
    with contextlib.suppress(Exception):
        mod_log_compaction(data)
    with contextlib.suppress(Exception):
        mod_queue_memory_flush(data)


if __name__ == "__main__":
    main()
