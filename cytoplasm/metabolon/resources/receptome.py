"""Techne — the organism's practiced capabilities.

Resources:
  vivesca://techne — index of all active receptors (CC: skills) with metadata
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import yaml

_SKILLS_ROOT = Path.home() / "skills"
_SUBDIRS = ["compound-engineering", "superpowers"]


def _parse_frontmatter(path: Path) -> dict | None:
    """Extract YAML frontmatter from a SKILL.md file."""
    try:
        text = path.read_text()
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return None


def _operon_entry(skill_dir: Path, prefix: str = "") -> dict | None:
    """Build a receptor entry dict from a skill directory."""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return None
    fm = _parse_frontmatter(skill_file)
    if fm is None:
        return None

    stat = skill_file.stat()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=UTC)

    name = fm.get("name", skill_dir.name)
    if prefix:
        name = f"{prefix}:{name}"

    return {
        "name": name,
        "description": fm.get("description", ""),
        "user_invocable": fm.get("user_invocable", False),
        "runtime": fm.get("runtime", ""),
        "modified": modified.strftime("%Y-%m-%d"),
    }


def generate_operon_index(skills_root: Path | None = None) -> str:
    """Build a compact receptor index from disk."""
    root = skills_root or _SKILLS_ROOT
    entries: list[dict] = []

    if not root.exists():
        return "No receptor directory found."

    # Top-level receptors
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name in _SUBDIRS:
            continue
        if d.name == "archive":
            continue
        entry = _operon_entry(d)
        if entry:
            entries.append(entry)

    # Subdirectory receptors (compound-engineering, superpowers)
    for subdir in _SUBDIRS:
        sub = root / subdir
        if not sub.is_dir():
            continue
        for d in sorted(sub.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            entry = _operon_entry(d, prefix=subdir)
            if entry:
                entries.append(entry)

    # Format output
    lines: list[str] = []
    lines.append(f"# Skill Index ({len(entries)} active)\n")
    lines.append("| Skill | Description | Modified |")
    lines.append("|-------|-------------|----------|")
    for e in entries:
        desc = e["description"][:80] + "..." if len(e["description"]) > 80 else e["description"]
        lines.append(f"| `{e['name']}` | {desc} | {e['modified']} |")

    return "\n".join(lines)
