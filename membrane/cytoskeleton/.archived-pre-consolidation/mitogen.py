#!/usr/bin/env python3
from __future__ import annotations

"""UserPromptSubmit hook — mitogen: stimulates delegation of coding tasks.

Habituates: after 3 fires without /rector being invoked in the same session,
suppresses for the rest of the session. Repeated ignored nudges are noise,
not guidance. Dishabituates on new session.

Bio: mitogen = substance that triggers cell division. Habituation = reduced
response to repeated stimulation (simplest form of learning).
"""

import json
import os
import sys as _sys

_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re
import sys
import tempfile
from pathlib import Path

BUILD_VERBS = r"\b(build|implement|create|develop|port|refactor|write|add|make)\b"
CODING_NOUNS = r"\b(cli|tool|script|crate|binary|rust|python|typescript|feature|flag|subcommand|command|endpoint|api|function|struct|module|daemon|launchagent|hook)\b"

STANDALONE = [
    r"\bnew (cli|crate|binary|project|tool)\b",
    r"\bfix(ing)? (the )?(bug|error|crash|compile|panic|borrow)\b",
    r"\bcargo (build|test|run|check)\b",
    r"\bwrite.{0,15}(in rust|in python|using clap|using ureq)\b",
]

HABITUATION_THRESHOLD = 3


def is_coding_task(prompt: str) -> bool:
    p = prompt.lower()
    for pattern in STANDALONE:
        if re.search(pattern, p):
            return True
    for verb_match in re.finditer(BUILD_VERBS, p):
        start = max(0, verb_match.start() - 10)
        end = min(len(p), verb_match.end() + 60)
        window = p[start:end]
        if re.search(CODING_NOUNS, window):
            return True
    return False


def get_state(session_id: str) -> dict:
    state_file = Path(tempfile.gettempdir()) / f"mitogen-{session_id}.json"
    try:
        return json.loads(state_file.read_text())
    except Exception:
        return {"fires": 0}


def set_state(session_id: str, state: dict) -> None:
    state_file = Path(tempfile.gettempdir()) / f"mitogen-{session_id}.json"
    state_file.write_text(json.dumps(state))


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError, EOFError:
        return

    prompt = data.get("prompt", "")
    session_id = data.get("session_id", "unknown")
    if not prompt:
        return

    # Dishabituation: /nucleation in prompt resets the counter
    if "/nucleation" in prompt.lower():
        set_state(session_id, {"fires": 0})
        return

    if not is_coding_task(prompt):
        return

    # Log prediction for Hebbian accuracy tracking
    try:
        from hebbian_nudge import log_nudge

        log_nudge("mitogen", "delegate", prompt_snippet=prompt[:200])
    except Exception:
        pass

    state = get_state(session_id)
    fires = state.get("fires", 0)

    # Habituated — suppress silently
    if fires >= HABITUATION_THRESHOLD:
        return

    fires += 1
    set_state(session_id, {"fires": fires})

    if fires == HABITUATION_THRESHOLD:
        # Last fire before suppression — note the habituation
        print(
            "[mitogen] Coding task detected — /nucleation available. "
            "(Suppressing further nudges this session — you know the path.)"
        )
    else:
        print(
            "[mitogen] Coding task detected — use /nucleation as the on-ramp "
            "(receptor-scan → CE plan → delegate to Codex/Gemini). "
            "Don't implement in-session unless trivial (<50 lines, single file)."
        )


if __name__ == "__main__":
    main()
