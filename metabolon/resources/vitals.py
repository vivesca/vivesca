from __future__ import annotations

"""Vitals — point-in-time health snapshot.

Resources:
  vivesca://vitals — nightly health report, plugins, activity stats
"""


import json
from pathlib import Path

_HEALTH_FILE = Path.home() / ".claude" / "nightly-health.md"
_SETTINGS = Path.home() / ".claude" / "settings.json"
_STATS_CACHE = Path.home() / ".claude" / "stats-cache.json"


def express_vitals(
    health_path: Path | None = None,
    settings_path: Path | None = None,
    stats_path: Path | None = None,
) -> str:
    """Build a health report from nightly health + live checks."""
    hp = health_path or _HEALTH_FILE
    sp = settings_path or _SETTINGS
    stp = stats_path or _STATS_CACHE

    lines: list[str] = []
    lines.append("# Claude Code Health\n")

    # Nightly health report (if available)
    if hp.exists():
        try:
            content = hp.read_text().strip()
            lines.append("## Nightly Report\n")
            lines.append(content)
            lines.append("")
        except OSError:
            lines.append("_(nightly health report unreadable)_\n")
    else:
        lines.append("_(no nightly health report)_\n")

    # Plugin status
    if sp.exists():
        try:
            data = json.loads(sp.read_text())
            plugins = data.get("enabledPlugins", {})
            if plugins:
                enabled = [k for k, v in plugins.items() if v]
                disabled = [k for k, v in plugins.items() if not v]
                lines.append("## Plugins\n")
                if enabled:
                    lines.append(
                        f"**Enabled ({len(enabled)}):** " + ", ".join(f"`{p}`" for p in enabled)
                    )
                if disabled:
                    lines.append(
                        f"**Disabled ({len(disabled)}):** " + ", ".join(f"`{p}`" for p in disabled)
                    )
                lines.append("")
        except (json.JSONDecodeError, OSError):
            pass

    # Recent activity stats
    if stp.exists():
        try:
            raw = json.loads(stp.read_text())
            # Handle both formats: {dailyActivity: [...]} and flat {date: {...}}
            if isinstance(raw, dict) and "dailyActivity" in raw:
                activity = raw["dailyActivity"]
            elif isinstance(raw, list):
                activity = raw
            elif isinstance(raw, dict):
                # Flat dict: {date: {messages: N, ...}}
                activity = [{"date": k, **v} for k, v in raw.items() if isinstance(v, dict)]
            else:
                activity = []

            if activity:
                # Sort by date descending, take last 5
                recent = sorted(activity, key=lambda x: x.get("date", ""), reverse=True)[:5]
                lines.append("## Recent Activity\n")
                lines.append("| Date | Messages | Sessions | Tool Calls |")
                lines.append("|------|----------|----------|------------|")
                for day in recent:
                    date = day.get("date", "?")
                    msgs = day.get("messageCount", day.get("messages", 0))
                    sessions = day.get("sessionCount", day.get("sessions", 0))
                    tools = day.get("toolCallCount", day.get("tool_calls", 0))
                    lines.append(f"| {date} | {msgs} | {sessions} | {tools} |")
                lines.append("")
        except (json.JSONDecodeError, OSError):
            pass

    return "\n".join(lines)
