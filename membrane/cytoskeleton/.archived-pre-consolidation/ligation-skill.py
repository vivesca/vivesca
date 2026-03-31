#!/usr/bin/env python3
"""PostToolUse hook: auto-commit skill file changes to ~/skills git repo."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILLS_DIR = Path.home() / "skills"


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Resolve symlinks so ~/.claude/skills/ and ~/skills/ both match
    try:
        real_path = Path(file_path).resolve()
    except Exception:
        sys.exit(0)

    if not str(real_path).startswith(str(SKILLS_DIR)):
        sys.exit(0)

    # Build a concise commit message: e.g. "todo/SKILL.md"
    try:
        rel = real_path.relative_to(SKILLS_DIR)
    except ValueError:
        rel = real_path.name

    subprocess.run(["git", "-C", str(SKILLS_DIR), "add", "-A"], capture_output=True)

    status = subprocess.run(
        ["git", "-C", str(SKILLS_DIR), "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if not status.stdout.strip():
        sys.exit(0)  # nothing staged

    subprocess.run(
        ["git", "-C", str(SKILLS_DIR), "commit", "-m", f"Auto-update: {rel}"],
        capture_output=True,
    )

    # Regenerate skill trigger map for skill-suggest hook
    gen_script = Path.home() / ".claude" / "hooks" / "skill-trigger-gen.py"
    if gen_script.exists():
        subprocess.run(["python3", str(gen_script)], capture_output=True)

    sys.exit(0)


if __name__ == "__main__":
    main()
