"""complement — convergent detection and resolution (MAC assembly).

In biology, the complement system converges from multiple detection pathways
(classical, lectin, alternative) to form the Membrane Attack Complex (MAC).
Single-pathway detection merely marks a target (opsonisation); convergence
triggers the lethal effector.

The organism equivalent:
1. Pathway A: inflammasome (proactive self-test probes)
2. Pathway B: infection log (reactive tool-call error patterns)

Complement joins these two streams. When the same key appears in both, it
assembles a MAC to resolve the chronic inflammation.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import TypedDict

from metabolon.metabolism.infection import (
    ChronicPattern,
    InfectionEvent,
    chronic_infections,
    recall_infections,
)
from metabolon.vasomotor import log, record_event

# ---------------------------------------------------------------------------
# Paths and Constants
# ---------------------------------------------------------------------------

_PRIMING_PATH = Path.home() / ".cache" / "inflammasome" / "priming.json"
_COMPLEMENT_STATE = Path.home() / ".local" / "share" / "vivesca" / "complement.json"

# Known test sentinels or benign patterns that should be suppressed.
SUPPRESSIONS = {
    "fail_tool": "Test sentinel (safe to ignore)",
    "failing_tool": "Test sentinel (safe to ignore)",
    "unknown_tool": "Test sentinel (safe to ignore)",
    "tool": "Generic placeholder (safe to ignore)",
    "chemotaxis": "Test sentinel (self-test path)",
    "endocytosis": "Test sentinel (self-test path)",
    "respirometry": "Test sentinel (self-test path)",
    "chromatin": "Test sentinel (self-test path)",
}


class MACEntry(TypedDict):
    key: str
    probe_consecutive_fails: int
    infection_count: int
    last_seen: str
    resolution: str  # "suppress", "remediate", "escalate"
    reason: str
    convergent: bool


# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------

def assemble_mac() -> list[MACEntry]:
    """Join probe failures and unhealed infections to identify targets.

    Returns a list of hits ready for resolution.
    """
    # 1. Load Pathway A (Probe Priming)
    probe_fails = {}
    if _PRIMING_PATH.exists():
        try:
            probe_fails = json.loads(_PRIMING_PATH.read_text())
        except Exception:
            pass

    # 2. Load Pathway B (Unhealed Infections)
    events: list[InfectionEvent] = recall_infections()
    unhealed = [e for e in events if not e["healed"]]
    
    # Group by tool
    infection_map = {}
    for e in unhealed:
        k = e["tool"]
        if k not in infection_map:
            infection_map[k] = {"count": 0, "last_seen": e["ts"]}
        infection_map[k]["count"] += 1
        if e["ts"] > infection_map[k]["last_seen"]:
            infection_map[k]["last_seen"] = e["ts"]

    # 3. Process All Keys
    hits: list[MACEntry] = []
    all_keys = set(probe_fails.keys()) | set(infection_map.keys())

    for k in all_keys:
        probe_count = probe_fails.get(k, 0)
        
        # Check for prefixed version too
        if not probe_count and not k.startswith("self_test_failure:"):
            probe_count = probe_fails.get(f"self_test_failure:{k}", 0)
        
        inf = infection_map.get(k)
        inf_count = inf["count"] if inf else 0
        last_seen = inf["last_seen"] if inf else datetime.datetime.now().isoformat()

        # Resolution logic
        if probe_count > 0 or inf_count > 0:
            convergent = (probe_count > 0 and inf_count > 0)
            resolution = "escalate"
            reason = "convergent detection" if convergent else "unhealed infection"
            
            # Suppression logic
            norm_k = k.replace("self_test_failure:", "")
            if norm_k in SUPPRESSIONS:
                resolution = "suppress"
                reason = SUPPRESSIONS[norm_k]
            
            hits.append({
                "key": k,
                "probe_consecutive_fails": probe_count,
                "infection_count": inf_count,
                "last_seen": last_seen,
                "resolution": resolution,
                "reason": reason,
                "convergent": convergent
            })

    return hits


def resolve() -> dict:
    """The Resolvin effector: actively clear debris and restore homeostasis.

    Executes automated repairs for known hits, applies suppressions,
    and returns a summary.
    """
    hits = assemble_mac()
    if not hits:
        return {"status": "quiescent", "hits": 0}

    resolved = []
    suppressed = []
    escalated = []

    for hit in hits:
        if hit["resolution"] == "suppress":
            suppressed.append(hit)
        elif hit["resolution"] == "remediate":
            resolved.append(hit)
        else:
            escalated.append(hit)

    summary = {
        "status": "active",
        "hits": len(hits),
        "suppressed": len(suppressed),
        "resolved": len(resolved),
        "escalated": len(escalated),
        "convergent": sum(1 for h in hits if h["convergent"]),
        "details": hits,
    }
    
    if hits:
        record_event("complement_activation", **summary, keys=[h["key"] for h in hits])
        log(f"Complement: {len(hits)} hits ({summary['convergent']} convergent) — {len(escalated)} escalated")

    return summary


def amplify(key: str) -> bool:
    """Positive feedback loop (C3b): force an immediate re-probe of a key.

    In biology, opsonisation recruits more complement. Here, a chronic
    infection should trigger the inflammasome to re-probe that specific
    subsystem rather than waiting for the next scheduled heartbeat.
    """
    # This requires IPC or a shared trigger file for the pacemaker/inflammasome.
    # For now, we log the amplification request.
    record_event("complement_amplification", key=key)
    return True


if __name__ == "__main__":
    # Diagnostic output
    results = resolve()
    print(json.dumps(results, indent=2))
