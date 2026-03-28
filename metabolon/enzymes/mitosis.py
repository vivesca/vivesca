"""mitosis — DR sync tools for gemmule hot standby.

One-way push from iMac to gemmule (fly.io, nrt).
Mac is authoritative. Lucerna never writes back.
"""

from __future__ import annotations

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Vital


@tool(
    name="mitosis_sync",
    description="Push current state to gemmule DR site. One-way sync, Mac authoritative.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def mitosis_sync(targets: list[str] | None = None) -> EffectorResult:
    """Sync organism state to gemmule hot standby.

    Args:
        targets: Specific targets to sync (e.g. ["chromatin", "marks"]).
                 None syncs all targets.
    """
    from metabolon.organelles.mitosis import sync

    report = sync(targets)
    results_summary = [
        {
            "target": r.target,
            "ok": r.success,
            "elapsed_s": round(r.elapsed_s, 1),
            "error": r.message,
        }
        for r in report.results
    ]
    return EffectorResult(
        success=report.ok,
        message=report.summary,
        data={"results": results_summary, "elapsed_s": round(report.elapsed_s, 1)},
    )


@tool(
    name="mitosis_status",
    description="Check gemmule DR site health and sync freshness.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def mitosis_status() -> Vital:
    """Check reachability, machine state, and per-target sync age."""
    from metabolon.organelles.mitosis import status

    info = status()
    if not info["reachable"]:
        return Vital(
            status="error",
            message="gemmule unreachable via Tailscale",
            details=info,
        )

    stale = [
        name
        for name, t in info.get("targets", {}).items()
        if t.get("state") in ("stale", "missing")
    ]
    if stale:
        return Vital(
            status="warning",
            message=f"gemmule reachable but {len(stale)} targets stale/missing: {', '.join(stale)}",
            details=info,
        )

    return Vital(
        status="ok",
        message=f"gemmule healthy, machine {info.get('machine_state', 'unknown')}",
        details=info,
    )
