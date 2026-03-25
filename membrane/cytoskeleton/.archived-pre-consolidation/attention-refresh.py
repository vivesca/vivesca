#!/usr/bin/env python3
"""PostToolUse hook: re-inject Tonus.md every N mutating tool calls.
Combats 'lost in the middle' on long sessions. (Stolen from Manus todo.md pattern.)"""

import os

MARKER = "/tmp/claude-attention-counter"
INTERVAL = 25  # mutating tool calls between refreshes
NOW_PATH = os.path.expanduser("~/epigenome/chromatin/Tonus.md")

# Read current count
try:
    with open(MARKER) as f:
        count = int(f.read().strip())
except (FileNotFoundError, ValueError):
    count = 0

count += 1

# Write back
with open(MARKER, "w") as f:
    f.write(str(count))

# Every INTERVAL calls, output reminder
if count % INTERVAL == 0 and os.path.exists(NOW_PATH):
    with open(NOW_PATH) as f:
        content = f.read()
    # Strip HTML comments for cleaner output
    lines = [l for l in content.splitlines() if not l.strip().startswith("<!--")]
    print(f"[attention-refresh] Re-grounding after {count} tool calls:")
    print("\n".join(lines))
