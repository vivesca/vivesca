"""Proprioception — sensing the organism's structural state and gradients.

Biology: proprioception at the cell level = mechanosensing of shape,
tension, structural integrity. Cells sense GRADIENTS — is tension
increasing? Is shape changing? — not just static state.

Gradient sensing: each reading logs key metrics. On query, current
reading is compared to recent history to surface trends.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from fastmcp.tools import tool

HKT = timezone(timedelta(hours=8))
_GRADIENT_LOG = os.path.expanduser("~/logs/proprioception.jsonl")

Target = Literal[
    "genome",  # system rules and behavioral constraints
    "anatomy",  # organism structure — tools, substrates, operons
    "circadian",  # today's schedule in HKT
    "vitals",  # system health — nightly report, plugins, activity
    "glycogen",  # current token budget and usage (energy reserves)
    "reflexes",  # inventory of all Claude Code lifecycle hooks
    "consolidation",  # memory consolidation candidates (sense only)
    "operons",  # capability map — skills, expressed/dormant/crystallised
    "sensorium",  # recent search queries
    "hippocampus",  # memory database statistics
    "effectors",  # unified tool index — MCP and CLI tools
]


@tool()
def proprioception(target: Target) -> str:
    """Sense organism internal state with gradient detection. Targets: genome, anatomy, circadian, vitals, glycogen, reflexes, consolidation, operons, sensorium, hippocampus, effectors."""
    reading = _DISPATCH[target]()
    gradient = _log_and_gradient(target, reading)
    if gradient:
        reading = f"{reading}\n\n--- Gradient ---\n{gradient}"
    return reading


def _log_and_gradient(target: str, reading: str) -> str | None:
    """Log reading size and detect change gradients."""
    now = datetime.now(HKT).isoformat()
    size = len(reading)
    entry = {"ts": now, "target": target, "size": size}

    # Append to log
    os.makedirs(os.path.dirname(_GRADIENT_LOG), exist_ok=True)
    with open(_GRADIENT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Read recent history for this target
    try:
        with open(_GRADIENT_LOG) as f:
            history = [
                json.loads(line)
                for line in f
                if line.strip() and json.loads(line).get("target") == target
            ]
    except (FileNotFoundError, json.JSONDecodeError):
        return None

    if len(history) < 2:
        return None

    recent = history[-5:]  # last 5 readings
    sizes = [h["size"] for h in recent]
    delta = sizes[-1] - sizes[0]
    if abs(delta) < 50:  # noise threshold
        return None

    direction = "growing" if delta > 0 else "shrinking"
    pct = abs(delta) / max(sizes[0], 1) * 100
    return f"{target}: {direction} ({delta:+d} chars, {pct:.0f}% over last {len(recent)} readings)"


def _genome() -> str:
    from metabolon.resources.constitution import CANONICAL

    if not CANONICAL.exists():
        return "No constitution found."
    return CANONICAL.read_text()


def _anatomy() -> str:
    from metabolon.resources.anatomy import express_anatomy

    return express_anatomy()


def _circadian() -> str:
    """Circadian oscillator: rhythm phases, not just event lists."""

    from metabolon.organelles.circadian_clock import scheduled_events

    events = scheduled_events()

    # Circadian oscillator: overlay rhythm phases onto events
    hour = datetime.now(HKT).hour
    if hour < 7:
        phase = "dormancy (pre-dawn)"
    elif hour < 9:
        phase = "photoreception (morning activation)"
    elif hour < 12:
        phase = "deep-work (peak focus)"
    elif hour < 14:
        phase = "transition (midday)"
    elif hour < 17:
        phase = "deep-work (afternoon)"
    elif hour < 19:
        phase = "wind-down (evening)"
    else:
        phase = "dormancy preparation"

    return f"Phase: {phase}\n\n{events}"


def _vitals() -> str:
    from metabolon.resources.vitals import express_vitals

    return express_vitals()


def _glycogen() -> str:
    from metabolon.organelles.respiration_sensor import sense as _respiration_sense

    s = _respiration_sense()
    if "error" in s:
        return f"Token budget: unavailable ({s['error']})"
    status = s.get("status", "?")
    weekly = s.get("weekly_pct", 0)
    sonnet = s.get("sonnet_pct", 0)
    stale = f" [{s['stale_label']}]" if s.get("stale") and s.get("stale_label") else ""
    return f"Token budget: {status} — weekly {weekly:.0f}%, sonnet {sonnet:.0f}%{stale}"


def _reflexes() -> str:
    from metabolon.resources.reflexes import express_reflex_inventory

    return express_reflex_inventory()


def _consolidation() -> str:
    from metabolon.metabolism.substrates.memory import ConsolidationSubstrate

    substrate = ConsolidationSubstrate()
    sensed = substrate.sense(days=30)
    if not sensed:
        return "No memory files found."
    return substrate.report(sensed, [])


def _operons() -> str:
    from metabolon.resources.operons import express_operon_map
    from metabolon.resources.receptome import express_operon_index

    return express_operon_map() + "\n\n" + express_operon_index()


def _sensorium() -> str:
    """Recent search queries. Reads chemotaxis signal log if available."""
    import json

    log_path = Path.home() / "germline" / "loci" / "signals" / "chemotaxis.jsonl"
    if not log_path.exists():
        return "(no search log available)"
    lines = log_path.read_text().strip().splitlines()
    recent = lines[-10:] if len(lines) > 10 else lines
    entries = []
    for line in recent:
        try:
            row = json.loads(line)
            entries.append(f"{row.get('ts', '?')}  {row.get('query', '?')}")
        except json.JSONDecodeError:
            continue
    return "\n".join(entries) if entries else "(no search log available)"


def _hippocampus() -> str:
    """Memory database statistics via Python oghma package (migrated from Rust binary)."""
    from io import StringIO

    from oghma.config import load_config
    from oghma.storage import Storage

    config = load_config()
    storage = Storage(config=config)
    memories = storage.get_all_memories(status="active")

    if not memories:
        return "hippocampus: 0 active memories"

    category_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for memory in memories:
        category_counts[memory["category"]] = category_counts.get(memory["category"], 0) + 1
        source_counts[memory["source_tool"]] = source_counts.get(memory["source_tool"], 0) + 1

    buf = StringIO()
    buf.write(f"Total active memories: {len(memories)}\n")
    buf.write("\nBy category:\n")
    for cat, count in sorted(category_counts.items()):
        buf.write(f"  {cat}: {count}\n")
    buf.write("\nBy source tool:\n")
    for src, count in sorted(source_counts.items()):
        buf.write(f"  {src}: {count}\n")
    return buf.getvalue().strip()


def _effectors() -> str:
    from metabolon.resources.proteome import express_effector_index

    return express_effector_index()


_DISPATCH: dict[str, callable] = {
    "genome": _genome,
    "anatomy": _anatomy,
    "circadian": _circadian,
    "vitals": _vitals,
    "glycogen": _glycogen,
    "reflexes": _reflexes,
    "consolidation": _consolidation,
    "operons": _operons,
    "sensorium": _sensorium,
    "hippocampus": _hippocampus,
    "effectors": _effectors,
}
