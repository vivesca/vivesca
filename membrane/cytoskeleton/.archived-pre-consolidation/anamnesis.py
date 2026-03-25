#!/usr/bin/env python3
"""UserPromptSubmit hook — selective anamnesis at session start.

Fires once per session. Pulls ~/code/vivesca-terry/chromatin, then injects all vivesca resources.
Core context (Tonus, constitution) always loads first.
Optional resources reordered by keyword relevance to the first prompt —
primacy effect means relevant context gets attended to.
Never blocks Claude Code.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

NOTES_DIR = Path.home() / "code" / "vivesca-terry" / "chromatin"
NOW_FILE = NOTES_DIR / "Tonus.md"
CONSTITUTION = Path.home() / "reticulum" / "constitution.md"
TMP_DIR = Path(tempfile.gettempdir())

# Domain keywords → resource keys (for reordering)
DOMAIN_SIGNALS = {
    "anatomy": {
        "code",
        "vivesca",
        "hook",
        "mcp",
        "rename",
        "tool",
        "skill",
        "substrate",
        "metabolism",
        "pipeline",
        "agent",
    },
    "effectors": {"cli", "command", "binary", "script", "tool", "run", "which"},
    "circadian": {
        "calendar",
        "meeting",
        "schedule",
        "tomorrow",
        "today",
        "week",
        "plan",
        "agenda",
    },
    "vitals": {
        "health",
        "gym",
        "oura",
        "sleep",
        "exercise",
        "hrv",
        "readiness",
        "workout",
        "pain",
        "headache",
    },
    "budget": {"budget", "token", "usage", "cost", "quota", "limit", "red", "respirometry"},
}


def _score_relevance(prompt_lower: str) -> list[str]:
    """Score optional resources by keyword match count, return sorted keys."""
    scores = {}
    prompt_words = set(prompt_lower.split())
    for resource_key, keywords in DOMAIN_SIGNALS.items():
        scores[resource_key] = len(prompt_words & keywords)
    # Sort by score descending, then alphabetical for ties
    return sorted(scores, key=lambda k: (-scores[k], k))


def _load_anatomy() -> str:
    from vivesca.resources.architecture import generate_anatomy

    return generate_anatomy()


def _load_effectors() -> str:
    from vivesca.resources.tool_index import generate_effector_index

    return generate_effector_index()


def _load_circadian() -> str:
    result = subprocess.run(
        ["fasti", "list", "today"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return ""


def _load_vitals() -> str:
    from vivesca.resources.claude_code_health import generate_vitals

    return generate_vitals()


def _load_budget() -> str:
    result = subprocess.run(
        ["respirometry"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return ""


RESOURCE_LOADERS = {
    "anatomy": ("Anatomy (auto-generated)", _load_anatomy),
    "effectors": ("Effectors (tool routing)", _load_effectors),
    "circadian": ("Circadian (today's schedule)", _load_circadian),
    "vitals": ("Vitals", _load_vitals),
    "budget": ("Budget", _load_budget),
}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    session_id = data.get("session_id", "")
    if not session_id:
        sys.exit(0)

    marker = TMP_DIR / f"vault-pull-{session_id}.done"
    if marker.exists():
        sys.exit(0)

    # Extract prompt for relevance scoring
    prompt = (
        data.get("message", {}).get("content", "") if isinstance(data.get("message"), dict) else ""
    )
    prompt_lower = prompt.lower() if prompt else ""

    try:
        subprocess.run(
            ["git", "-C", str(NOTES_DIR), "pull", "--no-rebase", "-X", "ours", "-q"],
            capture_output=True,
            timeout=15,
        )
        marker.touch()
    except Exception:
        pass  # Never block Claude Code

    # === Core context (always first) ===

    try:
        import datetime

        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        day_str = now.strftime("%A, %d %B %Y (HKT)")
        print(f"Current date/time: {day_str}")
    except Exception:
        pass

    try:
        now_content = NOW_FILE.read_text(encoding="utf-8").strip()
        if now_content:
            print(f"\nTonus.md (active session state):\n{now_content}")
    except Exception:
        pass

    try:
        constitution_content = CONSTITUTION.read_text(encoding="utf-8").strip()
        if constitution_content:
            print(f"\nConstitution (vivesca canonical rules):\n{constitution_content}")
    except Exception:
        pass

    # === Optional resources (reordered by relevance) ===

    resource_order = _score_relevance(prompt_lower) if prompt_lower else list(RESOURCE_LOADERS)

    for key in resource_order:
        label, loader = RESOURCE_LOADERS[key]
        try:
            content = loader()
            if content:
                print(f"\n{label}:\n{content}")
        except Exception:
            pass  # Never block Claude Code

    sys.exit(0)


if __name__ == "__main__":
    main()
