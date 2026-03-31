from __future__ import annotations

"""Show what a completed sortase task changed via git history."""


import re
import subprocess
from pathlib import Path


def find_task_commit(task_name: str, project_dir: Path) -> str | None:
    """Search git log for a translocon/sortase commit matching *task_name*.

    Commits authored by sortase use messages like
    ``sortase: <plan_name>`` or ``translocon: <description>``.
    Returns the short commit hash or ``None`` if no match is found.
    """
    result = subprocess.run(
        ["git", "log", "--all", "--format=%h %s", "--", "."],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    task_lower = task_name.lower()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split(" ", 1)
        if len(parts) < 2:
            continue
        commit_hash, message = parts
        # Match sortase or translocon commit prefixes, or any commit whose
        # message body contains the task name.
        if message.lower().startswith(("sortase:", "translocon:")) and task_lower in message.lower():
            return commit_hash
        if task_lower in message.lower():
            return commit_hash

    return None


def get_task_diff(commit_hash: str, project_dir: Path) -> str:
    """Return the full diff for *commit_hash*."""
    result = subprocess.run(
        ["git", "show", "--format=", "--patch", commit_hash],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def format_diff_summary(diff: str) -> str:
    """Summarise a unified diff: files changed, lines added/removed.

    Returns a human-readable multi-line string.
    """
    if not diff.strip():
        return "No changes."

    files: dict[str, dict[str, int]] = {}
    current_file = ""

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            match = re.search(r"b/(.+)$", line)
            if match:
                current_file = match.group(1)
                files.setdefault(current_file, {"added": 0, "removed": 0})
        elif current_file:
            if line.startswith("+") and not line.startswith("+++"):
                files[current_file]["added"] += 1
            elif line.startswith("-") and not line.startswith("---"):
                files[current_file]["removed"] += 1

    if not files:
        return "No changes."

    total_added = sum(f["added"] for f in files.values())
    total_removed = sum(f["removed"] for f in files.values())
    lines: list[str] = [
        f"Files changed: {len(files)}",
        f"Lines: +{total_added} / -{total_removed}",
        "",
    ]
    for filepath, stats in sorted(files.items()):
        lines.append(f"  {filepath}  +{stats['added']} / -{stats['removed']}")
    return "\n".join(lines)
