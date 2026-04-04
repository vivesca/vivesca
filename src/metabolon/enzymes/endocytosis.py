
"""endocytosis — RSS ingestion and status tools.

Actions: status|fetch|stats|top
"""


import contextlib
from datetime import datetime
from typing import Any

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.locus import endocytosis_affinity
from metabolon.morphology import EffectorResult, Secretion


class EndocytosisResult(Secretion):
    output: str
    status: str = ""
    total_scored: int = 0
    total_engaged: int = 0
    signal_ratio: float = 0.0
    avg_engaged_score: float = 0.0
    false_positives_count: int = 0
    false_negatives: list[str] = []
    items: list[dict[str, Any]] = []
    count: int = 0
    days_window: int = 0


_ACTIONS = (
    "status — check endocytosis config and sync status. "
    "fetch — trigger an RSS fetch cycle. Optional: no_archive. "
    "stats — display signal-to-noise ratio and engagement stats. "
    "top — list top-scored ligands from the recent window. Optional: limit, days."
)


def _status_result() -> EndocytosisResult:
    from metabolon.organelles.endocytosis_rss.cli import _file_age, _parse_aware
    from metabolon.organelles.endocytosis_rss.config import restore_config
    from metabolon.organelles.endocytosis_rss.state import restore_state

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
                if parsed is not None
            ),
            default=None,
        )
        if latest is not None:
            lines.append(f"Last fetch:    {latest.strftime('%Y-%m-%d %H:%M')}")

    if config.article_cache_dir.exists():
        cache_files = list(config.article_cache_dir.glob("*.json"))
        size_kb = sum(path.stat().st_size for path in cache_files) / 1024
        lines.append(f"Article cache: {len(cache_files)} files, {size_kb:.0f} KB")
    else:
        lines.append(f"Article cache: missing ({config.article_cache_dir})")

    return EndocytosisResult(output="\n".join(lines), status="ok")


def _stats_result() -> EndocytosisResult:
    from metabolon.organelles.endocytosis_rss.relevance import (
        _read_jsonl,
        affinity_stats,
    )

    scored_rows = _read_jsonl(endocytosis_affinity)
    if not scored_rows:
        return EndocytosisResult(
            output="Insufficient data: no affinity log entries",
            status="insufficient_data",
        )

    scored: dict[str, int] = {}
    for entry in scored_rows:
        title = str(entry.get("title", ""))
        if not title:
            continue
        with contextlib.suppress(TypeError, ValueError):
            scored[title] = int(entry.get("score", 0))

    signal_count = sum(1 for score in scored.values() if score >= 5)
    signal_ratio = signal_count / len(scored) if scored else 0.0

    stats = affinity_stats()
    if stats.get("status") == "insufficient_data":
        summary_lines = [
            f"Signal ratio: {signal_ratio:.1%} ({len(scored)} scored)",
            "Insufficient engagement data for affinity analysis.",
        ]
        return EndocytosisResult(
            output="\n".join(summary_lines),
            status="insufficient_data",
            total_scored=len(scored),
            signal_ratio=round(signal_ratio, 3),
        )

    false_negatives = [str(title) for title in stats.get("false_negatives", [])]
    false_positives_count = int(stats.get("false_positives_count", 0))
    total_engaged = int(stats.get("total_engaged", 0))
    avg_engaged_score = float(stats.get("avg_engaged_score", 0.0))

    summary_lines = [
        f"Signal ratio: {signal_ratio:.1%} ({len(scored)} scored)",
        f"Engaged: {total_engaged} items (avg score {avg_engaged_score:.1f}/10)",
        f"False positives: {false_positives_count}",
    ]
    if false_negatives:
        summary_lines.append(
            "False negatives (low score, high engagement): " + "; ".join(false_negatives[:3])
        )

    return EndocytosisResult(
        output="\n".join(summary_lines),
        status="ok",
        total_scored=int(stats.get("total_scored", len(scored))),
        total_engaged=total_engaged,
        signal_ratio=round(signal_ratio, 3),
        avg_engaged_score=round(avg_engaged_score, 2),
        false_positives_count=false_positives_count,
        false_negatives=false_negatives,
    )


def _top_result(limit: int, days: int) -> EndocytosisResult:
    from metabolon.organelles.endocytosis_rss.relevance import top_cargo

    items = top_cargo(limit=limit, days=days)
    if not items:
        return EndocytosisResult(
            output=f"No items found in last {days} days.",
            items=[],
            count=0,
            days_window=days,
            status="ok",
        )

    lines: list[str] = []
    for index, item in enumerate(items, 1):
        score = item.get("score", 0)
        title = item.get("title", "Untitled")
        source = item.get("source", "Unknown")
        angle = str(item.get("banking_angle", "")).strip()
        line = f"{index}. [{score}/10] {title} — {source}"
        if angle and angle != "N/A":
            line += f"\n   Banking angle: {angle}"
        lines.append(line)

    return EndocytosisResult(
        output="\n".join(lines),
        items=items,
        count=len(items),
        days_window=days,
        status="ok",
    )


@tool(
    name="endocytosis",
    description=f"RSS ingestion and scoring. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def endocytosis(
    action: str,
    no_archive: bool = False,
    limit: int = 10,
    days: int = 7,
) -> EndocytosisResult | EffectorResult:
    """Unified RSS tool."""
    action = action.lower().strip()

    if action == "status":
        return _status_result()

    if action == "fetch":
        from metabolon.organelles.endocytosis_rss.cli import _fetch_locked
        from metabolon.organelles.endocytosis_rss.config import restore_config
        from metabolon.organelles.endocytosis_rss.state import lockfile

        config = restore_config()
        with lockfile(config.state_path):
            _fetch_locked(config, no_archive)
        return EffectorResult(
            success=True,
            message="Fetch cycle complete.",
            data={"no_archive": no_archive},
        )

    if action == "stats":
        return _stats_result()

    if action == "top":
        return _top_result(limit=limit, days=days)

    return EffectorResult(
        success=False,
        message=f"Unknown action '{action}'. Valid: status, fetch, stats, top",
    )
