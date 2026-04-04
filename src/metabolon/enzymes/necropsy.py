"""necropsy — dead session forensics for Claude Code JSONL files.

Post-mortem analysis of terminated Claude Code sessions.
List, extract, and timeline session data from ~/.claude/projects/*/.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

CLAUDE_HOME = Path.home() / ".claude"


def _find_session_file(claude_home: Path, session_id: str) -> Path:
    """Find a session JSONL file by session ID (supports prefix matching)."""
    projects_dir = claude_home / "projects"
    if not projects_dir.exists():
        raise FileNotFoundError(f"No projects directory: {projects_dir}")

    for jsonl_path in sorted(projects_dir.rglob("*.jsonl")):
        if jsonl_path.name == "history.jsonl":
            continue
        stem = jsonl_path.stem
        if stem == session_id or stem.startswith(session_id):
            return jsonl_path

    raise KeyError(f"Session not found: {session_id}")


def _parse_jsonl(path: Path) -> list[dict]:
    """Parse a JSONL file into a list of records."""
    records: list[dict] = []
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def list_sessions(claude_home: Path, project_filter: str | None = None) -> list[dict]:
    """List all sessions found in claude_home/projects/*/.

    Returns list of session summary dicts.
    """
    projects_dir = claude_home / "projects"
    if not projects_dir.exists():
        return []

    sessions: list[dict] = []
    for jsonl_path in sorted(projects_dir.rglob("*.jsonl")):
        if jsonl_path.name == "history.jsonl":
            continue

        records = _parse_jsonl(jsonl_path)
        if not records:
            continue

        session_id = jsonl_path.stem
        project = jsonl_path.parent.name

        if project_filter and project_filter not in project:
            continue

        timestamps: list[str] = []
        user_turns = 0
        assistant_turns = 0
        slug: str | None = None
        total_input_tokens = 0
        total_output_tokens = 0

        for rec in records:
            ts = rec.get("timestamp")
            if ts:
                timestamps.append(ts)

            rec_type = rec.get("type")

            if rec_type == "user":
                msg = rec.get("message", {})
                content = msg.get("content")
                if isinstance(content, str):
                    user_turns += 1
            elif rec_type == "assistant":
                assistant_turns += 1
                msg = rec.get("message", {})
                usage = msg.get("usage", {})
                total_input_tokens += usage.get("input_tokens", 0)
                total_output_tokens += usage.get("output_tokens", 0)
            elif rec_type == "system" and rec.get("subtype") == "turn_duration":
                if rec.get("slug"):
                    slug = rec["slug"]

        session_dict: dict = {
            "session_id": session_id,
            "project": project,
            "first_timestamp": min(timestamps) if timestamps else None,
            "last_timestamp": max(timestamps) if timestamps else None,
            "user_turns": user_turns,
            "assistant_turns": assistant_turns,
        }
        if slug:
            session_dict["slug"] = slug
        if total_input_tokens:
            session_dict["total_input_tokens"] = total_input_tokens
        if total_output_tokens:
            session_dict["total_output_tokens"] = total_output_tokens

        sessions.append(session_dict)

    sessions.sort(key=lambda s: s.get("first_timestamp") or "")
    return sessions


def extract_session(claude_home: Path, session_id: str) -> dict:
    """Extract structured content from a session.

    Returns dict with 'entries' (classified content) and 'summary'.
    """
    jsonl_path = _find_session_file(claude_home, session_id)
    records = _parse_jsonl(jsonl_path)

    entries: list[dict] = []

    for rec in records:
        rec_type = rec.get("type")
        ts = rec.get("timestamp")

        if rec_type == "user":
            msg = rec.get("message", {})
            content = msg.get("content")
            if isinstance(content, str):
                entries.append(
                    {
                        "type": "user_text",
                        "text": content,
                        "timestamp": ts,
                    }
                )

        elif rec_type == "assistant":
            msg = rec.get("message", {})
            content_blocks = msg.get("content", [])
            if isinstance(content_blocks, list):
                for block in content_blocks:
                    if block.get("type") == "text":
                        entries.append(
                            {
                                "type": "assistant_text",
                                "text": block["text"],
                                "timestamp": ts,
                            }
                        )
                    elif block.get("type") == "tool_use":
                        entries.append(
                            {
                                "type": "tool_use",
                                "tool_name": block.get("name", ""),
                                "timestamp": ts,
                            }
                        )

        elif rec_type == "queue-operation" and rec.get("operation") == "enqueue":
            content = rec.get("content", "")
            match = re.search(r"<task-id>(.*?)</task-id>", content)
            task_id = match.group(1) if match else ""
            entries.append(
                {
                    "type": "agent_dispatch",
                    "task_id": task_id,
                    "timestamp": ts,
                }
            )

    entries.sort(key=lambda e: e.get("timestamp") or "\uffff")

    return {
        "entries": entries,
        "summary": {
            "total_entries": len(entries),
        },
    }


def timeline(claude_home: Path, session_id: str) -> str:
    """Produce a human-readable timeline of a session."""
    data = extract_session(claude_home, session_id)
    entries = data["entries"]

    if not entries:
        return "No entries found for session."

    lines: list[str] = []
    for entry in entries:
        ts = entry.get("timestamp", "?")
        if ts and ts != "?":
            try:
                time_part = ts.split("T")[1][:5] if "T" in ts else ts
            except IndexError, ValueError:
                time_part = ts
        else:
            time_part = "?"

        entry_type = entry.get("type", "?")

        if entry_type == "user_text":
            lines.append(f"[{time_part}] USER: {entry.get('text', '')}")
        elif entry_type == "assistant_text":
            lines.append(f"[{time_part}] ASSISTANT: {entry.get('text', '')}")
        elif entry_type == "tool_use":
            lines.append(f"[{time_part}] TOOL: {entry.get('tool_name', '?')}")
        elif entry_type == "agent_dispatch":
            lines.append(f"[{time_part}] AGENT DISPATCH: {entry.get('task_id', '?')}")
        else:
            lines.append(f"[{time_part}] {entry_type}")

    return "\n".join(lines)


@tool(
    name="necropsy",
    description="Dead session forensics. Actions: list|extract|timeline",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def necropsy(action: str, session_id: str | None = None) -> str:
    """Post-mortem analysis of terminated Claude Code sessions.

    Args:
        action: 'list', 'extract', or 'timeline'.
        session_id: Session ID (required for extract/timeline; prefix matching supported).
    """
    action = action.lower().strip()

    if action == "list":
        sessions = list_sessions(CLAUDE_HOME)
        if not sessions:
            return "No sessions found."
        lines: list[str] = []
        for s in sessions:
            slug = s.get("slug", "—")
            turns = f"u:{s.get('user_turns', 0)} a:{s.get('assistant_turns', 0)}"
            lines.append(
                f"{s['session_id'][:12]}  {slug:<30} {turns}  {s.get('first_timestamp', '?')}"
            )
        return "\n".join(lines)

    elif action == "extract":
        if not session_id:
            return "session_id required for extract action."
        data = extract_session(CLAUDE_HOME, session_id)
        lines = []
        for e in data["entries"]:
            detail = e.get("text", e.get("tool_name", e.get("task_id", "")))
            lines.append(f"[{e.get('type')}] {detail}")
        return "\n".join(lines)

    elif action == "timeline":
        if not session_id:
            return "session_id required for timeline action."
        return timeline(CLAUDE_HOME, session_id)

    else:
        return f"Unknown action: {action}. Use: list|extract|timeline"
