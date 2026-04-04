"""Tests for metabolon.enzymes.necropsy — dead session forensics."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Synthetic JSONL fixtures
# ---------------------------------------------------------------------------


def _ts(hour: int, minute: int = 0) -> str:
    """ISO timestamp helper for 2026-04-03 HKT."""
    return f"2026-04-03T{hour:02d}:{minute:02d}:00.000Z"


def _user_record(
    session_id: str,
    text: str,
    uuid: str = "u1",
    timestamp: str | None = None,
    slug: str = "test-session",
) -> dict:
    return {
        "type": "user",
        "message": {"role": "user", "content": text},
        "uuid": uuid,
        "timestamp": timestamp or _ts(10, 0),
        "sessionId": session_id,
        "slug": slug,
        "cwd": "/home/terry",
        "version": "2.1.91",
    }


def _assistant_text_record(
    session_id: str,
    text: str,
    uuid: str = "a1",
    parent_uuid: str = "u1",
    timestamp: str | None = None,
    model: str = "claude-opus-4-6",
    input_tokens: int = 100,
    output_tokens: int = 200,
) -> dict:
    return {
        "type": "assistant",
        "parentUuid": parent_uuid,
        "isSidechain": False,
        "message": {
            "model": model,
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        },
        "uuid": uuid,
        "timestamp": timestamp or _ts(10, 1),
        "sessionId": session_id,
    }


def _assistant_tool_use_record(
    session_id: str,
    tool_name: str,
    tool_input: dict,
    tool_use_id: str = "toolu_01",
    uuid: str = "a2",
    timestamp: str | None = None,
) -> dict:
    return {
        "type": "assistant",
        "parentUuid": "u1",
        "isSidechain": False,
        "message": {
            "model": "claude-opus-4-6",
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": tool_use_id,
                    "name": tool_name,
                    "input": tool_input,
                },
            ],
            "usage": {"input_tokens": 50, "output_tokens": 80},
        },
        "uuid": uuid,
        "timestamp": timestamp or _ts(10, 2),
        "sessionId": session_id,
    }


def _tool_result_record(
    session_id: str,
    content: str,
    uuid: str = "u2",
    timestamp: str | None = None,
) -> dict:
    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": [
                {"type": "tool_result", "content": content},
            ],
        },
        "uuid": uuid,
        "timestamp": timestamp or _ts(10, 3),
        "sessionId": session_id,
    }


def _turn_duration_record(
    session_id: str,
    duration_ms: int,
    message_count: int,
    slug: str = "test-session",
    timestamp: str | None = None,
) -> dict:
    return {
        "type": "system",
        "subtype": "turn_duration",
        "durationMs": duration_ms,
        "messageCount": message_count,
        "timestamp": timestamp or _ts(10, 5),
        "sessionId": session_id,
        "slug": slug,
    }


def _queue_operation_record(
    session_id: str,
    operation: str = "enqueue",
    task_id: str = "task123",
    summary: str = "Agent completed",
    timestamp: str | None = None,
) -> dict:
    return {
        "type": "queue-operation",
        "operation": operation,
        "timestamp": timestamp or _ts(10, 4),
        "sessionId": session_id,
        "content": (
            f"<task-notification>\n"
            f"<task-id>{task_id}</task-id>\n"
            f"<summary>{summary}</summary>\n"
            f"</task-notification>"
        ),
    }


def _last_prompt_record(session_id: str, text: str) -> dict:
    return {
        "type": "last-prompt",
        "lastPrompt": text,
        "sessionId": session_id,
    }


def _permission_mode_record(session_id: str, mode: str = "bypassPermissions") -> dict:
    return {"type": "permission-mode", "permissionMode": mode, "sessionId": session_id}


def _write_session(project_dir: Path, session_id: str, records: list[dict]) -> Path:
    """Write a synthetic session JSONL file."""
    path = project_dir / f"{session_id}.jsonl"
    with open(path, "w") as fh:
        fh.writelines(json.dumps(record) + "\n" for record in records)
    return path


# ---------------------------------------------------------------------------
# Fixture: synthetic .claude/projects layout
# ---------------------------------------------------------------------------


@pytest.fixture()
def claude_projects(tmp_path: Path):
    """Create a synthetic .claude/projects directory with multiple sessions."""
    projects_dir = tmp_path / ".claude" / "projects"
    home_terry = projects_dir / "-home-terry"
    home_terry.mkdir(parents=True)

    germline = projects_dir / "-home-terry-germline"
    germline.mkdir(parents=True)

    # Session A: full session with text, tools, agents, duration
    session_a = "aaaa1111-0000-0000-0000-000000000000"
    _write_session(
        home_terry,
        session_a,
        [
            _last_prompt_record(session_a, "build the thing"),
            _permission_mode_record(session_a),
            _user_record(session_a, "build the feature", uuid="ua1", timestamp=_ts(10, 0)),
            _assistant_text_record(
                session_a,
                "I'll build this for you.",
                uuid="aa1",
                parent_uuid="ua1",
                timestamp=_ts(10, 1),
                input_tokens=500,
                output_tokens=1000,
            ),
            _assistant_tool_use_record(
                session_a,
                "Bash",
                {"command": "ls -la"},
                uuid="aa2",
                timestamp=_ts(10, 2),
            ),
            _tool_result_record(session_a, "file1.py\nfile2.py", uuid="ua2", timestamp=_ts(10, 3)),
            _assistant_text_record(
                session_a,
                "Done. Created two files.",
                uuid="aa3",
                parent_uuid="ua2",
                timestamp=_ts(10, 10),
                input_tokens=600,
                output_tokens=300,
            ),
            _queue_operation_record(session_a, "enqueue", "task_x", "Agent research OCI"),
            _queue_operation_record(
                session_a, "dequeue", "task_x", "Agent research OCI completed"
            ),
            _turn_duration_record(
                session_a, 30000, 7, slug="brave-dancing-fox", timestamp=_ts(10, 11)
            ),
            _turn_duration_record(
                session_a, 15000, 3, slug="brave-dancing-fox", timestamp=_ts(10, 15)
            ),
        ],
    )

    # Session B: short session, different project
    session_b = "bbbb2222-0000-0000-0000-000000000000"
    _write_session(
        germline,
        session_b,
        [
            _user_record(session_b, "fix the tests", uuid="ub1", timestamp=_ts(11, 0)),
            _assistant_text_record(
                session_b,
                "Tests are green now.",
                uuid="ab1",
                parent_uuid="ub1",
                timestamp=_ts(11, 5),
                input_tokens=200,
                output_tokens=150,
            ),
            _turn_duration_record(
                session_b, 5000, 2, slug="quiet-silver-moon", timestamp=_ts(11, 6)
            ),
        ],
    )

    # Session C: dead session (no turn_duration, no slug — crashed)
    session_c = "cccc3333-0000-0000-0000-000000000000"
    _write_session(
        home_terry,
        session_c,
        [
            _user_record(session_c, "investigate disk", uuid="uc1", timestamp=_ts(12, 0)),
            _assistant_text_record(
                session_c,
                "Disk is at 80%.",
                uuid="ac1",
                parent_uuid="uc1",
                timestamp=_ts(12, 1),
            ),
        ],
    )

    # Also write history.jsonl
    history = tmp_path / ".claude" / "history.jsonl"
    history.write_text(
        json.dumps(
            {
                "display": "build the feature",
                "timestamp": 1775170800000,
                "sessionId": session_a,
                "project": "/home/terry",
            }
        )
        + "\n"
        + json.dumps(
            {
                "display": "fix the tests",
                "timestamp": 1775174400000,
                "sessionId": session_b,
                "project": "/home/terry/germline",
            }
        )
        + "\n"
        + json.dumps(
            {
                "display": "investigate disk",
                "timestamp": 1775178000000,
                "sessionId": session_c,
                "project": "/home/terry",
            }
        )
        + "\n"
    )

    return tmp_path


# ===========================================================================
# Tests: list_sessions
# ===========================================================================


class TestListSessions:
    """necropsy.list_sessions(claude_home) -> list of session summaries."""

    def test_finds_all_sessions(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import list_sessions

        sessions = list_sessions(claude_projects / ".claude")
        session_ids = [s["session_id"] for s in sessions]

        assert len(sessions) == 3
        assert "aaaa1111" in session_ids[0]
        assert "bbbb2222" in session_ids[1] or "bbbb2222" in session_ids[2]

    def test_session_has_required_fields(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import list_sessions

        sessions = list_sessions(claude_projects / ".claude")
        required = {
            "session_id",
            "project",
            "first_timestamp",
            "last_timestamp",
            "user_turns",
            "assistant_turns",
        }

        for session in sessions:
            assert required.issubset(session.keys()), (
                f"Missing fields: {required - session.keys()}"
            )

    def test_session_counts_turns(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import list_sessions

        sessions = list_sessions(claude_projects / ".claude")
        session_a = next(s for s in sessions if s["session_id"].startswith("aaaa"))
        # 2 user text records (ua1, ua2 is tool_result)
        assert session_a["user_turns"] >= 1
        assert session_a["assistant_turns"] >= 2  # aa1, aa3 (text) + aa2 (tool_use)

    def test_session_has_slug(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import list_sessions

        sessions = list_sessions(claude_projects / ".claude")
        session_a = next(s for s in sessions if s["session_id"].startswith("aaaa"))
        assert session_a.get("slug") == "brave-dancing-fox"

    def test_session_has_token_totals(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import list_sessions

        sessions = list_sessions(claude_projects / ".claude")
        session_a = next(s for s in sessions if s["session_id"].startswith("aaaa"))
        assert session_a.get("total_input_tokens", 0) > 0
        assert session_a.get("total_output_tokens", 0) > 0

    def test_filter_by_project(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import list_sessions

        sessions = list_sessions(claude_projects / ".claude", project_filter="germline")
        assert len(sessions) == 1
        assert sessions[0]["session_id"].startswith("bbbb")

    def test_dead_session_still_listed(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import list_sessions

        sessions = list_sessions(claude_projects / ".claude")
        dead = next(s for s in sessions if s["session_id"].startswith("cccc"))
        assert dead is not None
        assert dead["user_turns"] >= 1


# ===========================================================================
# Tests: extract_session
# ===========================================================================


class TestExtractSession:
    """necropsy.extract_session(jsonl_path, session_id) -> structured content."""

    def test_extracts_assistant_text(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import extract_session

        result = extract_session(
            claude_projects / ".claude",
            "aaaa1111-0000-0000-0000-000000000000",
        )
        texts = [e["text"] for e in result["entries"] if e["type"] == "assistant_text"]
        assert "I'll build this for you." in texts
        assert "Done. Created two files." in texts

    def test_extracts_tool_calls(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import extract_session

        result = extract_session(
            claude_projects / ".claude",
            "aaaa1111-0000-0000-0000-000000000000",
        )
        tool_calls = [e for e in result["entries"] if e["type"] == "tool_use"]
        assert len(tool_calls) >= 1
        assert tool_calls[0]["tool_name"] == "Bash"

    def test_extracts_user_messages(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import extract_session

        result = extract_session(
            claude_projects / ".claude",
            "aaaa1111-0000-0000-0000-000000000000",
        )
        user_msgs = [e for e in result["entries"] if e["type"] == "user_text"]
        assert any("build the feature" in m["text"] for m in user_msgs)

    def test_extracts_agent_dispatches(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import extract_session

        result = extract_session(
            claude_projects / ".claude",
            "aaaa1111-0000-0000-0000-000000000000",
        )
        agents = [e for e in result["entries"] if e["type"] == "agent_dispatch"]
        assert len(agents) >= 1
        assert "task_x" in agents[0]["task_id"]

    def test_entries_ordered_by_timestamp(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import extract_session

        result = extract_session(
            claude_projects / ".claude",
            "aaaa1111-0000-0000-0000-000000000000",
        )
        timestamps = [e["timestamp"] for e in result["entries"] if "timestamp" in e]
        assert timestamps == sorted(timestamps)

    def test_prefix_match(self, claude_projects: Path):
        """Session ID prefix should work (like anam)."""
        from metabolon.enzymes.necropsy import extract_session

        result = extract_session(claude_projects / ".claude", "aaaa1111")
        assert len(result["entries"]) > 0

    def test_nonexistent_session_raises(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import extract_session

        with pytest.raises((KeyError, FileNotFoundError, ValueError)):
            extract_session(claude_projects / ".claude", "zzzz9999")

    def test_has_summary(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import extract_session

        result = extract_session(
            claude_projects / ".claude",
            "aaaa1111-0000-0000-0000-000000000000",
        )
        assert "summary" in result
        assert result["summary"]["total_entries"] > 0


# ===========================================================================
# Tests: timeline (formatted output)
# ===========================================================================


class TestTimeline:
    """necropsy.timeline(jsonl_path, session_id) -> human-readable timeline."""

    def test_returns_string(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import timeline

        output = timeline(
            claude_projects / ".claude",
            "aaaa1111-0000-0000-0000-000000000000",
        )
        assert isinstance(output, str)
        assert len(output) > 50

    def test_includes_timestamps(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import timeline

        output = timeline(
            claude_projects / ".claude",
            "aaaa1111-0000-0000-0000-000000000000",
        )
        assert "10:0" in output or "10:" in output  # HH:MM from timestamps

    def test_includes_tool_names(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import timeline

        output = timeline(
            claude_projects / ".claude",
            "aaaa1111-0000-0000-0000-000000000000",
        )
        assert "Bash" in output

    def test_includes_user_and_assistant(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import timeline

        output = timeline(
            claude_projects / ".claude",
            "aaaa1111-0000-0000-0000-000000000000",
        )
        # Should contain both user text and assistant text
        assert "build the feature" in output
        assert "Done" in output or "build this" in output


# ===========================================================================
# Tests: MCP tool interface
# ===========================================================================


class TestMcpTool:
    """The necropsy MCP tool should be importable and callable."""

    def test_importable(self):
        from metabolon.enzymes.necropsy import necropsy

        assert callable(necropsy)

    def test_list_action(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import necropsy

        with patch("metabolon.enzymes.necropsy.CLAUDE_HOME", claude_projects / ".claude"):
            result = necropsy(action="list")
        assert "aaaa1111" in result

    def test_extract_action(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import necropsy

        with patch("metabolon.enzymes.necropsy.CLAUDE_HOME", claude_projects / ".claude"):
            result = necropsy(action="extract", session_id="aaaa1111")
        assert "build this" in result or "Created two files" in result

    def test_timeline_action(self, claude_projects: Path):
        from metabolon.enzymes.necropsy import necropsy

        with patch("metabolon.enzymes.necropsy.CLAUDE_HOME", claude_projects / ".claude"):
            result = necropsy(action="timeline", session_id="aaaa1111")
        assert "Bash" in result
