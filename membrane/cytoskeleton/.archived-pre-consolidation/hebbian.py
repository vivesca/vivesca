#!/usr/bin/env python3
from __future__ import annotations

"""
PostToolUse hook (Skill) — learn from misses.

When a skill is invoked that skill-suggest didn't predict:
1. Log the miss (skill name + prompt snippet)
2. These accumulate in skill-suggest-log.tsv for weekly reconciliation

The flywheel: miss → log → weekly review → new trigger added → fewer misses.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

SUGGEST_LOG = Path.home() / ".claude" / "skill-suggest-log.tsv"
PROMPT_CACHE = Path.home() / ".claude" / "last-prompt.txt"


def recent_suggestions(skill_name: str, window_seconds: int = 30) -> bool:
    """Check if skill-suggest predicted this skill in the last N seconds."""
    if not SUGGEST_LOG.exists():
        return False

    now = datetime.now()
    try:
        for line in SUGGEST_LOG.read_text().strip().split("\n")[-20:]:
            parts = line.split("\t")
            if len(parts) >= 3 and parts[1] == "suggested" and parts[2] == skill_name:
                ts = datetime.strptime(parts[0], "%Y-%m-%dT%H:%M:%S")
                if (now - ts).total_seconds() < window_seconds:
                    return True
    except ValueError, OSError:
        pass
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError, EOFError:
        return

    skill_name = data.get("tool_input", {}).get("skill", "") or data.get("tool_input", {}).get(
        "name", ""
    )
    if not skill_name:
        return

    # Skip non-user-facing skills (compound-engineering:*, superpowers:*, etc.)
    if ":" in skill_name:
        return

    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    was_predicted = recent_suggestions(skill_name)

    # Read the cached prompt
    prompt_snippet = ""
    try:
        if PROMPT_CACHE.exists():
            prompt_snippet = PROMPT_CACHE.read_text().strip()[:200]
    except OSError:
        pass

    try:
        with SUGGEST_LOG.open("a") as f:
            if was_predicted:
                f.write(f"{ts}\thit\t{skill_name}\t\n")
            else:
                f.write(f"{ts}\tmiss\t{skill_name}\t{prompt_snippet}\n")
    except OSError:
        pass

    # Misses logged silently — surfaced at /ecdysis, not per-invocation


if __name__ == "__main__":
    main()
