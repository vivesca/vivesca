"""expression — Weekly career forge pre-flight checks.

Deterministic pre-flight for the expression/forge skill:
- Verify source files exist and have content
- List existing consulting library assets by subdirectory
- Report spark count for the current week

Orchestration (Opus planning + Sonnet workers) stays in the skill.
These tools give the skill grounded facts before dispatch.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.locus import chromatin
from metabolon.morphology import Secretion

_SPARKS = chromatin / "Consulting" / "_sparks.md"
_THALAMUS = chromatin / "Thalamus.md"
_NEWS_LOG = chromatin / "AI News Log.md"
_NORTH_STAR = chromatin / "North Star.md"
_CONSULTING = chromatin / "Consulting"

_LIBRARY_DIRS = {
    "Policies": _CONSULTING / "Policies",
    "Architectures": _CONSULTING / "Architectures",
    "Use Cases": _CONSULTING / "Use Cases",
    "Experiments": _CONSULTING / "Experiments",
    "Weekly": _CONSULTING / "_weekly",
}


class ForgePreflightResult(Secretion):
    """Pre-flight check results for the expression forge."""

    ready: bool
    spark_count: int
    missing_files: list[str]
    warnings: list[str]
    summary: str


class ForgeLibraryResult(Secretion):
    """Consulting library asset counts per subdirectory."""

    totals: dict[str, int]
    recent_7d: dict[str, int]
    summary: str


def _count_sparks(path: Path) -> int:
    """Count non-empty, non-header lines in the sparks file."""
    if not path.exists():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    return sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))


def _file_age_days(path: Path) -> float | None:
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    return (datetime.datetime.now().timestamp() - mtime) / 86400


@tool(
    name="expression_preflight",
    description="Check forge prerequisites: sparks, source files, ready to run.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def expression_preflight() -> ForgePreflightResult:
    """Verify all source files the forge needs exist and have content.

    Returns:
        ready: True if all required files present and sparks non-empty.
        spark_count: Lines in _sparks.md (proxy for available material).
        missing_files: Source files that don't exist.
        warnings: Non-blocking issues (stale files, low spark count).
    """
    required = {
        "_sparks.md": _SPARKS,
        "Thalamus.md": _THALAMUS,
        "AI News Log.md": _NEWS_LOG,
        "North Star.md": _NORTH_STAR,
    }

    missing: list[str] = []
    warnings: list[str] = []

    for name, path in required.items():
        if not path.exists():
            missing.append(name)

    spark_count = _count_sparks(_SPARKS)
    if spark_count == 0 and _SPARKS.exists():
        warnings.append("_sparks.md exists but is empty — forge will have nothing to process.")
    elif spark_count < 3:
        warnings.append(f"Low spark count ({spark_count}) — consider running spark agent first.")

    # Warn on stale thalamus (>7 days)
    thal_age = _file_age_days(_THALAMUS)
    if thal_age is not None and thal_age > 7:
        warnings.append(
            f"Thalamus.md is {thal_age:.0f} days old — landscape context may be stale."
        )

    ready = not missing and spark_count > 0

    parts = [f"Forge pre-flight: {'READY' if ready else 'NOT READY'}"]
    parts.append(f"Sparks: {spark_count} items in _sparks.md")
    for name in missing:
        parts.append(f"MISSING: {name}")
    for w in warnings:
        parts.append(f"WARN: {w}")

    return ForgePreflightResult(
        ready=ready,
        spark_count=spark_count,
        missing_files=missing,
        warnings=warnings,
        summary="\n".join(parts),
    )


@tool(
    name="expression_library",
    description="List consulting library asset counts. Dedup/enrichment input for forge.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def expression_library() -> ForgeLibraryResult:
    """Count existing consulting assets per subdirectory.

    Returns total file counts and files created in the last 7 days.
    The forge uses this to dedup (avoid recreating existing assets)
    and to identify enrichment candidates.
    """
    cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
    totals: dict[str, int] = {}
    recent: dict[str, int] = {}

    for label, dirpath in _LIBRARY_DIRS.items():
        if not dirpath.exists():
            totals[label] = 0
            recent[label] = 0
            continue
        files = [f for f in dirpath.glob("*.md") if f.is_file()]
        totals[label] = len(files)
        recent[label] = sum(
            1 for f in files if datetime.datetime.fromtimestamp(f.stat().st_mtime) > cutoff
        )

    grand_total = sum(totals.values())
    grand_recent = sum(recent.values())

    lines = [f"Consulting library: {grand_total} assets ({grand_recent} in last 7d)"]
    for label in _LIBRARY_DIRS:
        t = totals.get(label, 0)
        r = recent.get(label, 0)
        lines.append(f"  {label}: {t} total, {r} recent")

    return ForgeLibraryResult(
        totals=totals,
        recent_7d=recent,
        summary="\n".join(lines),
    )
