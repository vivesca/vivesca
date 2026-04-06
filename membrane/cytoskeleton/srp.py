#!/usr/bin/env python3
"""srp.py — Signal Recognition Particle for ribosome supervised mode.

Minimal PreToolUse hook that detects "signal peptides" (sensitive operations)
during headless ribosome execution and returns defer to pause translation.

Only active when RIBOSOME_DEFER_ENABLED=1. Zero overhead otherwise.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def _defer(reason: str):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "defer",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    print(f"[srp] DEFERRED: {reason}", file=sys.stderr)
    sys.exit(0)


def _has_pattern(cmd: str, pattern: str) -> bool:
    return bool(re.search(pattern, cmd))


def _outside_worktree(file_path: str) -> bool:
    """Check if file_path is outside the current working directory (worktree)."""
    cwd = os.getcwd()
    try:
        Path(file_path).resolve().relative_to(Path(cwd).resolve())
        return False
    except ValueError:
        return True


BASH_SIGNALS = [
    (r"\bgit\s+push\b", "git push to remote"),
    (r"\bcurl\b.*-X\s*(POST|PUT|PATCH|DELETE)", "outbound HTTP mutation"),
    (r"\bssh\b(?!.*ganglion)", "SSH to unknown host"),
    (r"\bdocker\s+(run|exec|rm|stop|kill)\b", "docker container mutation"),
    (r"\bfly\s+(deploy|scale|destroy|machine)\b", "fly.io infrastructure change"),
    (r"\bsupervisorctl\s+(stop|restart|shutdown)\b", "supervisor service mutation"),
    (r"\bsystemctl\s+(stop|restart|disable)\b", "systemd service mutation"),
    (r"\brm\s+-r", "recursive deletion"),
]


def main():
    if not os.environ.get("RIBOSOME_DEFER_ENABLED"):
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool = data.get("tool", "")
    tool_input = data.get("tool_input", {})

    if tool == "Bash":
        cmd = tool_input.get("command", "")
        for pattern, reason in BASH_SIGNALS:
            if _has_pattern(cmd, pattern):
                _defer(reason)

    elif tool in ("Write", "Edit", "MultiEdit"):
        file_path = tool_input.get("file_path", "")
        if file_path and _outside_worktree(file_path):
            _defer(f"file write outside worktree: {file_path}")


if __name__ == "__main__":
    main()
