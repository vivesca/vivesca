from __future__ import annotations

import re
from pathlib import Path

DEFAULT_COACHING_PATH = Path.home() / "epigenome" / "marks" / "feedback_golem_coaching.md"


def load_coaching_notes(path: Path | None = None) -> list[dict]:
    """Parse a coaching markdown file into structured entries.

    Returns a list of dicts with keys:
        category: the ### heading text
        notes: list of strings (the bullet content under that heading)
    """
    target = path or DEFAULT_COACHING_PATH
    if not target.exists():
        return []

    text = target.read_text(encoding="utf-8")
    entries: list[dict] = []
    current_category: str | None = None
    current_notes: list[str] = []

    for line in text.splitlines():
        heading_match = re.match(r"^###\s+(.+)$", line)
        if heading_match:
            if current_category is not None:
                entries.append({"category": current_category, "notes": current_notes})
            current_category = heading_match.group(1).strip()
            current_notes = []
            continue

        bullet_match = re.match(r"^-\s+(.+)$", line)
        if bullet_match and current_category is not None:
            current_notes.append(bullet_match.group(1).strip())

    if current_category is not None:
        entries.append({"category": current_category, "notes": current_notes})

    return entries


def list_categories(path: Path | None = None) -> list[str]:
    """Return all category headings from the coaching file."""
    entries = load_coaching_notes(path)
    return [entry["category"] for entry in entries]


def add_coaching_note(
    path: Path | None = None,
    category: str = "",
    note: str = "",
) -> None:
    """Append a new note under the specified category.

    If the category already exists, the note is appended beneath it.
    If the category does not exist, a new ### section is appended at the end.
    """
    target = path or DEFAULT_COACHING_PATH
    if not target.exists():
        return

    text = target.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Search for the category heading
    category_header = f"### {category}"
    category_idx = None
    for index, line in enumerate(lines):
        if line.strip() == category_header:
            category_idx = index
            break

    if category_idx is not None:
        # Find the last bullet under this category
        insert_idx = category_idx + 1
        while insert_idx < len(lines) and lines[insert_idx].startswith("- "):
            insert_idx += 1
        lines.insert(insert_idx, f"- {note}")
    else:
        # Append new category at the end
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(f"### {category}")
        lines.append(f"- {note}")

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_coaching_patterns(path: Path | None = None) -> list[str]:
    """Load coaching note headings/patterns for gap detection."""
    target = path or DEFAULT_COACHING_PATH
    if not target.exists():
        return []
    text = target.read_text(encoding="utf-8")
    # Extract pattern headings (### lines and **bold** items)
    patterns: list[str] = []
    for line in text.splitlines():
        if line.startswith("###") or line.startswith("- **"):
            patterns.append(line)
    return patterns


def search_coaching(path: Path | None = None, query: str = "") -> list[dict]:
    """Search coaching notes by keyword (case-insensitive).

    Returns matching entries as list of dicts with keys:
        category, notes (only matching notes)
    """
    entries = load_coaching_notes(path)
    query_lower = query.lower()
    results: list[dict] = []

    for entry in entries:
        matching_notes = [note for note in entry["notes"] if query_lower in note.lower()]
        if matching_notes:
            results.append({"category": entry["category"], "notes": matching_notes})

    return results
