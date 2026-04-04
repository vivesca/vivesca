
"""Infection log — structured record of tool errors for immune pattern detection.

Honest immunity: the organism cannot auto-heal deterministically, so it does the
next best thing — it detects, records, and surfaces patterns for human review.

Detection first, then repair (autopoiesis trajectory).

Log path: ~/.local/share/vivesca/infections.jsonl
Chronic threshold: CHRONIC_THRESHOLD repeated errors with the same fingerprint.
"""


import configparser
import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from metabolon.locus import infections_log

logger = logging.getLogger(__name__)

DEFAULT_LOG = infections_log

_CONF_PATH = Path(__file__).parent / "infection.conf"
_conf = configparser.ConfigParser()
_conf.read(_CONF_PATH)

# A tool+error pattern repeated this many times is flagged as a chronic infection.
CHRONIC_THRESHOLD = _conf.getint("detection", "chronic_threshold", fallback=3)


class InfectionEvent(TypedDict):
    ts: str  # ISO-8601 UTC
    tool: str
    error: str  # truncated error message
    fingerprint: str  # sha256[:12] of tool+error for pattern matching
    healed: bool  # whether LLM repair was attempted and accepted


def _fingerprint(tool: str, error: str) -> str:
    """Stable 12-char hex digest for a tool+error pattern."""
    raw = f"{tool}:{error[:200]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def record_infection(
    tool: str,
    error: str,
    healed: bool = False,
    log_path: Path = DEFAULT_LOG,
) -> InfectionEvent:
    """Append one infection event to the structured log. Never raises."""
    event: InfectionEvent = {
        "ts": datetime.now(UTC).isoformat(),
        "tool": tool,
        "error": error[:300],
        "fingerprint": _fingerprint(tool, error),
        "healed": healed,
    }
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        logger.debug("Infection log write failed for %s", tool, exc_info=True)
    return event


def recall_infections(log_path: Path = DEFAULT_LOG) -> list[InfectionEvent]:
    """Read all infection events from the log. Returns empty list if log absent."""
    if not log_path.exists():
        return []
    events: list[InfectionEvent] = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


class ChronicPattern(TypedDict):
    tool: str
    fingerprint: str
    count: int
    last_error: str
    last_seen: str
    healed_count: int


def chronic_infections(
    log_path: Path = DEFAULT_LOG,
    threshold: int = CHRONIC_THRESHOLD,
) -> list[ChronicPattern]:
    """Return tool+error patterns that exceed the chronic threshold.

    A chronic infection is a fingerprint with >= threshold *unhealed* events.
    Fully-healed patterns are suppressed even if they were historically chronic.
    """
    events = recall_infections(log_path)
    if not events:
        return []

    # Group by fingerprint
    groups: dict[str, list[InfectionEvent]] = {}
    for ev in events:
        fp = ev["fingerprint"]
        groups.setdefault(fp, []).append(ev)

    patterns: list[ChronicPattern] = []
    for fp, group in groups.items():
        unhealed = [e for e in group if not e["healed"]]
        # Only chronic if unhealed occurrences meet the threshold
        if len(unhealed) < threshold:
            continue
        # Most recent unhealed event
        latest = max(unhealed, key=lambda e: e["ts"])
        patterns.append(
            ChronicPattern(
                tool=latest["tool"],
                fingerprint=fp,
                count=len(group),
                last_error=latest["error"],
                last_seen=latest["ts"],
                healed_count=sum(1 for e in group if e["healed"]),
            )
        )

    # Sort by count descending (most infected first)
    patterns.sort(key=lambda p: p["count"], reverse=True)
    return patterns


def infection_summary(log_path: Path = DEFAULT_LOG) -> str:
    """Human-readable summary line for homeostasis_system output.

    Returns an empty string if no infections are logged.
    """
    events = recall_infections(log_path)
    if not events:
        return ""

    total = len(events)
    unhealed = sum(1 for e in events if not e["healed"])
    chronics = chronic_infections(log_path)

    parts = [f"Infections: {total} events, {unhealed} unhealed"]
    if chronics:
        chronic_lines = [
            f"  CHRONIC: {p['tool']} x{p['count']} (healed {p['healed_count']})"
            f" — {p['last_error'][:80]}"
            for p in chronics
        ]
        parts.append("  Chronic patterns (human review needed):")
        parts.extend(chronic_lines)
    return "\n".join(parts)
