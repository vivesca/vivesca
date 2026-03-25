#!/usr/bin/env python3
"""
PostToolUse hook — logs tool failures to ~/notes/failures.md.
Fires when: Bash exit non-zero, or is_error=true on any tool.
Skipped: expected non-zero (grep/diff), hook-blocked calls.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

FAILURES_FILE = Path.home() / "notes" / "failures.md"
EXPECTED_NONZERO = {"grep", "diff", "rg", "test", "[ "}


def is_expected_failure(tool, tool_input, stderr):
    if tool != "Bash":
        return False
    cmd = (tool_input.get("command") or "").strip()
    return any(cmd.startswith(t) for t in EXPECTED_NONZERO)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool = data.get("tool", "")
    tool_input = data.get("tool_input", {})
    response = data.get("tool_response", {})

    is_error = response.get("is_error", False)
    exit_code = response.get("exit_code")
    stderr = (response.get("stderr") or "").strip()

    if "DELEGATE GATE" in stderr or "hook" in stderr.lower():
        sys.exit(0)

    failed = is_error or (exit_code is not None and exit_code != 0)
    if not failed:
        sys.exit(0)

    if is_expected_failure(tool, tool_input, stderr):
        sys.exit(0)

    ts = datetime.now().strftime("%Y-%m-%dT%H:%M")

    if tool == "Bash":
        cmd = (tool_input.get("command") or "").strip()[:200]
        entry = f"\n## {ts} — Bash (exit {exit_code})\n**Command:** `{cmd}`\n**Error:** {stderr[:300] or '(no stderr)'}\n"
    else:
        file_path = tool_input.get("file_path") or tool_input.get("path") or "(no path)"
        entry = f"\n## {ts} — {tool} (error)\n**Path:** `{file_path}`\n**Error:** {stderr[:300] or str(response)[:200]}\n"

    try:
        FAILURES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with FAILURES_FILE.open("a") as f:
            f.write(entry)
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
