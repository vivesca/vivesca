"""ingestion — meal plan read and order log append.

Deterministic actions for the ingestion meal-suggestion skill:
- Read the weekly meal plan (rotation + order log)
- Append a new entry to the order log section
"""

from __future__ import annotations

import re
from datetime import date

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.locus import experiments as EXPERIMENTS_DIR
from metabolon.locus import meal_plan as MEAL_PLAN


def _cross_link_experiment(entry: str, dish: str) -> str | None:
    """If an active experiment watches keywords matching this dish, append a note."""
    if not EXPERIMENTS_DIR.exists():
        return None

    dish_lower = dish.lower()
    for exp_file in EXPERIMENTS_DIR.glob("assay-*.md"):
        text = exp_file.read_text()
        if "status: active" not in text:
            continue
        # Extract watch_keywords from frontmatter
        match = re.search(r"watch_keywords:\s*\[(.+?)\]", text)
        if not match:
            continue
        keywords = [kw.strip().lower() for kw in match.group(1).split(",")]
        if any(kw in dish_lower for kw in keywords):
            intake_note = f"\n> **Intake logged:** {entry}\n"
            exp_file.write_text(text.rstrip() + "\n" + intake_note + "\n")
            return f"Cross-linked to experiment: {exp_file.name}"
    return None


@tool(
    name="ingestion_read_plan",
    description="Read weekly meal plan rotation and order log.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ingestion_read_plan() -> str:
    """Return the full meal plan file content."""
    if not MEAL_PLAN.exists():
        return f"Meal plan not found at {MEAL_PLAN}"
    return MEAL_PLAN.read_text()


@tool(
    name="ingestion_log_meal",
    description="Append a meal entry to the order log in the meal plan.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def ingestion_log_meal(
    meal_date: str,
    restaurant: str,
    dish: str,
    meal_type: str = "Lunch",
) -> str:
    """Append one entry to the ## Order log section of the meal plan.

    Format: - YYYY-MM-DD (Day): Restaurant, dish. Lunch/Snack.

    Args:
        meal_date: ISO date string (YYYY-MM-DD).
        restaurant: Restaurant name.
        dish: Dish ordered.
        meal_type: "Lunch" or "Snack" (default: Lunch).
    """
    try:
        d = date.fromisoformat(meal_date)
    except ValueError:
        return f"Invalid date format: {meal_date!r}. Use YYYY-MM-DD."

    day_name = d.strftime("%a")
    entry = f"- {meal_date} ({day_name}): {restaurant}, {dish}. {meal_type}."

    if not MEAL_PLAN.exists():
        return f"Meal plan not found at {MEAL_PLAN}"

    text = MEAL_PLAN.read_text()

    # Find the ## Order log section and append before the next ## or EOF
    log_marker = "## Order log"
    if log_marker not in text:
        return "'## Order log' section not found in meal plan."

    log_start = text.index(log_marker)
    # Find end of section (next ## heading or EOF)
    next_section = text.find("\n## ", log_start + len(log_marker))
    if next_section == -1:
        # Append at end
        new_text = text.rstrip() + "\n" + entry + "\n"
    else:
        # Insert before next section
        before = text[:next_section].rstrip()
        after = text[next_section:]
        new_text = before + "\n" + entry + after

    MEAL_PLAN.write_text(new_text)
    result = f"Logged: {entry}"

    xlink = _cross_link_experiment(entry, dish)
    if xlink:
        result += f"\n{xlink}"

    return result
