"""ultradian — deterministic situational context gathering.

The ultradian skill needs a `ultradian-gather` equivalent as a tool.
This implements the deterministic gathering steps:
  - Current date/time (HKT)
  - NOW.md open decisions
  - Unchecked job alerts count (post-noon only)
  - Efferens (notice board) messages
  - Praxis today/overdue tasks

The LLM skill reads this output and synthesises the situational snapshot.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.locus import chromatin as CHROMATIN

HKT = timezone(timedelta(hours=8))

_NOW_MD = CHROMATIN / "NOW.md"
_JOB_HUNT_DIR = CHROMATIN / "Job Hunting"


def _hkt_now() -> datetime:
    return datetime.now(HKT)


def _read_now_md() -> str:
    """Extract open decisions from NOW.md (not [decided] or [done])."""
    if not _NOW_MD.exists():
        return "NOW.md not found."
    try:
        text = _NOW_MD.read_text()
        # Surface lines that look like open gates/decisions
        # Exclude lines containing [decided], [done], [x], or checked boxes
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            lower = stripped.lower()
            if any(marker in lower for marker in ["[decided]", "[done]", "[x]", "- [x]"]):
                continue
            lines.append(stripped)
        if not lines:
            return "NOW.md: no open items."
        return "NOW.md open items:\n" + "\n".join(f"  {ln}" for ln in lines[:20])
    except Exception as e:
        return f"NOW.md read error: {e}"


def _count_job_alerts() -> str:
    """Count unchecked flagged job alerts for today or most recent file."""
    now = _hkt_now()
    today_str = now.strftime("%Y-%m-%d")
    alert_file = _JOB_HUNT_DIR / f"Job Alerts {today_str}.md"

    if not alert_file.exists():
        # Try most recent
        candidates = sorted(_JOB_HUNT_DIR.glob("Job Alerts *.md"))
        if not candidates:
            return "No job alert files found."
        alert_file = candidates[-1]

    try:
        text = alert_file.read_text()
        unchecked = len(re.findall(r"^- \[ \]", text, re.MULTILINE))
        total = len(re.findall(r"^- \[[ x]\]", text, re.MULTILINE))
        return f"Job alerts ({alert_file.name}): {unchecked}/{total} unchecked."
    except Exception as e:
        return f"Job alerts read error: {e}"


def _read_efferens() -> str:
    """Read efferens notice board via acta."""
    try:
        sys.path.insert(0, str(Path.home() / "code" / "acta" / "src"))
        import acta
        msgs = acta.read()
        if not msgs:
            return "Efferens: board empty."
        lines = [f"Efferens ({len(msgs)} message(s)):"]
        for m in msgs[:5]:
            sev = m.get("severity", "info")
            sender = m.get("from", "?")
            body = m.get("body", "")[:80].replace("\n", " ")
            lines.append(f"  [{sev}] {sender}: {body}")
        return "\n".join(lines)
    except Exception as e:
        return f"Efferens unavailable: {e}"


def _read_praxis_today() -> str:
    """Read today's and overdue Praxis tasks (max 5)."""
    try:
        from metabolon.organelles import praxis as _praxis
        data = _praxis.today()
        items = []
        for group in ("overdue", "today"):
            for item in data.get(group, []):
                label = item.get("text") or item.get("title", "")
                due = item.get("due", "")
                items.append(f"  [{group}] {label}" + (f" (due {due})" if due else ""))
        if not items:
            return "Praxis: nothing due today."
        return "Praxis (today/overdue):\n" + "\n".join(items[:5])
    except Exception as e:
        return f"Praxis unavailable: {e}"


@tool(
    name="ultradian_gather",
    description="Gather situational context: time, NOW.md, job alerts, efferens, Praxis.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ultradian_gather(json_output: bool = False) -> str:
    """Collect all deterministic situational inputs for the ultradian skill.

    Gathers: current HKT time, NOW.md open decisions, job alert count,
    efferens notice board, and today's/overdue Praxis tasks.

    Args:
        json_output: Return structured JSON instead of human-readable text.
    """
    now = _hkt_now()
    time_str = now.strftime("%I:%M%p %A %Y-%m-%d HKT").lstrip("0")
    hour = now.hour

    sections: dict[str, str] = {
        "time": time_str,
        "now_md": _read_now_md(),
        "praxis": _read_praxis_today(),
        "efferens": _read_efferens(),
    }

    # Job alerts: only post-noon per skill spec
    if hour >= 12:
        sections["job_alerts"] = _count_job_alerts()
    else:
        sections["job_alerts"] = f"Job alerts: skipped (pre-noon, {time_str})."

    if json_output:
        return json.dumps(sections, ensure_ascii=False, indent=2)

    parts = [f"Situational snapshot @ {time_str}"]
    parts.append("")
    for key in ("now_md", "praxis", "efferens", "job_alerts"):
        parts.append(sections[key])
        parts.append("")

    return "\n".join(parts).strip()
