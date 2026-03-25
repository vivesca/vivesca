"""ConsolidationSubstrate — cortical metabolism of memory files.

Hippocampal consolidation: senses memory files, classifies by type,
checks signal correlation and constitution overlap, then proposes
promote/migrate/prune actions. Short-term → long-term.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from metabolon.metabolism.signals import SensorySystem

# Type to consolidation pathway — mirrors cli.py CONSOLIDATION_PATHWAYS
CONSOLIDATION_PATHWAYS: dict[str, tuple[str, str]] = {
    "feedback": ("Constitution", "Behavioral rules that govern every session"),
    "finding": (
        "Program (hook/guard/linter)",
        "Technical gotchas should be enforced, not remembered",
    ),
    "user": (
        "Constitution user section or relevant skill",
        "Preferences that matter every session",
    ),
    "project": ("Vault note (~/epigenome/chromatin/)", "Project state belongs in source of truth"),
    "reference": ("tool-index.md or skill file", "Pointers belong where the action is"),
}


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML frontmatter from a markdown file."""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta


def _keyword_overlap(text_a: str, text_b: str, min_word_len: int = 4) -> set[str]:
    """Return significant words shared between two texts."""

    def _words(text: str) -> set[str]:
        return {
            w.lower()
            for w in re.findall(r"[a-z][a-z0-9_]+", text.lower())
            if len(w) >= min_word_len
        }

    return _words(text_a) & _words(text_b)


class ConsolidationSubstrate:
    """Cortical substrate: consolidates memory into long-term knowledge."""

    name: str = "memory"

    def __init__(
        self,
        memory_dir: Path | None = None,
        constitution_path: Path | None = None,
        collector: SensorySystem | None = None,
    ):
        self.memory_dir = memory_dir or (
            Path.home() / ".claude" / "projects" / "-Users-terry" / "memory"
        )
        self.constitution_path = constitution_path or (
            Path.home() / ".local" / "share" / "vivesca" / "genome.md"
        )
        self.collector = collector or SensorySystem()

    def sense(self, days: int = 30) -> list[dict]:
        """Read memory files, classify, and check signal/constitution correlation."""
        if not self.memory_dir.exists():
            return []

        md_files = sorted(p for p in self.memory_dir.glob("*.md") if p.name != "MEMORY.md")
        if not md_files:
            return []

        # Read constitution for overlap detection
        constitution = ""
        if self.constitution_path.exists():
            constitution = self.constitution_path.read_text()

        # Read signals
        since = datetime.now(UTC) - timedelta(days=days)
        signals = self.collector.recall_since(since)

        active_enzymes: set[str] = set()
        for s in signals:
            active_enzymes.add(s.tool.lower())
            if "_" in s.tool:
                active_enzymes.add(s.tool.split("_")[0].lower())

        # Parse and annotate
        memories: list[dict] = []
        for fp in md_files:
            text = fp.read_text()
            meta = _parse_frontmatter(text)
            mem_type = meta.get("type", "unknown")

            overlap = _keyword_overlap(text, constitution)
            mem_words = {w.lower() for w in text.split() if len(w) >= 3}
            signal_match = bool(mem_words & active_enzymes)

            target = CONSOLIDATION_PATHWAYS.get(
                mem_type, ("Unknown", "No migration rule for this type")
            )

            memories.append(
                {
                    "path": str(fp),
                    "name": meta.get("name", fp.stem),
                    "description": meta.get("description", ""),
                    "type": mem_type,
                    "text": text,
                    "target": target,
                    "constitution_overlap": overlap,
                    "signal_match": signal_match,
                }
            )

        return memories

    def candidates(self, sensed: list[dict]) -> list[dict]:
        """Identify memories that need action.

        Categories:
        - feedback/user with high constitution overlap: already promoted
        - feedback/user with signal match: high-priority promotion
        - finding with signal match: high-priority program candidate
        - project/reference: migration candidates
        - no overlap and no signal: dead candidates (prune)
        """
        results: list[dict] = []

        for mem in sensed:
            mt = mem["type"]
            overlap = mem["constitution_overlap"]
            signal_match = mem["signal_match"]

            if mt == "feedback":
                if len(overlap) >= 5:
                    mem["action"] = "already_promoted"
                elif signal_match:
                    mem["action"] = "promote"
                    mem["priority"] = "high (signal evidence)"
                else:
                    mem["action"] = "promote"

            elif mt == "finding":
                if signal_match:
                    mem["action"] = "program"
                    mem["priority"] = "high (signal evidence)"
                else:
                    mem["action"] = "program"

            elif mt in ("project", "reference"):
                mem["action"] = "migrate"

            elif mt == "user":
                if len(overlap) >= 5:
                    mem["action"] = "already_promoted"
                else:
                    mem["action"] = "promote"

            else:
                mem["action"] = "unknown"

            # Dead check: no overlap and no signal
            if not overlap and not signal_match and mem.get("action") != "already_promoted":
                mem["dead"] = True

            results.append(mem)

        return results

    def act(self, candidate: dict) -> str:
        """Propose a migration action for a memory.

        Does not auto-act — returns descriptive proposals.
        """
        action = candidate.get("action", "unknown")
        name = candidate["name"]
        priority = candidate.get("priority", "")

        if candidate.get("dead"):
            return f"prune candidate: {name} (no signal or constitution evidence)"

        if action == "already_promoted":
            overlap_count = len(candidate.get("constitution_overlap", set()))
            return f"already promoted: {name} (overlap: {overlap_count} keywords)"

        if action == "promote":
            suffix = f" [{priority}]" if priority else ""
            return f"promote to constitution: {name}{suffix}"

        if action == "program":
            suffix = f" [{priority}]" if priority else ""
            return f"program candidate: {name}{suffix}"

        if action == "migrate":
            target_name, rationale = candidate.get("target", ("Unknown", ""))
            return f"migrate to {target_name}: {name} ({rationale})"

        return f"review: {name} (type={candidate['type']})"

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        """Format a memory dissolution report."""
        lines: list[str] = []
        lines.append(f"Consolidation substrate: {len(sensed)} file(s) sensed")
        lines.append("")

        # By type
        type_counts: dict[str, int] = {}
        for mem in sensed:
            t = mem["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        lines.append("-- Memories by type --")
        for t in sorted(type_counts):
            target_name, _ = CONSOLIDATION_PATHWAYS.get(t, ("Unknown", ""))
            lines.append(f"  {t}: {type_counts[t]}  -> {target_name}")

        # Actions
        if acted:
            lines.append("")
            lines.append("-- Actions --")

            promote = [a for a in acted if a.startswith("promote")]
            already = [a for a in acted if a.startswith("already")]
            program = [a for a in acted if a.startswith("program")]
            migrate = [a for a in acted if a.startswith("migrate")]
            prune = [a for a in acted if a.startswith("prune")]
            other = [
                a
                for a in acted
                if not any(
                    a.startswith(p) for p in ("promote", "already", "program", "migrate", "prune")
                )
            ]

            for label, items in [
                ("Promote", promote),
                ("Already promoted", already),
                ("Program", program),
                ("Migrate", migrate),
                ("Prune", prune),
                ("Other", other),
            ]:
                if items:
                    lines.append(f"  {label}:")
                    for a in items:
                        lines.append(f"    {a}")

        # Summary
        promote_count = sum(1 for a in acted if a.startswith("promote"))
        already_count = sum(1 for a in acted if a.startswith("already"))
        program_count = sum(1 for a in acted if a.startswith("program"))
        migrate_count = sum(1 for a in acted if a.startswith("migrate"))
        prune_count = sum(1 for a in acted if a.startswith("prune"))

        lines.append("")
        lines.append(
            f"Summary: {promote_count} to promote, "
            f"{already_count} already promoted, "
            f"{program_count} to program, "
            f"{migrate_count} to migrate, "
            f"{prune_count} to prune."
        )

        return "\n".join(lines)
