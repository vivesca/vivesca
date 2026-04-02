from __future__ import annotations

"""metabolism_loop — self-improvement state machine via LangGraph.

Wires the metabolism subsystems (fitness, infection, repair, sweep) into an
autonomous loop that measures health, detects problems, attempts repairs, and
sweeps for broader issues before reporting.

State machine:
  measure_fitness → detect_infections → [if infected] → repair → verify_fix
                                        [if clean] → sweep_for_issues
      ↑                                                       |
      └──── [if more issues found] ←─────────────────────────┘
            [if healthy] → report → END

Iteration cap at 3 prevents infinite loops.

Usage:
    python -m metabolon.organelles.metabolism_loop
    from metabolon.organelles.metabolism_loop import run_metabolism
"""


import operator
import time
from typing import Annotated, TypedDict

from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from metabolon.metabolism.fitness import sense_affect
from metabolon.metabolism.infection import chronic_infections, infection_summary
from metabolon.metabolism.repair import ImmuneRequest, ImmuneResult, immune_response
from metabolon.metabolism.sweep import select
from metabolon.symbiont import transduce_safe

# ── constants ────────────────────────────────────────────────

MAX_ITERATIONS = 3
ANALYSIS_MODEL = "claude"

# Health score thresholds
HEALTHY_THRESHOLD = 0.7   # above this → healthy, skip repair
INFECTED_THRESHOLD = 0.3  # below this → definitely needs repair

# ── state ────────────────────────────────────────────────────


class MetabolismState(TypedDict):
    """Graph state for one metabolism cycle."""

    # Fitness measurement
    health_score: float

    # Detected issues (chronic infection patterns)
    infections: list[dict]

    # What repair attempted
    repairs_attempted: Annotated[list[dict], operator.add]

    # Broader hygiene findings from sweep
    sweep_results: list[dict]

    # Cycle counter (capped at MAX_ITERATIONS)
    iteration: int

    # Final human-readable summary
    report: str

    # Internal routing flags
    _has_infections: bool
    _sweep_found_issues: bool


# ── node functions ───────────────────────────────────────────


def measure_fitness(state: MetabolismState) -> dict:
    """Read the signal log and compute aggregate health score.

    Uses sense_affect() from fitness.py to compute per-enzyme emotion, then
    derives a scalar health_score as the mean valence across all enzymes that
    have sufficient data. Falls back to LLM analysis if no signals exist.
    """
    # recall_all() may raise ValidationError on schema-mismatched legacy records.
    # Parse line-by-line to skip corrupt entries rather than failing the whole loop.
    from metabolon.metabolism.signals import DEFAULT_LOG, Stimulus
    stimuli = []
    if DEFAULT_LOG.exists():
        for line in DEFAULT_LOG.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                stimuli.append(Stimulus.model_validate_json(line))
            except Exception:
                continue

    health_score = 0.5  # neutral default

    if stimuli:
        emotions = sense_affect(stimuli)
        valences = [e.valence for e in emotions.values() if e.valence is not None]
        if valences:
            health_score = sum(valences) / len(valences)
            # Normalise: valence is unbounded above, clamp to [0, 1]
            health_score = min(1.0, max(0.0, health_score))
        else:
            # All enzymes have insufficient data — ask LLM to assess
            stimulus_summary = f"{len(stimuli)} signals recorded, all insufficient data"
            _, result = transduce_safe(
                ANALYSIS_MODEL,
                f"Metabolism signal log has {stimulus_summary}. "
                "Estimate system health on a scale 0.0-1.0. Reply with only a float.",
                timeout=30,
            )
            try:
                health_score = float(result.strip())
                health_score = min(1.0, max(0.0, health_score))
            except (ValueError, TypeError):
                health_score = 0.5
    else:
        # No signals at all — fresh system or logging gap
        health_score = 0.5

    return {
        "health_score": health_score,
        "iteration": state.get("iteration", 0) + 1,
    }


def detect_infections(state: MetabolismState) -> dict:
    """Read infection log and surface chronic patterns.

    Uses chronic_infections() from infection.py to find tool+error fingerprints
    that have crossed the chronic threshold. Each pattern becomes a dict in
    state["infections"] for downstream repair logic.
    """
    patterns = chronic_infections()

    infections = [
        {
            "tool": p["tool"],
            "fingerprint": p["fingerprint"],
            "count": p["count"],
            "last_error": p["last_error"],
            "last_seen": p["last_seen"],
            "healed_count": p["healed_count"],
        }
        for p in patterns
    ]

    has_infections = len(infections) > 0

    return {
        "infections": infections,
        "_has_infections": has_infections,
    }


def repair(state: MetabolismState) -> dict:
    """Attempt immune response for each chronic infection.

    Wraps immune_response() (async in repair.py) by running it synchronously
    via asyncio.run(). For each chronic infection, builds an ImmuneRequest with
    the tool name and last error, then records the outcome.
    """
    import asyncio

    infections = state.get("infections", [])
    repairs_attempted = []

    for infection in infections:
        tool = infection["tool"]
        last_error = infection["last_error"]

        # Fetch current description via LLM delegation — repair.py uses
        # immune_response which needs current_description. We ask the LLM.
        _, current_desc = transduce_safe(
            ANALYSIS_MODEL,
            f"Describe in 1-2 sentences what the MCP tool '{tool}' does. "
            "Be concise and accurate. Reply with only the description.",
            timeout=30,
        )

        request = ImmuneRequest(
            tool=tool,
            current_description=current_desc.strip()[:500],
            failure_reason=last_error[:300],
            context=f"Chronic infection: {infection['count']} occurrences, "
                    f"{infection['healed_count']} previously healed",
        )

        try:
            result: ImmuneResult = asyncio.run(immune_response(request))
            repair_record = {
                "tool": tool,
                "fingerprint": infection["fingerprint"],
                "accepted": result.accepted,
                "attempts": result.attempts,
                "candidate": result.candidate,
                "gate_passed": result.gate_result.passed,
                "gate_reason": result.gate_result.reason,
            }
        except Exception as e:
            repair_record = {
                "tool": tool,
                "fingerprint": infection["fingerprint"],
                "accepted": False,
                "attempts": 0,
                "candidate": None,
                "gate_passed": False,
                "gate_reason": f"repair exception: {e}",
            }

        repairs_attempted.append(repair_record)

    return {"repairs_attempted": repairs_attempted}


def verify_fix(state: MetabolismState) -> dict:
    """Check if repairs resolved the infections.

    Compares accepted repairs against the infection list. Updates health_score
    upward for each accepted repair. Sets _has_infections based on remaining
    unresolved infections.
    """
    infections = state.get("infections", [])
    repairs = state.get("repairs_attempted", [])

    # Build set of fingerprints that were accepted
    healed_fingerprints = {
        r["fingerprint"] for r in repairs if r.get("accepted", False)
    }

    # Remaining unresolved infections
    remaining = [
        inf for inf in infections
        if inf["fingerprint"] not in healed_fingerprints
    ]

    # Bump health score for each successful repair
    accepted_count = len(healed_fingerprints)
    current_score = state.get("health_score", 0.5)
    if accepted_count > 0 and infections:
        heal_ratio = accepted_count / len(infections)
        new_score = current_score + (1.0 - current_score) * heal_ratio * 0.3
        new_score = min(1.0, new_score)
    else:
        new_score = current_score

    return {
        "health_score": new_score,
        "infections": remaining,
        "_has_infections": len(remaining) > 0,
        "_sweep_found_issues": False,
    }


def sweep_for_issues(state: MetabolismState) -> dict:
    """Run differential evolution sweep to identify low-fitness tools.

    Uses select() from sweep.py to find underperforming tools, then delegates
    analysis of each candidate to the LLM via transduce_safe(). Results are
    stored as sweep_results for the report.
    """
    from metabolon.metabolism.signals import DEFAULT_LOG, Stimulus
    stimuli = []
    if DEFAULT_LOG.exists():
        for line in DEFAULT_LOG.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                stimuli.append(Stimulus.model_validate_json(line))
            except Exception:
                continue

    sweep_results = []

    if stimuli:
        emotions = sense_affect(stimuli)
        candidates = select(emotions)

        for tool_name in candidates[:5]:  # cap at 5 to stay bounded
            emotion = emotions.get(tool_name)
            valence_str = (
                f"{emotion.valence:.3f}" if emotion and emotion.valence is not None
                else "insufficient data"
            )
            activations = emotion.activations if emotion else 0
            success_rate = emotion.success_rate if emotion else 0.0

            _, analysis = transduce_safe(
                ANALYSIS_MODEL,
                f"Tool '{tool_name}' has low fitness: valence={valence_str}, "
                f"activations={activations}, success_rate={success_rate:.2f}. "
                "In 1 sentence, suggest the most likely reason and fix.",
                timeout=30,
            )

            sweep_results.append({
                "tool": tool_name,
                "valence": valence_str,
                "activations": activations,
                "success_rate": success_rate,
                "analysis": analysis.strip()[:300],
            })
    else:
        # No signals — use LLM to do a meta-sweep of the infection log
        summary = infection_summary()
        if summary:
            _, analysis = transduce_safe(
                ANALYSIS_MODEL,
                f"Metabolism sweep with no signal data. Infection summary:\n{summary}\n\n"
                "Identify the top 2 hygiene issues in 2 bullet points.",
                timeout=30,
            )
            sweep_results.append({
                "tool": "system",
                "valence": "unknown",
                "activations": 0,
                "success_rate": 0.0,
                "analysis": analysis.strip()[:300],
            })

    found_issues = len(sweep_results) > 0

    return {
        "sweep_results": sweep_results,
        "_sweep_found_issues": found_issues,
    }


def report(state: MetabolismState) -> dict:
    """Compile a final human-readable metabolism report.

    Summarises health score, infections found, repairs attempted, sweep
    findings, and iteration count into a concise markdown string.
    """
    health_score = state.get("health_score", 0.5)
    infections = state.get("infections", [])
    repairs = state.get("repairs_attempted", [])
    sweep = state.get("sweep_results", [])
    iteration = state.get("iteration", 1)

    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    lines = [
        f"# Metabolism Report — {ts}",
        "",
        "## Health",
        f"- Score: {health_score:.2f} / 1.00",
        f"- Cycles: {iteration}",
        "",
    ]

    if infections:
        lines += [f"## Remaining Infections ({len(infections)})"]
        for inf in infections:
            lines.append(
                f"- **{inf['tool']}** [{inf['fingerprint']}] "
                f"x{inf['count']} — {inf['last_error'][:80]}"
            )
        lines.append("")

    if repairs:
        accepted = [r for r in repairs if r.get("accepted")]
        rejected = [r for r in repairs if not r.get("accepted")]
        lines += [f"## Repairs ({len(accepted)} accepted, {len(rejected)} rejected)"]
        for r in accepted:
            lines.append(f"- HEALED: **{r['tool']}** in {r['attempts']} attempt(s)")
        for r in rejected:
            lines.append(
                f"- UNRESOLVED: **{r['tool']}** — {r.get('gate_reason', 'unknown')}"
            )
        lines.append("")

    if sweep:
        lines += [f"## Sweep Findings ({len(sweep)} candidates)"]
        for s in sweep:
            lines.append(
                f"- **{s['tool']}** (valence={s['valence']}, "
                f"success={s.get('success_rate', 0):.0%}): {s['analysis']}"
            )
        lines.append("")

    if not infections and not sweep:
        lines += ["## Verdict", "System healthy. No chronic infections or low-fitness tools detected.", ""]

    report_text = "\n".join(lines)
    return {"report": report_text}


# ── routing functions ─────────────────────────────────────────


def route_after_detection(state: MetabolismState) -> str:
    """After detect_infections: route to repair if infected, sweep if clean."""
    if state.get("_has_infections", False):
        return "repair"
    return "sweep_for_issues"


def route_after_verify(state: MetabolismState) -> str:
    """After verify_fix: loop back if still infected and under cap, else sweep."""
    iteration = state.get("iteration", 1)
    if state.get("_has_infections", False) and iteration < MAX_ITERATIONS:
        return "measure_fitness"
    return "sweep_for_issues"


def route_after_sweep(state: MetabolismState) -> str:
    """After sweep: loop back if issues found and under cap, else report."""
    iteration = state.get("iteration", 1)
    if state.get("_sweep_found_issues", False) and iteration < MAX_ITERATIONS:
        return "measure_fitness"
    return "report"


# ── graph assembly ────────────────────────────────────────────


def build_graph() -> StateGraph:
    """Assemble the metabolism loop graph."""
    graph = StateGraph(MetabolismState)

    graph.add_node("measure_fitness", measure_fitness)
    graph.add_node("detect_infections", detect_infections)
    graph.add_node("repair", repair)
    graph.add_node("verify_fix", verify_fix)
    graph.add_node("sweep_for_issues", sweep_for_issues)
    graph.add_node("report", report)

    graph.set_entry_point("measure_fitness")
    graph.add_edge("measure_fitness", "detect_infections")

    graph.add_conditional_edges(
        "detect_infections",
        route_after_detection,
        {
            "repair": "repair",
            "sweep_for_issues": "sweep_for_issues",
        },
    )

    graph.add_edge("repair", "verify_fix")

    graph.add_conditional_edges(
        "verify_fix",
        route_after_verify,
        {
            "measure_fitness": "measure_fitness",
            "sweep_for_issues": "sweep_for_issues",
        },
    )

    graph.add_conditional_edges(
        "sweep_for_issues",
        route_after_sweep,
        {
            "measure_fitness": "measure_fitness",
            "report": "report",
        },
    )

    graph.add_edge("report", END)

    return graph


# ── public API ────────────────────────────────────────────────


def _open_checkpointer(persistent: bool = True):
    """Open a checkpointer — SQLite for persistence, InMemory for tests."""
    if not persistent:
        return InMemorySaver()
    import sqlite3
    from pathlib import Path

    db_path = Path.home() / ".local" / "share" / "vivesca" / "checkpoints.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSaver(sqlite3.connect(str(db_path), check_same_thread=False))


def run_metabolism(
    thread_id: str = "default",
    persistent: bool = True,
    interactive: bool = False,
) -> dict:
    """Run one metabolism self-improvement cycle.

    Returns the final state dict including the report string.

    Args:
        thread_id: LangGraph checkpoint thread ID. Default "default".
        persistent: If True, use SQLite checkpointer (survives crashes).
        interactive: If True, interrupt before repair for operator review.
    """
    checkpointer = _open_checkpointer(persistent)
    graph = build_graph()

    interrupt = ["repair"] if interactive else None
    app = graph.compile(checkpointer=checkpointer, interrupt_before=interrupt)

    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}  # type: ignore[typed-dict]  # pyright: ignore[reportArgumentType]

    initial_state: MetabolismState = {
        "health_score": 0.5,
        "infections": [],
        "repairs_attempted": [],
        "sweep_results": [],
        "iteration": 0,
        "report": "",
        "_has_infections": False,
        "_sweep_found_issues": False,
    }

    final_state = app.invoke(initial_state, config)
    return final_state


# ── CLI ───────────────────────────────────────────────────────


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="metabolism_loop — self-improvement state machine"
    )
    parser.add_argument(
        "--thread",
        default="default",
        help="LangGraph checkpoint thread ID (default: default)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Measure fitness only, no repair or sweep",
    )
    args = parser.parse_args()

    if args.dry_run:
        from metabolon.metabolism.signals import DEFAULT_LOG, Stimulus
        stimuli = []
        if DEFAULT_LOG.exists():
            for _line in DEFAULT_LOG.read_text().splitlines():
                _line = _line.strip()
                if not _line:
                    continue
                try:
                    stimuli.append(Stimulus.model_validate_json(_line))
                except Exception:
                    continue
        print(f"Signal log: {len(stimuli)} valid stimuli")
        summary = infection_summary()
        print(f"Infection summary: {summary or 'none'}")
        chronics = chronic_infections()
        print(f"Chronic infections: {len(chronics)}")
        return

    final = run_metabolism(thread_id=args.thread)
    print(final.get("report", "(no report generated)"))
    print(f"\nHealth score: {final.get('health_score', 0.5):.2f}")
    print(f"Iterations: {final.get('iteration', 0)}")


if __name__ == "__main__":
    main()
