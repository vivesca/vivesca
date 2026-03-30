"""sortase.graph — LangGraph executor for plan-based agent orchestration.

Reimplements the sortase exec flow as a LangGraph StateGraph:

  decompose → route → [INTERRUPT] → execute → validate → log → END
                                       ↓ (on failure + retries left)
                                     retry_with_fallback ──→ execute

The interrupt before execute lets the operator review routing decisions
before CLI agents start coding. SQLite checkpoints let multi-task runs
survive process crashes.

Nodes call CLI agents (gemini, codex, goose, headless CC) via subprocess.
Zero API key cost for free-tier CLIs.
"""

from __future__ import annotations

import asyncio
import logging
import operator
import sqlite3
import subprocess
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Annotated, TypedDict

logger = logging.getLogger(__name__)

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from metabolon.sortase.decompose import TaskSpec, decompose_plan
from metabolon.sortase.executor import execute_tasks, summarize_cost_estimates
from metabolon.sortase.logger import append_log
from metabolon.sortase.router import route_description
from metabolon.sortase.validator import validate_execution

# ── constants ────────────────────────────────────────────────

CHECKPOINT_DB = Path.home() / ".local" / "share" / "vivesca" / "checkpoints.db"


# ── state ────────────────────────────────────────────────────


class SortaseState(TypedDict):
    """Graph state for one sortase execution."""

    # Inputs
    plan_file: str
    project_dir: str
    serial: bool
    backend: str  # empty string = auto-route
    test_command: str  # empty string = none
    timeout: int

    # After decompose
    tasks: list[dict]  # serialized TaskSpecs
    task_count: int

    # After route
    tool_by_task: dict[str, str]
    route_decisions: list[dict]

    # After execute
    results: Annotated[list[dict], operator.add]
    executed: bool

    # After validate
    validation_issues: list[dict]
    changed_files: list[str]

    # Final
    success: bool
    log_entry: dict
    errors: Annotated[list[str], operator.add]


# ── node functions ───────────────────────────────────────────


def decompose(state: SortaseState) -> dict:
    """Parse plan file into independent tasks."""
    plan_path = Path(state["plan_file"])

    try:
        tasks = decompose_plan(plan_path, smart=False)
        return {
            "tasks": [asdict(t) for t in tasks],
            "task_count": len(tasks),
        }
    except Exception as e:
        return {
            "tasks": [],
            "task_count": 0,
            "errors": [f"Decompose failed: {e}"],
        }


def route(state: SortaseState) -> dict:
    """Route each task to a CLI agent."""
    tasks = state.get("tasks", [])
    backend = state.get("backend", "") or None

    tool_by_task: dict[str, str] = {}
    decisions: list[dict] = []

    for task_dict in tasks:
        name = task_dict["name"]
        desc = task_dict.get("description", "")
        decision = route_description(desc, forced_backend=backend)
        tool_by_task[name] = decision.tool
        decisions.append({
            "task": name,
            "tool": decision.tool,
            "reason": decision.reason,
        })

    return {
        "tool_by_task": tool_by_task,
        "route_decisions": decisions,
    }


def execute(state: SortaseState) -> dict:
    """Dispatch tasks to CLI agents via subprocess."""
    task_dicts = state.get("tasks", [])
    if not task_dicts:
        return {"results": [], "executed": True, "errors": ["No tasks to execute"]}

    project_dir = Path(state["project_dir"])
    tool_by_task = state.get("tool_by_task", {})
    serial = state.get("serial", False)
    timeout = state.get("timeout", 600)

    # Reconstruct TaskSpec objects
    tasks = [
        TaskSpec(
            name=t["name"],
            description=t["description"],
            spec=t["spec"],
            files=t.get("files", []),
            signal=t.get("signal", "default"),
            prerequisite=t.get("prerequisite"),
            temp_file=t.get("temp_file"),
        )
        for t in task_dicts
    ]

    results = asyncio.run(
        execute_tasks(tasks, project_dir, tool_by_task, serial=serial, timeout_sec=timeout)
    )

    return {
        "results": [
            {
                "task_name": r.task_name,
                "tool": r.tool,
                "success": r.success,
                "output": r.output[-1000:] if r.output else "",
                "fallbacks": r.fallbacks,
                "fallback_chain": r.fallback_chain,
                "prompt_file": r.prompt_file,
                "cost_estimate": r.cost_estimate,
            }
            for r in results
        ],
        "executed": True,
    }


def validate(state: SortaseState) -> dict:
    """Check for dependency pollution, scope, placeholders, tests."""
    project_dir = Path(state["project_dir"])
    test_command = state.get("test_command", "") or None

    diff = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=project_dir,
        capture_output=True,
        check=False,
        text=True,
    )
    changed_files = [line for line in diff.stdout.splitlines() if line.strip()]

    issues = validate_execution(
        project_dir,
        new_files=changed_files,
        test_command=test_command,
        pyproject_path=project_dir / "pyproject.toml",
        cargo_path=project_dir / "Cargo.toml",
    )

    return {
        "validation_issues": [
            {"check": i.check, "message": i.message, "severity": i.severity}
            for i in issues
        ],
        "changed_files": changed_files,
    }


def log_results(state: SortaseState) -> dict:
    """Write execution log and compute success."""
    results = state.get("results", [])
    validation_issues = state.get("validation_issues", [])

    all_tasks_ok = all(r.get("success", False) for r in results)
    no_errors = not any(i["severity"] == "error" for i in validation_issues)
    success = all_tasks_ok and no_errors

    duration_s = 0.0  # Not tracked in graph state — could add if needed
    fallbacks = [tool for r in results for tool in r.get("fallbacks", [])]
    fallback_chain = [step.to_dict() for r in results for step in r.get("fallback_chain", [])]

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "plan": Path(state["plan_file"]).name,
        "project": Path(state["project_dir"]).name,
        "tasks": state.get("task_count", 0),
        "tool": state.get("backend") or (results[0]["tool"] if results else "unknown"),
        "fallbacks": fallbacks,
        "fallback_chain": fallback_chain,
        "duration_s": duration_s,
        "success": success,
        "failure_reason": next(
            (i["check"] for i in validation_issues if i["severity"] == "error"),
            None,
        ),
        "files_changed": len(state.get("changed_files", [])),
        "tests_passed": 0 if any(i["check"] == "tests" for i in validation_issues) else 1,
        "executor": "langgraph",
        "cost_estimate": summarize_cost_estimates(
            [r.get("cost_estimate", "") for r in results if r.get("cost_estimate")]
        ),
    }

    append_log(entry)

    return {"success": success, "log_entry": entry}


# ── graph assembly ───────────────────────────────────────────


def build_graph() -> StateGraph:
    """Assemble the sortase execution graph."""
    graph = StateGraph(SortaseState)

    graph.add_node("decompose", decompose)
    graph.add_node("route", route)
    graph.add_node("execute", execute)
    graph.add_node("validate", validate)
    graph.add_node("log_results", log_results)

    graph.set_entry_point("decompose")
    graph.add_edge("decompose", "route")
    graph.add_edge("route", "execute")
    graph.add_edge("execute", "validate")
    graph.add_edge("validate", "log_results")
    graph.add_edge("log_results", END)

    return graph


# ── public API ───────────────────────────────────────────────


def _open_checkpointer() -> SqliteSaver:
    """Open (or create) the SQLite checkpoint store.

    Returns the checkpointer.  Logs the resolved path so operators know
    exactly where crash-recovery state is persisted.
    """
    CHECKPOINT_DB.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Checkpoint store: %s", CHECKPOINT_DB)
    conn = sqlite3.connect(str(CHECKPOINT_DB), check_same_thread=False)
    return SqliteSaver(conn)


def run(
    plan_file: str | Path,
    project_dir: str | Path,
    serial: bool = False,
    backend: str | None = None,
    test_command: str | None = None,
    timeout: int = 600,
    interactive: bool = False,
    thread_id: str | None = None,
) -> dict:
    """Execute a plan via the LangGraph sortase graph.

    Args:
        plan_file: Path to plan YAML or markdown file.
        project_dir: Target project directory.
        serial: If True, execute tasks sequentially.
        backend: Force a specific CLI agent (gemini/codex/goose).
        test_command: Optional test command to run after execution.
        timeout: Per-task timeout in seconds.
        interactive: If True, pause before execute for routing review.
        thread_id: Checkpoint thread ID. Auto-generated if None.
    """
    checkpointer = _open_checkpointer()
    graph = build_graph()

    interrupt = ["execute"] if interactive else None
    app = graph.compile(checkpointer=checkpointer, interrupt_before=interrupt)

    if thread_id is None:
        thread_id = f"sortase-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    logger.info(
        "run  thread_id=%s  checkpoint_db=%s  interactive=%s",
        thread_id, CHECKPOINT_DB, interactive,
    )

    config = {"configurable": {"thread_id": thread_id}}

    initial_state: SortaseState = {
        "plan_file": str(plan_file),
        "project_dir": str(project_dir),
        "serial": serial,
        "backend": backend or "",
        "test_command": test_command or "",
        "timeout": timeout,
        "tasks": [],
        "task_count": 0,
        "tool_by_task": {},
        "route_decisions": [],
        "results": [],
        "executed": False,
        "validation_issues": [],
        "changed_files": [],
        "success": False,
        "log_entry": {},
        "errors": [],
    }

    result = app.invoke(initial_state, config)

    if interactive and not result.get("executed", False):
        # Graph paused before execute — return state with routing for review
        return {
            "status": "paused",
            "thread_id": thread_id,
            "checkpoint_db": str(CHECKPOINT_DB),
            "route_decisions": result.get("route_decisions", []),
            "tasks": result.get("tasks", []),
        }

    return result


def review_and_continue(
    thread_id: str,
    approve: bool = True,
    override_routing: dict[str, str] | None = None,
) -> dict:
    """Resume a paused sortase run after reviewing routing.

    Args:
        thread_id: Thread ID from the paused run.
        approve: If True, continue execution. If False, abort.
        override_routing: Optional {task_name: tool} overrides.
    """
    checkpointer = _open_checkpointer()
    graph = build_graph()
    app = graph.compile(checkpointer=checkpointer, interrupt_before=["execute"])

    logger.info(
        "resume  thread_id=%s  approve=%s  checkpoint_db=%s",
        thread_id, approve, CHECKPOINT_DB,
    )

    config = {"configurable": {"thread_id": thread_id}}

    if not approve:
        app.update_state(
            config,
            {"errors": ["Operator aborted."], "executed": True, "success": False},
            as_node="log_results",
        )
        return app.invoke(None, config)

    if override_routing:
        state = app.get_state(config)
        current = state.values.get("tool_by_task", {})
        current.update(override_routing)
        app.update_state(config, {"tool_by_task": current})

    return app.invoke(None, config)
