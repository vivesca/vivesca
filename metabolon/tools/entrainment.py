"""entrainment — morning brief + circadian sync.

Tools:
  entrainment_brief  — sleep scores + overnight results in one call
  entrainment_status — circadian sync: zeitgeber state and schedule recommendations
"""

from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import VIVESCA_ROOT, invoke_organelle
from metabolon.morphology import Secretion

SOPOR = "sopor"
NIGHTLY_HEALTH = Path.home() / ".claude" / "nightly-health.md"
SKILL_FLYWHEEL = Path.home() / ".claude" / "skill-flywheel-daily.md"


class EntrainmentResult(Secretion):
    """Morning brief sections."""

    sleep: str
    overnight: str
    alerts: list[str]


def _read_if_fresh(path: Path, max_age_hours: int = 24) -> str | None:
    """Read file if it exists and was modified within max_age_hours."""
    try:
        if not path.exists():
            return None
        import time

        age_hours = (time.time() - path.stat().st_mtime) / 3600
        if age_hours > max_age_hours:
            return None
        return path.read_text().strip()
    except Exception:
        return None


@tool(
    name="entrainment_brief",
    description="Morning brief: sleep scores + overnight system health.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def entrainment_brief() -> EntrainmentResult:
    """Gather morning brief: sleep data + overnight results."""
    alerts: list[str] = []

    # Sleep
    try:
        from metabolon.organelles.chemoreceptor import sense as _sense

        sleep = _sense().get("formatted", "")
        # Flag low readiness
        import re

        match = re.search(r"Readiness:\s*(\d+)", sleep)
        if match and int(match.group(1)) < 65:
            alerts.append(f"Low readiness ({match.group(1)}) -- consider an easier day")
    except Exception:
        sleep = "sopor unavailable"

    # Overnight results
    overnight_parts = []

    health = _read_if_fresh(NIGHTLY_HEALTH)
    if health:
        # Surface warnings only
        warning_lines = [
            ln for ln in health.splitlines() if "warning" in ln.lower() or "red" in ln.lower()
        ]
        if warning_lines:
            overnight_parts.append("System health: " + "; ".join(warning_lines[:3]))
        else:
            overnight_parts.append("System health: all green")

    flywheel = _read_if_fresh(SKILL_FLYWHEEL)
    if flywheel:
        miss_lines = [ln for ln in flywheel.splitlines() if "miss" in ln.lower() or "0%" in ln]
        if miss_lines:
            overnight_parts.append("Skill routing: " + "; ".join(miss_lines[:3]))

    # Kinesin overnight results
    try:
        kinesin_out = invoke_organelle(
            str(VIVESCA_ROOT / "effectors" / "overnight-gather"), ["brief"], timeout=15
        )
        if "NEEDS_ATTENTION" in kinesin_out or "CRITICAL" in kinesin_out:
            attention = [
                ln
                for ln in kinesin_out.splitlines()
                if "NEEDS_ATTENTION" in ln or "CRITICAL" in ln
            ]
            overnight_parts.extend(attention[:3])
            alerts.extend(attention[:3])
        elif kinesin_out.strip():
            overnight_parts.append(kinesin_out[:200])
    except Exception:
        pass

    overnight = "\n".join(overnight_parts) if overnight_parts else "No overnight data"

    return EntrainmentResult(sleep=sleep, overnight=overnight, alerts=alerts)


class EntrainmentStatusResult(Secretion):
    """Circadian sync: zeitgeber state and schedule recommendations."""

    signals: dict
    recommendations: dict
    summary: str


@tool(
    name="entrainment_status",
    description="Circadian sync: zeitgeber state and schedule recommendations.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def entrainment_status() -> EntrainmentStatusResult:
    """Read current zeitgebers and return advisory schedule adjustments."""
    from metabolon.organelles.entrainment import optimal_schedule, zeitgebers

    signals = zeitgebers()
    schedule = optimal_schedule(signals)
    return EntrainmentStatusResult(
        signals=signals,
        recommendations=schedule["recommendations"],
        summary=schedule["summary"],
    )
