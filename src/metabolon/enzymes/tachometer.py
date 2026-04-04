
"""tachometer — dispatch speed monitor. Actions: speed|trend|slowest|coaching|eta"""


from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.organelles.tachometer import (
    coaching_effectiveness,
    current_rate,
    estimate_completion,
    slowest_recent,
    success_trend,
)


def _fmt_slowest(s: dict | None) -> str:
    if s is None:
        return "No tasks in window."
    return (
        f"Plan: {s['plan']}\n"
        f"Duration: {s['duration_s']:.1f}s\n"
        f"Tool: {s['tool']}\n"
        f"Timestamp: {s['timestamp']}\n"
        f"Success: {s['success']}"
    )


def _fmt_trend(t: dict) -> str:
    return (
        f"Recent ({t['recent_count']}): {t['recent_rate']:.1%}\n"
        f"Historical ({t['historical_count']}): {t['historical_rate']:.1%}\n"
        f"Delta: {t['delta']:+.3f} — {t['direction']}"
    )


def _fmt_coaching(c: dict) -> str:
    return (
        f"Before coaching failure rate: {c['before_failure_rate']:.1%}\n"
        f"After coaching failure rate:  {c['after_failure_rate']:.1%}\n"
        f"Improvement: {c['improvement_pct']:+.1f}pp\n"
        f"Notes analyzed: {c['notes_analyzed']} over {c['total_entries']} entries"
    )


@tool(
    name="tachometer",
    description="Dispatch speed monitor. Actions: speed|trend|slowest|coaching|eta",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def tachometer(
    action: str,
    hours: int = 1,
    remaining_tasks: int = 0,
) -> str:
    """Query sortase dispatch throughput metrics.

    Args:
        action: speed (tasks/hr), trend (success comparison), slowest (longest task),
                coaching (effectiveness score), eta (estimated completion hours).
        hours: Window in hours for slowest/recent queries (default 1).
        remaining_tasks: Number of remaining tasks for eta calculation.
    """
    action = action.lower().strip()

    if action == "speed":
        rate = current_rate()
        return f"Dispatch rate: {rate:.1f} tasks/hour (last 60 min)"

    if action == "trend":
        t = success_trend()
        return _fmt_trend(t)

    if action == "slowest":
        s = slowest_recent(hours=hours)
        return _fmt_slowest(s)

    if action == "coaching":
        c = coaching_effectiveness()
        return _fmt_coaching(c)

    if action == "eta":
        hours_est = estimate_completion(remaining_tasks=remaining_tasks)
        return f"Estimated completion: {hours_est:.1f} hours for {remaining_tasks} remaining tasks"

    return f"Unknown action: {action}. Use: speed|trend|slowest|coaching|eta"
