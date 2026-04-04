from __future__ import annotations

"""Pacemakers — live state of all vivesca LaunchAgent oscillators.

Resources:
  vivesca://oscillators — schedule, status, exit code, and type for each pacemaker
"""


import platform
import plistlib
import re
import subprocess
from pathlib import Path

_LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"
_PATTERNS = ["com.vivesca.*.plist", "com.terry.*.plist"]


def _scan_pacemaker_plists() -> list[Path]:
    """Return all matching plist paths, sorted by name."""
    found: list[Path] = []
    for pattern in _PATTERNS:
        found.extend(_LAUNCH_AGENTS.glob(pattern))
    return sorted(set(found), key=lambda p: p.name)


def _launchctl_status(label: str) -> dict:
    """Run launchctl list <label> and return parsed fields."""
    if platform.system() != "Darwin":
        return {"running": False, "pid": None, "last_exit": None, "loaded": False}
    try:
        result = subprocess.run(
            ["launchctl", "list", label],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return {"running": False, "pid": None, "last_exit": None, "loaded": False}

        raw = result.stdout
        pid_match = re.search(r'"PID"\s*=\s*(\d+)', raw)
        exit_match = re.search(r'"LastExitStatus"\s*=\s*(-?\d+)', raw)
        pid = int(pid_match.group(1)) if pid_match else None
        last_exit = int(exit_match.group(1)) if exit_match else None
        return {
            "running": pid is not None,
            "pid": pid,
            "last_exit": last_exit,
            "loaded": True,
        }
    except (subprocess.TimeoutExpired, OSError):
        return {"running": False, "pid": None, "last_exit": None, "loaded": False}


def _parse_schedule(plist_data: dict) -> str:
    """Extract a human-readable schedule from a parsed plist dict."""
    if "StartCalendarInterval" in plist_data:
        sci = plist_data["StartCalendarInterval"]
        # May be a list of dicts (multiple intervals) or a single dict
        if isinstance(sci, list):
            return "; ".join(_format_calendar_interval(item) for item in sci)
        return _format_calendar_interval(sci)

    if "StartInterval" in plist_data:
        seconds = int(plist_data["StartInterval"])
        if seconds < 60:
            return f"every {seconds}s"
        elif seconds < 3600:
            return f"every {seconds // 60}m"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"every {hours:.0f}h" if hours == int(hours) else f"every {hours:.1f}h"
        else:
            days = seconds / 86400
            return f"every {days:.0f}d" if days == int(days) else f"every {days:.1f}d"

    if plist_data.get("RunAtLoad") and not plist_data.get("StartInterval"):
        return "on-load only"

    return "on-demand"


def _format_calendar_interval(sci: dict) -> str:
    """Format a StartCalendarInterval dict as a human-readable string."""
    parts: list[str] = []
    weekday_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    if "Weekday" in sci:
        wd = int(sci["Weekday"])
        parts.append(weekday_names[wd] if 0 <= wd <= 6 else f"wd{wd}")

    if "Day" in sci:
        parts.append(f"day {sci['Day']}")

    if "Hour" in sci and "Minute" in sci:
        parts.append(f"{int(sci['Hour']):02d}:{int(sci['Minute']):02d}")
    elif "Hour" in sci:
        parts.append(f"{int(sci['Hour']):02d}:xx")
    elif "Minute" in sci:
        parts.append(f"xx:{int(sci['Minute']):02d}")

    return " ".join(parts) if parts else "scheduled"


def _status_label(info: dict) -> str:
    """Map launchctl status to a concise status word."""
    if not info["loaded"]:
        return "unloaded"
    if info["running"]:
        return "running"
    last_exit = info.get("last_exit")
    if last_exit is None:
        return "idle"
    if last_exit == 0:
        return "idle"
    return "error"


def _plist_type(path: Path) -> str:
    """Return 'symlink' if path is a symlink, else 'copy'."""
    return "symlink" if path.is_symlink() else "copy"


def express_pacemaker_status() -> str:
    """Build a markdown table of all vivesca pacemaker LaunchAgents and their live state."""
    plists = _scan_pacemaker_plists()
    if not plists:
        return "# Pacemakers\n\n_(no com.vivesca.* or com.terry.* plists found)_\n"

    rows: list[dict] = []
    for plist_path in plists:
        label = plist_path.stem  # filename without .plist

        # Parse plist
        schedule = "parse error"
        try:
            with plist_path.open("rb") as fh:
                data = plistlib.load(fh)
            label = data.get("Label", label)
            schedule = _parse_schedule(data)
        except Exception:
            pass

        lc = _launchctl_status(label)
        status = _status_label(lc)
        last_exit = lc["last_exit"]
        exit_str = str(last_exit) if last_exit is not None else "—"
        pid_str = f" (pid {lc['pid']})" if lc["pid"] else ""
        ptype = _plist_type(plist_path)

        rows.append(
            {
                "label": label,
                "schedule": schedule,
                "status": f"{status}{pid_str}",
                "last_exit": exit_str,
                "type": ptype,
            }
        )

    # Counters for summary line
    running = sum(1 for r in rows if r["status"].startswith("running"))
    errors = sum(1 for r in rows if r["status"].startswith("error"))
    unloaded = sum(1 for r in rows if r["status"] == "unloaded")

    lines: list[str] = []
    lines.append("# Pacemakers\n")
    lines.append(
        f"_{len(rows)} agents — {running} running, {errors} errors, {unloaded} unloaded_\n"
    )
    lines.append("| Label | Schedule | Status | Last Exit | Type |")
    lines.append("|-------|----------|--------|-----------|------|")
    for r in rows:
        lines.append(
            f"| `{r['label']}` | {r['schedule']} | {r['status']} | {r['last_exit']} | {r['type']} |"
        )

    return "\n".join(lines)
