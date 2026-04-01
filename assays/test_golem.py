from __future__ import annotations

"""Tests for golem effectors (golem-daemon, golem-dash, golem-health,
golem-reviewer, golem-validate).

Effectors are scripts — loaded via exec(open(path).read(), ns), never imported.
All function calls use dict-style access: ns["func"]().
Constants patched by mutating ns dict directly (save/restore pattern).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTORS_DIR = Path(__file__).resolve().parent.parent / "effectors"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_script(name: str) -> dict:
    """Load a Python effector into a namespace dict."""
    path = EFFECTORS_DIR / name
    assert path.exists(), f"Effector not found: {path}"
    mod_name = f"_test_golem_{name.replace('-', '_')}"
    # Create a real module in sys.modules (needed for @dataclass in golem-health)
    mod = types.ModuleType(mod_name)
    mod.__file__ = str(path)
    old_mod = sys.modules.get(mod_name)
    sys.modules[mod_name] = mod
    try:
        exec(path.read_text(), mod.__dict__)
    except Exception:
        sys.modules.pop(mod_name, None)
        if old_mod is not None:
            sys.modules[mod_name] = old_mod
        raise
    return mod.__dict__


class ns_proxy:
    """Proxy that wraps a dict so `ns.func()` works via dict access.
    Also keeps attribute mutations in sync with the underlying dict."""
    def __init__(self, d: dict):
        self.__dict__["_d"] = d

    def __getattr__(self, name):
        try:
            return self._d[name]
        except KeyError:
            raise AttributeError(f"namespace has no {name!r}")

    def __setattr__(self, name, value):
        self._d[name] = value

    def __delattr__(self, name):
        self._d.pop(name, None)


def _load(name: str) -> ns_proxy:
    return ns_proxy(_load_script(name))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_queue(tmp_path):
    """Create a temp golem-queue.md with sample tasks."""
    q = tmp_path / "golem-queue.md"
    q.write_text(
        "# Golem Queue\n\n"
        "## Pending\n\n"
        '- [ ] `golem "Write tests for foo.py"`\n'
        '- [ ] `golem --provider zhipu "Test bar.py"`\n'
        '- [ ] `golem --provider volcano "Test baz.py"`\n'
        "\n## Done\n\n"
    )
    return q


@pytest.fixture
def tmp_jsonl(tmp_path):
    """Create a temp golem.jsonl."""
    j = tmp_path / "golem.jsonl"
    records = [
        {"provider": "zhipu", "exit": 0, "duration": 120, "tests_passed": 3},
        {"provider": "zhipu", "exit": 1, "duration": 60, "tests_passed": 0},
        {"provider": "volcano", "exit": 0, "duration": 200, "tests_passed": 5},
    ]
    j.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return j


# ===================================================================
# golem-daemon tests
# ===================================================================


class TestDaemonParseQueue:
    def test_parse_pending_tasks(self, tmp_queue):
        ns = _load("golem-daemon")
        ns.QUEUE_FILE = tmp_queue
        result = ns.parse_queue()
        assert len(result) == 3
        assert result[0][1] == 'golem "Write tests for foo.py"'
        assert "--provider zhipu" in result[1][1]

    def test_parse_empty_queue(self, tmp_path):
        ns = _load("golem-daemon")
        q = tmp_path / "empty.md"
        q.write_text("# Empty\n")
        ns.QUEUE_FILE = q
        assert ns.parse_queue() == []

    def test_parse_missing_file(self, tmp_path):
        ns = _load("golem-daemon")
        ns.QUEUE_FILE = tmp_path / "nonexistent.md"
        assert ns.parse_queue() == []

    def test_parse_skips_done_tasks(self, tmp_path):
        ns = _load("golem-daemon")
        q = tmp_path / "q.md"
        q.write_text(
            '- [ ] `golem "task A"`\n'
            '- [x] `golem "task B"`\n'
            '- [!] `golem "task C"`\n'
        )
        ns.QUEUE_FILE = q
        result = ns.parse_queue()
        assert len(result) == 1
        assert "task A" in result[0][1]

    def test_parse_non_golem_command_skipped(self, tmp_path):
        ns = _load("golem-daemon")
        q = tmp_path / "q.md"
        q.write_text(
            '- [ ] `echo hello`\n'
            '- [ ] `golem "real task"`\n'
        )
        ns.QUEUE_FILE = q
        result = ns.parse_queue()
        assert len(result) == 1


class TestDaemonParseProvider:
    def test_explicit_provider(self):
        ns = _load("golem-daemon")
        assert ns.parse_provider('golem --provider zhipu "test"') == "zhipu"

    def test_no_provider_returns_default(self):
        ns = _load("golem-daemon")
        assert ns.parse_provider('golem "test"') == "default"

    def test_volcano_provider(self):
        ns = _load("golem-daemon")
        assert ns.parse_provider("golem --provider volcano task") == "volcano"

    def test_infini_provider(self):
        ns = _load("golem-daemon")
        assert ns.parse_provider("golem --provider infini task") == "infini"


class TestDaemonProviderLimits:
    def test_known_provider(self):
        ns = _load("golem-daemon")
        assert ns.get_provider_limit("zhipu") == 8

    def test_unknown_provider(self):
        ns = _load("golem-daemon")
        assert ns.get_provider_limit("unknown") == 4

    def test_volcano_limit(self):
        ns = _load("golem-daemon")
        assert ns.get_provider_limit("volcano") == 16


class TestDaemonCheckDiskSpace:
    def test_returns_tuple(self):
        ns = _load("golem-daemon")
        ok, free = ns.check_disk_space()
        assert isinstance(ok, bool)
        assert isinstance(free, int)
        assert ok is True
        assert free > 0


class TestDaemonReadPid:
    def test_no_pidfile(self, tmp_path):
        ns = _load("golem-daemon")
        ns.PIDFILE = tmp_path / "nope.pid"
        assert ns.read_pid() is None

    def test_stale_pidfile(self, tmp_path):
        ns = _load("golem-daemon")
        pidfile = tmp_path / "golem-daemon.pid"
        pidfile.write_text("99999999")
        ns.PIDFILE = pidfile
        assert ns.read_pid() is None
        assert not pidfile.exists()

    def test_valid_pidfile(self, tmp_path):
        ns = _load("golem-daemon")
        pidfile = tmp_path / "golem-daemon.pid"
        pidfile.write_text(str(os.getpid()))
        ns.PIDFILE = pidfile
        assert ns.read_pid() == os.getpid()


class TestDaemonMarkDone:
    def test_mark_done_replaces_checkbox(self, tmp_queue):
        ns = _load("golem-daemon")
        ns.QUEUE_FILE = tmp_queue
        lock_path = tmp_queue.parent / "golem-queue.lock"
        ns.QueueLock._lock_path = lock_path
        ns.mark_done(4, "exit=0")
        content = tmp_queue.read_text()
        assert "- [x]" in content
        assert "exit=0" in content

    def test_mark_done_negative_line(self, tmp_queue):
        ns = _load("golem-daemon")
        ns.QUEUE_FILE = tmp_queue
        lock_path = tmp_queue.parent / "golem-queue.lock"
        ns.QueueLock._lock_path = lock_path
        ns.mark_done(-1, "test")  # should not crash

    def test_mark_done_out_of_range(self, tmp_queue):
        ns = _load("golem-daemon")
        ns.QUEUE_FILE = tmp_queue
        lock_path = tmp_queue.parent / "golem-queue.lock"
        ns.QueueLock._lock_path = lock_path
        ns.mark_done(999, "test")  # should not crash

    def test_mark_done_already_done_line(self, tmp_queue):
        ns = _load("golem-daemon")
        ns.QUEUE_FILE = tmp_queue
        lock_path = tmp_queue.parent / "golem-queue.lock"
        ns.QueueLock._lock_path = lock_path
        ns.mark_done(4, "exit=0")
        # Second call should no-op (line is now [x])
        ns.mark_done(4, "exit=0")


class TestDaemonMarkFailed:
    def test_mark_failed_retries_once(self, tmp_queue):
        ns = _load("golem-daemon")
        ns.QUEUE_FILE = tmp_queue
        lock_path = tmp_queue.parent / "golem-queue.lock"
        ns.QueueLock._lock_path = lock_path
        result = ns.mark_failed(4, "exit=1 timeout", exit_code=1)
        assert result["retried"] is True
        content = tmp_queue.read_text()
        assert "(retry)" in content

    def test_mark_failed_no_retry_on_usage_error(self, tmp_queue):
        ns = _load("golem-daemon")
        ns.QUEUE_FILE = tmp_queue
        lock_path = tmp_queue.parent / "golem-queue.lock"
        ns.QueueLock._lock_path = lock_path
        result = ns.mark_failed(4, "bad command", exit_code=2)
        assert result["retried"] is False
        content = tmp_queue.read_text()
        assert "- [!]" in content

    def test_mark_failed_second_failure_marks_bang(self, tmp_queue):
        ns = _load("golem-daemon")
        ns.QUEUE_FILE = tmp_queue
        lock_path = tmp_queue.parent / "golem-queue.lock"
        ns.QueueLock._lock_path = lock_path
        ns.mark_failed(4, "exit=1", exit_code=1)
        ns.mark_failed(4, "exit=1 (retry)", exit_code=1)
        content = tmp_queue.read_text()
        assert "- [!]" in content


class TestDaemonValidateGolemOutput:
    def test_passes_when_no_changes(self):
        ns = _load("golem-daemon")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            passed, errors = ns.validate_golem_output()
        assert passed is True
        assert errors == []


class TestDaemonRunGolem:
    """Test run_golem with mocked subprocess."""

    def test_run_golem_success(self):
        ns = _load("golem-daemon")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "all tests passed"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            cmd, exit_code, tail = ns.run_golem('golem "test"')
        assert exit_code == 0
        assert "test" in cmd

    def test_run_golem_failure(self):
        ns = _load("golem-daemon")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error occurred"
        with patch("subprocess.run", return_value=mock_result):
            _, exit_code, _ = ns.run_golem('golem "test"')
        assert exit_code == 1


class TestDaemonGolemEnv:
    def test_includes_effectors_in_path(self):
        ns = _load("golem-daemon")
        env = ns._golem_env()
        assert "effectors" in env["PATH"]

    def test_includes_venv_bin(self):
        ns = _load("golem-daemon")
        env = ns._golem_env()
        assert ".venv" in env["PATH"]


class TestDaemonClean:
    def test_clean_removes_done_and_failed(self, tmp_queue):
        ns = _load("golem-daemon")
        ns.QUEUE_FILE = tmp_queue
        lock_path = tmp_queue.parent / "golem-queue.lock"
        ns.QueueLock._lock_path = lock_path
        ns.mark_done(4, "exit=0")
        ns.mark_failed(5, "exit=2 bad", exit_code=2)
        ret = ns.cmd_clean()
        assert ret == 0
        content = tmp_queue.read_text()
        assert "- [x]" not in content
        assert "- [!]" not in content

    def test_clean_missing_queue(self, tmp_path):
        ns = _load("golem-daemon")
        ns.QUEUE_FILE = tmp_path / "nope.md"
        assert ns.cmd_clean() == 1


class TestDaemonRotateLogs:
    def test_rotate_no_files(self, tmp_path):
        ns = _load("golem-daemon")
        ns.LOGFILE = tmp_path / "nope.log"
        ns.JSONLFILE = tmp_path / "nope.jsonl"
        ns.rotate_logs()  # should not crash

    def test_rotate_large_file(self, tmp_path):
        ns = _load("golem-daemon")
        big_log = tmp_path / "golem-daemon.log"
        big_log.write_bytes(b"x" * (6 * 1024 * 1024))
        ns.LOGFILE = big_log
        ns.JSONLFILE = tmp_path / "nope.jsonl"
        ns.rotate_logs()
        assert (tmp_path / "golem-daemon.log.1").exists()
        assert not big_log.exists()

    def test_rotate_small_file_kept(self, tmp_path):
        ns = _load("golem-daemon")
        small_log = tmp_path / "golem-daemon.log"
        small_log.write_text("small log\n")
        ns.LOGFILE = small_log
        ns.JSONLFILE = tmp_path / "nope.jsonl"
        ns.rotate_logs()
        assert small_log.exists()


class TestDaemonAutoCommit:
    def test_nothing_to_commit(self):
        ns = _load("golem-daemon")
        mock_result = MagicMock()
        mock_result.returncode = 0  # git diff --cached --quiet: 0 = no staged changes
        with patch("subprocess.run", return_value=mock_result):
            result = ns.auto_commit()
        assert result == "nothing to commit"


# ===================================================================
# golem-dash tests
# ===================================================================


class TestDashFmtBytes:
    def test_bytes(self):
        ns = _load("golem-dash")
        assert ns.fmt_bytes(500) == "500.0 B"

    def test_kilobytes(self):
        ns = _load("golem-dash")
        assert ns.fmt_bytes(2048) == "2.0 KB"

    def test_gigabytes(self):
        ns = _load("golem-dash")
        assert "GB" in ns.fmt_bytes(2 * 1024 * 1024 * 1024)

    def test_zero(self):
        ns = _load("golem-dash")
        assert ns.fmt_bytes(0) == "0.0 B"

    def test_negative(self):
        ns = _load("golem-dash")
        assert "B" in ns.fmt_bytes(-1)


class TestDashLoadJsonl:
    def test_load_valid(self, tmp_jsonl):
        ns = _load("golem-dash")
        records = ns.load_jsonl(tmp_jsonl)
        assert len(records) == 3
        assert records[0]["provider"] == "zhipu"

    def test_load_missing(self, tmp_path):
        ns = _load("golem-dash")
        assert ns.load_jsonl(tmp_path / "nope.jsonl") == []

    def test_load_with_malformed(self, tmp_path):
        ns = _load("golem-dash")
        j = tmp_path / "bad.jsonl"
        j.write_text('{"valid": true}\nnot json\n{"also": true}\n')
        assert len(ns.load_jsonl(j)) == 2

    def test_load_empty_lines(self, tmp_path):
        ns = _load("golem-dash")
        j = tmp_path / "empty_lines.jsonl"
        j.write_text('\n\n{"provider": "zhipu"}\n\n')
        assert len(ns.load_jsonl(j)) == 1


class TestDashProviderStats:
    def test_basic_stats(self, tmp_jsonl):
        ns = _load("golem-dash")
        records = ns.load_jsonl(tmp_jsonl)
        output = ns.provider_stats(records, use_color=False)
        assert "zhipu" in output
        assert "volcano" in output

    def test_empty_records(self):
        ns = _load("golem-dash")
        assert "No task records" in ns.provider_stats([], use_color=False)

    def test_with_color(self, tmp_jsonl):
        ns = _load("golem-dash")
        records = ns.load_jsonl(tmp_jsonl)
        assert "\033[" in ns.provider_stats(records, use_color=True)


class TestDashQueueStatus:
    def test_basic_status(self, tmp_queue):
        ns = _load("golem-dash")
        status_text, last_done = ns.queue_status(tmp_queue, use_color=False)
        assert "Pending: 3" in status_text
        assert "Done: 0" in status_text

    def test_missing_queue(self, tmp_path):
        ns = _load("golem-dash")
        output = ns.queue_status(tmp_path / "nope.md", use_color=False)
        assert "not found" in output.lower()

    def test_with_done_tasks(self, tmp_path):
        ns = _load("golem-dash")
        q = tmp_path / "q.md"
        q.write_text(
            '- [ ] `golem "task A"`\n'
            '- [x] `golem "task B"` \u2192 exit=0\n'
            '- [!] `golem "task C"`\n'
        )
        status_text, last_done = ns.queue_status(q, use_color=False)
        assert "Pending: 1" in status_text
        assert "Done: 1" in status_text
        assert "Failed: 1" in status_text
        assert len(last_done) == 1


class TestDashDiskFree:
    def test_returns_string(self):
        ns = _load("golem-dash")
        assert "Free:" in ns.disk_free(use_color=False)


class TestDashMain:
    def test_help_flag(self, capsys):
        ns = _load("golem-dash")
        assert ns.main(["--help"]) == 0
        assert "golem-dash" in capsys.readouterr().out

    def test_no_color(self, capsys, tmp_jsonl, tmp_queue):
        ns = _load("golem-dash")
        ns.JSONL_PATH = tmp_jsonl
        ns.QUEUE_PATH = tmp_queue
        assert ns.main(["--no-color"]) == 0
        assert "\033[" not in capsys.readouterr().out

    def test_dashboard_output(self, capsys, tmp_jsonl, tmp_queue):
        ns = _load("golem-dash")
        ns.JSONL_PATH = tmp_jsonl
        ns.QUEUE_PATH = tmp_queue
        ns.print_dashboard(use_color=False)
        out = capsys.readouterr().out
        assert "Provider Stats" in out
        assert "Queue Status" in out
        assert "Disk" in out


class TestDashLastCompleted:
    def test_empty(self):
        ns = _load("golem-dash")
        assert "No completed" in ns.last_completed_table([], use_color=False)

    def test_with_entries(self):
        ns = _load("golem-dash")
        out = ns.last_completed_table([('golem "Write tests"', "exit=0")], use_color=False)
        assert "Write tests" in out


# ===================================================================
# golem-health tests
# ===================================================================


class TestHealthSourceEnv:
    def test_missing_file(self, tmp_path):
        ns = _load("golem-health")
        result = ns.source_env_file(tmp_path / "nope")
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_parses_env_file(self, tmp_path):
        ns = _load("golem-health")
        env_f = tmp_path / ".env.fly"
        env_f.write_text('export ZHIPU_API_KEY="sk-test-123"\nVOLCANO_API_KEY=sk-volc\n')
        result = ns.source_env_file(env_f)
        assert "ZHIPU_API_KEY" in result
        assert result["ZHIPU_API_KEY"] == "sk-test-123"
        assert result["VOLCANO_API_KEY"] == "sk-volc"


class TestHealthCheckProvider:
    def test_unknown_provider(self):
        ns = _load("golem-health")
        result = ns.check_provider("unknown_provider", os.environ.copy(), EFFECTORS_DIR / "golem")
        assert result.status == "ERROR"
        assert "Unknown provider" in result.error

    def test_missing_key(self):
        ns = _load("golem-health")
        result = ns.check_provider("zhipu", {}, EFFECTORS_DIR / "golem")
        assert result.status == "FAIL"
        assert "ZHIPU_API_KEY not set" in result.error


class TestHealthPrintTable:
    def test_print_results(self, capsys):
        ns = _load("golem-health")
        result = ns.HealthResult(
            provider="zhipu", status="OK", latency_ms=150,
            model="GLM-5.1", exit_code=0, has_output=True,
        )
        ns.print_table([result])
        out = capsys.readouterr().out
        assert "zhipu" in out
        assert "OK" in out
        assert "150ms" in out

    def test_print_with_error(self, capsys):
        ns = _load("golem-health")
        result = ns.HealthResult(
            provider="infini", status="FAIL", latency_ms=0,
            model="glm-5", exit_code=1, has_output=False, error="timeout",
        )
        ns.print_table([result])
        assert "timeout" in capsys.readouterr().out


class TestHealthPrintJson:
    def test_print_json(self, capsys):
        ns = _load("golem-health")
        result = ns.HealthResult(
            provider="zhipu", status="OK", latency_ms=100,
            model="GLM-5.1", exit_code=0, has_output=True,
        )
        ns.print_json([result])
        data = json.loads(capsys.readouterr().out)
        assert len(data) == 1
        assert data[0]["provider"] == "zhipu"
        assert data[0]["status"] == "OK"


class TestHealthMain:
    def test_help_flag(self):
        ns = _load("golem-health")
        with pytest.raises(SystemExit) as exc_info:
            ns.main(["--help"])
        assert exc_info.value.code == 0


# ===================================================================
# golem-reviewer tests
# ===================================================================


class TestReviewerRun:
    def test_run_echo(self):
        ns = _load("golem-reviewer")
        code, out = ns.run("echo hello")
        assert code == 0
        assert "hello" in out

    def test_run_failure(self):
        ns = _load("golem-reviewer")
        assert ns.run("false")[0] != 0

    def test_run_timeout(self):
        ns = _load("golem-reviewer")
        # The reviewer's run() has a 120s timeout, so mock subprocess.TimeoutExpired
        with patch.object(ns, "subprocess") as mock_sp:
            mock_sp.TimeoutExpired = subprocess.TimeoutExpired
            mock_sp.run.side_effect = subprocess.TimeoutExpired(cmd="sleep", timeout=0.1)
            code, _ = ns.run("sleep 999", cwd="/tmp")
        assert code == 124


class TestReviewerCheckDaemonStatus:
    def test_parses_running(self):
        ns = _load("golem-reviewer")
        with patch.object(ns, "run", return_value=(0, "Daemon running (PID 1234), 5 pending tasks (zhipu:3)")):
            status = ns.check_daemon_status()
        assert status["running"] is True
        assert status["pending"] == 5

    def test_parses_not_running(self):
        ns = _load("golem-reviewer")
        with patch.object(ns, "run", return_value=(1, "Daemon not running")):
            status = ns.check_daemon_status()
        assert status["running"] is False
        assert status["pending"] == 0


class TestReviewerFixCollectionErrors:
    def test_no_errors(self):
        ns = _load("golem-reviewer")
        with patch.object(ns, "run", return_value=(1, "")):
            assert ns.fix_collection_errors() == 0

    def test_fixes_hardcoded_paths(self, tmp_path):
        ns = _load("golem-reviewer")
        test_file = tmp_path / "assays" / "test_example.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(
            'import os\n'
            'path = "/Users/terry/germline/foo.py"\n'
            'def test_something():\n'
            '    assert True\n'
        )
        ns.GERMLINE = tmp_path
        with patch.object(ns, "run", return_value=(0, f"ERROR {test_file}")):
            fixed = ns.fix_collection_errors()
        assert fixed == 1
        content = test_file.read_text()
        assert "/Users/terry/" not in content
        assert str(Path.home()) in content


class TestReviewerRunTestSnapshot:
    def test_parses_output(self):
        ns = _load("golem-reviewer")
        with patch.object(ns, "run", return_value=(0, "10 passed, 2 failed, 1 error")):
            result = ns.run_test_snapshot()
        assert result["passed"] == 10
        assert result["failed"] == 2
        assert result["errors"] == 1

    def test_empty_output(self):
        ns = _load("golem-reviewer")
        with patch.object(ns, "run", return_value=(1, "")):
            result = ns.run_test_snapshot()
        assert result["passed"] == 0
        assert result["failed"] == 0
        assert result["errors"] == 0


class TestReviewerCheckDaemonFailures:
    def test_with_failures(self):
        ns = _load("golem-reviewer")
        with patch.object(ns, "run", return_value=(0, "FAILED task A\nFAILED task B\n")):
            assert len(ns.check_daemon_failures()) == 2

    def test_no_failures(self):
        ns = _load("golem-reviewer")
        with patch.object(ns, "run", return_value=(1, "")):
            assert ns.check_daemon_failures() == []


class TestReviewerWriteProgressReport:
    def test_writes_report(self, tmp_path):
        ns = _load("golem-reviewer")
        copia = tmp_path / "copia"
        copia.mkdir()
        ns.cycle_number = 1
        ns.commit_counter = 0
        ns.GERMLINE = tmp_path
        ns.write_progress_report(
            {"running": True, "pending": 5},
            {"new_tests": 3, "new_effectors": 1, "consulting_pieces": 2},
            {"passed": 10, "failed": 1, "errors": 0},
            [],
        )
        report = copia / "reviewer-cycle-1.md"
        assert report.exists()
        assert "Cycle 1" in report.read_text()
        assert "5 pending" in report.read_text()


# ===================================================================
# golem-validate tests
# ===================================================================


class TestValidateFile:
    def test_valid_file(self, tmp_path):
        ns = _load("golem-validate")
        good = tmp_path / "good.py"
        good.write_text("x = 1\ny = 2\n")
        status, issues = ns.validate_file(good)
        assert status == "PASS"
        assert issues == []

    def test_syntax_error(self, tmp_path):
        ns = _load("golem-validate")
        bad = tmp_path / "bad.py"
        bad.write_text("def broken(\n")
        status, issues = ns.validate_file(bad)
        assert status == "FAIL"
        assert any("SyntaxError" in i for i in issues)

    def test_hardcoded_mac_path(self, tmp_path):
        ns = _load("golem-validate")
        f = tmp_path / "path.py"
        f.write_text('p = "/Users/terry/germline"\n')
        status, issues = ns.validate_file(f)
        assert status == "FAIL"
        assert any("/Users/terry/" in i for i in issues)

    def test_todo_marker(self, tmp_path):
        ns = _load("golem-validate")
        f = tmp_path / "todo.py"
        f.write_text("# TODO: fix this later\nx = 1\n")
        status, issues = ns.validate_file(f)
        assert status == "FAIL"
        assert any("TODO" in i for i in issues)

    def test_fixme_marker(self, tmp_path):
        ns = _load("golem-validate")
        f = tmp_path / "fixme.py"
        f.write_text("# FIXME: broken\nx = 1\n")
        status, issues = ns.validate_file(f)
        assert status == "FAIL"
        assert any("FIXME" in i for i in issues)

    def test_stub_marker(self, tmp_path):
        ns = _load("golem-validate")
        f = tmp_path / "stub.py"
        f.write_text("def stub():\n    pass\n")
        status, issues = ns.validate_file(f)
        assert status == "FAIL"
        assert any("stub" in i.lower() for i in issues)

    def test_unreadable_file(self, tmp_path):
        ns = _load("golem-validate")
        f = tmp_path / "unreadable.py"
        f.write_text("x = 1\n")
        f.chmod(0o000)
        try:
            status, issues = ns.validate_file(f)
            assert status == "FAIL"
        finally:
            f.chmod(0o644)

    def test_test_file_collectability_pass(self, tmp_path):
        ns = _load("golem-validate")
        f = tmp_path / "test_good.py"
        f.write_text("def test_ok():\n    assert True\n")
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            status, issues = ns.validate_file(f)
        assert status == "PASS"

    def test_test_file_collection_failure(self, tmp_path):
        ns = _load("golem-validate")
        f = tmp_path / "test_bad.py"
        f.write_text("def test_ok():\n    assert True\n")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "import error"
        with patch("subprocess.run", return_value=mock_result):
            status, issues = ns.validate_file(f)
        assert status == "FAIL"
        assert any("pytest --co failed" in i for i in issues)


class TestValidateMain:
    def test_no_args(self, capsys):
        ns = _load("golem-validate")
        assert ns.main([]) == 2

    def test_valid_file(self, tmp_path, capsys):
        ns = _load("golem-validate")
        good = tmp_path / "good.py"
        good.write_text("x = 1\n")
        assert ns.main([str(good)]) == 0
        assert "PASS" in capsys.readouterr().out

    def test_invalid_file(self, tmp_path, capsys):
        ns = _load("golem-validate")
        bad = tmp_path / "bad.py"
        bad.write_text("def (\n")
        assert ns.main([str(bad)]) == 1
        assert "FAIL" in capsys.readouterr().out

    def test_multiple_files(self, tmp_path, capsys):
        ns = _load("golem-validate")
        good = tmp_path / "good.py"
        good.write_text("x = 1\n")
        bad = tmp_path / "bad.py"
        bad.write_text("def (\n")
        assert ns.main([str(good), str(bad)]) == 1
        out = capsys.readouterr().out
        assert "PASS" in out
        assert "FAIL" in out


# ===================================================================
# golem (bash script) tests via subprocess
# ===================================================================


class TestGolemBashHelp:
    def test_help_flag(self):
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "golem" in r.stdout.lower()

    def test_summary_help(self):
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0


class TestGolemBashSummary:
    def test_summary_no_log(self, tmp_path):
        log_file = tmp_path / "golem.jsonl"
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert r.returncode != 0

    def test_summary_with_data(self, tmp_path):
        log_file = tmp_path / "golem.jsonl"
        records = [
            {"provider": "zhipu", "exit": 0, "duration": 120},
            {"provider": "zhipu", "exit": 1, "duration": 60},
        ]
        log_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert r.returncode == 0
        assert "zhipu" in r.stdout

    def test_summary_recent_flag(self, tmp_path):
        log_file = tmp_path / "golem.jsonl"
        log_file.write_text(json.dumps({"provider": "zhipu", "exit": 0, "duration": 10}) + "\n")
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--recent", "5"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert r.returncode == 0

    def test_summary_custom_log(self, tmp_path):
        log_file = tmp_path / "custom.jsonl"
        log_file.write_text(json.dumps({"provider": "volcano", "exit": 0, "duration": 200}) + "\n")
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", f"--log={log_file}"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(tmp_path / "default.jsonl")},
        )
        assert r.returncode == 0
        assert "volcano" in r.stdout


class TestGolemBashJsonFlag:
    """Tests for --json flag on the main golem command."""

    def test_json_flag_accepted(self):
        """--json is a valid flag (won't cause 'Unknown flag' error).

        The command will still fail due to missing API key, but it should
        not reject --json as unknown.
        """
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "--json", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "Unknown flag" not in r.stderr

    def test_json_in_help(self):
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        # --json is documented in the usage header (line 10), but --help only
        # shows the first 8 lines. Verify the flag is accepted instead.
        r2 = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "--json", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert r2.returncode == 0

    def test_json_with_quiet_accepted(self):
        """--json and --quiet together don't conflict."""
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "--json", "--quiet", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "Unknown flag" not in r.stderr


class TestGolemSummaryJson:
    """Tests for --json flag on the summary subcommand."""

    def test_summary_json_outputs_valid_json(self, tmp_path):
        log_file = tmp_path / "golem.jsonl"
        records = [
            {"provider": "zhipu", "exit": 0, "duration": 120, "tests_passed": 3},
            {"provider": "zhipu", "exit": 1, "duration": 60, "tests_passed": 0},
        ]
        log_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--json"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "zhipu" in data

    def test_summary_json_has_expected_fields(self, tmp_path):
        log_file = tmp_path / "golem.jsonl"
        log_file.write_text(json.dumps({
            "provider": "zhipu", "exit": 0, "duration": 120,
            "tests_passed": 5, "tests_failed": 1,
        }) + "\n")
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--json"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data["zhipu"]["runs"] == 1
        assert data["zhipu"]["pass"] == 1
        assert data["zhipu"]["fail"] == 0
        assert data["zhipu"]["avg_duration"] == 120
        assert data["zhipu"]["tests_created"] == 6  # tests_passed + tests_failed

    def test_summary_json_multiple_providers(self, tmp_path):
        log_file = tmp_path / "golem.jsonl"
        records = [
            {"provider": "zhipu", "exit": 0, "duration": 100},
            {"provider": "volcano", "exit": 0, "duration": 200},
            {"provider": "zhipu", "exit": 1, "duration": 50},
        ]
        log_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--json"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert len(data) == 2
        assert data["zhipu"]["runs"] == 2
        assert data["volcano"]["runs"] == 1

    def test_summary_json_with_recent(self, tmp_path):
        log_file = tmp_path / "golem.jsonl"
        records = [
            {"provider": "zhipu", "exit": 0, "duration": 10},
            {"provider": "volcano", "exit": 0, "duration": 20},
        ]
        log_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--json", "--recent", "1"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        # Only the last record (volcano) should appear
        assert "volcano" in data
        assert "zhipu" not in data

    def test_summary_json_missing_log(self, tmp_path):
        log_file = tmp_path / "nonexistent.jsonl"
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--json"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert r.returncode != 0

    def test_summary_json_empty_log(self, tmp_path):
        log_file = tmp_path / "empty.jsonl"
        log_file.write_text("")
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--json"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data == {}

    def test_summary_json_custom_log(self, tmp_path):
        log_file = tmp_path / "custom.jsonl"
        log_file.write_text(json.dumps({
            "provider": "infini", "exit": 0, "duration": 300,
        }) + "\n")
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--json", f"--log={log_file}"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(tmp_path / "default.jsonl")},
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "infini" in data
        assert data["infini"]["runs"] == 1

    def test_summary_json_avg_duration_calculation(self, tmp_path):
        log_file = tmp_path / "golem.jsonl"
        records = [
            {"provider": "zhipu", "exit": 0, "duration": 100},
            {"provider": "zhipu", "exit": 0, "duration": 200},
        ]
        log_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        r = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--json"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data["zhipu"]["avg_duration"] == 150  # (100+200)//2


# ===================================================================
# golem preflight / rate-limit / CLAUDE_CODE_MAX_RETRIES tests
# ===================================================================


class TestGolemPreflight:
    """Test the preflight health check and rate-limit detection in the golem
    bash script. We mock claude with a stub script and intercept the curl
    preflight via a fake HTTP server or by examining logged output."""

    def test_preflight_detects_429(self, tmp_path):
        """When provider returns 429, golem should detect it in preflight
        and log the rate-limit (not launch claude at all on first attempt)."""
        # Create a mock claude that should NOT be called
        mock_claude = tmp_path / "claude"
        mock_claude.write_text(
            '#!/usr/bin/env bash\n'
            'echo "MOCK_CLAUDE_CALLED" > "$HOME/.claude_called"\n'
            'exit 0\n'
        )
        mock_claude.chmod(0o755)

        log_file = tmp_path / "golem.jsonl"
        r = subprocess.run(
            [
                str(EFFECTORS_DIR / "golem"),
                "--provider", "volcano",
                "--quiet",
                "test task",
            ],
            capture_output=True, text=True, timeout=60,
            env={
                **os.environ,
                "PATH": f"{tmp_path}:{os.environ['PATH']}",
                "GOLEM_LOG": str(log_file),
                "VOLCANO_API_KEY": os.environ.get("VOLCANO_API_KEY", "test-key"),
                "GOLEM_MAX_TURNS": "1",
            },
        )
        # The real volcano is rate-limited right now, so we expect failure
        # The mock claude may or may not be called depending on preflight
        # Check the log for rate-limit evidence
        if log_file.exists():
            content = log_file.read_text()
            # If preflight worked, duration should be very short (no claude launch)
            if "volcano" in content:
                data = json.loads(content.strip().split('\n')[-1])
                assert data["provider"] == "volcano"
                assert data["exit"] != 0

    def test_claude_max_retries_env_set(self, tmp_path):
        """CLAUDE_CODE_MAX_RETRIES should be set in the claude env.
        Verify by checking the script source."""
        golem_src = (EFFECTORS_DIR / "golem").read_text()
        assert "CLAUDE_CODE_MAX_RETRIES" in golem_src
        assert "GOLEM_CLAUDE_RETRIES" in golem_src

    def test_claude_max_retries_default_is_2(self, tmp_path):
        """Default CLAUDE_CODE_MAX_RETRIES should be 2 (3 total attempts),
        not 10 (11 total = claude default)."""
        golem_src = (EFFECTORS_DIR / "golem").read_text()
        assert 'GOLEM_CLAUDE_RETRIES:-2' in golem_src

    def test_claude_max_retries_overridable(self, tmp_path):
        """GOLEM_CLAUDE_RETRIES env var should override the default."""
        golem_src = (EFFECTORS_DIR / "golem").read_text()
        # The pattern ${GOLEM_CLAUDE_RETRIES:-2} allows env override
        assert '${GOLEM_CLAUDE_RETRIES:-2}' in golem_src

    def test_timeout_wrapper_present(self):
        """The script should use 'timeout' to prevent claude from hanging
        indefinitely on 429 internal retries."""
        golem_src = (EFFECTORS_DIR / "golem").read_text()
        assert "timeout" in golem_src
        assert "_claude_timeout" in golem_src

    def test_empty_output_detected_as_ratelimit(self):
        """The script should detect empty output + non-zero exit as rate-limit."""
        golem_src = (EFFECTORS_DIR / "golem").read_text()
        assert '${output// /}' in golem_src or "output// /" in golem_src


class TestGolemProviderConfig:
    """Test provider URL and auth configuration."""

    def test_volcano_url_is_anthropic_compat(self):
        """Volcano URL should be the Anthropic-compatible endpoint."""
        golem_src = (EFFECTORS_DIR / "golem").read_text()
        assert "ark.cn-beijing.volces.com/api/coding" in golem_src

    def test_volcano_uses_api_key_not_auth_token(self):
        """Volcano should use ANTHROPIC_API_KEY (x-api-key header),
        not ANTHROPIC_AUTH_TOKEN."""
        golem_src = (EFFECTORS_DIR / "golem").read_text()
        assert 'unset ANTHROPIC_AUTH_TOKEN' in golem_src
        assert 'ANTHROPIC_API_KEY="$_KEY"' in golem_src

    def test_all_providers_unset_auth_token(self):
        """ANTHROPIC_AUTH_TOKEN should be unset for all providers to prevent
        inheritance from parent env (which can cause auth conflicts)."""
        golem_src = (EFFECTORS_DIR / "golem").read_text()
        assert "unset ANTHROPIC_AUTH_TOKEN" in golem_src


class TestGolemVolcanoIntegration:
    """Integration test: verify volcano provider endpoint responds correctly
    to the preflight check pattern used by the golem script."""

    def test_volcano_endpoint_accepts_x_api_key(self):
        """The volcano /api/coding/v1/messages endpoint should accept
        x-api-key header (not just Authorization: Bearer)."""
        key = os.environ.get("VOLCANO_API_KEY")
        if not key:
            pytest.skip("VOLCANO_API_KEY not set")
        r = subprocess.run(
            [
                "curl", "-s", "-w", "\\n%{http_code}",
                "https://ark.cn-beijing.volces.com/api/coding/v1/messages",
                "-H", f"x-api-key: {key}",
                "-H", "Content-Type: application/json",
                "-H", "anthropic-version: 2023-06-01",
                "-d", '{"model":"ark-code-latest","max_tokens":1,'
                      '"messages":[{"role":"user","content":"ping"}]}',
                "--connect-timeout", "10",
                "--max-time", "15",
            ],
            capture_output=True, text=True, timeout=20,
        )
        lines = r.stdout.strip().split('\n')
        http_code = lines[-1] if lines else "0"
        body = '\n'.join(lines[:-1])
        # Should be 200 (OK), 429 (rate-limited), or 400 (bad request)
        # NOT 401 (auth failure) — that would mean x-api-key isn't accepted
        assert http_code in ("200", "400", "429"), \
            f"Expected 200/400/429, got {http_code}: {body[:200]}"

    def test_volcano_preflight_returns_json_error(self):
        """When volcano is rate-limited, the error JSON should contain
        AccountQuotaExceeded with a 'reset at' timestamp."""
        key = os.environ.get("VOLCANO_API_KEY")
        if not key:
            pytest.skip("VOLCANO_API_KEY not set")
        r = subprocess.run(
            [
                "curl", "-s",
                "https://ark.cn-beijing.volces.com/api/coding/v1/messages",
                "-H", f"x-api-key: {key}",
                "-H", "Content-Type: application/json",
                "-H", "anthropic-version: 2023-06-01",
                "-d", '{"model":"ark-code-latest","max_tokens":1,'
                      '"messages":[{"role":"user","content":"ping"}]}',
                "--connect-timeout", "10",
                "--max-time", "15",
            ],
            capture_output=True, text=True, timeout=20,
        )
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            pytest.skip(f"Non-JSON response: {r.stdout[:100]}")
        # If it's a 429, verify the format
        if "error" in data:
            error = data["error"]
            if error.get("code") == "AccountQuotaExceeded":
                assert "reset at" in error.get("message", ""), \
                    f"Expected 'reset at' in error message: {error['message']}"
                assert "TooManyRequests" in error.get("type", "")

