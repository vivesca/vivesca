"""Proprioception — sensing the organism's structural state and gradients.

Biology: proprioception at the cell level = mechanosensing of shape,
tension, structural integrity. Cells sense GRADIENTS — is tension
increasing? Is shape changing? — not just static state.

Gradient sensing: each reading logs key metrics. On query, current
reading is compared to recent history to surface trends.
"""

import filecmp
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import yaml
from fastmcp.tools.function_tool import tool

if TYPE_CHECKING:
    from collections.abc import Callable

HKT = timezone(timedelta(hours=8))
_GRADIENT_LOG = str(Path.home() / "logs" / "proprioception.jsonl")

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
    "histone_store",  # memory database statistics
    "effectors",  # unified tool index — MCP and CLI tools
    "oscillators",  # LaunchAgent state — schedule, status, exit code, type
    "sense",  # goal readiness sensing
    "drill",  # record drill results
    "gradient",  # polarity gradient detection
    "skills",  # skill/enzyme directory scan
    "timing",  # tool call latency stats from rotating buffer
]


@tool()
def proprioception(
    target: Target,
    # drill params (only used when target="drill")
    goal: str = "",
    category: str = "",
    score: int = 0,
    drill_type: str = "flashcard",
    material: str = "",
    notes: str = "",
) -> str:
    """Sense organism internal state with gradient detection. Targets: genome, anatomy, circadian, vitals, glycogen, reflexes, consolidation, operons, sensorium, histone_store, effectors, oscillators, sense, drill, gradient, skills, timing."""
    if target == "drill":
        reading = _drill(goal, category, score, drill_type, material, notes)
    else:
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
    from metabolon.organelles.vasomotor_sensor import sense as _vasomotor_sense

    s = _vasomotor_sense()
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
    """Recent search queries. Reads rheotaxis signal log if available."""
    import json

    log_path = Path.home() / "germline" / "loci" / "signals" / "rheotaxis.jsonl"
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


def _histone_store() -> str:
    """Memory marks statistics (file-based, oghma retired)."""
    from pathlib import Path

    marks_dir = Path.home() / "epigenome" / "marks"
    files = list(marks_dir.glob("*.md"))
    if not files:
        return "histone_store: 0 mark files"

    total_size = sum(f.stat().st_size for f in files)
    return f"histone_store: {len(files)} marks, {total_size / 1024:.0f}KB at {marks_dir}"


def _effectors() -> str:
    from metabolon.resources.proteome import express_effector_index

    return express_effector_index()


def _oscillators() -> str:
    from metabolon.resources.oscillators import express_pacemaker_status

    return express_pacemaker_status()


# -- sense: proprioceptive readiness sensing (from receptor.py) ------------


def _sense() -> str:
    """Proprioceptive readiness check against active goals."""
    from metabolon.organelles.receptor_sense import (
        GOALS_DIR as _ORGANELLE_GOALS_DIR,
    )
    from metabolon.organelles.receptor_sense import (
        SIGNALS_DIR as _ORGANELLE_SIGNALS_DIR,
    )
    from metabolon.organelles.receptor_sense import (
        ProprioceptiveStore,
        restore_goals,
        synthesize_signal_summary,
    )

    _goals_dir = _ORGANELLE_GOALS_DIR
    _signals_dir = _ORGANELLE_SIGNALS_DIR

    goals = restore_goals(_goals_dir)
    if not goals:
        return "No goals configured. Add a YAML file to ~/.local/share/vivesca/goals/"

    parts = []
    for goal in goals:
        goal_slug = goal["name"].lower().replace(" ", "-")
        store = ProprioceptiveStore(_signals_dir / f"{goal_slug}-signals.jsonl")
        summary = synthesize_signal_summary(goal, store)

        phase_info = f"Phase: {summary['phase']}"
        if summary["days_to_next_phase"] is not None:
            phase_info += f" ({summary['days_to_next_phase']} days to next phase)"

        weakest_info = ""
        if summary["weakest"]:
            weak_details = []
            for cat in summary["weakest"]:
                cat_data = summary["categories"][cat]
                if cat_data["drill_count"] == 0:
                    weak_details.append(f"{cat}: never drilled")
                else:
                    weak_details.append(f"{cat}: avg {cat_data['avg_score']:.1f}/3")
            weakest_info = "Weakest: " + ", ".join(weak_details)

        parts.append(
            f"**{summary['goal']}** — {phase_info}. "
            f"Total drills: {summary['total_drills']}. "
            f"{weakest_info}"
        )

    return "\n\n".join(parts)


# -- drill: record proprioceptive drill results (from receptor.py) ---------


def _drill(
    goal: str,
    category: str,
    score: int,
    drill_type: str = "flashcard",
    material: str = "",
    notes: str = "",
) -> str:
    """Record a proprioceptive drill signal."""
    from metabolon.organelles.receptor_sense import (
        SIGNALS_DIR as _ORGANELLE_SIGNALS_DIR,
    )
    from metabolon.organelles.receptor_sense import (
        ProprioceptiveStore,
    )

    if score < 1 or score > 3:
        return f"Failed: score must be 1-3, got {score}"

    _signals_dir = _ORGANELLE_SIGNALS_DIR
    store = ProprioceptiveStore(_signals_dir / f"{goal}-signals.jsonl")
    store.append(
        goal=goal,
        material=material,
        category=category,
        score=score,
        drill_type=drill_type,
        notes=notes,
    )

    return f"Recorded {drill_type} drill: {category} = {score}/3 (goal: {goal})"


# -- gradient_detect: polarity gradient detection (from gradient.py) --------


def _gradient_detect() -> str:
    """Sense directional gradients across the organism's sensor arrays."""
    from metabolon.organelles.gradient_sense import build_gradient_report

    report = build_gradient_report(7)

    lines = [f"Polarity: {report.polarity_vector}"]
    if report.interpretation:
        lines.append(report.interpretation)
    for g in report.gradients:
        lines.append(
            f"  {g.domain}: strength={g.signal_strength:.2f}, "
            f"coverage={g.sensor_coverage}/3, topology={g.topology_bonus}"
        )
        if g.top_titles:
            for t in g.top_titles[:3]:
                lines.append(f"    title: {t}")
        if g.top_queries:
            for q in g.top_queries[:3]:
                lines.append(f"    query: {q}")

    return "\n".join(lines)


# -- skills: upstream receptor fork change detection (from integrin.py) -----


_SKILLS_REGISTRY_PATH = Path.home() / ".local" / "share" / "vivesca" / "skill-forks.yaml"

_SKILLS_DEFAULT_REGISTRY = {
    "superpowers": {
        "local": str(Path.home() / "germline" / "receptors" / "superpowers"),
        "cache_pattern": str(
            Path.home()
            / ".claude"
            / "plugins"
            / "cache"
            / "claude-plugins-official"
            / "superpowers"
        ),
    },
    "compound-engineering": {
        "local": str(Path.home() / "germline" / "receptors" / "compound-engineering"),
        "cache_pattern": str(
            Path.home()
            / ".claude"
            / "plugins"
            / "cache"
            / "every-marketplace"
            / "compound-engineering"
        ),
    },
}

_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _restore_fork_registry(path: Path = _SKILLS_REGISTRY_PATH) -> dict:
    """Load fork registry from YAML, or return defaults."""
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return _SKILLS_DEFAULT_REGISTRY


def _find_latest_cache_version(cache_dir: Path) -> Path | None:
    """Find the latest versioned directory in a cache path."""
    if not cache_dir.exists():
        return None

    versions: list[tuple[tuple[int, ...], Path]] = []
    for entry in cache_dir.iterdir():
        if entry.is_dir() and _VERSION_RE.match(entry.name):
            parts = tuple(int(x) for x in entry.name.split("."))
            skills_dir = entry / "skills"
            if skills_dir.exists():
                versions.append((parts, skills_dir))

    if not versions:
        return None
    versions.sort(key=lambda x: x[0])
    return versions[-1][1]


def _diff_fork(local_dir: Path, cache_dir: Path) -> dict:
    """Compare local fork against upstream cache."""
    modified: list[str] = []
    added_upstream: list[str] = []

    local_files: set[str] = set()
    cache_files: set[str] = set()

    for f in local_dir.rglob("*"):
        if f.is_file() and not any(p.name == ".git" for p in f.parents):
            local_files.add(str(f.relative_to(local_dir)))

    for f in cache_dir.rglob("*"):
        if f.is_file() and not any(p.name == ".git" for p in f.parents):
            cache_files.add(str(f.relative_to(cache_dir)))

    for rel in sorted(local_files & cache_files):
        if not filecmp.cmp(local_dir / rel, cache_dir / rel, shallow=False):
            modified.append(rel)

    added_upstream = sorted(cache_files - local_files)

    return {
        "modified": modified,
        "added_upstream": added_upstream,
        "total_changes": len(modified) + len(added_upstream),
    }


def _skills() -> str:
    """Proprioceptive check for upstream enzyme (skill) changes."""
    registry = _restore_fork_registry()
    parts: list[str] = []

    for suite_name, paths in registry.items():
        local_dir = Path(paths["local"])
        cache_base = Path(paths["cache_pattern"])

        if not local_dir.exists():
            continue

        cache_skills = _find_latest_cache_version(cache_base)
        if cache_skills is None:
            continue

        diff = _diff_fork(local_dir, cache_skills)
        if diff["total_changes"] == 0:
            continue

        lines = [f"**{suite_name}** — {diff['total_changes']} change(s):"]
        for f in diff["modified"]:
            lines.append(f"  modified: {f}")
        for f in diff["added_upstream"]:
            lines.append(f"  new upstream: {f}")
        parts.append("\n".join(lines))

    return "\n\n".join(parts) if parts else "No upstream skill changes detected."


def _timing() -> str:
    """Tool call latency statistics from the in-memory rotating buffer."""
    from statistics import mean, median

    from metabolon.membrane import timing_buffer

    entries = timing_buffer.snapshot()
    if not entries:
        return "No tool call timings recorded yet."

    total = len(entries)
    latencies = sorted(entry.latency_ms for entry in entries)

    avg_ms = mean(latencies)
    p50_ms = median(latencies)
    p95_idx = max(0, int(len(latencies) * 0.95) - 1)
    p95_ms = latencies[p95_idx]

    # Per-tool aggregation
    tool_latencies: dict[str, list[int]] = {}
    for entry in entries:
        tool_latencies.setdefault(entry.tool, []).append(entry.latency_ms)

    slowest_tools = sorted(
        ((name, max(times)) for name, times in tool_latencies.items()),
        key=lambda pair: pair[1],
        reverse=True,
    )[:5]

    lines = [
        f"Tool Timing Stats (last {total} calls):",
        f"  avg:   {avg_ms:.0f}ms",
        f"  p50:   {p50_ms:.0f}ms",
        f"  p95:   {p95_ms:.0f}ms",
        "",
        "Slowest tools (max latency):",
    ]
    for name, max_lat in slowest_tools:
        lines.append(f"  {name}: {max_lat}ms")

    # Outcome breakdown
    success_count = sum(1 for entry in entries if entry.outcome == "success")
    error_count = total - success_count
    lines.append("")
    lines.append(f"Outcomes: {success_count} success, {error_count} error")

    return "\n".join(lines)


_DISPATCH: dict[str, Callable] = {
    "genome": _genome,
    "anatomy": _anatomy,
    "circadian": _circadian,
    "vitals": _vitals,
    "glycogen": _glycogen,
    "reflexes": _reflexes,
    "consolidation": _consolidation,
    "operons": _operons,
    "sensorium": _sensorium,
    "histone_store": _histone_store,
    "effectors": _effectors,
    "oscillators": _oscillators,
    "sense": _sense,
    "gradient": _gradient_detect,
    "skills": _skills,
    "timing": _timing,
}
