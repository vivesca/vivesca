#!/usr/bin/env python3
from __future__ import annotations

"""
Generate ~/.claude/skill-triggers.json from skill files.

Extracts trigger phrases from:
1. Skill description (frontmatter) — "Use when user says X, Y, Z"
2. ## Triggers section — bullet list of trigger phrases

Run after skill changes (e.g. from synaxis or skill-autocommit).
"""

import json
import re
from pathlib import Path

SKILLS_DIR = Path.home() / "germline" / "membrane" / "receptors"
OUTPUT = Path.home() / ".claude" / "skill-triggers.json"


def extract_triggers(skill_path: Path) -> list[str]:
    """Extract trigger phrases from a skill file."""
    text = skill_path.read_text()
    triggers = []

    # From description frontmatter — only short quoted phrases
    desc_match = re.search(r"^description:\s*(.+?)$", text, re.MULTILINE)
    if desc_match:
        desc = desc_match.group(1)
        # Extract quoted strings, but only short ones (likely trigger phrases)
        for phrase in re.findall(r'"([^"]+)"', desc):
            if len(phrase) < 40 and not phrase.startswith("Use "):
                triggers.append(phrase)

    # From ## Triggers section — bullet list
    triggers_section = re.search(r"## Triggers\s*\n((?:\s*-\s*.+\n?)+)", text)
    if triggers_section:
        for line in triggers_section.group(1).strip().split("\n"):
            phrase = re.sub(r"^\s*-\s*", "", line).strip().strip("\"'`/")
            if phrase and len(phrase) > 1:
                triggers.append(phrase)

    # Deduplicate, lowercase, filter noise
    seen = set()
    clean = []
    for t in triggers:
        t_lower = t.lower().strip()
        # Skip long sentences (not trigger phrases), duplicates, slash commands
        if (
            t_lower not in seen
            and 1 < len(t_lower) < 40
            and not t_lower.startswith("/")
            and " — " not in t_lower  # description fragments
            and "not for" not in t_lower  # exclusion clauses
            and "use when" not in t_lower
        ):  # meta instructions
            seen.add(t_lower)
            clean.append(t_lower)
    return clean


def main():
    mapping: dict[str, list[str]] = {}

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            skill_file = skill_dir / "skill.md"
        if not skill_file.exists():
            continue

        # Only user-invocable skills
        text = skill_file.read_text()
        if "user_invocable: true" not in text:
            continue

        name = skill_dir.name
        triggers = extract_triggers(skill_file)
        if triggers:
            mapping[name] = triggers

    OUTPUT.write_text(json.dumps(mapping, indent=2, ensure_ascii=False))
    print(
        f"Generated {OUTPUT}: {len(mapping)} skills, {sum(len(v) for v in mapping.values())} triggers"
    )


if __name__ == "__main__":
    main()
