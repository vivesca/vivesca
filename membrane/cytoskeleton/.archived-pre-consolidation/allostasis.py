#!/usr/bin/env python3
"""UserPromptSubmit hook — allostasis: predictive multi-dimensional regulation.

Cross-wires three signals:
1. Budget tier (from respirometry-cached) — metabolic reserves
2. Time-of-day (HKT) — circadian phase
3. Session depth (prompt count) — fatigue/drift risk

Real allostasis predicts demand across multiple axes and adjusts proactively,
not just reactively to one variable.

Bio: allostasis = achieving stability through change. Unlike homeostasis
(maintaining a setpoint), allostasis predicts future demand and adjusts
the setpoint itself.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STATE_FILE = Path.home() / ".local/share/respirometry/budget-tier.json"
HKT = timezone(timedelta(hours=8))


def read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def write_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))


def get_budget_tier() -> str:
    try:
        result = subprocess.run(
            ["respirometry-cached", "--budget"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def get_circadian_phase() -> str:
    """Classify current time into circadian phases."""
    hour = datetime.now(HKT).hour
    if 6 <= hour < 10:
        return "morning"  # high energy, generous
    elif 10 <= hour < 17:
        return "day"  # normal
    elif 17 <= hour < 21:
        return "evening"  # winding down
    else:
        return "night"  # should be stopping


def effective_tier(budget: str, phase: str, depth: int) -> str:
    """Cross-wire signals to compute effective regulation tier.

    Night shifts budget UP one severity level (yellow→red).
    Deep sessions (>30 prompts) shift UP one level.
    Morning shifts DOWN one level (yellow→green).
    Multiple shifts stack but cap at red.
    """
    tiers = ["green", "yellow", "red"]
    if budget not in tiers:
        return budget

    idx = tiers.index(budget)

    # Circadian modulation
    if phase == "night":
        idx += 1
    elif phase == "evening" and depth > 35:
        idx += 1  # evening + deep session — only escalate at real fatigue depth
    elif phase == "morning":
        idx -= 1

    # Session depth modulation (fatigue/drift risk)
    if depth > 50:
        idx += 1
    elif depth > 35:
        # Gentle nudge, don't shift tier but note it
        pass

    return tiers[max(0, min(idx, len(tiers) - 1))]


GUIDANCE = {
    "green": "",
    "yellow": "Prefer Sonnet subagents for heavy work. Keep effort default.",
    "red": "Switch to Sonnet. Drop effort to low. Maximize delegation, minimize subagents.",
}

CIRCADIAN_NOTES = {
    "night": "Late night — consider wrapping up.",
    "evening": "",
    "morning": "",
    "day": "",
}


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    session_id = data.get("session_id", "")

    # Read and update state
    state = read_state()
    prev_tier = state.get("tier", "")
    prev_session = state.get("session_id", "")

    # Track session depth (prompt count)
    if session_id != prev_session:
        depth = 1
    else:
        depth = state.get("depth", 0) + 1

    budget = get_budget_tier()
    phase = get_circadian_phase()
    tier = effective_tier(budget, phase, depth)

    write_state(
        {
            "tier": tier,
            "budget": budget,
            "phase": phase,
            "depth": depth,
            "session_id": session_id,
        }
    )

    parts = []

    # Surface tier label only on change or red
    changed = tier != prev_tier and prev_tier != ""
    if changed:
        reason = []
        if budget != tier:
            reason.append(f"budget={budget}, phase={phase}, depth={depth}")
        parts.append(
            f"Budget changed: {prev_tier} -> {tier}"
            + (f" ({', '.join(reason)})" if reason else "")
        )
    elif tier == "red":
        reason = f"budget={budget}, phase={phase}, depth={depth}"
        parts.append(f"Budget: red ({reason})")

    # Routing guidance
    guidance = GUIDANCE.get(tier, "")
    if guidance:
        parts.append(guidance)

    # Circadian note (only on night, and only once per session)
    circadian = CIRCADIAN_NOTES.get(phase, "")
    if circadian and depth <= 2:
        parts.append(circadian)

    if parts:
        # Log routing decision for Hebbian accuracy tracking
        try:
            from hebbian_nudge import log_nudge

            log_nudge(
                "allostasis",
                f"tier:{tier}",
                metadata={
                    "budget": budget,
                    "phase": phase,
                    "depth": depth,
                },
            )
        except Exception:
            pass
        print(" — ".join(parts))


if __name__ == "__main__":
    main()
