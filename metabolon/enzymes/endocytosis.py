"""endocytosis — RSS ingestion and status tools.

Actions: status|fetch|stats|top
"""

from __future__ import annotations

import contextlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.locus import endocytosis_affinity, endocytosis_recycling
from metabolon.morphology import EffectorResult, Secretion

AFFINITY_LOG = endocytosis_affinity
ENGAGEMENT_LOG = endocytosis_recycling


class EndocytosisResult(Secretion):
    output: str


class EndocytosisStatsResult(Secretion):
    status: str
    total_scored: int = 0
    total_engaged: int = 0
    signal_ratio: float = 0.0
    avg_engaged_score: float = 0.0
    false_positives_count: int = 0
    false_negatives: list[str] = []
    summary: str = ""


class EndocytosisTopResult(Secretion):
    items: list[dict[str, Any]]
    count: int
    days_window: int
    summary: str


_ACTIONS = (
    "status — Check endocytosis config and sync status. "
    "fetch — Trigger an RSS fetch cycle. Optional: no_archive. "
    "stats — Display signal-to-noise ratio and engagement stats. "
    "top — List top-scored ligands from the recent window. Optional: limit, days."
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


@tool(
    name="endocytosis",
    description=f"Endocytosis. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def endocytosis(
    action: str,
    no_archive: bool = False,
    limit: int = 10,
    days: int = 7,
) -> EndocytosisResult | EndocytosisStatsResult | EndocytosisTopResult | EffectorResult:
    """Unified RSS ingestion tool."""
    action = action.lower().strip()

    if action == "status":
        from metabolon.organelles.endocytosis_rss.config import restore_config
        from metabolon.organelles.endocytosis_rss.state import restore_state

        def _file_age(path: Path, now: datetime) -> str:
            if not path.exists():
                return "missing"
            modified = datetime.fromtimestamp(path.stat().st_mtime, tz=now.tzinfo)
            delta = now - modified
            if delta.total_seconds() < 60:
                return "just now"
            if delta.total_seconds() < 3600:
                return f"{int(delta.total_seconds() // 60)}m ago"
            if delta.total_seconds() < 86400:
                return f"{int(delta.total_seconds() // 3600)}h ago"
            return f"{delta.days}d ago"

        def _parse_aware(value: str) -> datetime | None:
            try:
                parsed = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                return None
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed

        config = restore_config()
        now = datetime.now().astimezone()
        lines = [
            f"Endocytosis Status  ({now.strftime('%Y-%m-%d %H:%M %Z')})",
            "=" * 44,
            f"\nConfig dir:    {config.config_dir}",
            f"Sources file:  {_file_age(config.sources_path, now)}",
            f"State file:    {_file_age(config.state_path, now)}",
            f"News log:      {_file_age(config.log_path, now)}",
        ]
        state = restore_state(config.state_path)
        if state:
            lines.append(f"Sources:       {len(state)} tracked")
            latest = max(
                (
                    parsed
                    for value in state.values()
                    if isinstance(value, str)
                    for parsed in [_parse_aware(value)]
                    if parsed
                ),
                default=None,
            )
            if latest is not None:
                lines.append(f"Last fetch:    {latest.strftime('%Y-%m-%d %H:%M')}")
        if config.article_cache_dir.exists():
            files = list(config.article_cache_dir.glob("*.json"))
            size_kb = sum(path.stat().st_size for path in files) / 1024
            lines.append(f"Article cache: {len(files)} files, {size_kb:.0f} KB")
        else:
            lines.append(f"Article cache: missing ({config.article_cache_dir})")
            
        return EndocytosisResult(output="\n".join(lines))

    elif action == "fetch":
        from metabolon.organelles.endocytosis_rss.cli import _fetch_locked
        from metabolon.organelles.endocytosis_rss.config import restore_config
        from metabolon.organelles.endocytosis_rss.state import lockfile

        config = restore_config()
        with lockfile(config.state_path):
            _fetch_locked(config, no_archive)
        return EffectorResult(success=True, message="Fetch cycle complete.", data={"no_archive": no_archive})

    elif action == "stats":
        scored_rows = _read_jsonl(AFFINITY_LOG)
        engaged_rows = _read_jsonl(ENGAGEMENT_LOG)
        
        if not scored_rows:
            return EndocytosisStatsResult(
                status="insufficient_data",
                summary="Insufficient data: no affinity log entries"
            )

        scored: dict[str, int] = {}
        for entry in scored_rows:
            title = str(entry.get("title", ""))
            if title:
                with contextlib.suppress(TypeError, ValueError):
                    scored[title] = int(entry.get("score", 0))

        engaged = {str(entry.get("title", "")) for entry in engaged_rows if entry.get("title")}
        false_negatives = sorted(title for title in engaged if scored.get(title, 5) < 5)
        false_positives = sorted(title for title, score in scored.items() if score >= 7 and title not in engaged)
        avg_engaged = sum(scored.get(title, 0) for title in engaged) / len(engaged) if engaged else 0.0
        signal_count = sum(1 for score in scored.values() if score >= 5)
        signal_ratio = signal_count / len(scored) if scored else 0.0

        summary_parts = [
            f"Signal ratio: {signal_ratio:.1%} ({len(scored)} scored)",
            f"Engaged: {len(engaged)} items (avg score {avg_engaged:.1f}/10)",
            f"False positives: {len(false_positives)}",
        ]
        if false_negatives:
            summary_parts.append(
                "False negatives (low score, high engagement): " + "; ".join(false_negatives[:3])
            )
            
        return EndocytosisStatsResult(
            status="ok",
            total_scored=len(scored),
            total_engaged=len(engaged),
            signal_ratio=round(signal_ratio, 3),
            avg_engaged_score=round(avg_engaged, 2),
            false_positives_count=len(false_positives),
            false_negatives=false_negatives[:5],
            summary="\n".join(summary_parts),
        )

    elif action == "top":
        cutoff = datetime.now(UTC) - timedelta(days=days)
        items: list[dict[str, Any]] = []
        for entry in _read_jsonl(AFFINITY_LOG):
            raw_timestamp = entry.get("timestamp")
            try:
                timestamp = datetime.fromisoformat(str(raw_timestamp))
            except (ValueError, TypeError):
                continue
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
            if timestamp < cutoff:
                continue
            items.append(entry)
            
        items.sort(key=lambda item: (int(item.get("score", 0)), str(item.get("timestamp", ""))), reverse=True)
        items = items[:limit]

        if not items:
            return EndocytosisTopResult(
                items=[], 
                count=0, 
                days_window=days, 
                summary=f"No items found in last {days} days."
            )
            
        lines = []
        for index, item in enumerate(items, 1):
            score = item.get("score", 0)
            title = item.get("title", "Untitled")
            source = item.get("source", "Unknown")
            angle = str(item.get("banking_angle", "")).strip()
            line = f"{index}. [{score}/10] {title} — {source}"
            if angle and angle != "N/A":
                line += f"\n   Banking angle: {angle}"
            lines.append(line)
            
        return EndocytosisTopResult(
            items=items, 
            count=len(items), 
            days_window=days, 
            summary="\n".join(lines)
        )

    else:
        return EndocytosisResult(output=f"Unknown action '{action}'. Valid: status, fetch, stats, top")