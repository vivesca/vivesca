from __future__ import annotations

import asyncio
import json
import shutil
import time
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from metabolon.sortase.decompose import decompose_plan
from metabolon.sortase.executor import execute_tasks, list_running
from metabolon.sortase.logger import aggregate_stats, append_log, read_logs
from metabolon.sortase.router import route_description
from metabolon.sortase.validator import validate_execution

console = Console()


@click.group()
def main() -> None:
    """sortase orchestrates free AI coding tools."""


@main.command("exec")
@click.argument("plan_file", type=click.Path(exists=True, path_type=Path))
@click.option("-p", "--project-dir", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--serial", is_flag=True, help="Execute tasks one at a time.")
@click.option("-b", "--backend", type=click.Choice(["gemini", "codex", "goose", "opencode", "cc-glm", "droid", "crush"]))
@click.option("--decompose", is_flag=True, help="Use Gemini to split the plan into independent tasks.")
@click.option("--test-command", default=None, help="Optional test command to run after execution.")
@click.option("--timeout", default=600, show_default=True, type=int)
@click.option("-v", "--verbose", is_flag=True, help="Stream backend output live.")
@click.option("--commit", is_flag=True, help="Auto-commit changes after successful execution.")
@click.option("--dry-run", is_flag=True, help="Show what would change without editing files.")
@click.option("--json-output", "json_out", is_flag=True, help="Output results as JSON.")
@click.option("--retries", default=0, show_default=True, type=int, help="Retry failed tasks N times.")
@click.option("-q", "--quiet", is_flag=True, help="Suppress all output except errors.")
@click.option("--no-coaching", is_flag=True, help="Skip coaching note prepend.")
def exec_command(
    plan_file: Path,
    project_dir: Path,
    serial: bool,
    backend: str | None,
    decompose: bool,
    test_command: str | None,
    timeout: int,
    verbose: bool,
    commit: bool,
    dry_run: bool,
    json_out: bool,
    retries: int,
    quiet: bool,
    no_coaching: bool,
) -> None:
    """Execute a plan file against a project directory."""

    tasks = decompose_plan(plan_file, smart=decompose)
    tool_by_task = {task.name: route_description(task.description, forced_backend=backend).tool for task in tasks}

    if not quiet:
        console.print(f"[bold]Executing[/bold] {len(tasks)} task(s) in {project_dir}")
    results = asyncio.run(execute_tasks(tasks, project_dir, tool_by_task, serial=serial, timeout_sec=timeout, verbose=verbose, dry_run=dry_run, max_retries=retries, coaching=not no_coaching))

    import subprocess as _sp
    _diff = _sp.run(
        ["git", "diff", "--name-only"],
        cwd=project_dir, capture_output=True, check=False, text=True,
    )
    changed_file_list = [line for line in _diff.stdout.splitlines() if line.strip()]
    changed_files = len(changed_file_list)
    validation_issues = validate_execution(
        project_dir,
        new_files=changed_file_list,
        test_command=test_command,
        pyproject_path=project_dir / "pyproject.toml",
        cargo_path=project_dir / "Cargo.toml",
    )

    if not json_out and not quiet:
        for result in results:
            status = "ok" if result.success else "failed"
            duration = sum(a.duration_s for a in result.attempts)
            timeout_pct = duration / timeout * 100 if timeout > 0 else 0
            suffix = f" [yellow]({timeout_pct:.0f}% of timeout)[/yellow]" if timeout_pct > 80 else ""
            console.print(f"{result.task_name}: {result.tool} [{status}] ({duration:.1f}s){suffix}")

        if validation_issues:
            console.print("[bold yellow]Validation issues[/bold yellow]")
            for issue in validation_issues:
                console.print(f"- {issue.severity}: {issue.message}")

        if changed_file_list:
            console.print(f"\n[bold]Changed files[/bold] ({changed_files}):")
            for cf in changed_file_list[:10]:
                console.print(f"  {cf}")
            if changed_files > 10:
                console.print(f"  ... and {changed_files - 10} more")

    duration_s = round(sum(attempt.duration_s for result in results for attempt in result.attempts), 3)
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "plan": plan_file.name,
        "project": project_dir.name,
        "tasks": len(tasks),
        "tool": backend or (results[0].tool if results else "unknown"),
        "fallbacks": [tool for result in results for tool in result.fallbacks],
        "duration_s": duration_s,
        "success": all(result.success for result in results) and not any(issue.severity == "error" for issue in validation_issues),
        "failure_reason": next((issue.check for issue in validation_issues if issue.severity == "error"), None),
        "files_changed": changed_files,
        "tests_passed": 0 if any(issue.check == "tests" for issue in validation_issues) else 1,
    }
    append_log(entry)
    if json_out:
        import json as _json
        output = {
            "success": entry["success"],
            "tasks": [
                {
                    "name": r.task_name,
                    "tool": r.tool,
                    "success": r.success,
                    "duration_s": sum(a.duration_s for a in r.attempts),
                    "fallbacks": r.fallbacks,
                }
                for r in results
            ],
            "files_changed": changed_file_list,
            "validation_issues": [
                {"severity": i.severity, "message": i.message}
                for i in validation_issues
            ],
            "duration_s": entry["duration_s"],
        }
        console.print(_json.dumps(output, indent=2))
    elif not quiet:
        console.print(f"Logged execution to history. Success={entry['success']}")
    if commit and entry["success"] and changed_files > 0:
        import subprocess as _sp2
        plan_name = plan_file.stem
        _sp2.run(
            ["git", "add", "-A"],
            cwd=project_dir, capture_output=True, check=False,
        )
        msg = f"sortase: {plan_name}\n\nBackend: {entry['tool']}, Duration: {entry['duration_s']}s"
        _sp2.run(
            ["git", "commit", "-m", msg],
            cwd=project_dir, capture_output=True, check=False,
        )
        if not quiet:
            console.print(f"[bold green]Committed[/bold green] ({changed_files} files changed)")


@main.command("graph-exec")
@click.argument("plan_file", type=click.Path(exists=True, path_type=Path))
@click.option("-p", "--project-dir", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--serial", is_flag=True, help="Execute tasks one at a time.")
@click.option("-b", "--backend", type=click.Choice(["gemini", "codex", "goose", "opencode", "cc-glm", "droid", "crush"]))
@click.option("--test-command", default=None, help="Optional test command to run after execution.")
@click.option("--timeout", default=600, show_default=True, type=int)
@click.option("--interactive", is_flag=True, help="Pause before execution for routing review.")
@click.option("--thread-id", default=None, help="Checkpoint thread ID for resume.")
def graph_exec_command(
    plan_file: Path,
    project_dir: Path,
    serial: bool,
    backend: str | None,
    test_command: str | None,
    timeout: int,
    interactive: bool,
    thread_id: str | None,
) -> None:
    """Execute a plan via LangGraph (checkpointed, interruptible)."""
    from metabolon.sortase.graph import run

    result = run(
        plan_file=plan_file,
        project_dir=project_dir,
        serial=serial,
        backend=backend,
        test_command=test_command,
        timeout=timeout,
        interactive=interactive,
        thread_id=thread_id,
    )

    if result.get("status") == "paused":
        console.print(f"[bold yellow]Paused[/bold yellow] before execution (thread: {result['thread_id']})")
        console.print("\nRouting decisions:")
        for d in result.get("route_decisions", []):
            console.print(f"  {d['task']}: {d['tool']} ({d['reason']})")
        console.print(f"\nResume: sortase graph-resume {result['thread_id']}")
        console.print(f"Abort:  sortase graph-resume {result['thread_id']} --reject")
        return

    for r in result.get("results", []):
        status = "ok" if r.get("success") else "failed"
        console.print(f"{r['task_name']}: {r['tool']} [{status}]")

    for issue in result.get("validation_issues", []):
        console.print(f"- {issue['severity']}: {issue['message']}")

    console.print(f"Success={result.get('success', False)}")


@main.command("graph-resume")
@click.argument("thread_id")
@click.option("--reject", is_flag=True, help="Abort the paused run.")
def graph_resume_command(thread_id: str, reject: bool) -> None:
    """Resume a paused graph-exec run."""
    from metabolon.sortase.graph import review_and_continue

    result = review_and_continue(thread_id=thread_id, approve=not reject)

    if reject:
        console.print("[bold red]Aborted.[/bold red]")
        return

    for r in result.get("results", []):
        status = "ok" if r.get("success") else "failed"
        console.print(f"{r['task_name']}: {r['tool']} [{status}]")

    console.print(f"Success={result.get('success', False)}")


@main.command()
@click.argument("description")
@click.option("-v", "--verbose", is_flag=True)
def route(description: str, verbose: bool) -> None:
    """Dry-run task routing."""

    decision = route_description(description)
    console.print(f"{decision.tool} -> {decision.reason}")

    if verbose:
        from metabolon.sortase.executor import TOOL_COMMANDS
        builder = TOOL_COMMANDS.get(decision.tool)
        if builder:
            cmd = builder(Path("."), "<prompt>")
            console.print(f"  command: {' '.join(cmd)}")
        else:
            console.print(f"  (no command template for {decision.tool})")


@main.command()
@click.option("--stats", is_flag=True, help="Show aggregate statistics.")
@click.option("--prune", default=0, type=int, help="Keep only last N entries (0 = no pruning).")
@click.option("--export", "export_path", default=None, type=click.Path(path_type=Path), help="Export log as CSV.")
@click.option("--last", "last_n", default=10, show_default=True, type=int, help="Show last N entries.")
def log(stats: bool, prune: int, export_path: Path | None, last_n: int) -> None:
    """Show execution history."""

    entries = read_logs()
    if stats:
        payload = aggregate_stats(entries)
        table = Table(title="sortase stats")
        table.add_column("Tool")
        table.add_column("Runs")
        table.add_column("Success rate")
        table.add_column("Avg (s)")
        table.add_column("P50 (s)")
        table.add_column("P90 (s)")
        table.add_column("24h")
        table.add_column("Coaching")
        for tool, details in sorted(payload["per_tool"].items()):
            table.add_row(
                tool,
                str(details["runs"]),
                str(details["success_rate"]),
                str(details["avg_duration_s"]),
                str(details["p50_duration_s"]),
                str(details["p90_duration_s"]),
                str(details["last_24h"]),
                str(details["coaching_triggers"]),
            )
        console.print(table)
        console.print(f"Failure reasons: {payload['failure_reasons']}")
        console.print(f"Fallback frequency: {payload['fallback_frequency']}")
        # Show coaching notes count
        coaching_path = Path.home() / "epigenome" / "marks" / "feedback_glm_coaching.md"
        if coaching_path.exists():
            content = coaching_path.read_text(encoding="utf-8")
            pattern_count = content.count("### ")
            console.print(f"Coaching patterns: {pattern_count}")
        return

    if export_path:
        import csv
        with open(export_path, "w", newline="") as f:
            if entries:
                writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                writer.writeheader()
                writer.writerows(entries)
        console.print(f"Exported {len(entries)} entries to {export_path}")
        return

    table = Table(title="sortase log")
    table.add_column("Timestamp")
    table.add_column("Plan")
    table.add_column("Project")
    table.add_column("Tool")
    table.add_column("Success")
    for entry in entries[-last_n:]:
        table.add_row(
            entry.get("timestamp", ""),
            entry.get("plan", ""),
            entry.get("project", ""),
            entry.get("tool", ""),
            str(entry.get("success", "")),
        )
    console.print(table)

    if prune > 0 and len(entries) > prune:
        from metabolon.sortase.logger import resolve_log_path
        log_path = resolve_log_path()
        kept = entries[-prune:]
        log_path.write_text(
            "\n".join(json.dumps(e) for e in kept) + "\n",
            encoding="utf-8",
        )
        console.print(f"Pruned: kept {prune} of {len(entries)} entries")


@main.command()
def status() -> None:
    """Show currently running executions."""

    entries = list_running()
    if not entries:
        console.print("No running executions.")
        return

    table = Table(title="sortase status")
    table.add_column("Task")
    table.add_column("Tool")
    table.add_column("Project")
    table.add_column("Started")
    table.add_column("Running for")
    for entry in entries:
        started_str = entry.get("started_at", "")
        if started_str:
            started = datetime.fromisoformat(started_str)
            elapsed = datetime.now() - started
            elapsed_str = f"{elapsed.total_seconds():.0f}s"
        else:
            elapsed_str = ""
        table.add_row(
            entry.get("task_name", ""),
            entry.get("tool", ""),
            entry.get("project_dir", ""),
            started_str,
            elapsed_str,
        )
    console.print(table)


@main.command()
@click.argument("watch_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("-p", "--project-dir", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("-b", "--backend", type=click.Choice(["gemini", "codex", "goose", "opencode", "cc-glm", "droid", "crush"]))
@click.option("--interval", default=30, show_default=True, type=int, help="Poll interval in seconds.")
@click.option("--timeout", default=600, show_default=True, type=int)
def watch(watch_dir: Path, project_dir: Path, backend: str | None, interval: int, timeout: int) -> None:
    """Watch a directory for new plan files and auto-execute them."""

    running_dir = watch_dir / "running"
    done_dir = watch_dir / "done"
    failed_dir = watch_dir / "failed"
    for d in (running_dir, done_dir, failed_dir):
        d.mkdir(exist_ok=True)

    seen: set[str] = set()
    done_count = 0
    failed_count = 0

    def _discover() -> list[Path]:
        files: list[Path] = []
        files.extend(watch_dir.glob("*.md"))
        files.extend(watch_dir.glob("*.yaml"))
        return [f for f in files if f.name not in seen]

    def _status_line(pending: int) -> str:
        ts = datetime.now().strftime("%H:%M:%S")
        return f"[{ts}] watching {watch_dir} ({pending} pending, {done_count} done, {failed_count} failed)"

    console.print(f"Watching {watch_dir} for plan files (interval={interval}s, timeout={timeout}s)")
    console.print("Press Ctrl+C to stop.\n")

    try:
        while True:
            new_files = _discover()
            pending = len(new_files)
            console.print(_status_line(pending))

            for plan_file in new_files:
                seen.add(plan_file.name)
                dest = running_dir / plan_file.name
                shutil.move(str(plan_file), str(dest))
                console.print(f"  [bold]Executing[/bold] {plan_file.name} ...")

                try:
                    tasks = decompose_plan(dest, smart=False)
                    tool_by_task = {
                        task.name: route_description(task.description, forced_backend=backend).tool
                        for task in tasks
                    }
                    results = asyncio.run(
                        execute_tasks(tasks, project_dir, tool_by_task, serial=False, timeout_sec=timeout, verbose=False)
                    )
                    success = all(r.success for r in results)
                    final_dest = done_dir / dest.name if success else failed_dir / dest.name
                    shutil.move(str(dest), str(final_dest))
                    if success:
                        done_count += 1
                        console.print(f"  [green]Done[/green] {plan_file.name} -> done/")
                    else:
                        failed_count += 1
                        for r in results:
                            if not r.success:
                                console.print(f"    [red]Failed[/red] {r.task_name}: {r.tool}")
                        console.print(f"  [red]Failed[/red] {plan_file.name} -> failed/")
                except Exception as exc:
                    final_dest = failed_dir / dest.name
                    shutil.move(str(dest), str(final_dest))
                    failed_count += 1
                    console.print(f"  [red]Error[/red] {plan_file.name}: {exc} -> failed/")

            time.sleep(interval)
    except KeyboardInterrupt:
        console.print(f"\n[bold]Stopped.[/bold] Summary: {done_count} done, {failed_count} failed")


@main.command()
def version() -> None:
    """Show sortase version."""
    from importlib.metadata import version as pkg_version

    console.print(f"sortase {pkg_version('sortase')}")


if __name__ == "__main__":
    main()
