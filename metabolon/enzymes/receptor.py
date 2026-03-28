"""receptor_sense — proprioceptive readiness sensing against long-lived goals.

Thin enzyme wrapper around the receptor_sense organelle.
Business logic lives in metabolon.organelles.receptor_sense.

Tools:
  proprioception_sense — sense readiness gaps and surface highest-value next action
  proprioception_drill — record a drill result to feed proprioceptive sensing
"""

from __future__ import annotations

from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations
from pydantic import Field

from metabolon.morphology import EffectorResult, Secretion
from metabolon.organelles.receptor_sense import (
    GOALS_DIR as _ORGANELLE_GOALS_DIR,
    SIGNALS_DIR as _ORGANELLE_SIGNALS_DIR,
    ProprioceptiveStore,
    current_phase,
    decode_flashcard_deck,
    restore_goals,
    synthesize_signal_summary,
)

# ---------------------------------------------------------------------------
# Module-level constants — tests monkeypatch these; tools reference them.
# ---------------------------------------------------------------------------

GOALS_DIR: Path = _ORGANELLE_GOALS_DIR
SIGNALS_DIR: Path = _ORGANELLE_SIGNALS_DIR


class ProprioceptionResult(Secretion):
    """Proprioceptive readiness summary for active goals."""

    has_goal: bool
    summary: str
    goals: list[dict] = Field(default_factory=list)


@tool(
    name="proprioception_sense",
    description="Sense readiness against active goals. Surfaces weakest areas and next action.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def proprioception_sense() -> ProprioceptionResult:
    """Proprioceptive readiness check."""
    goals = restore_goals(GOALS_DIR)
    if not goals:
        return ProprioceptionResult(
            has_goal=False,
            summary="No goals configured. Add a YAML file to ~/.local/share/vivesca/goals/",
        )

    summaries = []
    parts = []

    for goal in goals:
        goal_slug = goal["name"].lower().replace(" ", "-")
        store = ProprioceptiveStore(SIGNALS_DIR / f"{goal_slug}-signals.jsonl")
        summary = synthesize_signal_summary(goal, store)
        summaries.append(summary)

        # Format for LLM consumption
        phase_info = f"Phase: {summary['phase']}"
        if summary["days_to_next_phase"] is not None:
            phase_info += f" ({summary['days_to_next_phase']} days to next phase)"

        weakest_info = ""
        if summary["weakest"]:
            weak_details = []
            for cat in summary["weakest"]:
                cat_data = summary["categories"][cat]
                if cat_data["drill_count"] == 0:
                    weak_details.append(f"{cat}: never drilled")
                else:
                    weak_details.append(f"{cat}: avg {cat_data['avg_score']:.1f}/3")
            weakest_info = "Weakest: " + ", ".join(weak_details)

        parts.append(
            f"**{summary['goal']}** — {phase_info}. "
            f"Total drills: {summary['total_drills']}. "
            f"{weakest_info}"
        )

    return ProprioceptionResult(
        has_goal=True,
        summary="\n\n".join(parts),
        goals=summaries,
    )


@tool(
    name="proprioception_drill",
    description="Record a drill result (score 1-3, category, type). Feeds proprioception.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def proprioception_drill(
    goal: str,
    category: str,
    score: int,
    drill_type: str = "flashcard",
    material: str = "",
    notes: str = "",
) -> EffectorResult:
    """Record a proprioceptive drill signal."""
    if score < 1 or score > 3:
        return EffectorResult(success=False, message=f"Score must be 1-3, got {score}")

    store = ProprioceptiveStore(SIGNALS_DIR / f"{goal}-signals.jsonl")
    store.append(
        goal=goal,
        material=material,
        category=category,
        score=score,
        drill_type=drill_type,
        notes=notes,
    )

    return EffectorResult(
        success=True,
        message=f"Recorded {drill_type} drill: {category} = {score}/3",
        data={"goal": goal, "category": category, "score": score},
    )
