#!/usr/bin/env python3
"""flush_processor.py — drain the memory-flush queue.

Async processor for Hermes-style pre-compaction memory flushes. Compaction
transcripts persist on disk, so we queue from PreCompact (compaction.py) and
flush asynchronously here without blocking the user's UI.

For each pending entry: spawn `claude -p` with the transcript path and a
Hermes-style flush directive. The headless agent extracts durable substance
(user preferences, corrections, recurring patterns, env facts) into
~/epigenome/marks/ with `flush:` provenance frontmatter so cytokinesis dedups.

Usage:
    flush_processor.py          # process all pending entries
    flush_processor.py --once   # process one entry, then exit
    flush_processor.py --dry    # show planned actions without dispatching
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
QUEUE = HOME / "germline" / "loci" / "flush-queue.jsonl"
LOG = HOME / "germline" / "loci" / "flush-log.jsonl"
TIMEOUT_SEC = 300

FLUSH_PROMPT = """You are a memory flush agent for the Hermes-style pre-compaction primitive.

Your task: read the conversation transcript at the path below and extract durable substance worth preserving for future sessions BEFORE the live context gets compacted.

Transcript: {transcript_path}
Session: {session_id}
Triggered: {trigger}

SAVE (write mark files in ~/epigenome/marks/):
- User preferences (taste, format, communication style — confirmed not assumed)
- Corrections from Terry (especially architectural; mark protected: true if so)
- Recurring error patterns + fixes (would a fresh session hit the same wall?)
- Stable conventions (project structure, naming, infrastructure)
- Environment facts (paths, tools, system quirks)
- Surprises that revealed how something actually works

DO NOT SAVE:
- Task progress (current work state)
- Session results (what got drafted/sent — those go to standalone correspondence notes)
- Transient TODOs (those go to TODO.md or cyclin)
- Restating what's already in MEMORY.md

For every mark you write, include `flush: {session_id}` in the frontmatter so /cytokinesis can dedup. Use the existing mark frontmatter schema (name, description, type, source: cc, durability, protected if architectural).

After writing marks, update ~/epigenome/marks/MEMORY.md with one-line pointers (under ~150 chars) to any genuinely high-frequency new gotchas. Respect the 80-line / 150-char-per-line budget — if at cap, demote a low-confidence existing entry to overflow rather than busting budget.

If nothing in the transcript qualifies for filing (routine task work, no corrections, no surprises) say "nothing to flush" and exit. Over-filing is the failure mode, not under-filing — the bar is "would a fresh session benefit?"

Read the transcript with Read. Write marks with Write. Edit MEMORY.md with Edit. No other tools needed."""


def load_queue() -> list[dict]:
    if not QUEUE.exists():
        return []
    entries = []
    for line in QUEUE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"[flush_processor] skip malformed line: {line[:60]}", file=sys.stderr)
    return entries


def save_queue(entries: list[dict]) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUEUE.with_suffix(".jsonl.tmp")
    with tmp.open("w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    tmp.replace(QUEUE)


def append_log(record: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    record["logged_at"] = datetime.now().isoformat(timespec="seconds")
    with LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")


def dispatch_flush(entry: dict, dry: bool = False) -> dict:
    transcript = entry["transcript_path"]
    session_id = entry["session_id"]
    trigger = entry["trigger"]

    if not Path(transcript).exists():
        return {"status": "skipped", "reason": f"transcript missing: {transcript}"}

    prompt = FLUSH_PROMPT.format(
        transcript_path=transcript,
        session_id=session_id,
        trigger=trigger,
    )

    if dry:
        return {"status": "dry-run", "prompt_chars": len(prompt)}

    claude_bin = shutil.which("claude")
    if not claude_bin:
        return {"status": "error", "reason": "claude binary not on PATH"}

    cmd = [
        claude_bin,
        "-p",
        prompt,
        "--allowed-tools",
        "Read Write Edit Glob Grep",
        "--dangerously-skip-permissions",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "timeout_sec": TIMEOUT_SEC}

    return {
        "status": "completed" if result.returncode == 0 else "error",
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-500:] if result.stdout else "",
        "stderr_tail": result.stderr[-500:] if result.stderr else "",
    }


def process_queue(once: bool, dry: bool) -> int:
    entries = load_queue()
    if not entries:
        print("[flush_processor] queue empty", file=sys.stderr)
        return 0

    pending = [entry for entry in entries if entry.get("status") == "pending"]
    if not pending:
        print(f"[flush_processor] no pending entries (total: {len(entries)})", file=sys.stderr)
        return 0

    processed = 0
    remaining = [entry for entry in entries if entry.get("status") != "pending"]
    for entry in pending:
        outcome = dispatch_flush(entry, dry=dry)
        record = {**entry, "outcome": outcome}
        append_log(record)
        if outcome["status"] in ("completed", "skipped", "dry-run"):
            entry["status"] = outcome["status"]
        else:
            entry["status"] = "failed"
            entry["last_error"] = outcome
        remaining.append(entry)
        processed += 1
        print(
            f"[flush_processor] {entry['session_id'][:8]} -> {outcome['status']}",
            file=sys.stderr,
        )
        if once:
            break

    save_queue(remaining)
    return processed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="process one entry then exit")
    parser.add_argument(
        "--dry", action="store_true", help="show planned actions without dispatching"
    )
    args = parser.parse_args()

    return 0 if process_queue(args.once, args.dry) >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
