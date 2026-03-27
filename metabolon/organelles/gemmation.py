"""dispatcher — background AI agent job queue (formerly legatus).

Endosymbiosis: Rust binary -> Python organelle.
Manages YAML queue at ~/notes/agent-queue.yaml.
Dispatches detached processes (claude, gemini, codex, opencode).
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

QUEUE_PATH = Path.home() / "notes" / "agent-queue.yaml"
RUNS_DIR = Path.home() / ".cache" / "legatus-runs"
BACKENDS = ("claude", "gemini", "codex", "opencode")


def _load_queue(path: Path | None = None) -> list[dict]:
    p = path or QUEUE_PATH
    if not p.exists():
        return []
    data = yaml.safe_load(p.read_text())
    return data.get("tasks", []) if data else []


def _save_queue(tasks: list[dict], path: Path | None = None) -> None:
    p = path or QUEUE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.dump({"tasks": tasks}, default_flow_style=False, sort_keys=False))


def _find_task(tasks: list[dict], name: str) -> dict:
    for t in tasks:
        if t["name"] == name:
            return t
    raise ValueError(f"Task '{name}' not found. Available: {', '.join(t['name'] for t in tasks)}")


def _output_dir(name: str) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d-%H%M")
    return RUNS_DIR / ts / name


def _log_path(name: str) -> Path:
    return RUNS_DIR / f"hot-{name}.log"


def _full_prompt(task: dict, out_dir: Path) -> str:
    return (
        f"{task['prompt']}\n\n"
        f"## Output Location\n"
        f"Write all output files to: {out_dir}\n"
        f"Create a summary.md with:\n"
        f"- What you did\n"
        f"- Key findings\n"
        f"- Any issues or blockers\n"
        f"- PASS/FAIL status"
    )


def _build_cmd(task: dict, out_dir: Path) -> list[str]:
    home = Path.home()
    prompt = _full_prompt(task, out_dir)
    backend = task.get("backend", "opencode")

    if backend == "claude":
        import shutil

        claude = shutil.which("claude") or str(home / ".local/bin/claude")
        return [claude, "--dangerously-skip-permissions", "-p", prompt]
    elif backend == "gemini":
        return ["gemini", "-p", prompt, "--yolo"]
    elif backend == "codex":
        return [
            "codex",
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "danger-full-access",
            "--full-auto",
            prompt,
        ]
    elif backend == "opencode":
        title = task.get("title") or task["name"]
        return ["opencode", "run", "-m", "opencode/glm-5", "--title", title, prompt]
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _working_dir(task: dict) -> Path:
    wd = task.get("working_dir")
    if wd:
        return Path(os.path.expanduser(wd))
    return Path.home()


def list_tasks(queue_path: Path | None = None) -> str:
    """List all tasks. Returns formatted string."""
    tasks = _load_queue(queue_path)
    if not tasks:
        return "No tasks in queue."

    lines = [f"{'NAME':<25} {'BACKEND':<10} {'STATUS':<10} {'TIMEOUT':<8} SCHEDULE"]
    lines.append("-" * 80)
    for t in tasks:
        status = "hot" if t.get("run_now") else ("+ on" if t.get("enabled", True) else "- off")
        timeout = f"{t['timeout']}s" if t.get("timeout") else "-"
        schedule = t.get("schedule", "-") or "-"
        lines.append(
            f"{t['name']:<25} {t.get('backend', 'opencode'):<10} {status:<10} {timeout:<8} {schedule}"
        )
    return "\n".join(lines)


def run_task(name: str, queue_path: Path | None = None) -> str:
    """Dispatch a task as a detached process. Returns status message."""
    tasks = _load_queue(queue_path)
    task = _find_task(tasks, name)

    out_dir = _output_dir(name)
    out_dir.mkdir(parents=True, exist_ok=True)

    log = _log_path(name)
    log.parent.mkdir(parents=True, exist_ok=True)

    cmd = _build_cmd(task, out_dir)
    cwd = _working_dir(task)

    env = dict(os.environ)
    backend = task.get("backend", "opencode")
    if backend == "claude":
        env["CLAUDECODE"] = ""
    elif backend == "opencode":
        env["OPENCODE_HOME"] = str(Path.home() / ".opencode-lean")

    log_file = open(log, "a")
    child = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=log_file,
        stderr=log_file,
        start_new_session=True,
    )
    log_file.close()  # child inherited the fd; parent can release

    return (
        f"Dispatched '{name}' via {backend} (pid: {child.pid})\n"
        f"  Output: {out_dir}\n"
        f"  Log:    {log}\n"
        f"  Check:  legatus results {name}"
    )


def cancel_task(name: str, queue_path: Path | None = None) -> str:
    """Cancel a task (disable + clear run_now). Returns status."""
    p = queue_path or QUEUE_PATH
    tasks = _load_queue(p)
    task = _find_task(tasks, name)
    task["enabled"] = False
    task["run_now"] = False
    _save_queue(tasks, p)
    return f"Cancelled task '{name}'"


def get_results(name: str | None = None) -> str:
    """Read results for a task, or list all available results."""
    if name:
        # Find latest run dir containing this task
        if not RUNS_DIR.exists():
            return f"No results found for '{name}'."
        date_dirs = sorted(
            (d for d in RUNS_DIR.iterdir() if d.is_dir() and (d / name).exists()),
            key=lambda d: d.name,
        )
        if not date_dirs:
            return f"No results found for '{name}'."
        task_dir = date_dirs[-1] / name
        for fname in ("summary.md", "report.md", "stdout.txt"):
            f = task_dir / fname
            if f.exists():
                content = f.read_text()
                return f"-- results: {name} --\n{content}"
        return f"No results found for '{name}'."

    # List all tasks from latest date dir
    if not RUNS_DIR.exists():
        return "No results found."
    date_dirs = sorted(
        (d for d in RUNS_DIR.iterdir() if d.is_dir() and not d.name.startswith("hot-")),
        key=lambda d: d.name,
        reverse=True,
    )
    if not date_dirs:
        return "No results found."
    latest = date_dirs[0]
    tasks = sorted(d.name for d in latest.iterdir() if d.is_dir())
    if not tasks:
        return "No results found."
    return f"Latest run: {latest.name}\n" + "\n".join(f"  * {t}" for t in tasks)


def _cli() -> None:
    """CLI entry point (drop-in replacement for Rust legatus)."""
    import argparse

    parser = argparse.ArgumentParser(prog="legatus", description="Background AI agent job queue")
    parser.add_argument("--queue", type=Path, default=None)
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list")
    p_run = sub.add_parser("run")
    p_run.add_argument("name")
    p_cancel = sub.add_parser("cancel")
    p_cancel.add_argument("name")
    p_results = sub.add_parser("results")
    p_results.add_argument("name", nargs="?")

    args = parser.parse_args()

    if args.cmd == "list":
        print(list_tasks(args.queue))
    elif args.cmd == "run":
        print(run_task(args.name, args.queue))
    elif args.cmd == "cancel":
        print(cancel_task(args.name, args.queue))
    elif args.cmd == "results":
        print(get_results(args.name))
    else:
        parser.print_help()
