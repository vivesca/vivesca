"""circulation — autonomous overnight work loop via LangGraph.

Circulation is the pump. It cycles through north star goals, dispatches work,
evaluates results, and compounds — checkpointing after every systole so it
survives session disconnects. The nodes are pluggable; circulation just moves
blood through the system.

State machine:
  preflight → select_goals → [INTERRUPT] → dispatch → evaluate → compound → checkpoint
       ↑                                                                        |
       └──────────── (budget green) ────────────────────────────────────────────┘
                     (budget yellow/red) → report → END

The interrupt before dispatch is a LangGraph interrupt_before gate. In
interactive mode, the graph pauses after goal selection so the operator can
review before tokens are burned. In overnight mode, the gate is skipped.

Checkpoints persist to SQLite at ~/.local/share/vivesca/checkpoints.db so
overnight runs survive process crashes and can be resumed.

Usage:
    from metabolon.organelles.circulation import circulate
    circulate(mode="overnight")   # runs unattended, persistent checkpoints
    circulate(mode="interactive") # pauses before dispatch for review
"""

import json
import operator
import time
from pathlib import Path
from typing import Annotated, Any, TypedDict, cast

from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from metabolon.locus import (
    checkpoints_db,
    chromatin,
    north_star,
    now,
    poiesis_reports,
    praxis,
    tmp,
)
from metabolon.symbiont import transduce, transduce_safe

# ── paths ────────────────────────────────────────────────────

CHECKPOINT_DB = checkpoints_db

NORTH_STAR_PATH = north_star
SHAPES_PATH = chromatin / "euchromatin" / "epistemics" / "north-star-shapes.md"
DIVISION_PATH = chromatin / "euchromatin" / "epistemics" / "division-of-labour.md"
NOW_PATH = now
MANIFEST_PATH = tmp / "circulation-manifest.md"
REPORT_DIR = poiesis_reports

# ── models ───────────────────────────────────────────────────

PLANNER_MODEL = "glm"
WORKER_MODEL = "sonnet"
EVALUATOR_MODEL = "claude"

# ── state ────────────────────────────────────────────────────


class CirculationState(TypedDict):
    """Graph state — persisted at every checkpoint."""

    # Context loaded at preflight
    north_stars: str
    praxis_items: str
    budget_status: str  # "green", "yellow", "red"
    mode: str  # "interactive", "overnight"

    # Per-systole
    systole_num: int
    selected_goals: list[dict[str, str]]  # [{star, goal, deliverable, model}]
    dispatched_work: Annotated[list[dict[str, Any]], operator.add]  # append-only
    evaluation: str
    compound_ideas: list[str]

    # Accumulator
    total_produced: int
    total_for_review: int
    errors: Annotated[list[str], operator.add]
    should_stop: bool
    stop_reason: str
    report: str


# ── node functions ───────────────────────────────────────────


def preflight(state: CirculationState) -> dict:
    """Load context: north stars, praxis, budget."""
    ns = ""
    if NORTH_STAR_PATH.exists():
        ns = NORTH_STAR_PATH.read_text(encoding="utf-8")[:3000]

    praxis_text = ""
    if praxis.exists():
        lines = praxis.read_text(encoding="utf-8").splitlines()[:80]
        praxis_text = "\n".join(lines)

    # Budget check — read from allostasis state
    budget = "green"
    allow_state = Path.home() / ".claude" / "allostasis-state.json"
    if allow_state.exists():
        try:
            data = json.loads(allow_state.read_text())
            tier = data.get("tier", "")
            if "catabolic" in tier or "autophagic" in tier:
                budget = "red"
            elif "homeostatic" in tier:
                budget = "yellow"
        except Exception:
            pass

    return {
        "north_stars": ns,
        "praxis_items": praxis_text,
        "budget_status": budget,
        "systole_num": state.get("systole_num", 0) + 1,
    }


def select_goals(state: CirculationState) -> dict:
    """Pick sub-goals for this systole using the shape/leverage filter."""
    mode = state.get("mode", "overnight")
    max_goals = 8 if mode == "overnight" else 4

    prompt = f"""You are a work dispatcher for an autonomous overnight agent system.

North stars:
{state["north_stars"][:2000]}

Current Praxis:
{state["praxis_items"][:2000]}

Systole #{state["systole_num"]}. Budget: {state["budget_status"]}.
Previous work this session: {state.get("total_produced", 0)} items produced.

Select up to {max_goals} concrete, automatable sub-goals. For each:
- Which north star it serves
- The specific deliverable (file path + format)
- Whether it needs sonnet (research/collection) or claude (synthesis/judgment)

FILTERS — skip anything that requires:
- Terry's physical presence or attention
- Terry forming his own view (sharpening)
- Interactive collaboration

Return JSON array: [{{"star": "...", "goal": "...", "deliverable": "...", "model": "sonnet|claude"}}]
Return ONLY the JSON array, no other text."""

    result = transduce(PLANNER_MODEL, prompt, timeout=120)

    goals = []
    try:
        # Extract JSON from response
        start = result.find("[")
        end = result.rfind("]") + 1
        if start >= 0 and end > start:
            goals = json.loads(result[start:end])
    except json.JSONDecodeError, ValueError:
        return {"errors": [f"Goal selection failed to parse: {result[:200]}"]}

    return {"selected_goals": goals[:max_goals]}


def dispatch(state: CirculationState) -> dict:
    """Execute work for each selected goal via symbiont."""
    goals = state.get("selected_goals", [])
    if not goals:
        return {"errors": ["No goals selected — nothing to dispatch"]}

    results = []
    for goal in goals:
        model = goal.get("model", "sonnet")
        deliverable = goal.get("deliverable", "")
        prompt = f"""Complete this task autonomously. Produce a concrete deliverable.

Task: {goal.get("goal", "")}
North star: {goal.get("star", "")}
Expected deliverable: {deliverable}

Be thorough but concise. Output the deliverable content directly."""

        model_name, output = transduce_safe(model, prompt, timeout=300)
        result = {
            "goal": goal.get("goal", ""),
            "star": goal.get("star", ""),
            "model": model_name,
            "deliverable_path": deliverable,
            "output": output[:5000],
            "success": not output.startswith("(error") and not output.startswith("(timed"),
        }
        results.append(result)

        # Write deliverable if path specified
        if result["success"] and deliverable:
            try:
                out_path = Path(deliverable.replace("~", str(Path.home())))
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(output, encoding="utf-8")
            except Exception as e:
                result["write_error"] = str(e)

    return {"dispatched_work": results}


def evaluate(state: CirculationState) -> dict:
    """Classify outputs: self-sufficient vs needs-review. Quality gate."""
    work = state.get("dispatched_work", [])
    # Only evaluate recent successful work
    recent = [w for w in work if w.get("success", False)]
    if not recent:
        return {
            "evaluation": "No successful outputs to evaluate.",
            "total_produced": state.get("total_produced", 0),
            "total_for_review": state.get("total_for_review", 0),
        }

    summaries = "\n".join(
        f"- [{w['star']}] {w['goal']}: {w['output'][:200]}..." for w in recent[-8:]
    )

    prompt = f"""Evaluate these agent outputs. For each:
1. SELF-SUFFICIENT (archive directly) or NEEDS-REVIEW (requires Terry)?
2. Quality: PASS / PARTIAL / FAIL

{summaries}

Return JSON: [{{"goal": "...", "classification": "self-sufficient|needs-review", "quality": "pass|partial|fail", "reason": "..."}}]
Return ONLY the JSON array."""

    eval_text = transduce(EVALUATOR_MODEL, prompt, timeout=120)
    produced = len(recent)
    review = 0
    try:
        start = eval_text.find("[")
        end = eval_text.rfind("]") + 1
        if start >= 0 and end > start:
            evals = json.loads(eval_text[start:end])
            review = sum(1 for e in evals if e.get("classification") == "needs-review")
    except json.JSONDecodeError, ValueError:
        pass

    return {
        "evaluation": eval_text[:2000],
        "total_produced": state.get("total_produced", 0) + produced,
        "total_for_review": state.get("total_for_review", 0) + review,
    }


def compound(state: CirculationState) -> dict:
    """Ask: what builds on this systole's outputs? Scout new directions."""
    work = state.get("dispatched_work", [])
    recent_successful = [w for w in work if w.get("success", False)][-8:]

    if not recent_successful:
        return {"compound_ideas": []}

    summaries = "\n".join(f"- [{w['star']}] {w['goal']}" for w in recent_successful)

    prompt = f"""These tasks were just completed in an autonomous overnight session:

{summaries}

Two questions:
1. COMPOUND: What naturally builds on these outputs? (next logical step for each)
2. SCOUT: What new directions do these reveal for the north stars?

Return JSON: [{{"idea": "...", "star": "...", "type": "compound|scout"}}]
Return ONLY the JSON array."""

    result = transduce(PLANNER_MODEL, prompt, timeout=90)
    ideas = []
    try:
        start = result.find("[")
        end = result.rfind("]") + 1
        if start >= 0 and end > start:
            ideas = [item.get("idea", "") for item in json.loads(result[start:end])]
    except json.JSONDecodeError, ValueError:
        pass

    return {"compound_ideas": ideas[:6]}


def checkpoint_node(state: CirculationState) -> dict:
    """Update manifest and decide: continue or stop."""
    # Write manifest
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    work = state.get("dispatched_work", [])
    lines = [
        f"# Circulation Manifest — Systole {state.get('systole_num', 0)}",
        "",
        f"Produced: {state.get('total_produced', 0)}",
        f"For review: {state.get('total_for_review', 0)}",
        f"Budget: {state.get('budget_status', 'unknown')}",
        "",
        "## Completed Work",
    ]
    for w in work:
        status = "ok" if w.get("success") else "FAILED"
        lines.append(f"- [{status}] [{w.get('star', '?')}] {w.get('goal', '?')}")

    if state.get("compound_ideas"):
        lines.append("\n## Compound Ideas")
        for idea in state["compound_ideas"]:
            lines.append(f"- {idea}")

    MANIFEST_PATH.write_text("\n".join(lines), encoding="utf-8")

    # Stop decision
    budget = state.get("budget_status", "green")
    if budget == "red":
        return {"should_stop": True, "stop_reason": "Budget red — stopping immediately."}
    if budget == "yellow":
        return {"should_stop": True, "stop_reason": "Budget yellow — finishing current systole."}
    if not state.get("selected_goals"):
        return {"should_stop": True, "stop_reason": "No goals could be selected."}

    return {"should_stop": False}


def write_report(state: CirculationState) -> dict:
    """Write session report."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d")
    report_path = REPORT_DIR / f"{ts}.md"

    report = f"""---
systoles: {state.get("systole_num", 0)}
items_produced: {state.get("total_produced", 0)}
items_for_review: {state.get("total_for_review", 0)}
mode: {state.get("mode", "unknown")}
---

# Poiesis Report — {ts}

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


# ── routing ──────────────────────────────────────────────────


def should_continue(state: CirculationState) -> str:
    """Route: continue cycling or stop and report."""
    if state.get("should_stop", False):
        return "report"
    return "preflight"


# ── graph assembly ───────────────────────────────────────────


def build_graph() -> StateGraph:
    """Assemble the circulation graph."""
    graph = StateGraph(CirculationState)

    graph.add_node("preflight", preflight)
    graph.add_node("select_goals", select_goals)
    graph.add_node("dispatch", dispatch)
    graph.add_node("evaluate", evaluate)
    graph.add_node("compound", compound)
    graph.add_node("checkpoint", checkpoint_node)
    graph.add_node("report", write_report)

    graph.set_entry_point("preflight")
    graph.add_edge("preflight", "select_goals")
    graph.add_edge("select_goals", "dispatch")
    graph.add_edge("dispatch", "evaluate")
    graph.add_edge("evaluate", "compound")
    graph.add_edge("compound", "checkpoint")
    graph.add_conditional_edges(
        "checkpoint",
        should_continue,
        {
            "preflight": "preflight",
            "report": "report",
        },
    )
    graph.add_edge("report", END)

    return graph


# ── public API ───────────────────────────────────────────────


def _open_checkpointer(persistent: bool = True):
    """Open a checkpointer — SQLite for persistence, InMemory for tests."""
    if not persistent:
        return InMemorySaver()
    import sqlite3

    CHECKPOINT_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CHECKPOINT_DB), check_same_thread=False)
    return SqliteSaver(conn)


def circulate(
    mode: str = "overnight",
    thread_id: str = "default",
    resume: bool = True,
    persistent: bool = True,
) -> dict:
    """Run the circulation loop.

    Args:
        mode: "overnight" (unattended) or "interactive" (pauses before dispatch)
        thread_id: Checkpoint thread ID for resume
        resume: If True, resume from last checkpoint if one exists
        persistent: If True, use SQLite checkpointer (survives crashes)
    """
    interactive = mode == "interactive"
    checkpointer = _open_checkpointer(persistent)
    graph = build_graph()

    interrupt = ["dispatch"] if interactive else None
    app = graph.compile(checkpointer=checkpointer, interrupt_before=interrupt)

    config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})

    # Check for existing checkpoint to resume
    if resume and persistent:
        existing = checkpointer.get(config)
        if existing is not None:
            final_state = app.invoke(None, config)
            return final_state

    initial_state: CirculationState = {
        "north_stars": "",
        "praxis_items": "",
        "budget_status": "green",
        "mode": mode,
        "systole_num": 0,
        "selected_goals": [],
        "dispatched_work": [],
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    final_state = app.invoke(initial_state, config)
    return final_state


def review_and_continue(
    thread_id: str = "default",
    approve: bool = True,
    updated_goals: list[dict[str, str]] | None = None,
) -> dict:
    """Resume an interrupted circulation run after reviewing goals.

    Called after circulate(mode="interactive") pauses at the dispatch gate.

    Args:
        thread_id: Must match the thread_id used in circulate()
        approve: If True, continue with selected goals. If False, stop.
        updated_goals: Optionally replace the selected_goals before continuing.
    """
    checkpointer = _open_checkpointer(persistent=True)
    graph = build_graph()
    app = graph.compile(checkpointer=checkpointer, interrupt_before=["dispatch"])

    config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})

    if not approve:
        # Jump to checkpoint's output edge — should_continue routes to report → END
        app.update_state(
            config,
            {"should_stop": True, "stop_reason": "Operator rejected goals."},
            as_node="checkpoint",
        )
        return app.invoke(None, config)

    if updated_goals is not None:
        app.update_state(config, {"selected_goals": updated_goals})

    return app.invoke(None, config)


# ── CLI ──────────────────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Circulation — autonomous work loop")
    parser.add_argument("--mode", choices=["overnight", "interactive"], default="overnight")
    parser.add_argument("--thread", default="default", help="Checkpoint thread ID")
    parser.add_argument("--dry-run", action="store_true", help="Preflight only")
    args = parser.parse_args()

    if args.dry_run:
        state = preflight(
            {  # type: ignore[arg-type]
                "systole_num": 0,
                "budget_status": "green",
                "mode": args.mode,
            }
        )
        print(f"Budget: {state['budget_status']}")
        print(f"North stars loaded: {len(state.get('north_stars', ''))} chars")
        print(f"Praxis items loaded: {len(state.get('praxis_items', ''))} chars")
        return

    result = circulate(mode=args.mode, thread_id=args.thread)
    print(f"Done. Systoles: {result.get('systole_num', 0)}")
    print(f"Produced: {result.get('total_produced', 0)}")
    print(f"For review: {result.get('total_for_review', 0)}")
    if result.get("report"):
        print(f"Report: {result['report']}")


if __name__ == "__main__":
    main()
