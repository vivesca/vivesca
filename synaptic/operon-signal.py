#!/usr/bin/env python3
"""
PostToolUse hook (Skill) — emit vivesca signals for skill invocations.

Skills are enzymes in the operon system but they invoke via Claude Code's
Skill tool, not vivesca's MCP server. Without this hook, the operon
heartbeat substrate is blind to skill activity — it only sees MCP tools.

This hook bridges the gap: Skill invocation → signal in signals.jsonl.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

SIGNALS_FILE = Path.home() / ".local" / "share" / "vivesca" / "signals.jsonl"


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    skill_name = data.get("tool_input", {}).get("skill", "") or data.get("tool_input", {}).get(
        "name", ""
    )
    if not skill_name:
        return

    # Emit a stimulus in the same format as vivesca's SensorySystem
    stimulus = {
        "ts": datetime.now(UTC).isoformat(),
        "tool": skill_name,
        "outcome": "success",
        "substrate_consumed": 0,
        "product_released": 0,
        "response_latency": 0,
        "error": None,
        "correction": None,
        "context": "skill_invocation",
    }

    try:
        SIGNALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with SIGNALS_FILE.open("a") as f:
            f.write(json.dumps(stimulus) + "\n")
    except OSError:
        pass  # Never block Claude Code


if __name__ == "__main__":
    main()
