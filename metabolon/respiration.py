"""respiration — metabolic conversion efficiency.

In biology, respiration is the conversion of fuel into usable energy,
with waste expelled. In the organism:

- Fuel in: tokens consumed (from vasomotor)
- Energy out: outputs Terry acted on (from Praxis/Tonus completion signals)
- Waste: tokens spent on saturated, duplicate, or ignored output

The core metric is ejection fraction: what fraction of pulse output
actually converted into Terry's actions or decisions?

This is the true measure of whether the organism is breathing —
not how much budget remains (vasomotor), not how well the heart
pumps (pulse), but whether the oxygen is reaching the cells.
"""

import datetime
import json
from pathlib import Path

from metabolon.vasomotor import log, record_event

PRAXIS_FILE = Path.home() / "epigenome" / "chromatin" / "Praxis.md"
TONUS_FILE = Path.home() / "epigenome" / "chromatin" / "Tonus.md"
RESPIRATION_STATE = Path.home() / "tmp" / "respiration-metrics.json"
CARDIAC_LOG = Path.home() / "tmp" / "pulse-manifest.md"


def _count_ejected() -> int:
    """Count total items pulse has routed to Terry (agent:terry in Praxis)."""
    if not PRAXIS_FILE.exists():
        return 0
    return sum(1 for line in PRAXIS_FILE.read_text().splitlines() if "agent:terry" in line.lower())


def _count_converted() -> int:
    """Count items Terry has acted on (marked done/completed)."""
    if not PRAXIS_FILE.exists():
        return 0
    count = 0
    for line in PRAXIS_FILE.read_text().splitlines():
        lower = line.lower()
        if "agent:terry" not in lower:
            continue
        if any(sig in lower for sig in ["[x]", "✅", "done", "completed", "resolved"]):
            count += 1
    return count


def _count_stale(days: int = 7) -> int:
    """Count agent:terry items older than N days with no completion signal."""
    if not PRAXIS_FILE.exists():
        return 0
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    count = 0
    for line in PRAXIS_FILE.read_text().splitlines():
        lower = line.lower()
        if "agent:terry" not in lower:
            continue
        if any(sig in lower for sig in ["[x]", "✅", "done", "completed"]):
            continue
        # Check for date in the line
        import re

        match = re.search(r"(\d{4}-\d{2}-\d{2})", line)
        if match:
            try:
                item_date = datetime.datetime.strptime(match.group(1), "%Y-%m-%d").date()
                if item_date < cutoff:
                    count += 1
            except ValueError:
                pass
    return count


def _count_waste() -> dict[str, int]:
    """Count waste signals from today's pulse events."""
    from metabolon.vasomotor import EVENT_LOG

    if not EVENT_LOG.exists():
        return {"saturated": 0, "churn_killed": 0, "failed": 0}

    today = datetime.date.today().isoformat()
    saturated = 0
    churn = 0
    failed = 0

    for line in EVENT_LOG.read_text().splitlines():
        if today not in line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        event = evt.get("event", "")
        if event == "saturation_detected":
            saturated += 1
        elif event == "reduced_ejection":
            churn += 1
        elif event == "systole_error":
            failed += 1

    return {"saturated": saturated, "churn_killed": churn, "failed": failed}


def ejection_fraction() -> float:
    """Core respiration metric: fraction of ejected work that converted.

    Returns 0.0-1.0. Higher = better metabolic efficiency.
    Returns -1.0 if no data (no ejected items).
    """
    ejected = _count_ejected()
    if ejected == 0:
        return -1.0
    converted = _count_converted()
    return round(converted / ejected, 3)


def tidal_volume() -> dict:
    """Full respiration snapshot — all metabolic metrics."""
    ejected = _count_ejected()
    converted = _count_converted()
    stale = _count_stale()
    waste = _count_waste()
    ef = round(converted / ejected, 3) if ejected > 0 else -1.0

    metrics = {
        "timestamp": datetime.datetime.now().isoformat(),
        "ejected": ejected,
        "converted": converted,
        "stale": stale,
        "ejection_fraction": ef,
        "waste": waste,
        "pending": ejected - converted,
    }

    # Persist for trending
    RESPIRATION_STATE.write_text(json.dumps(metrics, indent=2))
    record_event("respiration", **metrics)

    return metrics


def breathing_rate() -> str:
    """Human-readable respiration status."""
    m = tidal_volume()
    ef = m["ejection_fraction"]
    if ef < 0:
        return "APNEIC (no data)"
    if ef < 0.1:
        return f"DYSPNEIC (EF={ef:.0%} — most output ignored)"
    if ef < 0.3:
        return f"SHALLOW (EF={ef:.0%} — low conversion)"
    if ef < 0.6:
        return f"NORMAL (EF={ef:.0%})"
    return f"DEEP (EF={ef:.0%} — high conversion)"


def metabolic_waste_ratio() -> float:
    """Fraction of today's systoles that produced waste (saturated/churn/failed)."""
    from metabolon.vasomotor import EVENT_LOG

    if not EVENT_LOG.exists():
        return 0.0

    today = datetime.date.today().isoformat()
    total_systoles = 0
    waste_systoles = 0

    for line in EVENT_LOG.read_text().splitlines():
        if today not in line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        event = evt.get("event", "")
        if event == "systole_end":
            total_systoles += 1
        if event in ("saturation_detected", "reduced_ejection", "systole_error"):
            waste_systoles += 1

    return round(waste_systoles / total_systoles, 3) if total_systoles > 0 else 0.0


# ---------------------------------------------------------------------------
# Auto-conversion: raise EF by resolving items that don't need Terry
# ---------------------------------------------------------------------------

# Patterns that indicate an item is a confirmation, not a decision
_AUTO_RESOLVE_SIGNALS = [
    "verified complete",
    "verified ready",
    "all checks pass",
    "confirmed ready",
    "confirmed done",
    "no action needed",
    "info only",
    "already implemented",
    "already done",
    "already exists",
    "no changes needed",
    "up to date",
    "analysis done",
    "post confirmed ready",
]

# Items with these verbs need Terry's body/presence — never auto-resolve
_PHYSICAL_ACTION_VERBS = [
    "submit",
    "book",
    "call",
    "reach out",
    "schedule",
    "sign",
    "drop off",
    "pick up",
    "pay",
    "transfer",
    "send",
    "email",
    "meet",
    "attend",
    "visit",
    "go to",
    "promote to",
    "publish",
    "post to",
    "push to",
]


def phantom_sweep() -> dict:
    """Scan Praxis for agent:terry items that are phantom obligations.

    Phantom items are tasks the organism invented without Terry's request
    that require his name/voice/presence.  Unlike auto_convert (which marks
    completions), this flags items that should never have been tagged at all.

    Does NOT modify Praxis — returns a report for the systole to act on.
    The systole should: either remove the item, demote to archive, or
    requeue without the agent:terry tag.

    Returns:
        {"phantom_count": N, "phantoms": [{"line_number", "line", "reason"}]}
    """
    from metabolon.checkpoint import sweep_praxis_for_phantoms

    if not PRAXIS_FILE.exists():
        return {"phantom_count": 0, "phantoms": []}

    phantoms = sweep_praxis_for_phantoms(PRAXIS_FILE.read_text())
    if phantoms:
        record_event(
            "phantom_sweep", count=len(phantoms), items=[p["line"][:80] for p in phantoms]
        )
        log(f"Phantom sweep: {len(phantoms)} suspect agent:terry items found")

    return {"phantom_count": len(phantoms), "phantoms": phantoms}


def auto_convert() -> dict:
    """Sweep Praxis for agent:terry items that are confirmations, not decisions.

    Marks them [x] in-place. Returns summary of what was converted.
    This is the organism breathing deeper — absorbing oxygen automatically
    instead of waiting for Terry to inhale manually.
    """
    if not PRAXIS_FILE.exists():
        return {"converted": 0, "items": []}

    lines = PRAXIS_FILE.read_text().splitlines()
    converted = []
    new_lines = []

    for line in lines:
        lower = line.lower()
        # Only touch uncompleted agent:terry items
        if "agent:terry" in lower and "[x]" not in lower and "- [" in lower:
            # Never auto-resolve physical actions
            if any(verb in lower for verb in _PHYSICAL_ACTION_VERBS):
                new_lines.append(line)
                continue
            if any(sig in lower for sig in _AUTO_RESOLVE_SIGNALS):
                # Mark as auto-resolved
                new_line = line.replace("- [ ]", "- [x]", 1)
                if new_line == line:
                    # Try without space
                    new_line = line.replace("- []", "- [x]", 1)
                if new_line != line:
                    converted.append(line.strip()[:80])
                    new_lines.append(new_line)
                    continue
        new_lines.append(line)

    if converted:
        PRAXIS_FILE.write_text("\n".join(new_lines))
        record_event("auto_conversion", count=len(converted), items=converted)
        log(f"Auto-converted {len(converted)} confirmation items in Praxis")

    return {"converted": len(converted), "items": converted}
