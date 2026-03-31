"""Tests for effectors/autoimmune — meta-spiral guard hook.

Autoimmune is a script — loaded via exec(), never imported.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

AUTOIMMUNE_PATH = Path(__file__).resolve().parents[1] / "effectors" / "autoimmune.py"
GERMLINE_ROOT = Path(__file__).resolve().parents[1]


# ── Fixture ────────────────────────────────────────────────────────────────


@pytest.fixture()
def ai(tmp_path):
    """Load autoimmune via exec, redirecting paths to tmp_path."""
    # Ensure metabolon is importable for the `from metabolon.locus import praxis`
    if str(GERMLINE_ROOT) not in sys.path:
        sys.path.insert(0, str(GERMLINE_ROOT))

    state_file = tmp_path / "meta-spiral-state.json"
    praxis_file = tmp_path / "Praxis.md"
    log_file = tmp_path / "hook-fire-log.jsonl"

    ns: dict = {
        "__name__": "test_autoimmune",
        "__file__": str(AUTOIMMUNE_PATH),
    }
    source = AUTOIMMUNE_PATH.read_text(encoding="utf-8")
    exec(source, ns)

    # Redirect all file paths into tmp_path
    ns["STATE_FILE"] = state_file
    ns["PRAXIS_FILE"] = praxis_file
    ns["LOG_FILE"] = log_file
    return ns


def _praxis_line(todo: bool, due: str | None = None, text: str = "sample task") -> str:
    """Build a Praxis.md checklist line."""
    box = "[ ]" if todo else "[x]"
    line = f"- {box} {text}"
    if due:
        line += f" `due:{due}`"
    return line


# ── File basics ────────────────────────────────────────────────────────────


class TestBasics:
    def test_file_exists(self):
        assert AUTOIMMUNE_PATH.exists()

    def test_shebang(self):
        first = AUTOIMMUNE_PATH.read_text().split("\n")[0]
        assert first.startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        content = AUTOIMMUNE_PATH.read_text()
        assert '"""' in content
        assert "meta-spiral" in content


# ── load_state / save_state ───────────────────────────────────────────────


class TestState:
    def test_load_state_missing_file(self, ai):
        assert ai["load_state"]() == {}

    def test_load_state_corrupt_json(self, ai):
        ai["STATE_FILE"].parent.mkdir(parents=True, exist_ok=True)
        ai["STATE_FILE"].write_text("not json{{{")
        assert ai["load_state"]() == {}

    def test_save_load_roundtrip(self, ai):
        state = {"session_id": "abc", "sarcio_count": 5}
        ai["save_state"](state)
        loaded = ai["load_state"]()
        assert loaded["session_id"] == "abc"
        assert loaded["sarcio_count"] == 5

    def test_save_creates_parent_dirs(self, ai, tmp_path):
        deep = tmp_path / "a" / "b" / "state.json"
        ai["STATE_FILE"] = deep
        ai["save_state"]({"x": 1})
        assert deep.exists()

    def test_load_state_valid(self, ai):
        ai["STATE_FILE"].parent.mkdir(parents=True, exist_ok=True)
        ai["STATE_FILE"].write_text(json.dumps({"session_id": "s1", "sarcio_count": 2}))
        result = ai["load_state"]()
        assert result["sarcio_count"] == 2


# ── log_fire ──────────────────────────────────────────────────────────────


class TestLogFire:
    def test_creates_log_entry(self, ai):
        ai["log_fire"]("test reason")
        content = ai["LOG_FILE"].read_text()
        entry = json.loads(content.strip())
        assert entry["hook"] == "meta-spiral-guard"
        assert "test reason" in entry["rule"]

    def test_appends_entries(self, ai):
        ai["log_fire"]("reason 1")
        ai["log_fire"]("reason 2")
        lines = ai["LOG_FILE"].read_text().strip().split("\n")
        assert len(lines) == 2

    def test_truncates_long_reason(self, ai):
        ai["log_fire"]("x" * 200)
        content = ai["LOG_FILE"].read_text()
        entry = json.loads(content.strip())
        assert len(entry["rule"]) <= 80

    def test_handles_write_error_gracefully(self, ai):
        # Point log to an impossible path
        ai["LOG_FILE"] = Path("/nonexistent/dir/file.jsonl")
        # Should not raise
        ai["log_fire"]("should not crash")


# ── deny ──────────────────────────────────────────────────────────────────


class TestDeny:
    def test_outputs_deny_json(self, ai):
        with pytest.raises(SystemExit) as exc_info:
            ai["deny"]("blocked for testing")
        assert exc_info.value.code == 0

    def test_deny_json_structure(self, ai, capsys):
        with pytest.raises(SystemExit):
            ai["deny"]("blocked for testing")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "blocked for testing" in data["hookSpecificOutput"]["permissionDecisionReason"]

    def test_deny_logs_fire(self, ai, capsys):
        with pytest.raises(SystemExit):
            ai["deny"]("test deny")
        assert ai["LOG_FILE"].exists()


# ── has_open_items_due_within_days ────────────────────────────────────────


class TestPraxisCheck:
    def test_no_praxis_file(self, ai):
        assert ai["has_open_items_due_within_days"](7) is False

    def test_incomplete_item_due_soon(self, ai):
        soon = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        ai["PRAXIS_FILE"].write_text(_praxis_line(True, due=soon))
        assert ai["has_open_items_due_within_days"](7) is True

    def test_complete_item_due_soon_ignored(self, ai):
        soon = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        ai["PRAXIS_FILE"].write_text(_praxis_line(False, due=soon))
        assert ai["has_open_items_due_within_days"](7) is False

    def test_item_due_far_future(self, ai):
        far = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        ai["PRAXIS_FILE"].write_text(_praxis_line(True, due=far))
        assert ai["has_open_items_due_within_days"](7) is False

    def test_item_past_due(self, ai):
        past = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        ai["PRAXIS_FILE"].write_text(_praxis_line(True, due=past))
        assert ai["has_open_items_due_within_days"](7) is True

    def test_no_due_date_items(self, ai):
        ai["PRAXIS_FILE"].write_text("- [ ] some task without due date\n")
        assert ai["has_open_items_due_within_days"](7) is False

    def test_invalid_due_date_handled(self, ai):
        ai["PRAXIS_FILE"].write_text('- [ ] task `due:not-a-date`\n')
        assert ai["has_open_items_due_within_days"](7) is False


# ── main ──────────────────────────────────────────────────────────────────


class TestMain:
    def test_non_sarcio_skill_exits_cleanly(self, ai):
        data = json.dumps({"tool_input": {"skill": "other-skill"}, "session_id": "s1"})
        with patch("sys.argv", ["autoimmune"]), patch("sys.stdin", io.StringIO(data)):
            with pytest.raises(SystemExit) as exc_info:
                ai["main"]()
        assert exc_info.value.code == 0

    def test_no_session_id_exits_cleanly(self, ai):
        data = json.dumps({"tool_input": {"skill": "sarcio-publish"}})
        with patch("sys.argv", ["autoimmune"]), patch("sys.stdin", io.StringIO(data)):
            with pytest.raises(SystemExit) as exc_info:
                ai["main"]()
        assert exc_info.value.code == 0

    def test_below_threshold_exits_cleanly(self, ai):
        data = json.dumps({"tool_input": {"skill": "sarcio-publish"}, "session_id": "s1"})
        with patch("sys.argv", ["autoimmune"]), patch("sys.stdin", io.StringIO(data)):
            with pytest.raises(SystemExit) as exc_info:
                ai["main"]()
        assert exc_info.value.code == 0
        # Should have recorded count = 1
        state = ai["load_state"]()
        assert state["sarcio_count"] == 1

    def test_threshold_allows_without_deadline_items(self, ai):
        # Set state to count = 2 so next invocation hits threshold (3)
        ai["save_state"]({"session_id": "s1", "sarcio_count": 2})
        data = json.dumps({"tool_input": {"skill": "sarcio-publish"}, "session_id": "s1"})
        with patch("sys.argv", ["autoimmune"]), patch("sys.stdin", io.StringIO(data)):
            with pytest.raises(SystemExit) as exc_info:
                ai["main"]()
        assert exc_info.value.code == 0

    def test_threshold_blocks_with_deadline_items(self, ai, capsys):
        # Set state to count = 2
        ai["save_state"]({"session_id": "s1", "sarcio_count": 2})
        # Add a Praxis item due soon
        soon = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        ai["PRAXIS_FILE"].write_text(_praxis_line(True, due=soon))
        data = json.dumps({"tool_input": {"skill": "sarcio-publish"}, "session_id": "s1"})
        with patch("sys.stdin", io.StringIO(data)):
            with pytest.raises(SystemExit) as exc_info:
                ai["main"]()
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        result = json.loads(out)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_new_session_resets_counter(self, ai):
        ai["save_state"]({"session_id": "old-session", "sarcio_count": 10})
        data = json.dumps({"tool_input": {"skill": "sarcio-publish"}, "session_id": "new-session"})
        with patch("sys.stdin", io.StringIO(data)):
            with pytest.raises(SystemExit):
                ai["main"]()
        state = ai["load_state"]()
        assert state["sarcio_count"] == 1
        assert state["session_id"] == "new-session"

    def test_invalid_json_exits_cleanly(self, ai):
        with patch("sys.stdin", io.StringIO("not json")):
            with pytest.raises(SystemExit) as exc_info:
                ai["main"]()
        assert exc_info.value.code == 0

    def test_empty_stdin_exits_cleanly(self, ai):
        with patch("sys.stdin", io.StringIO("")):
            with pytest.raises(SystemExit) as exc_info:
                ai["main"]()
        assert exc_info.value.code == 0


# ── CLI subprocess tests ──────────────────────────────────────────────────


class TestCLI:
    def test_runs_with_empty_stdin(self):
        result = subprocess.run(
            [sys.executable, str(AUTOIMMUNE_PATH)],
            input="",
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should exit 0 (bad JSON → silent exit)
        assert result.returncode == 0

    def test_runs_with_non_sarcio_input(self):
        payload = json.dumps({"tool_input": {"skill": "other"}, "session_id": "s1"})
        result = subprocess.run(
            [sys.executable, str(AUTOIMMUNE_PATH)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
