#!/usr/bin/env python3
from __future__ import annotations

"""
PostToolUse hook — fires after every Skill invocation.

1. Logs skill usage to ~/.claude/skill-usage.tsv for analytics.
2. Reminds about description gaps if the skill was irrelevant.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

USAGE_LOG = Path.home() / ".claude" / "skill-usage.tsv"


def log_usage(skill_name: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with USAGE_LOG.open("a") as f:
        f.write(f"{ts}\t{skill_name}\n")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    skill_name = data.get("tool_input", {}).get("skill", "") or data.get("tool_input", {}).get(
        "name", ""
    )
    if skill_name:
        log_usage(skill_name)


if __name__ == "__main__":
    main()
