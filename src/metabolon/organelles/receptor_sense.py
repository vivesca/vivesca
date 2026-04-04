
"""receptor_sense — proprioceptive readiness sensing against long-lived goals.

Biology: Proprioception is the body's ability to sense its own position and
readiness. This organelle implements the sensing half: reads goal configurations,
aggregates drill signals by category, and synthesises readiness summaries so the
organism knows where its weakest areas are.

Functions:
  current_phase        — determine current goal phase from date markers
  restore_goals        — load goal YAML configs from directory
  decode_flashcard_deck — parse flashcard markdown into structured cards
  synthesize_signal_summary — build readiness summary for a single goal

Classes:
  ProprioceptiveStore  — append-only JSONL store for drill/prep signals
"""


import datetime
import json
import re
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Goal / signal directory defaults (overridable by callers)
# ---------------------------------------------------------------------------

GOALS_DIR = Path.home() / ".local" / "share" / "vivesca" / "goals"
SIGNALS_DIR = Path.home() / ".local" / "share" / "vivesca" / "goals"


# ---------------------------------------------------------------------------
# Phase detection
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Goal loading
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Signal store (append-only JSONL)
# ---------------------------------------------------------------------------


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
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries

    def recall_since(self, since: datetime.datetime) -> list[dict]:
        since_str = since.isoformat()
        return [e for e in self.recall_all() if e.get("ts", "") >= since_str]


# ---------------------------------------------------------------------------
# Flashcard deck decoder
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Goal slug matching
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Signal summary synthesis
# ---------------------------------------------------------------------------


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
