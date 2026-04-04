
"""Polarization gather -- overnight flywheel preflight (was poiesis).

Establishing cell polarity before division: which direction to grow.
Collects: consumption check, guard status, north stars.
"""


import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

GUARD_FILE = Path.home() / "tmp" / ".polarization-guard-active"
MANIFEST_FILE = Path.home() / "tmp" / "polarization-session.md"
REPORTS_DIR = Path.home() / "epigenome" / "chromatin" / "Poiesis Reports"
NORTH_STAR_FILE = Path.home() / "epigenome" / "chromatin" / "North Star.md"
PRAXIS_FILE = Path.home() / "epigenome" / "chromatin" / "Praxis.md"
NOW_FILE = Path.home() / "epigenome" / "chromatin" / "NOW.md"


# ---------------------------------------------------------------------------
# Data gatherers
# ---------------------------------------------------------------------------


def _consumption_count() -> int:
    """Count Poiesis Report files modified in the last 7 days."""
    if not REPORTS_DIR.exists():
        return 0
    cutoff = time.time() - 7 * 24 * 3600
    return sum(1 for f in REPORTS_DIR.iterdir() if f.stat().st_mtime >= cutoff)


def _respirometry() -> dict:
    """Call respirometry --json and return parsed dict, or error dict."""
    try:
        result = subprocess.run(
            ["respirometry", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return {"error": "respirometry unavailable"}


def _guard_status() -> bool:
    """Return True if the guard file is present."""
    return GUARD_FILE.exists()


def _manifest_summary() -> dict:
    """Return manifest presence and a short summary (first 5 lines)."""
    if not MANIFEST_FILE.exists():
        return {"exists": False, "summary": None}
    lines = MANIFEST_FILE.read_text().splitlines()
    summary = "\n".join(lines[:8])
    return {"exists": True, "summary": summary}


def _north_stars() -> list[str]:
    """Parse ## N. headings from North Star.md."""
    if not NORTH_STAR_FILE.exists():
        return []
    stars = []
    for line in NORTH_STAR_FILE.read_text().splitlines():
        if line.startswith("## ") and line[3:4].isdigit():
            stars.append(line[3:].strip())
    return stars


def _praxis_agent_claude() -> list[str]:
    """Return lines from Praxis.md that contain agent:claude."""
    if not PRAXIS_FILE.exists():
        return []
    return [
        line.strip() for line in PRAXIS_FILE.read_text().splitlines() if "agent:claude" in line
    ]


def _praxis_phantom_count() -> int:
    """Count agent:terry items in Praxis that fail the dispatch gate heuristic."""
    if not PRAXIS_FILE.exists():
        return 0
    try:
        from metabolon.checkpoint import sweep_praxis_for_phantoms

        phantoms = sweep_praxis_for_phantoms(PRAXIS_FILE.read_text())
        return len(phantoms)
    except Exception:
        return 0


def _now_md() -> str | None:
    """Return NOW.md content, or None if absent."""
    if not NOW_FILE.exists():
        return None
    return NOW_FILE.read_text().strip()


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def intake(as_json: bool = False) -> str:
    """Run polarization preflight gather. Returns formatted string."""
    consumption = _consumption_count()
    budget = _respirometry()
    guard = _guard_status()
    manifest = _manifest_summary()
    stars = _north_stars()
    agent_claude_items = _praxis_agent_claude()
    phantom_count = _praxis_phantom_count()
    now_content = _now_md()

    if as_json:
        data = {
            "consumption_count": consumption,
            "budget": budget,
            "guard_active": guard,
            "manifest": manifest,
            "north_stars": stars,
            "praxis_agent_claude_count": len(agent_claude_items),
            "praxis_agent_claude_items": agent_claude_items,
            "praxis_phantom_terry_count": phantom_count,
            "now_md": now_content,
        }
        return json.dumps(data, indent=2)

    # Human-readable output
    lines = ["=" * 60, "POLARIZATION PREFLIGHT", "=" * 60, ""]

    # Consumption
    if consumption <= 3:
        signal = "Consumed. Produce more."
    elif consumption <= 8:
        signal = "Backlog building. Self-sufficient outputs only."
    else:
        signal = "Overproduction. Triage before producing."
    lines.append(f"CONSUMPTION  {consumption} reports (last 7d)  --  {signal}")
    lines.append("")

    # Budget
    if "error" in budget:
        lines.append(f"BUDGET       {budget['error']}")
    else:
        weekly = budget.get("weekly_pct", "?")
        sonnet = budget.get("sonnet_pct", "?")
        resets = budget.get("resets_at", "?")
        stale = "  [stale]" if budget.get("stale") else ""
        lines.append(f"BUDGET       weekly {weekly}%  sonnet {sonnet}%  resets {resets}{stale}")
    lines.append("")

    # Guard
    guard_label = "ACTIVE" if guard else "inactive"
    lines.append(f"GUARD        {guard_label}  ({GUARD_FILE})")
    lines.append("")

    # Manifest
    if manifest["exists"]:
        lines.append(f"MANIFEST     {MANIFEST_FILE}")
        lines.append("")
        for mline in manifest["summary"].splitlines():
            lines.append(f"  {mline}")
    else:
        lines.append(f"MANIFEST     not found  ({MANIFEST_FILE})")
    lines.append("")

    # North stars
    lines.append("NORTH STARS")
    for star in stars:
        lines.append(f"  {star}")
    if not stars:
        lines.append("  (none found)")
    lines.append("")

    # Praxis agent:claude
    lines.append(f"PRAXIS agent:claude  ({len(agent_claude_items)} items)")
    for item in agent_claude_items:
        lines.append(f"  {item}")
    if not agent_claude_items:
        lines.append("  (none)")
    lines.append("")

    # Dispatch gate: phantom obligation check
    if phantom_count > 0:
        lines.append(
            f"DISPATCH GATE  {phantom_count} suspect phantom agent:terry item(s) in Praxis"
        )
        lines.append(
            "  Run `phantom_sweep()` in respiration to review. These may be un-sourced obligations."
        )
    else:
        lines.append("DISPATCH GATE  no phantom agent:terry items detected")
    lines.append("")

    # NOW.md
    if now_content:
        lines.append("NOW.md")
        for nline in now_content.splitlines()[:20]:
            lines.append(f"  {nline}")
        if len(now_content.splitlines()) > 20:
            lines.append("  [truncated]")
    else:
        lines.append("NOW.md       not found")
    lines.append("")

    return "\n".join(lines)


def guard(action: str = "status") -> str:
    """Control the polarization guard file (on/off/status)."""
    if action == "on":
        GUARD_FILE.parent.mkdir(parents=True, exist_ok=True)
        GUARD_FILE.touch()
        return f"Guard activated: {GUARD_FILE}"
    elif action == "off":
        if GUARD_FILE.exists():
            GUARD_FILE.unlink()
            return f"Guard deactivated: {GUARD_FILE}"
        return "Guard was not active."
    else:  # status
        if GUARD_FILE.exists():
            return f"Guard: ACTIVE ({GUARD_FILE})"
        return "Guard: inactive"


def manifest_init() -> str:
    """Create ~/tmp/polarization-session.md with a session template."""
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M HKT")
    content = f"""# Polarization Session -- {date_str}

Mode: Interactive
Started: {time_str}
Budget: (run polarization-gather preflight to populate)

## Wave 1 (dispatched {time_str})

| # | Agent | Star | Status | Output |
|---|---|---|---|---|

## Completed Outputs
(none yet)

## Decisions

"""
    MANIFEST_FILE.write_text(content)
    return f"Manifest created: {MANIFEST_FILE}"


def manifest_show() -> str:
    """Return the manifest contents."""
    if not MANIFEST_FILE.exists():
        return f"Manifest not found: {MANIFEST_FILE}"
    return MANIFEST_FILE.read_text()


# ---------------------------------------------------------------------------
# Budget subcommand
# ---------------------------------------------------------------------------

HKT = timezone(timedelta(hours=8))


def _fmt_resets(resets_at: str | None) -> str:
    """Format an ISO resets_at string as 'YYYY-MM-DD HH:MM HKT', or '?' on failure."""
    if not resets_at:
        return "?"
    try:
        dt = datetime.fromisoformat(resets_at)
        return dt.astimezone(HKT).strftime("%Y-%m-%d %H:%M HKT")
    except (ValueError, TypeError):
        return "?"


def budget(as_json: bool = False) -> str:
    """Fetch fresh budget data and return a clean summary."""
    usage = _respirometry()

    if "error" in usage:
        if as_json:
            return json.dumps({"error": usage["error"]}, indent=2)
        return f"Budget unavailable: {usage['error']}"

    seven_day = usage.get("seven_day", {})
    seven_day_sonnet = usage.get("seven_day_sonnet", {})
    opus_pct = float(seven_day.get("utilization", -1))
    sonnet_pct = float(seven_day_sonnet.get("utilization", -1))
    opus_resets = _fmt_resets(seven_day.get("resets_at"))
    sonnet_resets = _fmt_resets(seven_day_sonnet.get("resets_at"))
    stale = usage.get("stale", False)
    source = usage.get("source", "?")

    if as_json:
        data = {
            "opus_pct": opus_pct,
            "opus_resets": opus_resets,
            "sonnet_pct": sonnet_pct,
            "sonnet_resets": sonnet_resets,
            "stale": stale,
            "source": source,
        }
        return json.dumps(data, indent=2)

    stale_note = "  [stale]" if stale else ""
    lines = []
    if opus_pct >= 0:
        lines.append(f"opus:   {opus_pct:.0f}%  (resets {opus_resets}){stale_note}")
    if sonnet_pct >= 0:
        lines.append(f"sonnet: {sonnet_pct:.0f}%  (resets {sonnet_resets}){stale_note}")
    if not lines:
        lines.append("no budget data available")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Gather context for /polarization overnight flywheel."
    )
    sub = parser.add_subparsers(dest="command")

    preflight_cmd = sub.add_parser("preflight", help="Run pre-flight checks.")
    preflight_cmd.add_argument("--json", action="store_true", help="Output as JSON.")

    guard_cmd = sub.add_parser("guard", help="Control the polarization stop guard.")
    guard_cmd.add_argument(
        "action",
        nargs="?",
        default="status",
        choices=["on", "off", "status"],
    )

    manifest_cmd = sub.add_parser("manifest", help="Manage the session manifest.")
    manifest_cmd.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["init", "show", "update"],
    )

    budget_cmd = sub.add_parser("budget", help="Show current token budget usage.")
    budget_cmd.add_argument("--json", action="store_true", help="Output as JSON.")

    args = parser.parse_args()

    if args.command == "guard":
        print(guard(action=args.action))
    elif args.command == "manifest":
        if args.action == "init":
            print(manifest_init())
        elif args.action == "update":
            print("manifest update: agents write directly to the manifest file.")
        else:
            print(manifest_show())
    elif args.command == "budget":
        print(budget(as_json=args.json))
    else:
        # Default: preflight
        as_json = getattr(args, "json", False)
        print(intake(as_json=as_json))


if __name__ == "__main__":
    main()
