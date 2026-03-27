#!/usr/bin/env python3
"""PostToolUse hook: replicate MEMORY.md edits to docima backends.

When Edit/Write modifies MEMORY.md, extract new entries and add to all
docima backends silently. Closes the loop between memory capture and
the benchmark experiment.
"""

import contextlib
import json
import os
import subprocess
import sys


def main():
    data = json.loads(sys.stdin.read())
    tool = data.get("tool", "")
    tool_input = data.get("tool_input", {})

    if tool not in ("Edit", "Write"):
        return

    file_path = tool_input.get("file_path", "")
    if "MEMORY.md" not in file_path:
        return

    # Extract the new content being added
    new_string = tool_input.get("new_string", "") or tool_input.get("content", "")
    if not new_string:
        return

    # Extract bullet points as facts to replicate
    facts = []
    for line in new_string.splitlines():
        line = line.strip()
        if line.startswith("- **") and len(line) > 20:
            facts.append(line[2:].strip())

    if not facts:
        return

    # Silently add to docima backends
    for fact in facts:
        with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
            subprocess.run(
                ["uv", "run", "docima", "add", fact, "-b", "all", "--silent"],
                cwd=os.path.expanduser("~/code/docima"),
                capture_output=True,
                timeout=30,
                env={k: v for k, v in os.environ.items() if k != "CLAUDECODE"},
            )


if __name__ == "__main__":
    main()
