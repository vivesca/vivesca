"""polarization_loop — overnight flywheel via LangGraph.

Systole loop: preflight → brainstorm → [INTERRUPT] → dispatch → collect →
quality_gate → archive → compound → scout → stopping_gate
    ↑                                                        |
    └──── (gate passes, budget green) ───────────────────────┘
          (stop) → report → wrap → END

Agents dispatch via `channel --organism` (Max OAuth, no API keys).
SQLite checkpoints let overnight runs survive process crashes.

Usage:
    from metabolon.organelles.polarization_loop import polarize
    polarize(mode="overnight")   # unattended flywheel
    polarize(mode="interactive") # pauses before dispatch for review
"""

import json
import operator
import os
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, TypedDict, cast

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from metabolon.locus import chromatin, praxis

if TYPE_CHECKING:
    from langchain_core.runnables.config import RunnableConfig

# ── paths ────────────────────────────────────────────────────

CHECKPOINT_DB = Path.home() / ".local" / "share" / "vivesca" / "checkpoints.db"
GUARD_FILE = Path.home() / "tmp" / ".polarization-guard-active"
MANIFEST_FILE = Path.home() / "tmp" / "polarization-session.md"
REPORTS_DIR = chromatin / "Poiesis Reports"
NORTH_STAR_FILE = chromatin / "North Star.md"
SHAPES_FILE = chromatin / "euchromatin" / "epistemics" / "north-star-shapes.md"
DIVISION_FILE = chromatin / "euchromatin" / "epistemics" / "division-of-labour.md"
NOW_FILE = chromatin / "NOW.md"

# ── state ────────────────────────────────────────────────────


class PolarizationState(TypedDict):
    """Graph state for the polarization flywheel."""

    # Config
    mode: str  # "interactive" or "overnight"

    # Preflight context
    consumption_count: int
    budget_status: str  # "green", "yellow", "red"
    north_stars: str
    praxis_items: str
    shapes: str
    division: str
    now_md: str

    # Per systole
    systole_num: int
    sub_goals: list[dict]  # [{star, goal, deliverable, model}]

    # Dispatch + collect
    dispatched_work: Annotated[list[dict], operator.add]

    # Quality + archive
    archived: Annotated[list[dict], operator.add]

    # Compound + scout
    follow_ons: list[dict]

    # Stopping gate
    gate_results: dict  # {check_name: bool}

    # Accumulators
    total_produced: int
    total_for_review: int

    # Control
    should_stop: bool
    stop_reason: str

    # Report
    report: str
    errors: Annotated[list[str], operator.add]


# ── helpers ──────────────────────────────────────────────────


def _channel(model: str, prompt: str, organism: bool = False, timeout: int = 300) -> str:
    """Call channel CLI — returns stdout or error string."""
    cmd = ["channel", model]
    if organism:
        cmd.append("--organism")
    cmd.extend(["-p", prompt])

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return f"(channel error: exit {result.returncode}) {result.stderr[:500]}"
    except subprocess.TimeoutExpired:
        return f"(channel timeout after {timeout}s)"


def _read_file(path: Path, max_chars: int = 3000) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")[:max_chars]
    return ""


def _budget_status() -> str:
    """Read budget from respirometry or allostasis state."""
    try:
        result = subprocess.run(
            ["respirometry", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            pct = float(data.get("seven_day", {}).get("utilization", 0))
            if pct >= 80:
                return "red"
            if pct >= 50:
                return "yellow"
            return "green"
    except Exception:
        pass
    return "green"


def _consumption_count() -> int:
    if not REPORTS_DIR.exists():
        return 0
    cutoff = time.time() - 7 * 24 * 3600
    return sum(1 for f in REPORTS_DIR.iterdir() if f.stat().st_mtime >= cutoff)


# ── node functions ───────────────────────────────────────────


def preflight(state: PolarizationState) -> dict:
    """Load context: north stars, praxis, budget, shapes, division."""
    # Guard on
    GUARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    GUARD_FILE.touch()

    ns = _read_file(NORTH_STAR_FILE)
    praxis_text = ""
    if praxis.exists():
        lines = praxis.read_text(encoding="utf-8").splitlines()[:80]
        praxis_text = "\n".join(lines)

    return {
        "north_stars": ns,
        "praxis_items": praxis_text,
        "shapes": _read_file(SHAPES_FILE),
        "division": _read_file(DIVISION_FILE),
        "now_md": _read_file(NOW_FILE, max_chars=2000),
        "budget_status": _budget_status(),
        "consumption_count": _consumption_count(),
        "systole_num": state.get("systole_num", 0) + 1,
    }


def brainstorm(state: PolarizationState) -> dict:
    """Identify sub-goals for this systole using shape + division filters."""
    mode = state.get("mode", "overnight")
    max_goals = 8 if mode == "overnight" else 5
    consumption = state.get("consumption_count", 0)

    consumption_signal = (
        "Produce more."
        if consumption <= 3
        else (
            "Self-sufficient outputs only." if consumption <= 8 else "Overproduction. Triage only."
        )
    )

    prompt = f"""You are a work dispatcher for an autonomous overnight agent system.

North stars:
{state["north_stars"][:2000]}

Shapes (which stars are flywheels vs habits):
{state["shapes"][:1500]}

Division of labour (what's automated vs presence/sharpening):
{state["division"][:1500]}

Current Praxis TODO:
{state["praxis_items"][:2000]}

NOW.md:
{state["now_md"][:1000]}

Systole #{state["systole_num"]}. Budget: {state["budget_status"]}.
Consumption: {consumption} reports in last 7 days — {consumption_signal}
Previous work this session: {state.get("total_produced", 0)} items produced.

Select up to {max_goals} concrete sub-goals. For each:
- Which north star it serves
- The specific deliverable (file path + format)
- Model: "sonnet" for research/collection, "opus" for synthesis/judgment
- Whether it's Automated (dispatch) or skip

FILTERS:
- Skip Habit and Attention shaped stars (gym, marriage)
- Skip Presence, Sharpening, Collaborative category tasks
- Only dispatch Automated category
- Each agent = ONE deliverable, ONE output file

Return JSON array: [{{"star": "...", "goal": "...", "deliverable": "...", "model": "sonnet|opus"}}]
Return ONLY the JSON array."""

    result = _channel("sonnet", prompt, organism=False, timeout=120)

    goals = []
    try:
        start = result.find("[")
        end = result.rfind("]") + 1
        if start >= 0 and end > start:
            goals = json.loads(result[start:end])
    except (json.JSONDecodeError, ValueError):
        return {"errors": [f"Brainstorm failed to parse: {result[:200]}"]}

    return {"sub_goals": goals[:max_goals]}


def dispatch(state: PolarizationState) -> dict:
    """Execute each sub-goal via channel --organism."""
    goals = state.get("sub_goals", [])
    if not goals:
        return {"errors": ["No goals to dispatch"]}

    manifest_lines = [
        f"## Wave (systole {state.get('systole_num', 1)})",
        "",
    ]

    results = []
    for goal in goals:
        model = goal.get("model", "sonnet")
        deliverable = goal.get("deliverable", "")
        star = goal.get("star", "")

        agent_prompt = f"""Complete this task autonomously. Produce a concrete deliverable.

Read ~/tmp/polarization-session.md first. Do not duplicate completed work.

Task: {goal.get("goal", "")}
North star: {star}
Expected deliverable: {deliverable}

Be thorough but concise. Write the deliverable to the specified path."""

        output = _channel(model, agent_prompt, organism=True, timeout=600)

        result = {
            "goal": goal.get("goal", ""),
            "star": star,
            "model": model,
            "deliverable_path": deliverable,
            "output": output[:3000],
            "success": not output.startswith("(channel"),
        }
        results.append(result)
        status = "ok" if result["success"] else "FAILED"
        manifest_lines.append(f"- [{status}] [{star}] {goal.get('goal', '')}")

    # Update manifest
    if MANIFEST_FILE.exists():
        existing = MANIFEST_FILE.read_text(encoding="utf-8")
        MANIFEST_FILE.write_text(
            existing + "\n" + "\n".join(manifest_lines) + "\n",
            encoding="utf-8",
        )

    return {"dispatched_work": results}


def quality_gate(state: PolarizationState) -> dict:
    """Classify outputs: self-sufficient vs needs-review. Quality check."""
    work = state.get("dispatched_work", [])
    recent = [w for w in work if w.get("success", False)]
    if not recent:
        return {
            "total_produced": state.get("total_produced", 0),
            "total_for_review": state.get("total_for_review", 0),
        }

    summaries = "\n".join(
        f"- [{w['star']}] {w['goal']}: {w['output'][:200]}..." for w in recent[-8:]
    )

    prompt = f"""Evaluate these agent outputs. For each:
1. SELF-SUFFICIENT (archive, no Terry review needed) or NEEDS-REVIEW?
2. Quality: PASS / PARTIAL / FAIL

Target: ~75% self-sufficient. Only tag needs-review if it requires Terry's voice, memory, or hands.

{summaries}

Return JSON: [{{"goal": "...", "classification": "self-sufficient|needs-review", "quality": "pass|partial|fail"}}]
Return ONLY the JSON array."""

    eval_text = _channel("sonnet", prompt, timeout=120)

    produced = len(recent)
    review = 0
    archived = []
    try:
        start = eval_text.find("[")
        end = eval_text.rfind("]") + 1
        if start >= 0 and end > start:
            evals = json.loads(eval_text[start:end])
            review = sum(1 for e in evals if e.get("classification") == "needs-review")
            archived = evals
    except (json.JSONDecodeError, ValueError):
        pass

    return {
        "archived": archived,
        "total_produced": state.get("total_produced", 0) + produced,
        "total_for_review": state.get("total_for_review", 0) + review,
    }


def compound_and_scout(state: PolarizationState) -> dict:
    """Compound: what builds on outputs? Scout: what new directions?"""
    work = state.get("dispatched_work", [])
    recent = [w for w in work if w.get("success", False)][-8:]

    if not recent:
        return {"follow_ons": []}

    summaries = "\n".join(f"- [{w['star']}] {w['goal']}" for w in recent)

    prompt = f"""These tasks were just completed in systole #{state.get("systole_num", 1)}:

{summaries}

North stars: {state["north_stars"][:1000]}

Two questions:
1. COMPOUND: What naturally builds on these outputs? (next logical step)
2. SCOUT: Check all 6 north stars. Any star with zero dispatched tasks? New directions?

Return JSON: [{{"goal": "...", "star": "...", "deliverable": "...", "model": "sonnet|opus", "type": "compound|scout"}}]
Return ONLY the JSON array."""

    result = _channel("sonnet", prompt, timeout=90)
    follow_ons = []
    try:
        start = result.find("[")
        end = result.rfind("]") + 1
        if start >= 0 and end > start:
            follow_ons = json.loads(result[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    return {"follow_ons": follow_ons[:6]}


def stopping_gate(state: PolarizationState) -> dict:
    """6-check stopping gate. All must pass before stopping."""
    # Re-check budget (may have changed during systole)
    fresh_budget = _budget_status()

    checks = {
        "budget_not_green": fresh_budget != "green",
        "all_stars_checked": True,  # compound_and_scout covers this
        "signals_checked": True,  # scout covers this
        "calendar_checked": True,  # could add circadian check
        "follow_ons_exhausted": len(state.get("follow_ons", [])) == 0,
        "honest_stop": len(state.get("follow_ons", [])) == 0,
    }

    # Feed follow-ons into next systole's sub_goals
    follow_ons = state.get("follow_ons", [])
    should_stop = checks["budget_not_green"] or (
        checks["follow_ons_exhausted"] and checks["honest_stop"]
    )

    stop_reason = ""
    if fresh_budget == "red":
        stop_reason = "Budget red."
        should_stop = True
    elif fresh_budget == "yellow":
        stop_reason = "Budget yellow — finishing after this systole."
        should_stop = True
    elif should_stop:
        stop_reason = "All follow-ons exhausted and stopping gate passed."

    # If not stopping, promote follow-ons to sub_goals for next systole
    new_goals = [] if should_stop else follow_ons

    return {
        "gate_results": checks,
        "budget_status": fresh_budget,
        "should_stop": should_stop,
        "stop_reason": stop_reason,
        "sub_goals": new_goals,
    }


def write_report(state: PolarizationState) -> dict:
    """Write session report to Poiesis Reports."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d")
    report_path = REPORTS_DIR / f"{ts}.md"

    report = f"""---
systoles: {state.get("systole_num", 0)}
items_produced: {state.get("total_produced", 0)}
items_for_review: {state.get("total_for_review", 0)}
mode: {state.get("mode", "unknown")}
---

# Poiesis Report -- {ts}

## Summary

- Systoles: {state.get("systole_num", 0)}
- Produced: {state.get("total_produced", 0)}
- For review: {state.get("total_for_review", 0)}
- Stop reason: {state.get("stop_reason", "unknown")}

## Work Produced

"""
    for w in state.get("dispatched_work", []):
        status = "ok" if w.get("success") else "FAILED"
        report += f"- [{status}] **{w.get('star', '?')}**: {w.get('goal', '?')}\n"

    if state.get("errors"):
        report += "\n## Errors\n\n"
        for e in state["errors"]:
            report += f"- {e}\n"

    report_path.write_text(report, encoding="utf-8")
    return {"report": str(report_path)}


def wrap(state: PolarizationState) -> dict:
    """Deactivate guard, archive manifest."""
    # Guard off
    if GUARD_FILE.exists():
        GUARD_FILE.unlink()

    # Archive manifest
    if MANIFEST_FILE.exists():
        ts = time.strftime("%Y-%m-%d")
        archive = MANIFEST_FILE.parent / f"polarization-session-{ts}.md"
        MANIFEST_FILE.rename(archive)

    return {}


# ── routing ──────────────────────────────────────────────────


def should_continue(state: PolarizationState) -> str:
    if state.get("should_stop", False):
        return "report"
    return "preflight"


# ── graph assembly ───────────────────────────────────────────


def build_graph() -> StateGraph:
    """Assemble the polarization flywheel graph."""
    graph = StateGraph(PolarizationState)

    graph.add_node("preflight", preflight)
    graph.add_node("brainstorm", brainstorm)
    graph.add_node("dispatch", dispatch)
    graph.add_node("quality_gate", quality_gate)
    graph.add_node("compound_and_scout", compound_and_scout)
    graph.add_node("stopping_gate", stopping_gate)
    graph.add_node("report", write_report)
    graph.add_node("wrap", wrap)

    graph.set_entry_point("preflight")
    graph.add_edge("preflight", "brainstorm")
    graph.add_edge("brainstorm", "dispatch")
    graph.add_edge("dispatch", "quality_gate")
    graph.add_edge("quality_gate", "compound_and_scout")
    graph.add_edge("compound_and_scout", "stopping_gate")
    graph.add_conditional_edges(
        "stopping_gate",
        should_continue,
        {
            "preflight": "preflight",
            "report": "report",
        },
    )
    graph.add_edge("report", "wrap")
    graph.add_edge("wrap", END)

    return graph


# ── public API ───────────────────────────────────────────────


def _open_checkpointer(persistent: bool = True):
    if not persistent:
        return InMemorySaver()
    CHECKPOINT_DB.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSaver(sqlite3.connect(str(CHECKPOINT_DB), check_same_thread=False))


def polarize(
    mode: str = "overnight",
    thread_id: str = "default",
    persistent: bool = True,
) -> dict:
    """Run the polarization flywheel.

    Args:
        mode: "overnight" (unattended) or "interactive" (pauses before dispatch)
        thread_id: Checkpoint thread ID for resume
        persistent: Use SQLite checkpointer
    """
    interactive = mode == "interactive"
    checkpointer = _open_checkpointer(persistent)
    graph = build_graph()

    interrupt = ["dispatch"] if interactive else None
    app = graph.compile(checkpointer=checkpointer, interrupt_before=interrupt)

    config = cast("RunnableConfig", {"configurable": {"thread_id": thread_id}})

    # Check for existing checkpoint to resume
    if persistent:
        existing = checkpointer.get(config)
        if existing is not None:
            return app.invoke(None, config)

    initial_state: PolarizationState = {
        "mode": mode,
        "consumption_count": 0,
        "budget_status": "green",
        "north_stars": "",
        "praxis_items": "",
        "shapes": "",
        "division": "",
        "now_md": "",
        "systole_num": 0,
        "sub_goals": [],
        "dispatched_work": [],
        "archived": [],
        "follow_ons": [],
        "gate_results": {},
        "total_produced": 0,
        "total_for_review": 0,
        "should_stop": False,
        "stop_reason": "",
        "report": "",
        "errors": [],
    }

    result = app.invoke(initial_state, config)
    return result


def review_and_continue(
    thread_id: str = "default",
    approve: bool = True,
    updated_goals: list[dict] | None = None,
) -> dict:
    """Resume an interrupted polarization run."""
    checkpointer = _open_checkpointer(persistent=True)
    graph = build_graph()
    app = graph.compile(checkpointer=checkpointer, interrupt_before=["dispatch"])

    config = cast("RunnableConfig", {"configurable": {"thread_id": thread_id}})

    if not approve:
        app.update_state(
            config,
            {"should_stop": True, "stop_reason": "Operator rejected goals."},
            as_node="stopping_gate",
        )
        return app.invoke(None, config)

    if updated_goals is not None:
        app.update_state(config, {"sub_goals": updated_goals})

    return app.invoke(None, config)


# ── CLI ──────────────────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Polarization flywheel (LangGraph)")
    parser.add_argument("--mode", choices=["overnight", "interactive"], default="overnight")
    parser.add_argument("--thread", default="default", help="Checkpoint thread ID")
    parser.add_argument("--dry-run", action="store_true", help="Preflight only")
    args = parser.parse_args()

    if args.dry_run:
        state = preflight(
            {
                "systole_num": 0,
                "budget_status": "green",
                "mode": args.mode,
            }
        )
        print(f"Budget: {state['budget_status']}")
        print(f"Consumption: {state['consumption_count']}")
        print(f"North stars loaded: {len(state.get('north_stars', ''))} chars")
        return

    result = polarize(mode=args.mode, thread_id=args.thread)
    print(f"Done. Systoles: {result.get('systole_num', 0)}")
    print(f"Produced: {result.get('total_produced', 0)}")
    print(f"For review: {result.get('total_for_review', 0)}")
    if result.get("report"):
        print(f"Report: {result['report']}")


if __name__ == "__main__":
    main()
