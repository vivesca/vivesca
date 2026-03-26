"""angiogenesis — detect underserved subsystem connections and propose new integrations.

Angiogenesis = growing new blood vessels to supply hypoxic tissue.
Here: detect subsystem pairs that fail in sequence (hypoxia signal) and propose
the integration (vessel) that would connect them.

Detection is pure Python — no LLM. Proposals are logged for crystallization.
Registry lives at ~/.cache/angiogenesis/vessels.json.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

INFECTION_LOG = Path.home() / ".local" / "share" / "vivesca" / "infections.jsonl"
VESSEL_REGISTRY = Path.home() / ".cache" / "angiogenesis" / "vessels.json"
PROPOSAL_LOG = Path.home() / ".cache" / "angiogenesis" / "proposals.jsonl"

# Consecutive-failure window: events within this many seconds count as a sequence.
_SEQUENCE_WINDOW_S = 300
# Minimum co-failure count to flag a pair as hypoxic.
_HYPOXIA_THRESHOLD = 3


def detect_hypoxia() -> list[dict]:
    """Read infection log and identify subsystem pairs that fail in sequence.

    A pair (A, B) is hypoxic when B fails within _SEQUENCE_WINDOW_S seconds
    of A failing, at least _HYPOXIA_THRESHOLD times — indicating they need
    a shared connection.

    Returns list of {source, target, co_failures, last_seen}.
    """
    if not INFECTION_LOG.exists():
        return []

    events: list[dict] = []
    for line in INFECTION_LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
            if not ev.get("healed", True):  # only count unhealed events
                events.append(ev)
        except json.JSONDecodeError:
            continue

    # Sort by timestamp
    events.sort(key=lambda e: e.get("ts", ""))

    pair_counts: Counter = Counter()
    pair_last_seen: dict[tuple, str] = {}

    for i, ev_a in enumerate(events):
        ts_a_str = ev_a.get("ts", "")
        try:
            ts_a = datetime.fromisoformat(ts_a_str).timestamp()
        except ValueError:
            continue
        tool_a = ev_a.get("tool", "")

        for ev_b in events[i + 1 :]:
            ts_b_str = ev_b.get("ts", "")
            try:
                ts_b = datetime.fromisoformat(ts_b_str).timestamp()
            except ValueError:
                continue
            if ts_b - ts_a > _SEQUENCE_WINDOW_S:
                break
            tool_b = ev_b.get("tool", "")
            if tool_b == tool_a:
                continue
            pair = (tool_a, tool_b)
            pair_counts[pair] += 1
            pair_last_seen[pair] = ts_b_str

    return [
        {
            "source": src,
            "target": tgt,
            "co_failures": count,
            "last_seen": pair_last_seen[(src, tgt)],
        }
        for (src, tgt), count in pair_counts.items()
        if count >= _HYPOXIA_THRESHOLD
    ]


def propose_vessel(source: str, target: str) -> dict:
    """Propose an integration between two subsystems.

    Returns a proposal dict describing the connection and logs it
    to the proposal log for crystallization via methylation.
    """
    proposal = {
        "ts": datetime.now(UTC).isoformat(),
        "source": source,
        "target": target,
        "vessel_type": "pipeline",
        "description": (
            f"When {source} fails, check {target} health before retrying. "
            f"Shared failure pattern suggests a missing dependency or ordering constraint. "
            f"Candidate integration: add {source} as upstream probe gate for {target}, "
            f"or extract their shared dependency into a named subsystem."
        ),
        "status": "proposed",
    }
    PROPOSAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROPOSAL_LOG.open("a") as f:
        f.write(json.dumps(proposal) + "\n")
    return proposal


def vessel_registry() -> list[dict]:
    """List existing integrations from the vessel registry.

    Registry is a simple JSON array at ~/.cache/angiogenesis/vessels.json.
    Returns empty list if the registry does not exist yet.
    """
    if not VESSEL_REGISTRY.exists():
        return []
    try:
        return json.loads(VESSEL_REGISTRY.read_text())
    except (json.JSONDecodeError, OSError):
        return []
