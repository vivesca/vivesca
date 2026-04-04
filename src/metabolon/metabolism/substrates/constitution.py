
"""ExecutiveSubstrate — cortical metabolism of constitutional rules.

Deliberative: senses rules and their signal evidence, identifies prune
candidates (rules with no signal backing), proposes pruning actions,
and monitors biological naming precision across the codebase.
"""


import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from metabolon.locus import genome_md
from metabolon.metabolism.mismatch_repair import scan as precision_scan
from metabolon.metabolism.signals import SensorySystem


class ExecutiveSubstrate:
    """Cortical substrate: audits constitution rules + biological naming precision."""

    name: str = "constitution"

    def __init__(
        self,
        constitution_path: Path | None = None,
        collector: SensorySystem | None = None,
    ):
        self.constitution_path = constitution_path or genome_md
        self.collector = collector or SensorySystem()

    def sense(self, days: int = 30) -> list[dict]:
        """Read constitution rules and cross-reference with signal evidence."""
        if not self.constitution_path.exists():
            return []

        constitution = self.constitution_path.read_text()

        # Extract bold-prefixed rules
        rule_pattern = re.compile(r"\*\*([^*]+?)\.?\*\*\s*(.*)")
        rules: list[dict] = []
        for line in constitution.splitlines():
            stripped = line.strip()
            if not stripped.startswith("**"):
                continue
            m = rule_pattern.match(stripped)
            if m:
                title = m.group(1).strip()
                body = m.group(2).strip()
                rules.append({"title": title, "body": body, "line": stripped})

        if not rules:
            return []

        # Read signals
        since = datetime.now(UTC) - timedelta(days=days)
        signals = self.collector.recall_since(since)

        active_enzymes: set[str] = set()
        for s in signals:
            active_enzymes.add(s.tool)
            if "_" in s.tool:
                active_enzymes.add(s.tool.split("_")[0])

        # Cross-reference
        for rule in rules:
            search_text = (rule["title"] + " " + rule["body"]).lower()
            words = set(re.findall(r"[a-z][a-z0-9_]+", search_text))
            activated_enzymes = words & {t.lower() for t in active_enzymes}
            rule["activated_enzymes"] = activated_enzymes
            rule["has_evidence"] = bool(activated_enzymes)

        # Biological precision gaps (self-assessment)
        try:
            for report in precision_scan():
                if not report.closed:
                    rules.append(
                        {
                            "title": f"Precision gap ({report.kind}): {report.description[:60]}",
                            "body": "; ".join(report.references[:3]),
                            "line": "",
                            "has_evidence": False,
                            "precision_gap": True,
                            "references": report.references,
                        }
                    )
        except Exception:
            pass  # precision scan is non-critical

        return rules

    def candidates(self, sensed: list[dict]) -> list[dict]:
        """Rules without evidence + open precision gaps are candidates."""
        return [r for r in sensed if not r.get("has_evidence", False)]

    def act(self, candidate: dict) -> str:
        """Propose action for rules without evidence or precision gaps."""
        if candidate.get("precision_gap"):
            refs = candidate.get("references", [])
            return f"rename: {candidate['title']} ({len(refs)} reference(s) to update)"
        return f"prune candidate: {candidate['title']}"

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        """Format a constitution audit report."""
        lines: list[str] = []
        lines.append(f"Executive substrate: {len(sensed)} rule(s) sensed")
        lines.append("")

        supported_rules = [r for r in sensed if r.get("has_evidence")]
        unevidenced_rules = [r for r in sensed if not r.get("has_evidence")]

        lines.append("-- Rules with signal evidence --")
        if supported_rules:
            for r in supported_rules:
                tools_str = ", ".join(sorted(r["activated_enzymes"]))
                lines.append(f"  + {r['title']}  ({tools_str})")
        else:
            lines.append("  (none)")

        lines.append("")
        lines.append("-- Rules without signal evidence --")
        if unevidenced_rules:
            for r in unevidenced_rules:
                lines.append(f"  ? {r['title']}")
        else:
            lines.append("  (none)")

        if acted:
            lines.append("")
            lines.append("-- Actions --")
            for action in acted:
                lines.append(f"  {action}")

        lines.append("")
        lines.append(
            f"Summary: {len(supported_rules)} evidenced, {len(unevidenced_rules)} without evidence."
        )

        return "\n".join(lines)
