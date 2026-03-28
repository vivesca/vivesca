"""demethylase — active memory erasure tools.

Tools:
  demethylase_sweep  — scan marks for staleness, source distribution, clusters
"""

from __future__ import annotations

from dataclasses import dataclass

from fastmcp.tools import tool


@dataclass
class DemethylaseSweepResult:
    total_marks: int
    methyl_marks: int
    acetyl_marks: int
    protected_marks: int
    stale_count: int
    source_distribution: dict[str, int]
    type_distribution: dict[str, int]
    top_clusters: list[dict]
    stale_names: list[str]
    report: str


@tool(
    name="demethylase_sweep",
    description="Scan histone marks for staleness, source distribution, and combinatorial clusters.",
)
def demethylase_sweep(threshold_days: int = 90, dry_run: bool = True) -> DemethylaseSweepResult:
    """Run a demethylase sweep across all marks.

    Args:
        threshold_days: Days before a methyl mark is considered stale (default 90).
        dry_run: If True (default), only report — don't delete stale marks.
    """
    from metabolon.organelles.demethylase import format_report, sweep

    report = sweep(threshold_days=threshold_days, dry_run=dry_run)
    return DemethylaseSweepResult(
        total_marks=report.total_marks,
        methyl_marks=report.methyl_marks,
        acetyl_marks=report.acetyl_marks,
        protected_marks=report.protected_marks,
        stale_count=len(report.stale_candidates),
        source_distribution=report.source_distribution,
        type_distribution=report.type_distribution,
        top_clusters=report.mark_clusters[:10],
        stale_names=[m.path.name for m in report.stale_candidates],
        report=format_report(report),
    )
