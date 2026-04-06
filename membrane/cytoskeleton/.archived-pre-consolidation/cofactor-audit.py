#!/usr/bin/env python3
"""
PostToolUse hook (Skill) — nudge when quorum/transcription-factor run without naming a mental model.

The inline tables are useless if Claude skips them. This hook
checks the output and reminds Claude to apply a lens.
"""

import json
import sys

MODELS = [
    "opportunity cost",
    "sunk cost",
    "premortem",
    "second-order",
    "base rate",
    "confirmation bias",
    "incentives",
    "reversibility",
    "chesterton",
    "leverage point",
    "compounding",
    "inversion",
    "goodhart",
    "anchoring",
    "steel man",
    "survivorship",
]

TARGET_SKILLS = {"quorum", "transcription-factor"}


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    skill_name = data.get("tool_input", {}).get("skill", "") or data.get("tool_input", {}).get(
        "name", ""
    )

    if skill_name not in TARGET_SKILLS:
        return

    # Check tool_result for model mentions
    result_text = str(data.get("tool_result", "")).lower()

    found = [m for m in MODELS if m in result_text]

    if not found:
        print(
            f"[model-check] /{skill_name} ran without naming a mental model. "
            "Before proceeding, scan the lens table in the skill and name 1-2 "
            "that apply (e.g., 'this has an opportunity cost shape'). "
            "If genuinely none apply, say so explicitly."
        )


if __name__ == "__main__":
    main()
