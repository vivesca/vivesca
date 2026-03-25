"""receptor_sense — proprioceptive readiness sensing against long-lived goals.

Tools:
  proprioception_sense — sense readiness gaps and surface highest-value next action
  proprioception_drill — record a drill result to feed proprioceptive sensing
"""

from __future__ import annotations

import datetime
import json
import os
import re
from pathlib import Path

import yaml
from fastmcp.tools import tool
from mcp.types import ToolAnnotations
from pydantic import Field

from metabolon.morphology import EffectorResult, Secretion

GOALS_DIR = Path(os.path.expanduser("~/.local/share/vivesca/goals"))
SIGNALS_DIR = Path(os.path.expanduser("~/.local/share/vivesca/goals"))


def current_phase(phases: list[dict], today: datetime.date | None = None) -> dict:
    """Determine current phase based on date markers.

    Phases with 'until' dates transition when the date passes.
    The last phase (no 'until') is the terminal phase.
    """
    today = today or datetime.date.today()

    for phase in phases:
        until = phase.get("until")
        if until is None:
            return phase  # terminal phase
        if today < datetime.date.fromisoformat(str(until)):
            return phase

    # All dates passed — return last phase
    return phases[-1]


def restore_goals(goals_dir: Path = GOALS_DIR) -> list[dict]:
    """Load all goal configs from YAML files in the goals directory."""
    if not goals_dir.exists():
        return []

    goals = []
    for f in sorted(goals_dir.glob("*.yaml")):
        with open(f) as fh:
            goal = yaml.safe_load(fh)
            if goal:
                goal["_file"] = str(f)
                goals.append(goal)
    return goals


class ProprioceptiveStore:
    """Append-only JSONL store for proprioceptive drill/prep signals."""

    def __init__(self, path: Path):
        self.path = path

    def append(
        self,
        *,
        goal: str,
        material: str,
        category: str,
        score: int,
        drill_type: str,
        **extra: object,
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.datetime.now(datetime.UTC).isoformat(),
            "goal": goal,
            "material": material,
            "category": category,
            "score": score,
            "drill_type": drill_type,
            **extra,
        }
        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def recall_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        entries = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def recall_since(self, since: datetime.datetime) -> list[dict]:
        since_str = since.isoformat()
        return [e for e in self.recall_all() if e.get("ts", "") >= since_str]


def decode_flashcard_deck(path: Path) -> list[dict]:
    """Parse a flashcard deck markdown file into structured cards.

    Expected format:
      ## D{n} — Section Title
      ### Card {n} — D{n} — Card Type
      **Q:** Question text
      **A:** Answer text
    """
    text = path.read_text()
    cards: list[dict] = []

    # Split by H3 (card headers)
    sections = re.split(r"(?=^### )", text, flags=re.MULTILINE)

    for section in sections:
        # Check for H2 (category) before this card
        h2_match = re.search(r"^## (D\d+)", section, re.MULTILINE)
        if h2_match:
            pass  # category tracked via the card header itself

        # Parse card
        h3_match = re.match(r"### Card \d+ — (D\d+) — (.+)", section)
        if not h3_match:
            continue

        category = h3_match.group(1)
        card_type = h3_match.group(2).strip()

        q_match = re.search(r"\*\*Q:\*\*\s*(.+?)(?=\n\*\*A:\*\*)", section, re.DOTALL)
        a_match = re.search(r"\*\*A:\*\*\s*(.+?)(?=\n\n|\n###|\Z)", section, re.DOTALL)

        if q_match and a_match:
            cards.append(
                {
                    "category": category,
                    "card_type": card_type,
                    "question": q_match.group(1).strip(),
                    "answer": a_match.group(1).strip(),
                }
            )

    return cards


def _goal_slugs(goal: dict) -> set[str]:
    """Return all plausible slug forms for matching signals to a goal."""
    slugs: set[str] = set()
    name = goal.get("name", "")
    if name:
        slugs.add(name)  # exact name
        slugs.add(name.lower().replace(" ", "-"))  # kebab slug
    # File stem (e.g. "capco" from capco.yaml)
    file_path = goal.get("_file", "")
    if file_path:
        slugs.add(Path(file_path).stem)
    return slugs


def synthesize_signal_summary(
    goal: dict,
    store: ProprioceptiveStore,
    today: datetime.date | None = None,
) -> dict:
    """Build a structured summary for a goal's current readiness state.

    Returns a dict with goal, phase, days_to_next_phase, categories (with avg scores),
    and weakest categories. Designed to be under 500 tokens when serialised.
    """
    today = today or datetime.date.today()
    phase = current_phase(goal.get("phases", []), today)

    # Days to next phase
    until = phase.get("until")
    days_to_next = (datetime.date.fromisoformat(str(until)) - today).days if until else None

    # Collect all expected categories from materials
    all_categories: set[str] = set()
    for mat in goal.get("materials", []):
        all_categories.update(mat.get("categories", []))

    # Aggregate signals by category
    signals = store.recall_all()
    slugs = _goal_slugs(goal)
    goal_signals = [s for s in signals if s.get("goal") in slugs]

    # Deduplicate by timestamp
    seen_ts: set[str] = set()
    unique_signals: list[dict] = []
    for s in goal_signals:
        if s["ts"] not in seen_ts:
            seen_ts.add(s["ts"])
            unique_signals.append(s)

    cat_scores: dict[str, list[int]] = {}
    cat_last_drilled: dict[str, str] = {}
    for s in unique_signals:
        cat = s.get("category", "")
        if cat not in cat_scores:
            cat_scores[cat] = []
            cat_last_drilled[cat] = ""
        cat_scores[cat].append(s.get("score", 0))
        if s.get("ts", "") > cat_last_drilled.get(cat, ""):
            cat_last_drilled[cat] = s["ts"]

    categories: dict[str, dict] = {}
    for cat in sorted(all_categories):
        scores = cat_scores.get(cat, [])
        avg = sum(scores) / len(scores) if scores else 0
        categories[cat] = {
            "avg_score": avg,
            "drill_count": len(scores),
            "last_drilled": cat_last_drilled.get(cat, "never"),
        }

    # Weakest categories (lowest avg, or never drilled)
    weakest = sorted(categories.keys(), key=lambda c: categories[c]["avg_score"])[:3]

    return {
        "goal": goal.get("name", ""),
        "phase": phase["name"],
        "days_to_next_phase": days_to_next,
        "categories": categories,
        "weakest": weakest,
        "total_drills": len(unique_signals),
    }


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
