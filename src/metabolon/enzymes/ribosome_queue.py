"""ribosome_queue — MCP tool for managing the ribosome task queue.

Actions: list|add|remove|status|complete|fail

The queue lives at ~/germline/loci/translation-queue.md and uses markdown
checkbox syntax:

    - [ ] `ribosome [ID] ...`   — pending
    - [x] ...                   — completed
    - [!] ...                   — failed
"""

import fcntl
import os
import re
from pathlib import Path
from typing import Any

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations
from pydantic import Field

from metabolon.morphology import EffectorResult, Secretion

QUEUE_PATH = Path(os.path.expanduser("~/germline/loci/translation-queue.md"))

# Regex that matches a queue entry line.
# Captures: checkbox state ([ ], [x], [!]), task_id, optional tags, the rest.
_ENTRY_RE = re.compile(
    r"^-\s*\[(?P<state>[ x!])\]\s*`?ribosome\s+\[(?P<task_id>[^\]]+)\]"
    r"(?:\s+\[(?P<tags>[^\]]+)\])?"
    r"\s*(?P<rest>.*?)`?\s*$",
)

_PENDING_HEADER = "### Pending"


class QueueResult(Secretion):
    """Structured result for ribosome-queue operations."""

    output: str
    data: dict[str, Any] = Field(default_factory=dict)


# ── helpers ──────────────────────────────────────────────────────────────────


def _read_queue(path: Path) -> list[str]:
    """Return all lines of the queue file."""
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines(True)


def _write_queue(path: Path, lines: list[str]) -> None:
    """Write lines back to the queue file under an fcntl lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, "".join(lines).encode("utf-8"))
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _find_pending_section(lines: list[str]) -> int:
    """Return the index of the ``### Pending`` header line."""
    for i, line in enumerate(lines):
        if line.strip() == _PENDING_HEADER:
            return i
    return -1


def _parse_entries(lines: list[str]) -> list[dict[str, Any]]:
    """Parse all queue entries from *lines*, returning dicts with keys
    ``line_idx``, ``state``, ``task_id``, ``tags``, ``prompt``, ``raw``."""
    entries: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        m = _ENTRY_RE.match(line.strip())
        if m:
            state_char = m.group("state")
            state = {" ": "pending", "x": "completed", "!": "failed"}.get(state_char, "pending")
            tags = m.group("tags") or ""
            rest = m.group("rest") or ""
            # Extract --provider, --max-turns, and the prompt from rest
            provider_match = re.search(r"--provider\s+(\S+)", rest)
            turns_match = re.search(r"--max-turns\s+(\d+)", rest)
            # Prompt is the quoted string at the end
            prompt_match = re.search(r'"(.+)"\s*$', rest)

            entries.append(
                {
                    "line_idx": i,
                    "state": state,
                    "task_id": m.group("task_id"),
                    "tags": tags,
                    "provider": provider_match.group(1) if provider_match else "",
                    "max_turns": int(turns_match.group(1)) if turns_match else 0,
                    "prompt": prompt_match.group(1) if prompt_match else rest,
                    "raw": line.rstrip("\n"),
                }
            )
    return entries


def _build_entry_line(
    task_id: str,
    tags: str,
    provider: str,
    max_turns: int,
    prompt: str,
    state: str = " ",
) -> str:
    """Build a formatted queue entry line."""
    tag_parts = ""
    if tags:
        tag_parts = f" [{tags}]"
    state_char = {"pending": " ", "completed": "x", "failed": "!"}.get(state, " ")
    return (
        f"- [{state_char}] `ribosome [{task_id}]{tag_parts}"
        f' --provider {provider} --max-turns {max_turns} "{prompt}"`\n'
    )


# ── MCP tool ─────────────────────────────────────────────────────────────────


@tool(
    name="ribosome_queue",
    description=(
        "Ribosome task queue management. "
        "Actions: list|add|remove|status|complete|fail. "
        "Queue file: ~/germline/loci/translation-queue.md"
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def ribosome_queue(
    action: str,
    task_id: str = "",
    tags: str = "",
    provider: str = "zhipu",
    max_turns: int = 15,
    prompt: str = "",
) -> QueueResult | EffectorResult:
    """Manage the ribosome task queue.

    Parameters
    ----------
    action : str
        One of: list, add, remove, status, complete, fail.
    task_id : str
        Task identifier (e.g. ``t-abc123``). Required for add/remove/status/complete/fail.
    tags : str
        Comma-separated tag/alias IDs for the task (add only).
    provider : str
        Provider name (default ``zhipu``, add only).
    max_turns : int
        Maximum agent turns (default 15, add only).
    prompt : str
        Task description prompt (add only).
    """
    action = action.lower().strip()
    path = QUEUE_PATH

    # ── list ──────────────────────────────────────────────────────────────
    if action == "list":
        lines = _read_queue(path)
        entries = _parse_entries(lines)
        if not entries:
            return QueueResult(
                output="Queue is empty.", data={"pending": 0, "completed": 0, "failed": 0}
            )

        pending = [e for e in entries if e["state"] == "pending"]
        completed = [e for e in entries if e["state"] == "completed"]
        failed = [e for e in entries if e["state"] == "failed"]

        parts: list[str] = []
        for label, group in [("Pending", pending), ("Completed", completed), ("Failed", failed)]:
            if group:
                parts.append(f"## {label}")
                for e in group:
                    short = e["prompt"][:80] + ("..." if len(e["prompt"]) > 80 else "")
                    parts.append(f"  [{e['task_id']}] {short}")
                parts.append("")

        summary = (
            f"Total: {len(entries)} "
            f"(pending: {len(pending)}, completed: {len(completed)}, failed: {len(failed)})"
        )
        return QueueResult(
            output="\n".join(parts) + summary,
            data={
                "total": len(entries),
                "pending": len(pending),
                "completed": len(completed),
                "failed": len(failed),
                "tasks": entries,
            },
        )

    # ── add ───────────────────────────────────────────────────────────────
    if action == "add":
        if not task_id or not prompt:
            return EffectorResult(
                success=False,
                message="add requires: task_id and prompt",
            )

        lines = _read_queue(path)
        # Check for duplicate task_id
        existing = _parse_entries(lines)
        if any(e["task_id"] == task_id for e in existing):
            return EffectorResult(
                success=False,
                message=f"Task {task_id} already exists in queue.",
            )

        new_entry = _build_entry_line(task_id, tags, provider, max_turns, prompt)

        pending_idx = _find_pending_section(lines)
        if pending_idx == -1:
            # No Pending section — create the whole file skeleton
            lines = [
                "### Pending\n",
                "\n",
                new_entry,
                "\n",
                "### Completed\n",
                "\n",
            ]
        else:
            # Find the last pending entry (or the blank line right after the header)
            insert_idx = pending_idx + 1
            # Skip blank line right after header
            while insert_idx < len(lines) and lines[insert_idx].strip() == "":
                insert_idx += 1
            # Find end of pending entries
            while insert_idx < len(lines) and _ENTRY_RE.match(lines[insert_idx].strip()):
                insert_idx += 1
            # Insert before blank line / next section
            lines.insert(insert_idx, new_entry)

        _write_queue(path, lines)
        return QueueResult(
            output=f"Added task {task_id}.",
            data={"task_id": task_id, "state": "pending"},
        )

    # ── remove ────────────────────────────────────────────────────────────
    if action == "remove":
        if not task_id:
            return EffectorResult(success=False, message="remove requires: task_id")

        lines = _read_queue(path)
        entries = _parse_entries(lines)
        target = [e for e in entries if e["task_id"] == task_id]
        if not target:
            return EffectorResult(
                success=False,
                message=f"Task {task_id} not found.",
            )

        # Remove by line index (descending to preserve indices)
        for e in target:
            del lines[e["line_idx"]]

        _write_queue(path, lines)
        return QueueResult(
            output=f"Removed task {task_id}.",
            data={"task_id": task_id},
        )

    # ── status ────────────────────────────────────────────────────────────
    if action == "status":
        if not task_id:
            return EffectorResult(success=False, message="status requires: task_id")

        lines = _read_queue(path)
        entries = _parse_entries(lines)
        target = [e for e in entries if e["task_id"] == task_id]
        if not target:
            return EffectorResult(
                success=False,
                message=f"Task {task_id} not found.",
            )

        e = target[0]
        return QueueResult(
            output=f"[{e['state']}] {task_id}: {e['prompt'][:120]}",
            data=e,
        )

    # ── complete ──────────────────────────────────────────────────────────
    if action == "complete":
        if not task_id:
            return EffectorResult(success=False, message="complete requires: task_id")

        lines = _read_queue(path)
        entries = _parse_entries(lines)
        target = [e for e in entries if e["task_id"] == task_id]
        if not target:
            return EffectorResult(
                success=False,
                message=f"Task {task_id} not found.",
            )

        e = target[0]
        if e["state"] == "completed":
            return QueueResult(
                output=f"Task {task_id} is already completed.",
                data={"task_id": task_id, "state": "completed"},
            )

        # Swap checkbox state in the raw line
        old_line = lines[e["line_idx"]]
        new_line = re.sub(r"-\s*\[ \]", "- [x]", old_line, count=1)
        lines[e["line_idx"]] = new_line
        _write_queue(path, lines)
        return QueueResult(
            output=f"Marked task {task_id} as completed.",
            data={"task_id": task_id, "state": "completed"},
        )

    # ── fail ──────────────────────────────────────────────────────────────
    if action == "fail":
        if not task_id:
            return EffectorResult(success=False, message="fail requires: task_id")

        lines = _read_queue(path)
        entries = _parse_entries(lines)
        target = [e for e in entries if e["task_id"] == task_id]
        if not target:
            return EffectorResult(
                success=False,
                message=f"Task {task_id} not found.",
            )

        e = target[0]
        if e["state"] == "failed":
            return QueueResult(
                output=f"Task {task_id} is already failed.",
                data={"task_id": task_id, "state": "failed"},
            )

        old_line = lines[e["line_idx"]]
        new_line = re.sub(r"-\s*\[ \]", "- [!]", old_line, count=1)
        lines[e["line_idx"]] = new_line
        _write_queue(path, lines)
        return QueueResult(
            output=f"Marked task {task_id} as failed.",
            data={"task_id": task_id, "state": "failed"},
        )

    return EffectorResult(
        success=False,
        message="Unknown action. Valid: list, add, remove, status, complete, fail",
    )
