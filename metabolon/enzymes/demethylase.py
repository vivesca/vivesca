"""demethylase — active memory erasure tools.

Tools:
  demethylase_sweep  — scan marks for staleness, source distribution, clusters
"""

from __future__ import annotations

from dataclasses import dataclass, field

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


@dataclass
class SignalResult:
    name: str
    source: str
    content: str
    age_days: int
    downstream: list[str] = field(default_factory=list)
    cascades_fired: list[str] = field(default_factory=list)


@dataclass
class TransduceResult:
    name: str
    source: str
    cascades_fired: list[str]


@tool(
    name="demethylase_record_access",
    description="Record that a histone mark was accessed — strengthens it against decay (spaced repetition).",
)
def demethylase_record_access(mark_filename: str) -> str:
    """Increment access_count on a mark file. Call when a memory is used in a session."""
    from metabolon.locus import marks as MARKS_DIR
    from metabolon.organelles.demethylase import record_access

    path = MARKS_DIR / mark_filename
    if not path.exists():
        return f"Mark not found: {mark_filename}"
    record_access(path)
    return f"Access recorded for {mark_filename}"


@tool(
    name="demethylase_emit_signal",
    description="Emit an ephemeral paracrine signal for inter-agent communication.",
)
def demethylase_emit_signal(
    name: str,
    content: str,
    source: str = "unknown",
    downstream: list[str] | None = None,
) -> str:
    """Write a short-lived signal other agents can read. Auto-decays after 14 days.

    Args:
        name: Signal name (used for deduplication and filtering).
        content: Signal body text.
        source: Identifier of the emitting agent.
        downstream: Optional shell commands to run when this signal is transduced.
            Biology: ligand binds receptor → intracellular cascade fires.
    """
    from metabolon.organelles.demethylase import emit_signal

    path = emit_signal(name, content, source, downstream=downstream)
    cascade_note = f" ({len(downstream)} downstream commands)" if downstream else ""
    return f"Signal emitted: {path.name}{cascade_note}"


@tool(
    name="demethylase_read_signals",
    description="Read pending inter-agent signals from the ephemeral channel.",
)
def demethylase_read_signals(
    name_filter: str | None = None,
    desensitization_threshold: int = 5,
    include_desensitized: bool = False,
    execute_cascade: bool = False,
) -> list[SignalResult]:
    """Read signals, optionally filtered by name prefix.

    Args:
        name_filter: Filter by name prefix.
        desensitization_threshold: Signals fired >= this many times are excluded (receptor internalization).
        include_desensitized: If True, include desensitized signals in results.
        execute_cascade: If True, run each signal's downstream commands and mark it transduced.
    """
    from metabolon.organelles.demethylase import read_signals

    signals = read_signals(
        name_filter=name_filter,
        desensitization_threshold=desensitization_threshold,
        include_desensitized=include_desensitized,
        execute_cascade=execute_cascade,
    )
    return [
        SignalResult(
            name=s["name"], source=s["source"],
            content=s["content"], age_days=s["age_days"],
            downstream=s.get("downstream", []),
            cascades_fired=s.get("cascades_fired", []),
        )
        for s in signals
    ]


@tool(
    name="demethylase_transduce",
    description="Execute downstream cascades for all pending signals, marking each transduced.",
)
def demethylase_transduce(name_filter: str | None = None) -> list[TransduceResult]:
    """Transduce pending signals — run their downstream command cascades.

    Each signal with a downstream list has its commands executed via subprocess.
    After execution the signal is marked 'transduced: true' so it won't fire again.
    Biology: signal transduction — the ligand activates intracellular enzymes exactly once.

    Args:
        name_filter: Optional name prefix to restrict which signals are transduced.
    """
    from metabolon.organelles.demethylase import transduce

    results = transduce(name_filter=name_filter)
    return [
        TransduceResult(
            name=r["name"],
            source=r["source"],
            cascades_fired=r.get("cascades_fired", []),
        )
        for r in results
    ]


@tool(
    name="demethylase_resensitize",
    description="Re-sensitize a desensitized signal — receptor recycling, returns it to the surface.",
)
def demethylase_resensitize(name: str) -> str:
    """Reset a desensitized signal so it becomes readable again.

    Biology: internalized receptors recycle back to the cell surface after
    the stimulus clears. Resets fire_count to 1 and removes desensitized flag.
    """
    from metabolon.organelles.demethylase import resensitize

    found = resensitize(name)
    if found:
        return f"Signal '{name}' resensitized — receptor recycled to surface."
    return f"No desensitized signal found with name '{name}'."


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
