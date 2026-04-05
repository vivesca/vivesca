"""Spending substrate -- periodic trend analysis over parsed statement data.

Primarily a reporter: reads statement markdown files and surfaces insights about
spending trends, category drift, and subscription cost creep.
"""

import re
from typing import TYPE_CHECKING

from metabolon.locus import spending

if TYPE_CHECKING:
    from pathlib import Path

SPENDING_DIR = spending


class SpendingSubstrate:
    """Metabolism substrate for spending analysis."""

    name: str = "spending"

    def __init__(self, spending_dir: Path = SPENDING_DIR) -> None:
        self.spending_dir = spending_dir

    def sense(self, days: int = 90) -> list[dict]:
        """Read parsed statement files."""
        results = []
        for md in sorted(self.spending_dir.glob("????-??-*.md")):
            if md.name.endswith("-summary.md"):
                continue
            text = md.read_text()
            # Extract frontmatter
            fm_match = re.search(r"^---\n(.+?)\n---", text, re.DOTALL)
            if not fm_match:
                continue
            meta = {}
            for line in fm_match.group(1).splitlines():
                if ": " in line:
                    k, v = line.split(": ", 1)
                    meta[k.strip()] = v.strip()
            # Extract category totals from summary table
            metabolic_pathways = {}
            for m in re.finditer(r"\| (.+?) \| (\d+) \| (-?[\d,]+\.\d{2}) \|", text):
                cat, _count, total = m.group(1).strip(), m.group(2), m.group(3)
                if cat.startswith("**"):
                    continue
                metabolic_pathways[cat] = float(total.replace(",", ""))
            results.append({"file": md.name, "meta": meta, "categories": metabolic_pathways})
        return results

    def candidates(self, sensed: list[dict]) -> list[dict]:
        """Identify months with notable spending patterns."""
        if len(sensed) < 2:
            return []
        # Compare most recent month against prior months
        # Flag categories that increased >30% month-over-month
        recent = sensed[-1]
        prior = sensed[-2]
        candidates = []
        for cat, amount in recent["categories"].items():
            prior_amount = prior["categories"].get(cat, 0)
            if prior_amount != 0 and amount < 0:
                flux_delta = ((amount - prior_amount) / abs(prior_amount)) * 100
                if flux_delta < -30:  # spending increased >30% (more negative)
                    candidates.append(
                        {
                            "category": cat,
                            "current": amount,
                            "prior": prior_amount,
                            "flux_delta": flux_delta,
                        }
                    )
        return candidates

    def act(self, candidate: dict) -> str:
        """Propose review action (no auto-mutation)."""
        return (
            f"Review {candidate['category']}: "
            f"spending changed {candidate['flux_delta']:+.0f}% "
            f"({candidate['prior']:,.0f} -> {candidate['current']:,.0f} HKD)"
        )

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        """Format human-readable spending metabolism report."""
        lines = [f"Spending substrate: {len(sensed)} statement(s) in chromatin"]
        if acted:
            lines.append("")
            lines.append("Proposals:")
            for a in acted:
                lines.append(f"  - {a}")
        return "\n".join(lines)
