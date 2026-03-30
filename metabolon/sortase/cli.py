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

from metabolon.sortase.coaching_cli import coaching as coaching_group
from metabolon.sortase.decompose import decompose_plan
from metabolon.sortase.diff_viewer import find_task_commit, format_diff_summary, get_task_diff
from metabolon.sortase.linter import lint_plan as structured_lint, format_lint_report
from metabolon.sortase.executor import execute_tasks, list_running, summarize_cost_estimates
from metabolon.sortase.history import build_history_table, display_history
from metabolon.sortase.logger import aggregate_stats, analyze_logs, append_log, read_logs, resolve_log_path
from metabolon.sortase.compare import compare_sessions, format_compare_report
from metabolon.sortase.overnight import compute_overnight_stats, format_overnight_report, load_overnight_entries
from metabolon.sortase.router import route_description
from metabolon.sortase.validator import validate_execution

console = Console()


@click.group()
def main() -> None:
    """sortase orchestrates free AI coding tools."""


main.add_command(coaching_group, "coaching")


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
@click.option("--worktree", is_flag=True, help="Execute each task in an isolated git worktree.")
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
    worktree: bool,
) -> None:
    """Execute a plan file against a project directory."""

    tasks = decompose_plan(plan_file, smart=decompose)
    tool_by_task = {task.name: route_description(task.description, forced_backend=backend).tool for task in tasks}

    if not quiet:
        console.print(f"[bold]Executing[/bold] {len(tasks)} task(s) in {project_dir}")
    results = asyncio.run(execute_tasks(tasks, project_dir, tool_by_task, serial=serial, timeout_sec=timeout, verbose=verbose, dry_run=dry_run, max_retries=retries, coaching=not no_coaching, worktree=worktree))

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

            warning_placeholder_files = {
                issue.message.split(" in ", 1)[-1]
                for issue in validation_issues
                if issue.check == "placeholder-scan" and issue.severity == "warning"
            }
            if warning_placeholder_files:
                console.print(
                    f"[dim]Warning: {len(warning_placeholder_files)} placeholder marker file(s) "
                    f"found (not blocking).[/dim]"
                )

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
        "fallback_chain": [step.to_dict() for result in results for step in result.fallback_chain],
        "duration_s": duration_s,
        "success": all(result.success for result in results) and not any(issue.severity == "error" for issue in validation_issues),
        "failure_reason": next((issue.check for issue in validation_issues if issue.severity == "error"), None),
        "files_changed": changed_files,
        "tests_passed": 0 if any(issue.check == "tests" for issue in validation_issues) else 1,
        "cost_estimate": summarize_cost_estimates([r.cost_estimate for r in results if r.cost_estimate]),
    }
    append_log(entry)
    if json_out:
        import json as _json
        task_payload = [
            {
                "name": result.task_name,
                "tool": result.tool,
                "prompt_file": result.prompt_file,
                "success": result.success,
                "duration_s": sum(attempt.duration_s for attempt in result.attempts),
                "attempt_count": len(result.attempts),
                "fallbacks": result.fallbacks,
                "fallback_count": len(result.fallbacks),
                "fallback_chain": [step.to_dict() for step in result.fallback_chain],
                "failure_reason": next(
                    (
                        attempt.failure_reason
                        for attempt in reversed(result.attempts)
                        if attempt.failure_reason is not None
                    ),
                    None,
                ),
                "cost_estimate": result.cost_estimate or "N/A",
                "output": result.output,
                "attempts": [
                    {
                        "tool": attempt.tool,
                        "exit_code": attempt.exit_code,
                        "duration_s": attempt.duration_s,
                        "failure_reason": attempt.failure_reason,
                        "cost_estimate": attempt.cost_estimate or "N/A",
                        "output": attempt.output,
                    }
                    for attempt in result.attempts
                ],
            }
            for result in results
        ]
        validation_payload = [
            {"severity": issue.severity, "check": issue.check, "message": issue.message}
            for issue in validation_issues
        ]
        output = {
            "schema_version": 2,
            "success": entry["success"],
            "timestamp": entry["timestamp"],
            "plan": str(plan_file),
            "project_dir": str(project_dir),
            "requested_backend": backend,
            "resolved_backend": entry["tool"],
            "task_count": len(tasks),
            "tasks": task_payload,
            "files_changed": changed_file_list,
            "files_changed_count": changed_files,
            "validation_issues": validation_payload,
            "validation_issue_count": len(validation_payload),
            "failure_reason": entry["failure_reason"],
            "tests_passed": bool(entry["tests_passed"]),
            "cost_estimate": entry["cost_estimate"],
            "duration_s": entry["duration_s"],
            "total_duration_s": entry["duration_s"],
        }
        console.file.write(f"{_json.dumps(output, indent=2)}\n")
    elif not quiet:
        console.print(f"Logged execution to history. Success={entry['success']}")
    if dry_run and not quiet:
        console.print("[bold]Dry run complete — no files were changed.[/bold]")
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

    if entry["success"] and not dry_run:
        done_dir = plan_file.parent / "done"
        done_dir.mkdir(exist_ok=True)
        archive_dest = done_dir / plan_file.name
        shutil.move(str(plan_file), str(archive_dest))
        if not quiet:
            console.print(f"[dim]Archived plan to {archive_dest}[/dim]")


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
@click.option("--log", "log_path", default=None, type=click.Path(path_type=Path), help="Path to log.jsonl (default: sortase default).")
@click.option("--coaching", "coaching_path", default=None, type=click.Path(path_type=Path), help="Path to coaching notes file.")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON.")
def analyze(log_path: Path | None, coaching_path: Path | None, json_output: bool) -> None:
    """Analyze execution logs for patterns and coaching effectiveness."""

    result = analyze_logs(log_path=log_path, coaching_path=coaching_path)

    if result["total_entries"] == 0:
        console.print("No log entries found.")
        return

    if json_output:
        console.print(json.dumps(result, indent=2, sort_keys=True))
        return

    table = Table(title="Success Rate by Backend")
    table.add_column("Backend")
    table.add_column("Rate")
    table.add_column("Entries", justify="right")
    for tool, rate in sorted(result["success_rate_by_backend"].items()):
        table.add_row(tool, f"{rate:.1%}", str(result["entries_by_backend"].get(tool, 0)))
    console.print(table)

    table = Table(title="Success Rate by Hour")
    table.add_column("Hour")
    table.add_column("Rate")
    table.add_column("Entries", justify="right")
    for hour, rate in result["success_rate_by_hour"].items():
        table.add_row(hour, f"{rate:.1%}", str(result["entries_by_hour"].get(hour, 0)))
    console.print(table)

    table = Table(title="Avg Duration by Plan Complexity (file count)")
    table.add_column("Files", justify="right")
    table.add_column("Avg Duration (s)", justify="right")
    for file_count, avg_duration in result["avg_duration_by_plan_complexity"].items():
        table.add_row(str(file_count), f"{avg_duration:.1f}")
    console.print(table)

    if result["failure_reasons"]:
        table = Table(title="Failure Reasons")
        table.add_column("Reason")
        table.add_column("Count", justify="right")
        for reason, count in result["failure_reasons"].items():
            table.add_row(reason, str(count))
        console.print(table)

    coaching_gap = result["coaching_gap"]
    coaching_coverage = result["coaching_coverage"]
    if coaching_gap is not None and coaching_coverage is not None:
        console.print(
            "Coaching coverage gap: "
            f"{coaching_gap:.1%} of failures occurred before a relevant coaching note was added "
            f"({result['coaching_failures_without_prior_note']}/{result['coaching_failures_without_prior_note'] + result['coaching_failures_with_prior_note']})."
        )
        console.print(
            "Coaching coverage: "
            f"{coaching_coverage:.1%} had a relevant coaching note in place first."
        )
    else:
        console.print("Coaching coverage: N/A (no failures)")


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
@click.option("--max-concurrent", default=2, show_default=True, type=click.IntRange(min=1), help="Max parallel executions.")
@click.option("--log-file", default=None, type=click.Path(path_type=Path), help="Write results JSONL for morning review.")
def watch(
    watch_dir: Path,
    project_dir: Path,
    backend: str | None,
    interval: int,
    timeout: int,
    max_concurrent: int,
    log_file: Path | None,
) -> None:
    """Watch a directory for new plan files and auto-execute them."""

    running_dir = watch_dir / "running"
    done_dir = watch_dir / "done"
    for d in (running_dir, done_dir):
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

    def _append_watch_log(entry: dict) -> None:
        if log_file is None:
            return
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")

    console.print(f"Watching {watch_dir} for plan files (interval={interval}s, timeout={timeout}s)")
    if max_concurrent != 1:
        console.print(f"Max concurrent: {max_concurrent}")
    console.print("Press Ctrl+C to stop.\n")

    semaphore = asyncio.Semaphore(max_concurrent)

    async def _execute_plan(plan_name: str, plan_path: Path) -> None:
        nonlocal done_count, failed_count
        async with semaphore:
            dest = running_dir / plan_name
            shutil.move(str(plan_path), str(dest))
            console.print(f"  [bold]Executing[/bold] {plan_name} ...")
            start = time.monotonic()
            duration_s = 0.0
            success = False
            error_msg: str | None = None

            try:
                tasks = decompose_plan(dest, smart=False)
                tool_by_task = {
                    task.name: route_description(task.description, forced_backend=backend).tool
                    for task in tasks
                }
                results = await execute_tasks(
                    tasks, project_dir, tool_by_task,
                    serial=False, timeout_sec=timeout, verbose=False,
                )
                success = all(r.success for r in results)
            except Exception as exc:
                error_msg = str(exc)
            finally:
                duration_s = round(time.monotonic() - start, 1)
                shutil.move(str(dest), str(done_dir / dest.name))

            result_label = "success" if success else "fail"
            console.print(f"  TASK: {plan_name} | RESULT: {result_label} | DURATION: {duration_s}s")

            if success:
                done_count += 1
            else:
                failed_count += 1

            log_entry: dict = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "plan": plan_name,
                "success": success,
                "duration_s": duration_s,
            }
            if error_msg is not None:
                log_entry["error"] = error_msg
            _append_watch_log(log_entry)

    try:
        while True:
            new_files = _discover()
            pending = len(new_files)
            console.print(_status_line(pending))

            if new_files:
                plan_coros = []
                for plan_file in new_files:
                    seen.add(plan_file.name)
                    plan_coros.append(_execute_plan(plan_file.name, plan_file))

                async def _run_batch() -> None:
                    await asyncio.gather(*plan_coros)

                asyncio.run(_run_batch())

            time.sleep(interval)
    except KeyboardInterrupt:
        console.print(f"\n[bold]Stopped.[/bold] Summary: {done_count} done, {failed_count} failed")


@main.command()
@click.argument("plan_file", type=click.Path(exists=True, path_type=Path))
def lint(plan_file: Path) -> None:
    """Lint a plan file for common issues."""

    plan_text = plan_file.read_text(encoding="utf-8")
    issues = structured_lint(plan_text)

    has_errors = any(issue.severity == "error" for issue in issues)
    report = format_lint_report(issues)
    console.print(report)

    if has_errors:
        raise SystemExit(1)


@main.command()
@click.option("--last", "last_n", default=20, show_default=True, type=int, help="Number of recent dispatches to show.")
def history(last_n: int) -> None:
    """Show recent dispatch history in a rich table."""

    entries = read_logs()
    if not entries:
        console.print("[dim]No dispatch history found.[/dim]")
        return
    console.print(build_history_table(entries, limit=last_n))


@main.command()
def version() -> None:
    """Show sortase version."""
    from importlib.metadata import version as pkg_version

    console.print(f"sortase {pkg_version('metabolon')}")


@main.command()
@click.option("--output", "output_path", default=Path.home() / "tmp" / "sortase-dashboard.html", type=click.Path(path_type=Path), help="Output HTML path.")
@click.option("--log", "log_path", default=None, type=click.Path(path_type=Path), help="Path to log.jsonl (default: sortase default).")
def dashboard(output_path: Path, log_path: Path | None) -> None:
    """Generate a static HTML dashboard from execution logs."""

    entries = read_logs(log_path)
    if not entries:
        console.print("No log entries found.")
        return

    entries.sort(key=lambda e: e.get("timestamp", ""))

    total = len(entries)
    successes = sum(1 for e in entries if e.get("success"))
    failures = total - successes
    overall_rate = successes / total if total else 0

    # --- Success rate by date (bar chart) ---
    from collections import Counter, defaultdict

    date_buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"ok": 0, "fail": 0})
    for entry in entries:
        ts = entry.get("timestamp", "")
        date_key = ts[:10] if ts else "unknown"
        if entry.get("success"):
            date_buckets[date_key]["ok"] += 1
        else:
            date_buckets[date_key]["fail"] += 1
    sorted_dates = sorted(date_buckets.keys())
    max_per_date = max((b["ok"] + b["fail"]) for b in date_buckets.values()) if date_buckets else 1

    bar_chart_svg_parts: list[str] = []
    bar_group_width = 50
    bar_area_left = 40
    bar_chart_width = bar_area_left + len(sorted_dates) * bar_group_width + 20
    bar_chart_height = 200

    for idx, date_key in enumerate(sorted_dates):
        bucket = date_buckets[date_key]
        x_base = bar_area_left + idx * bar_group_width
        ok_height = int((bucket["ok"] / max_per_date) * (bar_chart_height - 30)) if max_per_date else 0
        fail_height = int((bucket["fail"] / max_per_date) * (bar_chart_height - 30)) if max_per_date else 0
        y_ok = bar_chart_height - 20 - ok_height
        y_fail = y_ok - fail_height
        if ok_height > 0:
            bar_chart_svg_parts.append(f'<rect x="{x_base + 5}" y="{y_ok}" width="18" height="{ok_height}" fill="#4ade80" rx="2"><title>{date_key}: {bucket["ok"]} ok</title></rect>')
        if fail_height > 0:
            bar_chart_svg_parts.append(f'<rect x="{x_base + 25}" y="{y_fail}" width="18" height="{fail_height}" fill="#f87171" rx="2"><title>{date_key}: {bucket["fail"]} fail</title></rect>')
        label = date_key[5:]  # MM-DD
        bar_chart_svg_parts.append(f'<text x="{x_base + 24}" y="{bar_chart_height - 4}" text-anchor="middle" font-size="9" fill="#94a3b8">{label}</text>')

    bar_chart_svg = (
        f'<svg viewBox="0 0 {bar_chart_width} {bar_chart_height}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="100%" height="100%" fill="#1e293b" rx="8"/>'
        f'<line x1="{bar_area_left}" y1="10" x2="{bar_area_left}" y2="{bar_chart_height - 20}" stroke="#475569" stroke-width="1"/>'
        f'<line x1="{bar_area_left}" y1="{bar_chart_height - 20}" x2="{bar_chart_width - 10}" y2="{bar_chart_height - 20}" stroke="#475569" stroke-width="1"/>'
        + "".join(bar_chart_svg_parts)
        + "</svg>"
    )

    # --- Failure reasons (pie chart) ---
    failure_reasons: dict[str, int] = Counter()
    for entry in entries:
        if not entry.get("success"):
            reason = entry.get("failure_reason") or "unknown"
            failure_reasons[reason] += 1

    pie_colors = ["#f87171", "#fb923c", "#fbbf24", "#a78bfa", "#60a5fa", "#34d399", "#f472b6", "#e879f9"]
    pie_center_x, pie_center_y, pie_radius = 120, 120, 100

    if failure_reasons:
        total_failures = sum(failure_reasons.values())
        pie_parts: list[str] = []
        legend_parts: list[str] = []
        cumulative_angle = 0
        for color_idx, (reason, count) in enumerate(failure_reasons.most_common()):
            slice_angle = (count / total_failures) * 360
            start_rad = cumulative_angle * 3.14159265 / 180
            end_rad = (cumulative_angle + slice_angle) * 3.14159265 / 180
            x1 = pie_center_x + pie_radius * __import__("math").cos(start_rad)
            y1 = pie_center_y + pie_radius * __import__("math").sin(start_rad)
            x2 = pie_center_x + pie_radius * __import__("math").cos(end_rad)
            y2 = pie_center_y + pie_radius * __import__("math").sin(end_rad)
            large_arc = 1 if slice_angle > 180 else 0
            color = pie_colors[color_idx % len(pie_colors)]
            if slice_angle >= 359.9:
                pie_parts.append(f'<circle cx="{pie_center_x}" cy="{pie_center_y}" r="{pie_radius}" fill="{color}"/>')
            else:
                pie_parts.append(
                    f'<path d="M{pie_center_x},{pie_center_y} L{x1:.1f},{y1:.1f} A{pie_radius},{pie_radius} 0 {large_arc},1 {x2:.1f},{y2:.1f} Z" fill="{color}"/>'
                )
            pct = count / total_failures * 100
            legend_parts.append(f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;"><span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:{color};"></span><span style="color:#cbd5e1;">{reason} ({count}, {pct:.0f}%)</span></div>')
            cumulative_angle += slice_angle
        pie_svg = f'<svg viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#1e293b" rx="8"/>{"".join(pie_parts)}</svg>'
        pie_legend = "".join(legend_parts)
    else:
        pie_svg = '<svg viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#1e293b" rx="8"/><text x="120" y="125" text-anchor="middle" fill="#94a3b8" font-size="14">No failures</text></svg>'
        pie_legend = '<div style="color:#94a3b8;">No failures recorded.</div>'

    # --- Backend distribution (horizontal bar chart) ---
    backend_counts: dict[str, int] = Counter(e.get("tool", "unknown") for e in entries)
    max_backend = max(backend_counts.values()) if backend_counts else 1
    backend_colors = ["#60a5fa", "#a78bfa", "#34d399", "#fbbf24", "#fb923c", "#f87171", "#e879f9", "#f472b6"]

    backend_bar_parts: list[str] = []
    backend_chart_height = max(len(backend_counts) * 36 + 20, 60)
    for idx, (backend_name, count) in enumerate(backend_counts.most_common()):
        y = 10 + idx * 36
        bar_width = int((count / max_backend) * 250) if max_backend else 0
        color = backend_colors[idx % len(backend_colors)]
        backend_bar_parts.append(f'<text x="0" y="{y + 14}" font-size="12" fill="#cbd5e1">{backend_name}</text>')
        backend_bar_parts.append(f'<rect x="80" y="{y}" width="{bar_width}" height="20" fill="{color}" rx="3"><title>{backend_name}: {count} runs</title></rect>')
        backend_bar_parts.append(f'<text x="{85 + bar_width}" y="{y + 14}" font-size="11" fill="#94a3b8">{count}</text>')

    backend_svg = (
        f'<svg viewBox="0 0 380 {backend_chart_height}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="100%" height="100%" fill="#1e293b" rx="8"/>'
        + "".join(backend_bar_parts)
        + "</svg>"
    )

    # --- Average duration trend (line chart) ---
    duration_by_date: dict[str, list[float]] = defaultdict(list)
    for entry in entries:
        ts = entry.get("timestamp", "")
        date_key = ts[:10] if ts else "unknown"
        dur = entry.get("duration_s", 0)
        if dur is not None:
            duration_by_date[date_key].append(dur)

    avg_duration_by_date = {d: sum(v) / len(v) for d, v in sorted(duration_by_date.items())}
    trend_dates = sorted(avg_duration_by_date.keys())
    trend_chart_width = max(bar_area_left + len(trend_dates) * bar_group_width + 20, 300)
    trend_chart_height = 180
    trend_area_top = 10
    trend_area_bottom = trend_chart_height - 25

    if avg_duration_by_date:
        max_dur = max(avg_duration_by_date.values())
        min_dur = min(avg_duration_by_date.values())
        dur_range = max_dur - min_dur if max_dur != min_dur else 1
        line_points: list[str] = []
        dot_parts: list[str] = []
        for idx, date_key in enumerate(trend_dates):
            avg = avg_duration_by_date[date_key]
            x = bar_area_left + idx * bar_group_width + 24
            y = trend_area_bottom - int(((avg - min_dur) / dur_range) * (trend_area_bottom - trend_area_top - 10))
            line_points.append(f"{x},{y}")
            dot_parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#38bdf8"><title>{date_key}: {avg:.1f}s avg</title></circle>')
            label = date_key[5:]
            dot_parts.append(f'<text x="{x}" y="{trend_chart_height - 6}" text-anchor="middle" font-size="9" fill="#94a3b8">{label}</text>')

        polyline = f'<polyline points="{" ".join(line_points)}" fill="none" stroke="#38bdf8" stroke-width="2"/>' if len(line_points) > 1 else ""
        trend_svg = (
            f'<svg viewBox="0 0 {trend_chart_width} {trend_chart_height}" xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="100%" height="100%" fill="#1e293b" rx="8"/>'
            f'<line x1="{bar_area_left}" y1="{trend_area_top}" x2="{bar_area_left}" y2="{trend_area_bottom}" stroke="#475569" stroke-width="1"/>'
            f'<line x1="{bar_area_left}" y1="{trend_area_bottom}" x2="{trend_chart_width - 10}" y2="{trend_area_bottom}" stroke="#475569" stroke-width="1"/>'
            f'<text x="{bar_area_left - 5}" y="{trend_area_top + 5}" text-anchor="end" font-size="9" fill="#94a3b8">{max_dur:.0f}s</text>'
            f'<text x="{bar_area_left - 5}" y="{trend_area_bottom}" text-anchor="end" font-size="9" fill="#94a3b8">{min_dur:.0f}s</text>'
            + polyline
            + "".join(dot_parts)
            + "</svg>"
        )
    else:
        trend_svg = '<svg viewBox="0 0 300 180" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#1e293b" rx="8"/><text x="150" y="95" text-anchor="middle" fill="#94a3b8">No duration data</text></svg>'

    # --- Compose HTML ---
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>sortase dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; padding: 24px; }}
  h1 {{ font-size: 24px; font-weight: 700; margin-bottom: 8px; }}
  .subtitle {{ color: #94a3b8; font-size: 14px; margin-bottom: 24px; }}
  .summary {{ display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap; }}
  .card {{ background: #1e293b; border-radius: 12px; padding: 20px 24px; min-width: 160px; flex: 1; }}
  .card .label {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }}
  .card .value {{ font-size: 28px; font-weight: 700; }}
  .card .value.green {{ color: #4ade80; }}
  .card .value.red {{ color: #f87171; }}
  .card .value.blue {{ color: #60a5fa; }}
  .charts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
  .chart-box {{ background: #1e293b; border-radius: 12px; padding: 16px; overflow: hidden; }}
  .chart-box h2 {{ font-size: 14px; color: #94a3b8; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
  .chart-box svg {{ width: 100%; height: auto; }}
  .full-width {{ grid-column: 1 / -1; }}
  .pie-row {{ display: flex; align-items: center; gap: 20px; }}
  .pie-row svg {{ flex-shrink: 0; width: 240px; height: 240px; }}
  .legend {{ flex: 1; }}
  .footer {{ margin-top: 24px; color: #475569; font-size: 12px; text-align: center; }}
</style>
</head>
<body>
<h1>sortase dashboard</h1>
<p class="subtitle">{total} executions &middot; generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>

<div class="summary">
  <div class="card">
    <div class="label">Total Runs</div>
    <div class="value blue">{total}</div>
  </div>
  <div class="card">
    <div class="label">Successes</div>
    <div class="value green">{successes}</div>
  </div>
  <div class="card">
    <div class="label">Failures</div>
    <div class="value red">{failures}</div>
  </div>
  <div class="card">
    <div class="label">Success Rate</div>
    <div class="value green">{overall_rate:.1%}</div>
  </div>
</div>

<div class="charts">
  <div class="chart-box full-width">
    <h2>Success / Failure Over Time</h2>
    {bar_chart_svg}
  </div>

  <div class="chart-box">
    <h2>Failure Reasons</h2>
    <div class="pie-row">
      {pie_svg}
      <div class="legend">{pie_legend}</div>
    </div>
  </div>

  <div class="chart-box">
    <h2>Backend Distribution</h2>
    {backend_svg}
  </div>

  <div class="chart-box full-width">
    <h2>Average Duration Trend</h2>
    {trend_svg}
  </div>
</div>

<div class="footer">sortase dashboard &middot; pure HTML+CSS &middot; no JS dependencies</div>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    console.print(f"Dashboard written to {output_path} ({total} entries)")


@main.command()
@click.option("--log", "log_path", default=None, type=click.Path(path_type=Path), help="Path to log.jsonl (default: sortase default).")
@click.option("--hours", default=8, show_default=True, type=int, help="Look-back window in hours.")
@click.option("--output", "output_path", default=None, type=click.Path(path_type=Path), help="Write report to file instead of stdout.")
def overnight(log_path: Path | None, hours: int, output_path: Path | None) -> None:
    """Generate an overnight session report from execution logs."""

    resolved = resolve_log_path(log_path)
    entries = load_overnight_entries(resolved, since_hours=hours)
    stats = compute_overnight_stats(entries)
    report = format_overnight_report(stats, entries)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        console.print(f"Report written to {output_path}")
    else:
        console.print(report)


@main.command()
@click.argument("task_name")
@click.option("-p", "--project-dir", default=Path("."), type=click.Path(exists=True, file_okay=False, path_type=Path), help="Project directory (default: cwd).")
@click.option("--summary", "show_summary", is_flag=True, help="Show only the summary, not the full diff.")
def diff(task_name: str, project_dir: Path, show_summary: bool) -> None:
    """Show what a completed task changed."""

    commit_hash = find_task_commit(task_name, project_dir)
    if commit_hash is None:
        console.print(f"[yellow]No commit found matching '{task_name}'[/yellow]")
        raise SystemExit(1)

    full_diff = get_task_diff(commit_hash, project_dir)

    if show_summary:
        console.print(format_diff_summary(full_diff))
    else:
        console.print(format_diff_summary(full_diff))
        console.print()
        console.print(full_diff)


@main.command()
@click.argument("date_a")
@click.argument("date_b")
@click.option("--log", "log_path", default=None, type=click.Path(path_type=Path), help="Path to log.jsonl (default: sortase default).")
def compare(date_a: str, date_b: str, log_path: Path | None) -> None:
    """Compare two overnight sessions (task count, success rate, duration deltas, new failures)."""

    resolved = resolve_log_path(log_path)
    delta = compare_sessions(resolved, date_a, date_b)
    report = format_compare_report(delta)
    console.print(report)


@main.command()
def speed() -> None:
    """Show sortase dispatch throughput metrics."""

    from metabolon.organelles.tachometer import (
        coaching_effectiveness,
        current_rate,
        estimate_completion,
        slowest_recent,
        success_trend,
    )

    rate = current_rate()
    trend = success_trend()
    slowest = slowest_recent(hours=1)
    coaching = coaching_effectiveness()

    console.print(f"[bold]Dispatch Rate:[/bold] {rate:.1f} tasks/hour (last 60 min)")

    console.print(
        f"[bold]Success Trend:[/bold] "
        f"recent ({trend['recent_count']}) {trend['recent_rate']:.1%} vs "
        f"historical ({trend['historical_count']}) {trend['historical_rate']:.1%} "
        f"— {trend['direction']}"
    )

    if slowest:
        console.print(
            f"[bold]Slowest (1h):[/bold] {slowest['plan']} "
            f"({slowest['duration_s']:.1f}s, {slowest['tool']})"
        )
    else:
        console.print("[bold]Slowest (1h):[/bold] no tasks in window")

    console.print(
        f"[bold]Coaching Effectiveness:[/bold] "
        f"failure rate {coaching['before_failure_rate']:.1%} → "
        f"{coaching['after_failure_rate']:.1%} "
        f"({coaching['improvement_pct']:+.1f}pp, "
        f"{coaching['notes_analyzed']} notes over {coaching['total_entries']} entries)"
    )


if __name__ == "__main__":
    main()
