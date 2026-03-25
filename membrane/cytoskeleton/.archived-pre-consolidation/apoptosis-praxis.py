#!/usr/bin/env python3
"""PostToolUse hook: block dismissed items from being added to Praxis.md.

Reads ~/code/vivesca-terry/chromatin/Praxis Dismissed.md for suppressed patterns.
On any Edit/Write to Praxis.md, scans new checkbox lines against the
dismissed list. If a match is found, prints a warning to stderr
(advisory hook — does not block the write, but surfaces to the LLM).
"""

import json
import sys
from pathlib import Path

DISMISSED_PATH = Path.home() / "code" / "vivesca-terry" / "chromatin" / "Praxis Dismissed.md"
PRAXIS_PATH = Path.home() / "code" / "vivesca-terry" / "chromatin" / "Praxis.md"


def load_dismissed() -> list[str]:
    """Return lowercase dismissed patterns from Praxis Dismissed.md."""
    if not DISMISSED_PATH.exists():
        return []
    entries = []
    for line in DISMISSED_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("- ") and len(line) > 2:
            entry = line[2:].strip().lower()
            if entry:
                entries.append(entry)
    return entries


def check_input(tool_input: dict, dismissed: list[str]) -> list[str]:
    """Check tool input for dismissed items. Returns list of matched patterns."""
    matches = []
    # For Edit: check new_string. For Write: check content.
    text = tool_input.get("new_string", "") or tool_input.get("content", "")
    for line in text.splitlines():
        stripped = line.strip()
        # Only check new checkbox lines
        if not stripped.startswith("- [ ]"):
            continue
        lower = stripped.lower()
        for pattern in dismissed:
            if pattern in lower:
                matches.append(pattern)
    return matches


def main():
    hook_input = json.load(sys.stdin)
    tool_input = hook_input.get("tool_input", {})

    dismissed = load_dismissed()
    if not dismissed:
        return

    matches = check_input(tool_input, dismissed)
    if matches:
        patterns = ", ".join(f"'{m}'" for m in matches)
        print(
            f"DISMISSED ITEM DETECTED in Praxis.md write: {patterns}. "
            f"This item was previously dismissed by Terry. "
            f"Remove it and do not re-add. See ~/code/vivesca-terry/chromatin/Praxis Dismissed.md.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
