"""Vigilia journal — persistence layer for copia overnight sessions.

Bridges the cold-start problem: each vigilia session writes a structured journal
so the next session knows what workers discovered, what patterns proved useful,
and where the queue left off.

Journal location: ~/notes/.vigilia-journal.md
Format: YAML frontmatter + markdown body (human-readable AND machine-parseable)

Usage:
    from vigilia_journal import read_journal, write_journal, append_worker_result
    state = read_journal()
    append_worker_result(path, "researcher-1", "HSBC DRA analysis", "completed", ["4-year governance gap"])
    write_journal(path, state)
"""

import datetime
import os
import re
from typing import Any

JOURNAL_PATH = os.path.expanduser("~/notes/.vigilia-journal.md")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _expand(path: str) -> str:
    return os.path.expanduser(path)


def _now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from markdown body. Returns (meta, body).

    Parses only the simple key: value and list formats we write ourselves —
    no external YAML dependency required.
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_block = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")

    meta: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] = []

    for line in fm_block.splitlines():
        # List item under current key
        if line.startswith("  - ") and current_key:
            current_list.append(line[4:].strip())
            continue

        # Flush previous list
        if current_key and current_list:
            meta[current_key] = current_list
            current_list = []
            current_key = None

        if ": " in line:
            k, v = line.split(": ", 1)
            k = k.strip()
            v = v.strip().strip('"')
            meta[k] = v
            current_key = k
        elif line.endswith(":"):
            current_key = line.rstrip(":").strip()
            current_list = []

    # Flush trailing list
    if current_key and current_list:
        meta[current_key] = current_list

    return meta, body


def _render_frontmatter(meta: dict) -> str:
    """Render dict as simple YAML frontmatter block."""
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f'{k}: "{v}"')
    lines.append("---")
    return "\n".join(lines)


def _empty_state() -> dict:
    return {
        "timestamp": "",
        "workers": [],
        "checker_patterns": [],
        "queue_state": {"completed": [], "remaining": [], "blocked": []},
        "recommendations": "",
    }


def _parse_body(body: str, state: dict) -> dict:
    """Extract structured data from the markdown body sections."""
    sections = re.split(r"^## ", body, flags=re.MULTILINE)

    for section in sections:
        if not section.strip():
            continue

        title_end = section.index("\n") if "\n" in section else len(section)
        title = section[:title_end].strip()
        content = section[title_end:].strip()

        if title == "Workers":
            state["workers"] = _parse_worker_section(content)
        elif title == "Checker Patterns":
            state["checker_patterns"] = [
                line.lstrip("- ").strip()
                for line in content.splitlines()
                if line.strip().startswith("- ")
            ]
        elif title == "Queue State":
            state["queue_state"] = _parse_queue_section(content)
        elif title == "Recommendations":
            state["recommendations"] = content

    return state


def _parse_worker_section(content: str) -> list[dict]:
    """Parse workers from markdown ### blocks."""
    workers = []
    blocks = re.split(r"^### ", content, flags=re.MULTILINE)
    for block in blocks:
        if not block.strip():
            continue
        lines = block.strip().splitlines()
        name = lines[0].strip()
        worker: dict[str, Any] = {"name": name, "task": "", "outcome": "", "discoveries": []}
        for line in lines[1:]:
            if line.startswith("**Task:**"):
                worker["task"] = line.replace("**Task:**", "").strip()
            elif line.startswith("**Outcome:**"):
                worker["outcome"] = line.replace("**Outcome:**", "").strip()
            elif line.startswith("- "):
                worker["discoveries"].append(line[2:].strip())
        workers.append(worker)
    return workers


def _parse_queue_section(content: str) -> dict:
    """Parse completed/remaining/blocked lists from queue section."""
    queue: dict[str, list] = {"completed": [], "remaining": [], "blocked": []}
    current: str | None = None
    for line in content.splitlines():
        lower = line.strip().lower().rstrip(":")
        if lower in ("completed", "remaining", "blocked"):
            current = lower
        elif line.strip().startswith("- ") and current:
            item = line.strip()[2:]
            if item != "(none)":
                queue[current].append(item)
    return queue


def _render_body(state: dict) -> str:
    """Render the human-readable markdown body from state."""
    parts: list[str] = []

    # Workers
    parts.append("## Workers\n")
    if state["workers"]:
        for w in state["workers"]:
            parts.append(f"### {w['name']}\n")
            parts.append(f"**Task:** {w.get('task', '')}")
            parts.append(f"**Outcome:** {w.get('outcome', '')}")
            discoveries = w.get("discoveries", [])
            if discoveries:
                parts.append("**Discoveries:**")
                for d in discoveries:
                    parts.append(f"- {d}")
            parts.append("")
    else:
        parts.append("_(no workers recorded)_\n")

    # Checker patterns
    parts.append("## Checker Patterns\n")
    patterns = state.get("checker_patterns", [])
    if patterns:
        for p in patterns:
            parts.append(f"- {p}")
        parts.append("")
    else:
        parts.append("_(none recorded)_\n")

    # Queue state
    parts.append("## Queue State\n")
    qs = state.get("queue_state", {"completed": [], "remaining": [], "blocked": []})
    for label in ("completed", "remaining", "blocked"):
        items = qs.get(label, [])
        parts.append(f"{label.capitalize()}:")
        if items:
            for item in items:
                parts.append(f"- {item}")
        else:
            parts.append("- (none)")
        parts.append("")

    # Recommendations
    parts.append("## Recommendations\n")
    recs = state.get("recommendations", "")
    parts.append(recs if recs else "_(none)_")
    parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def read_journal(path: str = JOURNAL_PATH) -> dict:
    """Read journal and return structured state dict.

    Returns an empty-state dict if the journal does not exist (first run).
    Keys: timestamp, workers, checker_patterns, queue_state, recommendations.
    """
    fpath = _expand(path)
    state = _empty_state()

    if not os.path.exists(fpath):
        return state

    with open(fpath, encoding="utf-8") as f:
        text = f.read()

    meta, body = _parse_frontmatter(text)
    # Frontmatter stores timestamp under "updated" key; support both for compat
    state["timestamp"] = meta.get("updated", meta.get("timestamp", ""))
    state["checker_patterns"] = meta.get("checker_patterns", [])
    if isinstance(state["checker_patterns"], str):
        state["checker_patterns"] = [state["checker_patterns"]]

    state = _parse_body(body, state)
    return state


def write_journal(path: str = JOURNAL_PATH, state: dict | None = None) -> None:
    """Write (overwrite) journal with the given state.

    State keys:
        timestamp        — ISO 8601 string; auto-set to now if empty
        workers          — list of {name, task, outcome, discoveries}
        checker_patterns — list of strings
        queue_state      — {completed: [...], remaining: [...], blocked: [...]}
        recommendations  — free-text string
    """
    if state is None:
        state = _empty_state()

    fpath = _expand(path)
    os.makedirs(os.path.dirname(fpath) if os.path.dirname(fpath) else ".", exist_ok=True)

    if not state.get("timestamp"):
        state["timestamp"] = _now_iso()

    # Build frontmatter with lightweight metadata
    meta: dict[str, Any] = {
        "title": "Vigilia Handoff Journal",
        "updated": state["timestamp"],
    }
    patterns = state.get("checker_patterns", [])
    if patterns:
        meta["checker_patterns"] = patterns

    fm = _render_frontmatter(meta)
    body = _render_body(state)

    content = f"{fm}\n\n# Vigilia Handoff Journal\n\n_Last session ended: {state['timestamp']}_\n\n{body}"

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)


def append_worker_result(
    path: str = JOURNAL_PATH,
    worker_name: str = "",
    task: str = "",
    outcome: str = "",
    discoveries: list[str] | str | None = None,
) -> None:
    """Append (or update) a single worker result to the journal mid-session.

    Reads the current journal, upserts the worker entry (matching by name),
    then rewrites. Safe to call repeatedly during a session.
    """
    state = read_journal(path)

    if isinstance(discoveries, str):
        discoveries = [d.strip() for d in discoveries.split(";") if d.strip()]
    elif discoveries is None:
        discoveries = []

    # Upsert: update existing worker entry if name matches
    existing = next((w for w in state["workers"] if w["name"] == worker_name), None)
    if existing:
        existing["task"] = task or existing["task"]
        existing["outcome"] = outcome or existing["outcome"]
        existing["discoveries"] = list(dict.fromkeys(existing["discoveries"] + discoveries))
    else:
        state["workers"].append(
            {
                "name": worker_name,
                "task": task,
                "outcome": outcome,
                "discoveries": discoveries,
            }
        )

    state["timestamp"] = _now_iso()
    write_journal(path, state)
