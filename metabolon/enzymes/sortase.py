from __future__ import annotations

"""sortase — dispatch coding tasks to cheap LLM backends.

Actions: dispatch|route|status|stats
"""


import asyncio
import tempfile
import threading
from pathlib import Path

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion


class SortaseResult(Secretion):
    success: bool = True
    message: str = ""
    tasks: list[dict] = []
    files_changed: list[str] = []
    validation_issues: list[dict] = []
    duration_s: float = 0.0


class RouteResult(Secretion):
    tool: str
    reason: str


class StatsResult(Secretion):
    entries: list[dict] = []
    per_tool: dict = {}
    total_runs: int = 0


@tool(
    name="sortase",
    description="Dispatch coding tasks to cheap LLM backends. Actions: dispatch|route|status|stats",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def sortase(
    action: str,
    prompt: str = "",
    project_dir: str = "",
    backend: str = "",
    timeout: int = 600,
    description: str = "",
    last_n: int = 10,
) -> SortaseResult | RouteResult | StatsResult:
    action = action.lower().strip()

    # -- dispatch --------------------------------------------------------
    if action == "dispatch":
        if not prompt or not project_dir:
            return SortaseResult(success=False, message="dispatch requires prompt and project_dir")

        proj = Path(project_dir).expanduser().resolve()
        if not proj.is_dir():
            return SortaseResult(success=False, message=f"Not a directory: {project_dir}")

        from metabolon.sortase.decompose import TaskSpec
        from metabolon.sortase.executor import execute_tasks
        from metabolon.sortase.router import route_description
        from metabolon.sortase.validator import validate_execution

        # Create a temp spec file (executor may need it)
        tmp = Path(tempfile.gettempdir()) / "sortase-mcp-dispatch.txt"
        tmp.write_text(prompt, encoding="utf-8")

        try:
            task = TaskSpec(
                name="mcp-dispatch",
                description=prompt[:120],
                spec=prompt,
                files=[],
                signal="default",
                temp_file=str(tmp),
            )

            forced = backend if backend else None
            tool_by_task = {task.name: route_description(task.description, forced_backend=forced).tool}

            # Handle existing event loop (FastMCP is async)
            def _run_dispatch() -> list:
                return asyncio.run(
                    execute_tasks(
                        [task], proj, tool_by_task,
                        serial=False, timeout_sec=timeout, verbose=False,
                    )
                )

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                container: dict = {}
                def _thread_target() -> None:
                    container["results"] = _run_dispatch()
                worker = threading.Thread(target=_thread_target)
                worker.start()
                worker.join(timeout=timeout + 30)
                results = container.get("results", [])
            else:
                results = _run_dispatch()

            # Validation
            import subprocess as _sp
            diff = _sp.run(
                ["git", "diff", "--name-only"], cwd=proj,
                capture_output=True, check=False, text=True,
            )
            changed = [line for line in diff.stdout.splitlines() if line.strip()]
            issues = validate_execution(
                proj, new_files=changed, test_command=None,
                pyproject_path=proj / "pyproject.toml", cargo_path=proj / "Cargo.toml",
            )

            # Log
            from metabolon.sortase.logger import append_log
            from datetime import datetime
            dur = round(sum(a.duration_s for r in results for a in r.attempts), 3)
            entry = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "plan": "mcp-dispatch",
                "project": proj.name,
                "tasks": 1,
                "tool": tool_by_task[task.name],
                "fallbacks": [fallback for r in results for fallback in r.fallbacks],
                "duration_s": dur,
                "success": all(r.success for r in results),
                "failure_reason": next((i.message for i in issues if i.severity == "error"), None),
                "files_changed": len(changed),
                "tests_passed": 0 if any(i.check == "tests" for i in issues) else 1,
            }
            append_log(entry)

            return SortaseResult(
                success=all(r.success for r in results),
                message=f"Dispatched to {tool_by_task[task.name]}",
                tasks=[
                    {
                        "name": r.task_name,
                        "tool": r.tool,
                        "success": r.success,
                        "duration_s": sum(a.duration_s for a in r.attempts),
                        "fallbacks": r.fallbacks,
                    }
                    for r in results
                ],
                files_changed=changed,
                validation_issues=[{"severity": i.severity, "message": i.message} for i in issues],
                duration_s=dur,
            )
        finally:
            tmp.unlink(missing_ok=True)

    # -- route -----------------------------------------------------------
    elif action == "route":
        from metabolon.sortase.router import route_description

        desc = description or prompt
        if not desc:
            return RouteResult(tool="unknown", reason="No description provided")
        decision = route_description(desc)
        return RouteResult(tool=decision.tool, reason=decision.reason)

    # -- status ----------------------------------------------------------
    elif action == "status":
        from metabolon.sortase.executor import list_running

        entries = list_running()
        return SortaseResult(
            success=True,
            message=f"{len(entries)} running",
            tasks=[
                {
                    "name": e.get("task_name", ""),
                    "tool": e.get("tool", ""),
                    "project": e.get("project_dir", ""),
                    "started_at": e.get("started_at", ""),
                }
                for e in entries
                if isinstance(e, dict)
            ],
        )

    # -- stats -----------------------------------------------------------
    elif action == "stats":
        from metabolon.sortase.logger import aggregate_stats, read_logs

        entries = read_logs()
        if not entries:
            return StatsResult(entries=[], per_tool={}, total_runs=0)
        payload = aggregate_stats(entries)
        recent = entries[-last_n:]
        return StatsResult(
            entries=[
                {
                    "timestamp": e.get("timestamp", ""),
                    "plan": e.get("plan", ""),
                    "tool": e.get("tool", ""),
                    "success": e.get("success", False),
                }
                for e in recent
            ],
            per_tool=payload.get("per_tool", {}),
            total_runs=len(entries),
        )

    else:
        return SortaseResult(
            success=False,
            message=f"Unknown action: {action}. Valid: dispatch|route|status|stats",
        )
