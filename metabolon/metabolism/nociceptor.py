"""nociceptor — unified error detection and pain signaling.

Fuses infection log, signal bus, and hook fire log into a unified
pain taxonomy. Classifies errors as transient/chronic and suggests actions.

Pain taxonomy:
  network   — timeout, connection refused (retryable)
  auth      — 401, 403 (manual fix)
  resource  — 429, disk full (pace/wait)
  logic     — repeated same error (investigate)
  chronic   — any type seen >CHRONIC_THRESHOLD times (escalate)
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

HKT = timezone(timedelta(hours=8))

INFECTION_LOG = Path.home() / ".local" / "share" / "vivesca" / "infections.jsonl"
SIGNAL_LOG = Path.home() / ".local" / "share" / "vivesca" / "signals.jsonl"
HOOK_LOG = Path.home() / "logs" / "hook-fire-log.jsonl"

CHRONIC_THRESHOLD = 3
PainType = Literal["network", "auth", "resource", "logic", "chronic", "unknown"]


@dataclass
class PainEvent:
    timestamp: str
    source: str  # infection, signal, hook
    site: str  # tool name or hook name
    error: str
    pain_type: PainType
    count: int = 1  # how many times this pattern seen
    recommended_action: str = "investigate"


def classify_error(error: str) -> PainType:
    """Classify an error string into a pain type."""
    e = error.lower()
    if any(w in e for w in ("timeout", "timed out", "connection refused", "connection reset", "dns")):
        return "network"
    if any(w in e for w in ("401", "403", "unauthorized", "forbidden", "auth", "token expired")):
        return "auth"
    if any(w in e for w in ("429", "rate limit", "quota", "disk full", "no space", "resource exhausted")):
        return "resource"
    if any(w in e for w in ("keyerror", "attributeerror", "typeerror", "valueerror", "assertion")):
        return "logic"
    return "unknown"


def recommended_action(pain_type: PainType, count: int) -> str:
    """Suggest an action based on pain type and frequency."""
    if count >= CHRONIC_THRESHOLD:
        return "escalate: file issue, disable if critical"
    actions = {
        "network": "retry with exponential backoff",
        "auth": "alert ops, pause related tasks",
        "resource": "throttle, wait for reset",
        "logic": "investigate root cause",
        "unknown": "investigate",
        "chronic": "escalate: file issue",
    }
    return actions.get(pain_type, "investigate")


def _read_jsonl(path: Path, max_age_hours: float = 24) -> list[dict]:
    """Read JSONL file, filtering to recent entries."""
    if not path.exists():
        return []
    cutoff = datetime.now(HKT) - timedelta(hours=max_age_hours)
    entries = []
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts_str = entry.get("ts", entry.get("timestamp", ""))
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=HKT)
                        if ts < cutoff:
                            continue
                    except (ValueError, TypeError):
                        pass
                entries.append(entry)
            except json.JSONDecodeError:
                continue
    except OSError:
        pass
    return entries


def scan(hours: float = 24) -> list[PainEvent]:
    """Scan all log sources for pain events in the last N hours."""
    events: list[PainEvent] = []
    pattern_counter: Counter[str] = Counter()

    # Infections
    for entry in _read_jsonl(INFECTION_LOG, hours):
        error = entry.get("error", "")
        fp = entry.get("fingerprint", "")
        pattern_counter[fp] += 1
        pain_type = classify_error(error)
        count = pattern_counter[fp]
        if count >= CHRONIC_THRESHOLD:
            pain_type = "chronic"
        events.append(PainEvent(
            timestamp=entry.get("ts", ""),
            source="infection",
            site=entry.get("tool", "unknown"),
            error=error[:200],
            pain_type=pain_type,
            count=count,
            recommended_action=recommended_action(pain_type, count),
        ))

    # Signals (errors only)
    for entry in _read_jsonl(SIGNAL_LOG, hours):
        outcome = entry.get("outcome", "")
        if outcome not in ("error", "correction"):
            continue
        error = entry.get("error", entry.get("message", ""))
        tool = entry.get("tool", entry.get("substrate", "unknown"))
        pain_type = classify_error(error)
        events.append(PainEvent(
            timestamp=entry.get("ts", entry.get("timestamp", "")),
            source="signal",
            site=tool,
            error=error[:200],
            pain_type=pain_type,
            recommended_action=recommended_action(pain_type, 1),
        ))

    # Hook denials
    for entry in _read_jsonl(HOOK_LOG, hours):
        rule = entry.get("rule", "")
        if not rule:
            continue
        events.append(PainEvent(
            timestamp=entry.get("ts", ""),
            source="hook",
            site=entry.get("hook", "unknown"),
            error=rule[:200],
            pain_type="logic",
            recommended_action="review hook rule",
        ))

    return events


def report(hours: float = 24) -> str:
    """Generate a human-readable pain report."""
    events = scan(hours)
    if not events:
        return f"No pain events in the last {hours:.0f}h."

    by_type: dict[str, list[PainEvent]] = {}
    for e in events:
        by_type.setdefault(e.pain_type, []).append(e)

    lines = [f"Pain report ({len(events)} events, last {hours:.0f}h):"]
    for ptype, pevents in sorted(by_type.items(), key=lambda x: -len(x[1])):
        lines.append(f"\n  {ptype.upper()} ({len(pevents)}):")
        seen = set()
        for e in pevents[:5]:
            key = f"{e.site}:{e.error[:50]}"
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"    [{e.source}] {e.site}: {e.error[:80]}")
            lines.append(f"      -> {e.recommended_action}")

    chronic = [e for e in events if e.pain_type == "chronic"]
    if chronic:
        lines.append(f"\n  CHRONIC INFECTIONS: {len(chronic)} (threshold: {CHRONIC_THRESHOLD})")
    return "\n".join(lines)
