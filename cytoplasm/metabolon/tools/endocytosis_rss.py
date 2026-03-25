"""endocytosis_rss — RSS content ingestion organelle (receptor-mediated endocytosis).

Biology: endocytosis is the process by which a cell internalises extracellular
ligands by engulfing them in a vesicle. This organelle performs RSS
receptor-mediated endocytosis — it binds feed sources (receptors), internalises
articles (ligands), and routes them through the endosomal sorting pathway.

Organelle wiring: the endocytosis_rss organelle lives at
metabolon.organelles.endocytosis_rss and is a first-class part of metabolon.
These tools call the vivesca CLI for operations that require the full fetch
environment (credentials, network), and read the relevance JSONL cache directly
for read-only analytics that don't need the network.

Tools:
  endocytosis_rss_status   — receptor status: last fetch times, cache size
  endocytosis_rss_fetch    — trigger a fetch cycle (endocytosis)
  endocytosis_rss_stats    — ligand signal stats: signal ratio, engagement
  endocytosis_rss_top      — top-scored ligands from the recent window
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import invoke_organelle
from metabolon.morphology import EffectorResult, Secretion

# Vivesca CLI binary: endocytosis subcommands are now vivesca endocytosis <cmd>
_VIVESCA = "vivesca"

# Affinity/engagement JSONL logs written during fetch cycles (path unchanged for data compat)
_AFFINITY_LOG = Path.home() / ".cache" / "lustro" / "relevance.jsonl"
_ENGAGEMENT_LOG = Path.home() / ".cache" / "lustro" / "engagement.jsonl"


# ---------------------------------------------------------------------------
# Internal JSONL reader (reads analytics logs without importing the organelle,
# which has a reticulum/lib path dependency that may not be on the MCP server's PATH)
# ---------------------------------------------------------------------------


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _compute_stats() -> dict[str, Any]:
    """Compute relevance vs engagement stats from the affinity JSONL logs."""
    scored_rows = _read_jsonl(_AFFINITY_LOG)
    engaged_rows = _read_jsonl(_ENGAGEMENT_LOG)

    if not scored_rows:
        return {"status": "insufficient_data", "reason": "no affinity log entries"}

    # Build scored title → score map (last score wins for duplicate titles)
    scored: dict[str, int] = {}
    for entry in scored_rows:
        title = str(entry.get("title", ""))
        if title:
            try:
                scored[title] = int(entry.get("score", 0))
            except (TypeError, ValueError):
                pass

    engaged: set[str] = {str(e.get("title", "")) for e in engaged_rows if e.get("title")}

    false_negatives = sorted(t for t in engaged if scored.get(t, 5) < 5)
    false_positives = sorted(t for t, s in scored.items() if s >= 7 and t not in engaged)

    avg_engaged = (
        sum(scored.get(t, 0) for t in engaged) / len(engaged) if engaged else 0.0
    )

    # Signal ratio: fraction scoring >= 5 across all scored items
    signal_count = sum(1 for s in scored.values() if s >= 5)
    signal_ratio = signal_count / len(scored) if scored else 0.0

    return {
        "status": "ok",
        "total_scored": len(scored),
        "total_engaged": len(engaged),
        "signal_ratio": round(signal_ratio, 3),
        "avg_engaged_score": round(avg_engaged, 2),
        "false_positives_count": len(false_positives),
        "false_negatives": false_negatives[:5],
    }


def _get_top_items(limit: int = 10, days: int = 7) -> list[dict[str, Any]]:
    """Return highest-scored items from the affinity log within the window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items: list[dict[str, Any]] = []
    for entry in _read_jsonl(_AFFINITY_LOG):
        raw_ts = entry.get("timestamp")
        try:
            ts = datetime.fromisoformat(str(raw_ts))
        except (ValueError, TypeError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts < cutoff:
            continue
        items.append(entry)

    items.sort(
        key=lambda x: (int(x.get("score", 0)), str(x.get("timestamp", ""))),
        reverse=True,
    )
    return items[:limit]


# ---------------------------------------------------------------------------
# Result schemas
# ---------------------------------------------------------------------------


class EndocytosisStatusResult(Secretion):
    """Receptor status: last fetch times, cache size, source counts."""

    output: str


class EndocytosisStatsResult(Secretion):
    """Ligand signal stats from the affinity log."""

    status: str
    total_scored: int = 0
    total_engaged: int = 0
    signal_ratio: float = 0.0
    avg_engaged_score: float = 0.0
    false_positives_count: int = 0
    false_negatives: list[str] = []
    summary: str = ""


class EndocytosisTopResult(Secretion):
    """Top-scored ligands from the recent window."""

    items: list[dict[str, Any]]
    count: int
    days_window: int
    summary: str


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


@tool(
    name="endocytosis_rss_status",
    description="Receptor status: last fetch time, source count, cache size.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def endocytosis_rss_status() -> EndocytosisStatusResult:
    """Check current receptor state: last fetch, tracked sources, cache."""
    output = invoke_organelle(_VIVESCA, ["endocytosis", "status"], timeout=15)
    return EndocytosisStatusResult(output=output)


@tool(
    name="endocytosis_rss_fetch",
    description="Trigger an RSS fetch cycle. Endocytoses new articles from all receptors.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def endocytosis_rss_fetch(no_archive: bool = False) -> EffectorResult:
    """Run a fetch cycle. Internalises new ligands from all active receptors.

    no_archive=True skips full-text archiving (faster, tier-1 sources only).
    This is a long-running operation (60-300s depending on source count).
    """
    args = ["endocytosis", "fetch"]
    if no_archive:
        args.append("--no-archive")
    output = invoke_organelle(_VIVESCA, args, timeout=300)
    return EffectorResult(success=True, message=output, data={"no_archive": no_archive})


@tool(
    name="endocytosis_rss_stats",
    description="Ligand signal stats: signal ratio, engagement rate, false positives.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def endocytosis_rss_stats() -> EndocytosisStatsResult:
    """Compute signal-to-noise metrics from the affinity log.

    Signal ratio = fraction of scored items scoring >= 5.
    False positives = high-scored (>=7) items that were never engaged with.
    False negatives = engaged items that scored < 5.
    """
    stats = _compute_stats()

    if stats.get("status") == "insufficient_data":
        return EndocytosisStatsResult(
            status="insufficient_data",
            summary=f"Insufficient data: {stats.get('reason', 'no affinity log')}",
        )

    summary_parts = [
        f"Signal ratio: {stats['signal_ratio']:.1%} ({stats['total_scored']} scored)",
        f"Engaged: {stats['total_engaged']} items (avg score {stats['avg_engaged_score']:.1f}/10)",
        f"False positives: {stats['false_positives_count']}",
    ]
    if stats["false_negatives"]:
        fn_titles = "; ".join(stats["false_negatives"][:3])
        summary_parts.append(f"False negatives (low score, high engagement): {fn_titles}")

    return EndocytosisStatsResult(
        status="ok",
        total_scored=stats["total_scored"],
        total_engaged=stats["total_engaged"],
        signal_ratio=stats["signal_ratio"],
        avg_engaged_score=stats["avg_engaged_score"],
        false_positives_count=stats["false_positives_count"],
        false_negatives=stats["false_negatives"],
        summary="\n".join(summary_parts),
    )


@tool(
    name="endocytosis_rss_top",
    description="Top-scored ligands from the recent window. Default: top 10 from last 7 days.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def endocytosis_rss_top(limit: int = 10, days: int = 7) -> EndocytosisTopResult:
    """Return highest-scored articles from the affinity log within the time window.

    Each item includes: title, source, score (1-10), banking_angle, talking_point.
    Items with banking_angle are highest-value for client meeting preparation.
    """
    items = _get_top_items(limit=limit, days=days)

    if not items:
        return EndocytosisTopResult(
            items=[],
            count=0,
            days_window=days,
            summary=f"No items found in last {days} days.",
        )

    lines = []
    for i, item in enumerate(items, 1):
        score = item.get("score", 0)
        title = item.get("title", "Untitled")
        source = item.get("source", "Unknown")
        angle = str(item.get("banking_angle", "")).strip()
        line = f"{i}. [{score}/10] {title} — {source}"
        if angle and angle not in ("N/A", ""):
            line += f"\n   Banking angle: {angle}"
        lines.append(line)

    return EndocytosisTopResult(
        items=items,
        count=len(items),
        days_window=days,
        summary="\n".join(lines),
    )
