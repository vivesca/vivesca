#!/usr/bin/env python3
"""PostToolUse hook — proprioception: the organism sensing its own state.

Tracks per-session:
- Total hook fires (from hook-fire-log.jsonl)
- Tool call count and error rate (from tool-call-log.jsonl)
- Session duration and prompt depth

Emits a one-line body-state summary every 20 tool calls. Silent otherwise.
Think of it as the background hum of body awareness — you don't notice it
until something's off.

Bio: proprioception = sense of body position and movement. Without it,
you can't coordinate. The organism needs to sense its own activity patterns
to self-regulate.
"""

import json
import os
import time
from pathlib import Path

TOOL_LOG = Path.home() / ".claude" / "tool-call-log.jsonl"
HOOK_LOG = Path.home() / "logs" / "hook-fire-log.jsonl"
STATE_FILE = Path(os.environ.get("TMPDIR", "/tmp")) / "proprioception-state.json"
INTERVAL = 20  # tool calls between proprioception checks


def read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"count": 0, "start": time.time()}


def write_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state))


def count_lines(path: Path, since_ts: float = 0) -> tuple[int, int]:
    """Count total and error lines in a JSONL file since a timestamp."""
    total = errors = 0
    if not path.exists():
        return 0, 0
    try:
        for line in path.read_text().strip().split("\n"):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                ts = entry.get("ts", "")
                if since_ts > 0 and ts:
                    from datetime import datetime

                    entry_ts = datetime.fromisoformat(ts).timestamp()
                    if entry_ts < since_ts:
                        continue
                total += 1
                if entry.get("hasError"):
                    errors += 1
            except (json.JSONDecodeError, ValueError):
                continue
    except Exception:
        pass
    return total, errors


def count_denials(since_ts: float = 0) -> int:
    """Count nociceptor denials from hook fire log."""
    count = 0
    if not HOOK_LOG.exists():
        return 0
    try:
        for line in HOOK_LOG.read_text().strip().split("\n"):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                ts = entry.get("ts", "")
                if since_ts > 0 and ts:
                    from datetime import datetime

                    entry_ts = datetime.fromisoformat(ts).timestamp()
                    if entry_ts < since_ts:
                        continue
                count += 1
            except (json.JSONDecodeError, ValueError):
                continue
    except Exception:
        pass
    return count


def main():
    state = read_state()
    state["count"] = state.get("count", 0) + 1
    session_start = state.get("start", time.time())
    write_state(state)

    if state["count"] % INTERVAL != 0:
        return

    # Proprioceptive snapshot
    elapsed_min = int((time.time() - session_start) / 60)
    tool_calls, tool_errors = count_lines(TOOL_LOG, session_start)
    denials = count_denials(session_start)

    error_rate = f"{tool_errors / tool_calls * 100:.0f}%" if tool_calls > 0 else "0%"

    parts = [f"depth={state['count']}"]
    parts.append(f"{elapsed_min}min")
    if tool_errors > 0:
        parts.append(f"errors={tool_errors} ({error_rate})")
    if denials > 0:
        parts.append(f"denials={denials}")

    # Only surface if something noteworthy
    if tool_errors > 3 or denials > 2 or elapsed_min > 90:
        summary = ", ".join(parts)
        print(f"[proprioception] {summary}")
        if elapsed_min > 90:
            print("Session >90min — consider /compact or /wrap to prevent context drift.")
        if tool_errors > 5:
            print("High error rate — are you stuck? Consider a different approach.")


if __name__ == "__main__":
    main()
