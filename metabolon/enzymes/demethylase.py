"""demethylase — signal + mark management (active memory erasure tools).

Actions: emit|read|transduce|resensitize|sweep|record_access
"""

from __future__ import annotations

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion


class DemethylaseResult(Secretion):
    results: str


_ACTIONS = (
    "emit — emit ephemeral paracrine signal. Requires: name, content. Optional: source, downstream. "
    "read — read pending inter-agent signals. Optional: name_filter, desensitization_threshold, include_desensitized, execute_cascade. "
    "transduce — execute downstream cascades for pending signals. Optional: name_filter. "
    "resensitize — re-sensitize a desensitized signal. Requires: name. "
    "sweep — scan histone marks for staleness. Optional: threshold_days, dry_run. "
    "record_access — record mark access for spaced repetition. Requires: mark_filename."
)


@tool(
    name="demethylase",
    description=f"Signal + mark management. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def demethylase(
    action: str,
    name: str = "",
    content: str = "",
    source: str = "unknown",
    downstream: list[str] | None = None,
    name_filter: str | None = None,
    desensitization_threshold: int = 5,
    include_desensitized: bool = False,
    execute_cascade: bool = False,
    threshold_days: int = 90,
    dry_run: bool = True,
    mark_filename: str = "",
) -> DemethylaseResult:
    """Unified signal and mark management tool."""
    action = action.lower().strip()

    if action == "emit":
        if not name or not content:
            return DemethylaseResult(results="emit requires: name, content")
        from metabolon.organelles.demethylase import emit_signal

        path = emit_signal(name, content, source, downstream=downstream)
        cascade_note = f" ({len(downstream)} downstream commands)" if downstream else ""
        return DemethylaseResult(results=f"Signal emitted: {path.name}{cascade_note}")

    elif action == "read":
        from metabolon.organelles.demethylase import read_signals

        signals = read_signals(
            name_filter=name_filter,
            desensitization_threshold=desensitization_threshold,
            include_desensitized=include_desensitized,
            execute_cascade=execute_cascade,
        )
        if not signals:
            return DemethylaseResult(results="No signals found.")
        lines = [f"{len(signals)} signal(s) pending:"]
        for s in signals:
            lines.append(f"  Signal: {s['name']}")
            lines.append(f"    Source: {s['source']}")
            lines.append(f"    Age: {s['age_days']} days")
            lines.append(f"    Content: {s['content']}")
            ds = s.get("downstream", [])
            if ds:
                lines.append(f"    Downstream: {', '.join(ds)}")
            cf = s.get("cascades_fired", [])
            if cf:
                lines.append(f"    Cascades fired: {', '.join(cf)}")
        return DemethylaseResult(results="\n".join(lines))

    elif action == "transduce":
        from metabolon.organelles.demethylase import transduce

        results = transduce(name_filter=name_filter)
        if not results:
            return DemethylaseResult(results="No signals transduced.")
        lines = [f"{len(results)} signal(s) transduced:"]
        for r in results:
            lines.append(f"  Signal: {r['name']}")
            lines.append(f"    Source: {r['source']}")
            cf = r.get("cascades_fired", [])
            if cf:
                lines.append(f"    Cascades fired: {', '.join(cf)}")
        return DemethylaseResult(results="\n".join(lines))

    elif action == "resensitize":
        if not name:
            return DemethylaseResult(results="resensitize requires: name")
        from metabolon.organelles.demethylase import resensitize

        found = resensitize(name)
        if found:
            return DemethylaseResult(
                results=f"Signal '{name}' resensitized — receptor recycled to surface."
            )
        return DemethylaseResult(results=f"No desensitized signal found with name '{name}'.")

    elif action == "sweep":
        from metabolon.organelles.demethylase import format_report, sweep

        report = sweep(threshold_days=threshold_days, dry_run=dry_run)
        header = (
            f"Marks: {report.total_marks} total "
            f"({report.methyl_marks} methyl, {report.acetyl_marks} acetyl, {report.protected_marks} protected). "
            f"Stale: {len(report.stale_candidates)}."
        )
        lines = [header, format_report(report)]
        if report.source_distribution:
            lines.append(
                "Source distribution: "
                + ", ".join(f"{k}={v}" for k, v in sorted(report.source_distribution.items()))
            )
        if report.type_distribution:
            lines.append(
                "Type distribution: "
                + ", ".join(f"{k}={v}" for k, v in sorted(report.type_distribution.items()))
            )
        if report.mark_clusters:
            lines.append(
                f"Top clusters: {len(report.mark_clusters[:10])} shown of {len(report.mark_clusters)}."
            )
        if report.stale_candidates:
            lines.append("Stale marks: " + ", ".join(m.path.name for m in report.stale_candidates))
        return DemethylaseResult(results="\n".join(lines))

    elif action == "record_access":
        if not mark_filename:
            return DemethylaseResult(results="record_access requires: mark_filename")
        from metabolon.locus import marks as MARKS_DIR
        from metabolon.organelles.demethylase import record_access

        path = MARKS_DIR / mark_filename
        if not path.exists():
            return DemethylaseResult(results=f"Mark not found: {mark_filename}")
        record_access(path)
        return DemethylaseResult(results=f"Access recorded for {mark_filename}")

    else:
        return DemethylaseResult(
            results=f"Unknown action '{action}'. Valid: emit, read, transduce, resensitize, sweep, record_access"
        )
