#!/usr/bin/env python3
from __future__ import annotations

"""
Generate ~/.claude/skill-triggers.json from skill files.

Extracts trigger phrases from THREE sources, in priority order:
1. YAML frontmatter `triggers:` list (canonical going forward)
2. Skill description quoted phrases (e.g. "search for", "find me")
3. ## Triggers markdown section (legacy convention; still supported)

Also extracts anti-triggers from `## Anti-Triggers` markdown section.
Anti-triggers suppress matching even when a positive trigger matches —
prevents e.g. `induction` firing on "garden post" because "post" is in it.

Output schema:
{
  "skill_name": {
    "triggers": ["phrase1", "phrase2", ...],
    "anti_triggers": ["phrase1", ...]
  }
}

Run after skill changes (invoked by dendrite.py PostToolUse on skill edits).

Fails loud — prints WARN to stderr if any per-skill parse fails, but never
crashes the whole generation. SKILLS_DIR not existing is a hard failure
(exit 1) because that's a configuration bug, not a per-skill issue.
"""

import json
import re
import sys
from pathlib import Path

SKILLS_DIR = Path.home() / "germline" / "membrane" / "receptors"
OUTPUT = Path.home() / ".claude" / "skill-triggers.json"


def _frontmatter(text: str) -> str:
    match = re.match(r"---\n(.*?)\n---", text, re.DOTALL)
    return match.group(1) if match else ""


def _parse_yaml_list(frontmatter: str, key: str) -> list[str]:
    pattern = rf"^{re.escape(key)}:\s*\n((?:\s+-\s+.+\n?)+)"
    match = re.search(pattern, frontmatter, re.MULTILINE)
    if not match:
        return []
    items = []
    for line in match.group(1).strip().split("\n"):
        item = re.sub(r"^\s*-\s*", "", line).strip().strip("\"'`")
        if item:
            items.append(item)
    return items


def _parse_md_bullets(text: str, heading: str) -> list[str]:
    pattern = rf"## {re.escape(heading)}\s*\n((?:\s*-\s*.+\n?)+)"
    match = re.search(pattern, text)
    if not match:
        return []
    phrases = []
    for line in match.group(1).strip().split("\n"):
        phrase = re.sub(r"^\s*-\s*", "", line).strip().strip("\"'`/")
        if phrase and len(phrase) > 1:
            phrases.append(phrase)
    return phrases


def _clean(phrases: list[str]) -> list[str]:
    seen = set()
    result = []
    for phrase in phrases:
        normalized = phrase.lower().strip()
        if (
            normalized not in seen
            and 1 < len(normalized) < 40
            and not normalized.startswith("/")
            and " — " not in normalized
            and "not for" not in normalized
            and "use when" not in normalized
            and "," not in normalized
            and "\\" not in normalized
            and any(c.isalpha() for c in normalized)
        ):
            seen.add(normalized)
            result.append(normalized)
    return result


def extract_triggers(skill_path: Path) -> list[str]:
    text = skill_path.read_text()
    frontmatter = _frontmatter(text)
    triggers = []

    triggers.extend(_parse_yaml_list(frontmatter, "triggers"))

    desc_match = re.search(r"^description:\s*(.+?)$", frontmatter, re.MULTILINE)
    if desc_match:
        for phrase in re.findall(r'"([^"]+)"', desc_match.group(1)):
            if len(phrase) < 40 and not phrase.startswith("Use "):
                triggers.append(phrase)

    triggers.extend(_parse_md_bullets(text, "Triggers"))

    return _clean(triggers)


def extract_anti_triggers(skill_path: Path) -> list[str]:
    text = skill_path.read_text()
    frontmatter = _frontmatter(text)
    anti = []
    anti.extend(_parse_yaml_list(frontmatter, "anti_triggers"))
    anti.extend(_parse_md_bullets(text, "Anti-Triggers"))
    return _clean(anti)


def main() -> int:
    if not SKILLS_DIR.exists():
        print(
            f"FATAL: SKILLS_DIR does not exist: {SKILLS_DIR}",
            file=sys.stderr,
        )
        return 1

    mapping: dict[str, dict[str, list[str]]] = {}
    duplicate_check: dict[str, list[str]] = {}
    parse_errors = 0

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            skill_file = skill_dir / "skill.md"
        if not skill_file.exists():
            continue

        try:
            text = skill_file.read_text()
            if "user_invocable: true" not in text:
                continue

            name = skill_dir.name
            triggers = extract_triggers(skill_file)
            anti_triggers = extract_anti_triggers(skill_file)

            if triggers or anti_triggers:
                mapping[name] = {
                    "triggers": triggers,
                    "anti_triggers": anti_triggers,
                }
                for phrase in triggers:
                    duplicate_check.setdefault(phrase, []).append(name)
        except Exception as exc:
            print(f"WARN: parse failed for {skill_file}: {exc}", file=sys.stderr)
            parse_errors += 1

    duplicates = {p: skills for p, skills in duplicate_check.items() if len(skills) > 1}
    if duplicates:
        print(
            f"WARN: {len(duplicates)} trigger phrases are claimed by multiple skills:",
            file=sys.stderr,
        )
        for phrase, skills in sorted(duplicates.items()):
            print(f"  '{phrase}' → {', '.join(skills)}", file=sys.stderr)

    OUTPUT.write_text(json.dumps(mapping, indent=2, ensure_ascii=False))

    total_triggers = sum(len(v["triggers"]) for v in mapping.values())
    total_anti = sum(len(v["anti_triggers"]) for v in mapping.values())
    print(
        f"Generated {OUTPUT}: {len(mapping)} skills, "
        f"{total_triggers} triggers, {total_anti} anti-triggers"
        + (f", {parse_errors} parse errors" if parse_errors else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
