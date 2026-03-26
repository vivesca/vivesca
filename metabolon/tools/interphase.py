"""interphase — daily note close write for evening routine.

The gather step is already covered by pinocytosis_interphase.
This tool handles the one deterministic write action: closing out
the daily note with the structured interphase summary block.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

DAILY_DIR = Path.home() / "epigenome" / "chromatin" / "Daily"


@tool(
    name="interphase_close_daily_note",
    description="Append interphase summary block to today's daily note.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def interphase_close_daily_note(
    shipped: str,
    tomorrow: str,
    open_threads: str,
    nudges: str,
    day_score: int,
    note_date: str = "",
) -> str:
    """Append the ## Interphase section to the daily note.

    Creates the note if it doesn't exist. Appends if already present.

    Args:
        shipped: 2-3 line summary of what shipped today.
        tomorrow: Key items for tomorrow (meetings, deadlines, prep).
        open_threads: Anything waiting on others.
        nudges: Items that need a poke tomorrow.
        day_score: 1-5 score based on what actually shipped vs what mattered.
        note_date: ISO date string (YYYY-MM-DD). Defaults to today.
    """
    if note_date:
        try:
            d = date.fromisoformat(note_date)
        except ValueError:
            return f"Invalid date format: {note_date!r}. Use YYYY-MM-DD."
    else:
        d = date.today()

    if not 1 <= day_score <= 5:
        return f"day_score must be 1-5, got {day_score}."

    note_path = DAILY_DIR / f"{d.isoformat()}.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)

    block = (
        "\n## Interphase\n\n"
        f"**Shipped:** {shipped}\n"
        f"**Tomorrow:** {tomorrow}\n"
        f"**Open threads:** {open_threads}\n"
        f"**Nudges:** {nudges}\n"
        f"**Day score:** {day_score}/5\n"
    )

    if note_path.exists():
        existing = note_path.read_text()
        if "## Interphase" in existing:
            return f"## Interphase block already present in {note_path.name}. Edit manually if needed."
        new_text = existing.rstrip() + "\n" + block
    else:
        new_text = f"# {d.isoformat()}\n" + block

    note_path.write_text(new_text)
    return f"Interphase block written to {note_path}"
