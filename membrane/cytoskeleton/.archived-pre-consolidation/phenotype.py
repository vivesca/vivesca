#!/usr/bin/env -S uv run --script --python 3.13
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""
UserPromptSubmit hook — auto-name tmux window from first prompt via Gemini Flash.

Gate: only fires when current window name is a default (cc, zsh, etc).
Once renamed, subsequent prompts skip automatically.
"""

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lib"))
from llm import query

DEFAULT_NAMES = {"cc", "zsh", "bash", "python", "claude", "fish", "sh"}


def in_tmux() -> bool:
    return bool(os.environ.get("TMUX"))


def current_window_name() -> str:
    try:
        result = subprocess.run(
            ["tmux", "display-message", "-p", "#W"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def current_window_id() -> str:
    try:
        result = subprocess.run(
            ["tmux", "display-message", "-p", "#{window_id}"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_label(prompt: str) -> str:
    llm_prompt = (
        "Give a 1-3 word kebab-case label for this task topic.\n"
        "Rules: lowercase, hyphens only, no punctuation, max 20 chars.\n"
        "Examples: hexis-build, capco-prep, fix-auth-bug, morning-brief\n"
        f"Task: {prompt[:300]}\n\n"
        "Label:"
    )
    raw = query("gemini-flash", llm_prompt, timeout=5).strip().lower()
    label = re.sub(r"[^a-z0-9-]", "-", raw).strip("-")[:20]
    return label


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    if not in_tmux():
        sys.exit(0)

    if current_window_name() not in DEFAULT_NAMES:
        sys.exit(0)

    window_id = current_window_id()  # capture before API call

    prompt = data.get("prompt", "").strip()
    if len(prompt) < 5:
        sys.exit(0)

    try:
        label = get_label(prompt)
        if label:
            target = ["-t", window_id] if window_id else []
            subprocess.run(["tmux", "rename-window", *target, label], timeout=2)
    except Exception:
        pass  # Never block Claude Code

    sys.exit(0)


if __name__ == "__main__":
    main()
