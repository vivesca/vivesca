from __future__ import annotations

"""Tests for golem-daemon task ID features.

Covers:
  1. _generate_task_id() format and uniqueness
  2. _extract_task_id() extraction from commands
  3. parse_queue() ID generation and preservation
  4. run_golem() sets GOLEM_TASK_ID env var
  5. _write_jsonl_record() writes JSONL with task_id field
  6. mark_done() includes task_id in result annotation
  7. mark_failed() includes task_id
  8. cmd_status() shows running task IDs
"""
import json
import os
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_golem_daemon():
    """Load the golem-daemon module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/golem-daemon").read()
    ns: dict = {"__name__": "golem_daemon"}
    exec(source, ns)
    return ns


_mod = _load_golem_daemon()
_generate_task_id = _mod["_generate_task_id"]
_extract_task_id = _mod["_extract_task_id"]
TASK_ID_RE = _mod["TASK_ID_RE"]
parse_queue = _mod["parse_queue"]
mark_done = _mod["mark_done"]
mark_failed = _mod["mark_failed"]
QUEUE_FILE = _mod["QUEUE_FILE"]
JSONLFILE = _mod["JSONLFILE"]
_write_jsonl_record = _mod["_write_jsonl_record"]
run_golem = _mod["run_golem"]
RUNNING_FILE = _mod["RUNNING_FILE"]


def _make_queue_dir(tmp_path: Path) -> Path:
    """Create the queue directory structure and return queue file path."""
    queue_dir = tmp_path / "germline" / "loci"
    queue_dir.mkdir(parents=True)
    return queue_dir / "golem-queue.md"


# ── _generate_task_id tests ────────────────────────────────────────────


class TestGenerateTaskID:
    """Tests for _generate_task_id(): format t-xxxxxx (6 hex chars)."""

    def test_format_prefix(self):
        """Task ID starts with 't-'."""
        tid = _generate_task_id()
        assert tid.startswith("t-")

    def test_format_hex_length(self):
        """Task ID has exactly 6 hex characters after 't-'."""
        tid = _generate_task_id()
        hex_part = tid[2:]
        assert len(hex_part) == 6
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_format_matches_regex(self):
        """Task ID matches TASK_ID_RE pattern."""
        tid = _generate_task_id()
        assert TASK_ID_RE.search(f"[{tid}]")

    def test_uniqueness(self):
        """Generated IDs are unique across multiple calls."""
        ids = {_generate_task_id() for _ in range(100)}
        assert len(ids) == 100

    def test_total_length(self):
        """Task ID total length is 8 (t- + 6 hex chars)."""
        assert len(_generate_task_id()) == 8


# ── _extract_task_id tests ─────────────────────────────────────────────


class TestExtractTaskID:
    """Tests for _extract_task_id(): extracts t-xxxxxx from command."""

    def test_extracts_existing_id(self):
        """Extracts task ID from command with [t-xxxxxx]."""
        cmd = 'golem [t-a1b2c3] --provider zhipu "do stuff"'
        assert _extract_task_id(cmd) == "t-a1b2c3"

    def test_returns_empty_for_no_id(self):
        """Returns empty string when command has no task ID."""
        cmd = 'golem --provider zhipu "do stuff"'
        assert _extract_task_id(cmd) == ""

    def test_extracts_from_middle(self):
        """Extracts ID regardless of position in command."""
        cmd = 'golem [t-deadbe] --max-turns 50 --provider infini "task"'
        assert _extract_task_id(cmd) == "t-deadbe"

    def test_extracts_from_high_priority(self):
        """Extracts ID from high-priority task command."""
        cmd = 'golem [t-ff00aa] --provider volcano "urgent"'
        assert _extract_task_id(cmd) == "t-ff00aa"

    def test_empty_command(self):
        """Returns empty string for empty command."""
        assert _extract_task_id("") == ""

    def test_multiple_ids_extracts_first(self):
        """If multiple IDs exist, extracts the first match."""
        cmd = 'golem [t-aabbcc] --provider zhipu [t-ddeeff] "task"'
        assert _extract_task_id(cmd) == "t-aabbcc"


# ── parse_queue ID generation tests ────────────────────────────────────


class TestParseQueueTaskIDs:
    """Tests for parse_queue() task ID generation and preservation."""

    def test_generates_id_for_task_without_one(self, tmp_path):
        """parse_queue generates a task ID for tasks that lack one."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text('- [ ] `golem --provider zhipu "task"`\n')
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert len(pending) == 1
        _, cmd, task_id = pending[0]
        assert task_id.startswith("t-")
        assert len(task_id) == 8
        # Command should now include the ID
        assert f"[{task_id}]" in cmd

    def test_preserves_existing_id(self, tmp_path):
        """parse_queue keeps existing task ID instead of generating new one."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text('- [ ] `golem [t-a1b2c3] --provider zhipu "task"`\n')
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert len(pending) == 1
        _, cmd, task_id = pending[0]
        assert task_id == "t-a1b2c3"
        assert "[t-a1b2c3]" in cmd

    def test_writes_generated_ids_back_to_queue(self, tmp_path):
        """parse_queue writes generated IDs back into the queue file."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text('- [ ] `golem --provider zhipu "task"`\n')
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        content = queue_path.read_text()
        task_id = pending[0][2]
        assert f"[{task_id}]" in content

    def test_mixed_ids_some_generated_some_preserved(self, tmp_path):
        """parse_queue handles mix of tasks with and without IDs."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            '- [ ] `golem [t-112233] --provider zhipu "has id"`\n'
            '- [ ] `golem --provider infini "no id"`\n'
            '- [ ] `golem [t-aabbcc] --provider volcano "also has id"`\n'
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert len(pending) == 3
        # First task preserves existing ID
        assert pending[0][2] == "t-112233"
        # Second task gets a generated ID
        assert pending[1][2].startswith("t-")
        assert len(pending[1][2]) == 8
        assert pending[1][2] != "t-112233"
        # Third task preserves existing ID
        assert pending[2][2] == "t-aabbcc"

    def test_generates_unique_ids_per_task(self, tmp_path):
        """parse_queue generates different IDs for different tasks."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            '- [ ] `golem "task1"`\n'
            '- [ ] `golem "task2"`\n'
            '- [ ] `golem "task3"`\n'
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        ids = {tid for _, _, tid in pending}
        assert len(ids) == 3  # all unique

    def test_id_not_regenerated_on_second_parse(self, tmp_path):
        """parse_queue does not change IDs on subsequent calls."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text('- [ ] `golem --provider zhipu "task"`\n')
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending1 = parse_queue()
            pending2 = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert pending1[0][2] == pending2[0][2]

    def test_high_priority_task_gets_id(self, tmp_path):
        """parse_queue generates ID for [!!] high-priority tasks."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text('- [!!] `golem --provider zhipu "urgent"`\n')
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert len(pending) == 1
        assert pending[0][2].startswith("t-")

    def test_high_priority_preserves_existing_id(self, tmp_path):
        """parse_queue preserves existing ID in [!!] tasks."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text('- [!!] `golem [t-beef42] "urgent"`\n')
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert pending[0][2] == "t-beef42"


# ── run_golem env var tests ────────────────────────────────────────────


class TestRunGolemTaskID:
    """Tests for run_golem() passing GOLEM_TASK_ID as env var."""

    def test_sets_golem_task_id_env_var(self, tmp_path, monkeypatch):
        """run_golem sets GOLEM_TASK_ID in the subprocess environment."""
        captured_env = {}

        def mock_run(cmd, **kwargs):
            captured_env.update(kwargs.get("env", {}))
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        with patch("subprocess.run", side_effect=mock_run):
            run_golem('golem [t-abcdef] --provider zhipu "task"')

        assert captured_env.get("GOLEM_TASK_ID") == "t-abcdef"

    def test_empty_task_id_when_no_id_in_cmd(self, tmp_path):
        """run_golem sets empty GOLEM_TASK_ID when command has no ID."""
        captured_env = {}

        def mock_run(cmd, **kwargs):
            captured_env.update(kwargs.get("env", {}))
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        with patch("subprocess.run", side_effect=mock_run):
            run_golem('golem --provider zhipu "no id task"')

        assert captured_env.get("GOLEM_TASK_ID") == ""

    def test_run_golem_returns_duration(self):
        """run_golem returns 4-tuple including duration."""
        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stdout = "output"
            result.stderr = ""
            return result

        with patch("subprocess.run", side_effect=mock_run):
            cmd, exit_code, tail, duration = run_golem('golem [t-123abc] "test"')

        assert exit_code == 0
        assert isinstance(duration, int)
        assert duration >= 0


# ── _write_jsonl_record tests ──────────────────────────────────────────


class TestWriteJsonlRecord:
    """Tests for _write_jsonl_record() writing JSONL with task_id field."""

    def test_writes_valid_jsonl(self, tmp_path):
        """_write_jsonl_record writes a valid JSON line."""
        jsonl_path = tmp_path / "golem.jsonl"
        original_jsonl = _mod["JSONLFILE"]
        try:
            _mod["JSONLFILE"] = jsonl_path
            _write_jsonl_record("t-a1b2c3", "zhipu", 0, 42, 'golem "task"')
        finally:
            _mod["JSONLFILE"] = original_jsonl

        assert jsonl_path.exists()
        line = jsonl_path.read_text().strip()
        record = json.loads(line)
        assert record["task_id"] == "t-a1b2c3"

    def test_jsonl_has_all_required_fields(self, tmp_path):
        """JSONL record contains ts, task_id, provider, exit, duration, cmd."""
        jsonl_path = tmp_path / "golem.jsonl"
        original_jsonl = _mod["JSONLFILE"]
        try:
            _mod["JSONLFILE"] = jsonl_path
            _write_jsonl_record("t-deadbe", "infini", 1, 120, 'golem "fail"')
        finally:
            _mod["JSONLFILE"] = original_jsonl

        record = json.loads(jsonl_path.read_text().strip())
        assert "ts" in record
        assert record["task_id"] == "t-deadbe"
        assert record["provider"] == "infini"
        assert record["exit"] == 1
        assert record["duration"] == 120
        assert "fail" in record["cmd"]

    def test_jsonl_timestamp_format(self, tmp_path):
        """JSONL timestamp starts with YYYY-MM-DD."""
        jsonl_path = tmp_path / "golem.jsonl"
        original_jsonl = _mod["JSONLFILE"]
        try:
            _mod["JSONLFILE"] = jsonl_path
            _write_jsonl_record("t-111111", "volcano", 0, 30, 'golem "task"')
        finally:
            _mod["JSONLFILE"] = original_jsonl

        record = json.loads(jsonl_path.read_text().strip())
        # ts should be YYYY-MM-DD HH:MM:SS
        assert re.match(r"\d{4}-\d{2}-\d{2}", record["ts"])

    def test_jsonl_appends_multiple_records(self, tmp_path):
        """_write_jsonl_record appends records, does not overwrite."""
        jsonl_path = tmp_path / "golem.jsonl"
        original_jsonl = _mod["JSONLFILE"]
        try:
            _mod["JSONLFILE"] = jsonl_path
            _write_jsonl_record("t-aaaaaa", "zhipu", 0, 10, 'cmd1')
            _write_jsonl_record("t-bbbbbb", "infini", 1, 20, 'cmd2')
        finally:
            _mod["JSONLFILE"] = original_jsonl

        lines = jsonl_path.read_text().strip().splitlines()
        assert len(lines) == 2
        r1 = json.loads(lines[0])
        r2 = json.loads(lines[1])
        assert r1["task_id"] == "t-aaaaaa"
        assert r2["task_id"] == "t-bbbbbb"

    def test_jsonl_cmd_truncated_at_120(self, tmp_path):
        """JSONL cmd field is truncated to 120 characters."""
        jsonl_path = tmp_path / "golem.jsonl"
        long_cmd = "golem " + "x" * 200
        original_jsonl = _mod["JSONLFILE"]
        try:
            _mod["JSONLFILE"] = jsonl_path
            _write_jsonl_record("t-cccccc", "zhipu", 0, 5, long_cmd)
        finally:
            _mod["JSONLFILE"] = original_jsonl

        record = json.loads(jsonl_path.read_text().strip())
        assert len(record["cmd"]) == 120

    def test_jsonl_creates_parent_dirs(self, tmp_path):
        """_write_jsonl_record creates parent directories if needed."""
        jsonl_path = tmp_path / "nested" / "dir" / "golem.jsonl"
        original_jsonl = _mod["JSONLFILE"]
        try:
            _mod["JSONLFILE"] = jsonl_path
            _write_jsonl_record("t-dddddd", "zhipu", 0, 1, "cmd")
        finally:
            _mod["JSONLFILE"] = original_jsonl

        assert jsonl_path.exists()

    def test_jsonl_oserror_does_not_crash(self, tmp_path):
        """_write_jsonl_record does not crash on OSError."""
        # Use a path that can't be created (e.g., /proc/fake)
        jsonl_path = Path("/proc/nonexistent/fake/golem.jsonl")
        original_jsonl = _mod["JSONLFILE"]
        try:
            _mod["JSONLFILE"] = jsonl_path
            # Should not raise
            _write_jsonl_record("t-eeeeee", "zhipu", 0, 1, "cmd")
        finally:
            _mod["JSONLFILE"] = original_jsonl


# ── mark_done with task_id tests ───────────────────────────────────────


class TestMarkDoneTaskID:
    """Tests for mark_done() including task_id in result annotation."""

    def test_mark_done_includes_task_id_in_done_section(self, tmp_path):
        """mark_done annotates the Done section entry with task_id."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            '- [ ] `golem [t-ff0000] --provider zhipu "task"`\n'
            "\n"
            "## Done\n"
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            mark_done(0, "exit=0", task_id="t-ff0000")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        content = queue_path.read_text()
        assert "[t-ff0000]" in content
        # Original line should be marked [x]
        assert "- [x]" in content

    def test_mark_done_without_task_id(self, tmp_path):
        """mark_done works when task_id is empty (backward compatible)."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            '- [ ] `golem "task"`\n'
            "\n"
            "## Done\n"
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            mark_done(0, "exit=0", task_id="")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        content = queue_path.read_text()
        assert "- [x]" in content

    def test_mark_done_result_annotation_with_task_id(self, tmp_path):
        """Result annotation in Done section shows task_id prefix."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            '- [ ] `golem [t-abcd12] "task"`\n'
            "\n"
            "## Done\n"
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            mark_done(0, "exit=0 all good", task_id="t-abcd12")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        content = queue_path.read_text()
        # The Done section entry should have [t-abcd12] prefix on the result
        lines = content.splitlines()
        done_entries = [l for l in lines if "exit=0 all good" in l]
        assert len(done_entries) >= 1
        assert "[t-abcd12]" in done_entries[0]


# ── mark_failed with task_id tests ─────────────────────────────────────


class TestMarkFailedTaskID:
    """Tests for mark_failed() task_id handling."""

    def test_mark_failed_retries_with_task_id(self, tmp_path):
        """mark_failed retries and uses task_id in log."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            '- [ ] `golem [t-failed1] --provider zhipu "task"`\n'
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            result = mark_failed(0, "exit=1 error", task_id="t-failed1")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert result["retried"] is True
        content = queue_path.read_text()
        assert "(retry)" in content

    def test_mark_failed_exit_2_with_task_id(self, tmp_path):
        """mark_failed with exit_code=2 and task_id marks as permanently failed."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            '- [ ] `golem [t-err002] --provider zhipu "task"`\n'
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            result = mark_failed(0, "bad command", exit_code=2, task_id="t-err002")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert result["retried"] is False
        content = queue_path.read_text()
        assert "- [!]" in content


# ── cmd_status task ID display tests ───────────────────────────────────


class TestCmdStatusTaskIDs:
    """Tests for cmd_status() showing running task IDs."""

    def test_status_shows_running_task_ids(self, tmp_path, capsys):
        """cmd_status displays task IDs of running tasks."""
        # Create a fake running state file with task IDs
        running_data = [
            {"task_id": "t-run001", "provider": "zhipu", "cmd": "golem task1"},
            {"task_id": "t-run002", "provider": "infini", "cmd": "golem task2"},
        ]
        running_path = tmp_path / "golem-running.json"
        running_path.write_text(json.dumps(running_data))

        # Create a queue file for parse_queue
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text("- [ ] `golem \"pending\"`\n")

        # Write a fake PID file
        pid_path = tmp_path / "golem-daemon.pid"
        pid_path.write_text(str(os.getpid()))

        original_queue = _mod["QUEUE_FILE"]
        original_running = _mod["RUNNING_FILE"]
        original_pid = _mod["PIDFILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            _mod["RUNNING_FILE"] = running_path
            _mod["PIDFILE"] = pid_path
            rc = _mod["cmd_status"]()
        finally:
            _mod["QUEUE_FILE"] = original_queue
            _mod["RUNNING_FILE"] = original_running
            _mod["PIDFILE"] = original_pid

        assert rc == 0
        out = capsys.readouterr().out
        assert "t-run001" in out
        assert "t-run002" in out
        assert "zhipu" in out
        assert "infini" in out

    def test_status_no_running_tasks(self, tmp_path, capsys):
        """cmd_status handles no running tasks gracefully."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text("- [ ] `golem \"pending\"`\n")

        running_path = tmp_path / "golem-running.json"
        running_path.write_text("[]")

        pid_path = tmp_path / "golem-daemon.pid"
        pid_path.write_text(str(os.getpid()))

        original_queue = _mod["QUEUE_FILE"]
        original_running = _mod["RUNNING_FILE"]
        original_pid = _mod["PIDFILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            _mod["RUNNING_FILE"] = running_path
            _mod["PIDFILE"] = pid_path
            rc = _mod["cmd_status"]()
        finally:
            _mod["QUEUE_FILE"] = original_queue
            _mod["RUNNING_FILE"] = original_running
            _mod["PIDFILE"] = original_pid

        assert rc == 0
        out = capsys.readouterr().out
        assert "Running tasks" not in out


# ── _update_running_file tests ─────────────────────────────────────────


class TestUpdateRunningFile:
    """Tests for _update_running_file() including task_id in output."""

    def test_running_file_includes_task_ids(self, tmp_path):
        """_update_running_file writes task IDs to the running state file."""
        running_path = tmp_path / "golem-running.json"
        original_running = _mod["RUNNING_FILE"]
        try:
            _mod["RUNNING_FILE"] = running_path
            running = {
                "fake_future_1": (0, 'golem [t-aa1111] "task1"', "zhipu", "t-aa1111"),
                "fake_future_2": (1, 'golem [t-bb2222] "task2"', "infini", "t-bb2222"),
            }
            _mod["_update_running_file"](running)
        finally:
            _mod["RUNNING_FILE"] = original_running

        data = json.loads(running_path.read_text())
        assert len(data) == 2
        ids = {d["task_id"] for d in data}
        assert "t-aa1111" in ids
        assert "t-bb2222" in ids

    def test_running_file_has_provider_and_cmd(self, tmp_path):
        """Running state file entries have provider and truncated cmd."""
        running_path = tmp_path / "golem-running.json"
        original_running = _mod["RUNNING_FILE"]
        try:
            _mod["RUNNING_FILE"] = running_path
            running = {
                "f1": (0, "short cmd", "volcano", "t-123456"),
            }
            _mod["_update_running_file"](running)
        finally:
            _mod["RUNNING_FILE"] = original_running

        data = json.loads(running_path.read_text())
        assert data[0]["provider"] == "volcano"
        assert "cmd" in data[0]


# ── Integration: parse_queue → run_golem → JSONL pipeline ──────────────


class TestTaskIDPipeline:
    """Integration tests for the full task ID pipeline."""

    def test_queue_to_jsonl_pipeline(self, tmp_path):
        """End-to-end: parse_queue generates ID, run_golem uses it, JSONL records it."""
        # Step 1: Create queue and parse (generates task ID)
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text('- [ ] `golem --provider zhipu "integration task"`\n')
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert len(pending) == 1
        line_num, cmd, task_id = pending[0]
        assert task_id.startswith("t-")
        assert f"[{task_id}]" in cmd

        # Step 2: Simulate run_golem extracting ID (mock subprocess)
        extracted_id = _extract_task_id(cmd)
        assert extracted_id == task_id

        # Step 3: Write JSONL record
        jsonl_path = tmp_path / "golem.jsonl"
        original_jsonl = _mod["JSONLFILE"]
        try:
            _mod["JSONLFILE"] = jsonl_path
            _write_jsonl_record(task_id, "zhipu", 0, 60, cmd)
        finally:
            _mod["JSONLFILE"] = original_jsonl

        record = json.loads(jsonl_path.read_text().strip())
        assert record["task_id"] == task_id
        assert record["provider"] == "zhipu"
        assert record["exit"] == 0
        assert record["duration"] == 60

    def test_id_roundtrip_stable(self, tmp_path):
        """Task ID survives queue → parse → write → re-parse without change."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text('- [ ] `golem [t-a0b1c2] "stable id"`\n')
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending1 = parse_queue()
            pending2 = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert pending1[0][2] == "t-a0b1c2"
        assert pending2[0][2] == "t-a0b1c2"
