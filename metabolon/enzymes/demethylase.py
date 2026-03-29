"""demethylase — signal + mark management (active memory erasure tools)."""

from __future__ import annotations

from dataclasses import dataclass, field

from fastmcp.tools import tool
from mcp.types import ToolAnnotations
from metabolon.morphology import EffectorResult, Secretion


class DemethylaseResult(Secretion):
    output: str


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


_ACTIONS = "emit|read|transduce|resensitize|sweep|record_access"


@tool(
    name="demethylase",
    description="Signal + mark management. Actions: emit|read|transduce|resensitize|sweep|record_access",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def demethylase(
    action: str,
    # emit params
    name: str = "",
    content: str = "",
    source: str = "unknown",
    downstream: list[str] | None = None,
    # read params
    name_filter: str | None = None,
    desensitization_threshold: int = 5,
    include_desensitized: bool = False,
    execute_cascade: bool = False,
    # sweep params
    threshold_days: int = 90,
    dry_run: bool = True,
    # record_access params
    mark_filename: str = "",
) -> DemethylaseResult | DemethylaseSweepResult | EffectorResult:
    action = action.lower().strip()

    # ── emit ──────────────────────────────────────────────────────────
    if action == "emit":
        from metabolon.organelles.demethylase import emit_signal

        path = emit_signal(name, content, source, downstream=downstream)
        cascade_note = f" ({len(downstream)} downstream commands)" if downstream else ""
        return DemethylaseResult(output=f"Signal emitted: {path.name}{cascade_note}")

    # ── read ──────────────────────────────────────────────────────────
    elif action == "read":
        from metabolon.organelles.demethylase import read_signals

        signals = read_signals(
            name_filter=name_filter,
            desensitization_threshold=desensitization_threshold,
            include_desensitized=include_desensitized,
            execute_cascade=execute_cascade,
        )
        results = [
            SignalResult(
                name=s["name"],
                source=s["source"],
                content=s["content"],
                age_days=s["age_days"],
                downstream=s.get("downstream", []),
                cascades_fired=s.get("cascades_fired", []),
            )
            for s in signals
        ]
        lines = []
        for r in results:
            lines.append(f"Signal: {r.name}")
            lines.append(f"  Source: {r.source}")
            lines.append(f"  Age: {r.age_days} days")
            lines.append(f"  Content: {r.content}")
            if r.downstream:
                lines.append(f"  Downstream: {', '.join(r.downstream)}")
            if r.cascades_fired:
                lines.append(f"  Cascades fired: {', '.join(r.cascades_fired)}")
            lines.append("")
        output_text = "\n".join(lines).strip() if lines else "No signals found."
        return DemethylaseResult(output=output_text)

    # ── transduce ─────────────────────────────────────────────────────
    elif action == "transduce":
        from metabolon.organelles.demethylase import transduce

        results = transduce(name_filter=name_filter)
        transduce_results = [
            TransduceResult(
                name=r["name"],
                source=r["source"],
                cascades_fired=r.get("cascades_fired", []),
            )
            for r in results
        ]
        lines = []
        for t in transduce_results:
            lines.append(f"Signal: {t.name}")
            lines.append(f"  Source: {t.source}")
            if t.cascades_fired:
                lines.append(f"  Cascades fired: {', '.join(t.cascades_fired)}")
            lines.append("")
        output_text = "\n".join(lines).strip() if lines else "No signals transduced."
        return DemethylaseResult(output=output_text)

    # ── resensitize ───────────────────────────────────────────────────
    elif action == "resensitize":
        from metabolon.organelles.demethylase import resensitize

        found = resensitize(name)
        if found:
            return DemethylaseResult(output=f"Signal '{name}' resensitized — receptor recycled to surface.")
        return DemethylaseResult(output=f"No desensitized signal found with name '{name}'.")

    # ── sweep ─────────────────────────────────────────────────────────
    elif action == "sweep":
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

    # ── record_access ─────────────────────────────────────────────────
    elif action == "record_access":
        from metabolon.locus import marks as MARKS_DIR
        from metabolon.organelles.demethylase import record_access

        path = MARKS_DIR / mark_filename
        if not path.exists():
            return DemethylaseResult(output=f"Mark not found: {mark_filename}")
        record_access(path)
        return DemethylaseResult(output=f"Access recorded for {mark_filename}")

    else:
        return EffectorResult(
            success=False,
            message=f"Unknown action '{action}'. Available: {_ACTIONS}",
        )
