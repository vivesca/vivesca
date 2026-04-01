from __future__ import annotations

"""Tests for golem-daemon task-ID features.

Covers: ID generation, ID extraction, parse_queue ID assignment,
run_golem GOLEM_TASK_ID env var, JSONL task_id field,
mark_done/mark_failed task_id propagation, cmd_status running task display.
"""

import json
import os
import re
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load():
    """Load golem-daemon by exec-ing its source (not __main__)."""
    src = open("/home/terry/germline/effectors/golem-daemon").read()
    ns: dict = {"__name__": "golem_daemon_test"}
    exec(src, ns)
    return ns


_mod = _load()

_generate_task_id = _mod["_generate_task_id"]
_extract_task_id = _mod["_extract_task_id"]
TASK_ID_RE = _mod["TASK_ID_RE"]
parse_queue = _mod["parse_queue"]
run_golem = _mod["run_golem"]
_write_jsonl_record = _mod["_write_jsonl_record"]
mark_done = _mod["mark_done"]
mark_failed = _mod["mark_failed"]
cmd_status = _mod["cmd_status"]
QueueLock = _mod["QueueLock"]
QUEUE_FILE = _mod["QUEUE_FILE"]
JSONLFILE = _mod["JSONLFILE"]
RUNNING_FILE = _mod["RUNNING_FILE"]


# ---------------------------------------------------------------------------
# 1. _generate_task_id
# ---------------------------------------------------------------------------

class TestGenerateTaskID:
    def test_format(self):
        tid = _generate_task_id()
        assert tid.startswith("t-")
        assert len(tid) == 8  # "t-" + 6 hex chars

    def test_hex_chars(self):
        tid = _generate_task_id()
        hex_part = tid[2:]
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_unique(self):
        ids = {_generate_task_id() for _ in range(100)}
        assert len(ids) == 100  # all unique


# ---------------------------------------------------------------------------
# 2. _extract_task_id
# ---------------------------------------------------------------------------

class TestExtractTaskID:
    def test_with_id(self):
        cmd = 'golem [t-a7f3b2] --provider zhipu "do stuff"'
        assert _extract_task_id(cmd) == "t-a7f3b2"

    def test_without_id(self):
        cmd = 'golem --provider zhipu "do stuff"'
        assert _extract_task_id(cmd) == ""

    def test_id_at_end(self):
        cmd = 'golem --provider zhipu [t-deadbe] "do stuff"'
        assert _extract_task_id(cmd) == "t-deadbe"

    def test_multiple_brackets_picks_first(self):
        cmd = 'golem [t-aaaaaa] other [t-bbbbbb] stuff'
        assert _extract_task_id(cmd) == "t-aaaaaa"


# ---------------------------------------------------------------------------
# 3. TASK_ID_RE
# ---------------------------------------------------------------------------

class TestTaskIDRegex:
    def test_match(self):
        m = TASK_ID_RE.search("golem [t-a1b2c3]")
        assert m is not None
        assert m.group(1) == "a1b2c3"

    def test_no_match_no_brackets(self):
        assert TASK_ID_RE.search("golem --provider zhipu") is None

    def test_no_match_wrong_length(self):
        assert TASK_ID_RE.search("[t-a1b2]") is None  # only 4 hex
        assert TASK_ID_RE.search("[t-a1b2c3d4]") is None  # 8 hex

    def test_no_match_uppercase(self):
        # regex is [0-9a-f], uppercase shouldn't match
        assert TASK_ID_RE.search("[t-A1B2C3]") is None


# ---------------------------------------------------------------------------
# 4. parse_queue generates IDs
# ---------------------------------------------------------------------------

class _FakeLock:
    """Context-manager stub for QueueLock used in tests."""
    def __enter__(self):
        return self
    def __exit__(self, *a):
        pass

_REAL_QUEUE_FILE = _mod["QUEUE_FILE"]
_REAL_QLOCK = _mod["QueueLock"]


class TestParseQueueIDs:
    @pytest.fixture(autouse=True)
    def _setup_queue(self, tmp_path):
        self.qf = tmp_path / "golem-queue.md"
        self._orig_qf = _mod["QUEUE_FILE"]
        self._orig_qlock = _mod["QueueLock"]
        _mod["QUEUE_FILE"] = self.qf
        _mod["QueueLock"] = _FakeLock

    def teardown_method(self):
        _mod["QUEUE_FILE"] = self._orig_qf
        _mod["QueueLock"] = self._orig_qlock

    def test_generates_id_for_task_without_one(self):
        self.qf.write_text(textwrap.dedent("""\
            ## Tasks
            - [ ] `golem --provider zhipu "hello"`
            ## Done
        """))
        result = parse_queue()
        assert len(result) == 1
        _line, cmd, task_id = result[0]
        assert task_id.startswith("t-")
        assert len(task_id) == 8
        assert f"[{task_id}]" in cmd

    def test_preserves_existing_id(self):
        self.qf.write_text(textwrap.dedent("""\
            ## Tasks
            - [ ] `golem [t-abcdef] --provider zhipu "hello"`
            ## Done
        """))
        result = parse_queue()
        assert len(result) == 1
        _line, cmd, task_id = result[0]
        assert task_id == "t-abcdef"

    def test_writes_id_back_to_file(self):
        self.qf.write_text(textwrap.dedent("""\
            ## Tasks
            - [ ] `golem --provider zhipu "hello"`
            ## Done
        """))
        parse_queue()
        content = self.qf.read_text()
        # Should now contain [t-xxxxxx] in the file
        m = re.search(r'\[t-([0-9a-f]{6})\]', content)
        assert m is not None, f"ID not written back to file: {content}"

    def test_high_priority_gets_id(self):
        self.qf.write_text(textwrap.dedent("""\
            ## Tasks
            - [!!] `golem --provider zhipu "urgent"`
            ## Done
        """))
        result = parse_queue()
        assert len(result) == 1
        _line, cmd, task_id = result[0]
        assert task_id.startswith("t-")
        assert f"[{task_id}]" in cmd

    def test_mixed_ids(self):
        self.qf.write_text(textwrap.dedent("""\
            ## Tasks
            - [ ] `golem [t-111111] --provider zhipu "has id"`
            - [ ] `golem --provider volcano "no id"`
            ## Done
        """))
        result = parse_queue()
        assert len(result) == 2
        _, cmd1, tid1 = result[0]
        _, cmd2, tid2 = result[1]
        assert tid1 == "t-111111"
        assert tid2.startswith("t-")
        assert len(tid2) == 8

    def test_empty_queue(self):
        self.qf.write_text("## Done\n")
        assert parse_queue() == []

    def test_nonexistent_file(self):
        self.qf.unlink(missing_ok=True)
        assert parse_queue() == []


# ---------------------------------------------------------------------------
# 5. run_golem sets GOLEM_TASK_ID env var
# ---------------------------------------------------------------------------

class TestRunGolemTaskID:
    def test_env_var_set(self):
        captured_env = {}

        def fake_run(cmd, **kwargs):
            captured_env.update(kwargs.get("env", {}))
            r = MagicMock()
            r.returncode = 0
            r.stdout = "ok"
            r.stderr = ""
            return r

        _real_run = _mod["subprocess"].run
        _mod["subprocess"].run = fake_run
        try:
            _cmd, _exit, _tail, _dur = run_golem('golem [t-beef42] --provider zhipu "test"')
        finally:
            _mod["subprocess"].run = _real_run
        assert captured_env.get("GOLEM_TASK_ID") == "t-beef42"

    def test_env_var_empty_when_no_id(self):
        captured_env = {}

        def fake_run(cmd, **kwargs):
            captured_env.update(kwargs.get("env", {}))
            r = MagicMock()
            r.returncode = 0
            r.stdout = "ok"
            r.stderr = ""
            return r

        _real_run = _mod["subprocess"].run
        _mod["subprocess"].run = fake_run
        try:
            _cmd, _exit, _tail, _dur = run_golem('golem --provider zhipu "test"')
        finally:
            _mod["subprocess"].run = _real_run
        assert captured_env.get("GOLEM_TASK_ID") == ""


# ---------------------------------------------------------------------------
# 6. _write_jsonl_record includes task_id
# ---------------------------------------------------------------------------

_REAL_JSONLFILE = _mod["JSONLFILE"]


class TestJsonlTaskID:
    def test_task_id_in_record(self, tmp_path):
        jsonl = tmp_path / "golem.jsonl"
        _mod["JSONLFILE"] = jsonl
        try:
            _write_jsonl_record("t-cafe00", "zhipu", 0, 42, 'golem [t-cafe00] --provider zhipu "x"')
            record = json.loads(jsonl.read_text().strip())
        finally:
            _mod["JSONLFILE"] = _REAL_JSONLFILE
        assert record["task_id"] == "t-cafe00"

    def test_empty_task_id(self, tmp_path):
        jsonl = tmp_path / "golem.jsonl"
        _mod["JSONLFILE"] = jsonl
        try:
            _write_jsonl_record("", "zhipu", 1, 10, 'golem --provider zhipu "x"')
            record = json.loads(jsonl.read_text().strip())
        finally:
            _mod["JSONLFILE"] = _REAL_JSONLFILE
        assert record["task_id"] == ""

    def test_record_shape(self, tmp_path):
        jsonl = tmp_path / "golem.jsonl"
        _mod["JSONLFILE"] = jsonl
        try:
            _write_jsonl_record("t-112233", "volcano", 0, 99, "cmd", tail="out")
            record = json.loads(jsonl.read_text().strip())
        finally:
            _mod["JSONLFILE"] = _REAL_JSONLFILE
        for key in ("ts", "task_id", "provider", "exit", "duration", "cmd", "tail"):
            assert key in record, f"missing key: {key}"


# ---------------------------------------------------------------------------
# 7. mark_done includes task_id in result
# ---------------------------------------------------------------------------

class TestMarkDoneTaskID:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.qf = tmp_path / "golem-queue.md"
        self._orig_qf = _mod["QUEUE_FILE"]
        self._orig_qlock = _mod["QueueLock"]
        _mod["QUEUE_FILE"] = self.qf
        _mod["QueueLock"] = _FakeLock

    def teardown_method(self):
        _mod["QUEUE_FILE"] = self._orig_qf
        _mod["QueueLock"] = self._orig_qlock

    def test_done_annotation_includes_task_id(self):
        self.qf.write_text(textwrap.dedent("""\
            ## Tasks
            - [ ] `golem [t-aabbcc] --provider zhipu "test"`
            ## Done
        """))
        mark_done(1, "exit=0", task_id="t-aabbcc")
        content = self.qf.read_text()
        assert "[t-aabbcc]" in content
        assert "exit=0" in content

    def test_done_without_task_id(self):
        self.qf.write_text(textwrap.dedent("""\
            ## Tasks
            - [ ] `golem --provider zhipu "test"`
            ## Done
        """))
        mark_done(1, "exit=0", task_id="")
        content = self.qf.read_text()
        # Should still mark done, just no [tid] prefix in annotation
        assert "exit=0" in content

    def test_high_priority_done(self):
        self.qf.write_text(textwrap.dedent("""\
            ## Tasks
            - [!!] `golem [t-ff00ff] --provider zhipu "urgent"`
            ## Done
        """))
        mark_done(1, "exit=0", task_id="t-ff00ff")
        content = self.qf.read_text()
        assert "[t-ff00ff]" in content


# ---------------------------------------------------------------------------
# 8. mark_failed includes task_id
# ---------------------------------------------------------------------------

class TestMarkFailedTaskID:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.qf = tmp_path / "golem-queue.md"
        self._orig_qf = _mod["QUEUE_FILE"]
        self._orig_qlock = _mod["QueueLock"]
        _mod["QUEUE_FILE"] = self.qf
        _mod["QueueLock"] = _FakeLock

    def teardown_method(self):
        _mod["QUEUE_FILE"] = self._orig_qf
        _mod["QueueLock"] = self._orig_qlock

    def test_retry_includes_task_id_in_log(self):
        """mark_failed should log with task_id when retrying."""
        self.qf.write_text(textwrap.dedent("""\
            ## Tasks
            - [ ] `golem [t-dead00] --provider zhipu "test"`
            ## Done
        """))
        _real_log = _mod["log"]
        _mod["log"] = lambda msg: None
        try:
            result = mark_failed(1, "exit=1 some error", exit_code=1, task_id="t-dead00")
        finally:
            _mod["log"] = _real_log
        # Should retry (exit=1, first failure)
        assert result["retried"] is True

    def test_permanent_failure_with_task_id(self):
        self.qf.write_text(textwrap.dedent("""\
            ## Tasks
            - [ ] `golem [t-badbad] --provider zhipu "test"`
            ## Done
        """))
        _real_log = _mod["log"]
        _mod["log"] = lambda msg: None
        try:
            # exit_code=2 with non-empty output = permanent failure
            # Must pass tail= so empty_output check is False
            result = mark_failed(1, "command not found: foo", exit_code=2, task_id="t-badbad", tail="command not found: foo")
        finally:
            _mod["log"] = _real_log
        assert result["retried"] is False
        content = self.qf.read_text()
        assert "- [!]" in content

    def test_rate_limited_retry_with_task_id(self):
        self.qf.write_text(textwrap.dedent("""\
            ## Tasks
            - [ ] `golem [t-ratel1] --provider zhipu "test"`
            ## Done
        """))
        _real_log = _mod["log"]
        _mod["log"] = lambda msg: None
        try:
            result = mark_failed(
                1, "Error: 429 rate limit exceeded", exit_code=2,
                task_id="t-ratel1"
            )
        finally:
            _mod["log"] = _real_log
        assert result["retried"] is True
        assert result["rate_limited"] is True


# ---------------------------------------------------------------------------
# 9. cmd_status shows running task IDs
# ---------------------------------------------------------------------------

_REAL_RUNNING_FILE = _mod["RUNNING_FILE"]
_REAL_READ_PID = _mod["read_pid"]


class TestCmdStatusRunningIDs:
    def test_shows_running_task_ids(self, tmp_path, capsys):
        _mod["QUEUE_FILE"] = tmp_path / "golem-queue.md"
        _mod["RUNNING_FILE"] = tmp_path / "running.json"
        _mod["read_pid"] = lambda: 1234
        (tmp_path / "golem-queue.md").write_text("## Done\n")
        try:
            running_data = [
                {"task_id": "t-abc123", "provider": "zhipu", "cmd": "golem [t-abc123] --provider zhipu do_x"},
                {"task_id": "t-def456", "provider": "volcano", "cmd": "golem [t-def456] --provider volcano do_y"},
            ]
            (tmp_path / "running.json").write_text(json.dumps(running_data))
            cmd_status()
            output = capsys.readouterr().out
        finally:
            _mod["QUEUE_FILE"] = _REAL_QUEUE_FILE
            _mod["RUNNING_FILE"] = _REAL_RUNNING_FILE
            _mod["read_pid"] = _REAL_READ_PID
        assert "t-abc123" in output
        assert "t-def456" in output
        assert "zhipu" in output
        assert "volcano" in output

    def test_no_running_file(self, tmp_path, capsys):
        _mod["QUEUE_FILE"] = tmp_path / "golem-queue.md"
        _mod["RUNNING_FILE"] = tmp_path / "nonexistent.json"
        _mod["read_pid"] = lambda: 5678
        (tmp_path / "golem-queue.md").write_text("## Done\n")
        try:
            cmd_status()
            output = capsys.readouterr().out
        finally:
            _mod["QUEUE_FILE"] = _REAL_QUEUE_FILE
            _mod["RUNNING_FILE"] = _REAL_RUNNING_FILE
            _mod["read_pid"] = _REAL_READ_PID
        assert "Daemon running" in output
        assert "5678" in output

    def test_daemon_not_running(self, capsys):
        _mod["read_pid"] = lambda: None
        try:
            ret = cmd_status()
            output = capsys.readouterr().out
        finally:
            _mod["read_pid"] = _REAL_READ_PID
        assert "not running" in output
        assert ret == 1
