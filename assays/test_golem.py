"""Tests for golem effectors (golem-daemon, golem-dash, golem-health,
golem-reviewer, golem-validate).

Effectors are scripts — loaded via exec(open(path).read(), ns), never imported.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import textwrap
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

EFFECTORS_DIR = Path(__file__).resolve().parent.parent / "effectors"
ASSAYS_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Helpers: load script namespaces
# ---------------------------------------------------------------------------

def _load_script(name: str) -> dict:
    """Load a Python effector into an isolated namespace."""
    path = EFFECTORS_DIR / name
    assert path.exists(), f"Effector not found: {path}"
    ns: dict = {"__name__": "test_golem_module", "__file__": str(path)}
    exec(path.read_text(), ns)
    return ns


def _load_daemon():
    return _load_script("golem-daemon")


def _load_dash():
    return _load_script("golem-dash")


def _load_health():
    return _load_script("golem-health")


def _load_reviewer():
    return _load_script("golem-reviewer")


def _load_validate():
    return _load_script("golem-validate")


def _patch_ns(ns: dict, **kwargs):
    """Return a patch.dict context manager for an exec'd namespace."""
    return patch.dict(ns, kwargs)


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
    lines = [json.dumps(r) for r in records]
    j.write_text("\n".join(lines) + "\n")
    return j


# ===================================================================
# golem-daemon tests
# ===================================================================


class TestDaemonParseQueue:
    """Tests for parse_queue()."""

    def test_parse_pending_tasks(self, tmp_queue):
        ns = _load_daemon()
        with _patch_ns(ns, QUEUE_FILE=tmp_queue):
            result = ns.parse_queue()
        assert len(result) == 3
        assert result[0][1] == 'golem "Write tests for foo.py"'
        assert "--provider zhipu" in result[1][1]

    def test_parse_empty_queue(self, tmp_path):
        ns = _load_daemon()
        q = tmp_path / "empty.md"
        q.write_text("# Empty\n")
        with _patch_ns(ns, QUEUE_FILE=q):
            result = ns.parse_queue()
        assert result == []

    def test_parse_missing_file(self, tmp_path):
        ns = _load_daemon()
        q = tmp_path / "nonexistent.md"
        with _patch_ns(ns, QUEUE_FILE=q):
            result = ns.parse_queue()
        assert result == []

    def test_parse_skips_done_tasks(self, tmp_path):
        ns = _load_daemon()
        q = tmp_path / "q.md"
        q.write_text(
            '- [ ] `golem "task A"`\n'
            '- [x] `golem "task B"`\n'
            '- [!] `golem "task C"`\n'
        )
        with _patch_ns(ns, QUEUE_FILE=q):
            result = ns.parse_queue()
        assert len(result) == 1
        assert "task A" in result[0][1]

    def test_parse_non_golem_command_skipped(self, tmp_path):
        ns = _load_daemon()
        q = tmp_path / "q.md"
        q.write_text(
            '- [ ] `echo hello`\n'
            '- [ ] `golem "real task"`\n'
        )
        with _patch_ns(ns, QUEUE_FILE=q):
            result = ns.parse_queue()
        assert len(result) == 1


class TestDaemonParseProvider:
    def test_explicit_provider(self):
        ns = _load_daemon()
        assert ns.parse_provider('golem --provider zhipu "test"') == "zhipu"

    def test_no_provider_returns_default(self):
        ns = _load_daemon()
        assert ns.parse_provider('golem "test"') == "default"

    def test_volcano_provider(self):
        ns = _load_daemon()
        assert ns.parse_provider("golem --provider volcano task") == "volcano"

    def test_infini_provider(self):
        ns = _load_daemon()
        assert ns.parse_provider("golem --provider infini task") == "infini"


class TestDaemonProviderLimits:
    def test_known_provider(self):
        ns = _load_daemon()
        assert ns.get_provider_limit("zhipu") == 8

    def test_unknown_provider(self):
        ns = _load_daemon()
        assert ns.get_provider_limit("unknown") == 4

    def test_volcano_limit(self):
        ns = _load_daemon()
        assert ns.get_provider_limit("volcano") == 16


class TestDaemonCheckDiskSpace:
    def test_returns_tuple(self):
        ns = _load_daemon()
        ok, free = ns.check_disk_space()
        assert isinstance(ok, bool)
        assert isinstance(free, int)
        assert ok is True
        assert free > 0


class TestDaemonReadPid:
    def test_no_pidfile(self, tmp_path):
        ns = _load_daemon()
        with _patch_ns(ns, PIDFILE=tmp_path / "nope.pid"):
            assert ns.read_pid() is None

    def test_stale_pidfile(self, tmp_path):
        ns = _load_daemon()
        pidfile = tmp_path / "golem-daemon.pid"
        pidfile.write_text("99999999")
        with _patch_ns(ns, PIDFILE=pidfile):
            assert ns.read_pid() is None
        assert not pidfile.exists()

    def test_valid_pidfile(self, tmp_path):
        ns = _load_daemon()
        pidfile = tmp_path / "golem-daemon.pid"
        pidfile.write_text(str(os.getpid()))
        with _patch_ns(ns, PIDFILE=pidfile):
            pid = ns.read_pid()
        assert pid == os.getpid()


class TestDaemonMarkDone:
    def test_mark_done_replaces_checkbox(self, tmp_queue):
        ns = _load_daemon()
        lock_path = tmp_queue.parent / "golem-queue.lock"
        with _patch_ns(ns, QUEUE_FILE=tmp_queue):
            # Patch QueueLock's _lock_path too
            ns["QueueLock"]._lock_path = lock_path
            ns.mark_done(4, "exit=0")
        content = tmp_queue.read_text()
        assert "- [x]" in content
        assert "exit=0" in content

    def test_mark_done_negative_line(self, tmp_queue):
        ns = _load_daemon()
        lock_path = tmp_queue.parent / "golem-queue.lock"
        with _patch_ns(ns, QUEUE_FILE=tmp_queue):
            ns["QueueLock"]._lock_path = lock_path
            ns.mark_done(-1, "test")

    def test_mark_done_out_of_range(self, tmp_queue):
        ns = _load_daemon()
        lock_path = tmp_queue.parent / "golem-queue.lock"
        with _patch_ns(ns, QUEUE_FILE=tmp_queue):
            ns["QueueLock"]._lock_path = lock_path
            ns.mark_done(999, "test")

    def test_mark_done_already_done_line(self, tmp_queue):
        ns = _load_daemon()
        lock_path = tmp_queue.parent / "golem-queue.lock"
        with _patch_ns(ns, QUEUE_FILE=tmp_queue):
            ns["QueueLock"]._lock_path = lock_path
            ns.mark_done(4, "exit=0")
            # Second call on same line — should no-op (line is now [x])
            ns.mark_done(4, "exit=0")


class TestDaemonMarkFailed:
    def test_mark_failed_retries_once(self, tmp_queue):
        ns = _load_daemon()
        lock_path = tmp_queue.parent / "golem-queue.lock"
        with _patch_ns(ns, QUEUE_FILE=tmp_queue):
            ns["QueueLock"]._lock_path = lock_path
            result = ns.mark_failed(4, "exit=1 timeout", exit_code=1)
        assert result["retried"] is True
        content = tmp_queue.read_text()
        assert "(retry)" in content

    def test_mark_failed_no_retry_on_usage_error(self, tmp_queue):
        ns = _load_daemon()
        lock_path = tmp_queue.parent / "golem-queue.lock"
        with _patch_ns(ns, QUEUE_FILE=tmp_queue):
            ns["QueueLock"]._lock_path = lock_path
            result = ns.mark_failed(4, "bad command", exit_code=2)
        assert result["retried"] is False
        content = tmp_queue.read_text()
        assert "- [!]" in content

    def test_mark_failed_second_failure_marks_bang(self, tmp_queue):
        ns = _load_daemon()
        lock_path = tmp_queue.parent / "golem-queue.lock"
        with _patch_ns(ns, QUEUE_FILE=tmp_queue):
            ns["QueueLock"]._lock_path = lock_path
            ns.mark_failed(4, "exit=1", exit_code=1)
            ns.mark_failed(4, "exit=1 (retry)", exit_code=1)
        content = tmp_queue.read_text()
        assert "- [!]" in content


class TestDaemonValidateGolemOutput:
    def test_passes_when_no_changes(self):
        ns = _load_daemon()
        mock_result = MagicMock()
        mock_result.returncode = 1  # git diff --quiet returns 1 if diff, but 0 if no diff
        # Actually diff --cached --quiet returns 0 when no staged changes
        mock_result.returncode = 0
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            passed, errors = ns.validate_golem_output()
        assert passed is True
        assert errors == []


class TestDaemonConfigureProvider:
    def test_zhipu_config(self):
        ns = _load_daemon()
        with patch.dict(os.environ, {"ZHIPU_API_KEY": "sk-test"}):
            ns._configure_provider("zhipu")
        assert ns._URL == "https://open.bigmodel.cn/api/anthropic"
        assert ns._OPUS == "GLM-5.1"

    def test_volcano_config(self):
        ns = _load_daemon()
        with patch.dict(os.environ, {"VOLCANO_API_KEY": "sk-test"}):
            ns._configure_provider("volcano")
        assert ns._AUTH_MODE == "token"

    def test_unknown_provider_returns_error(self):
        ns = _load_daemon()
        with pytest.raises(SystemExit):
            ns._configure_provider("nonexistent")

    def test_infini_config(self):
        ns = _load_daemon()
        with patch.dict(os.environ, {"INFINI_API_KEY": "sk-test"}):
            ns._configure_provider("infini")
        assert ns._URL == "https://cloud.infini-ai.com/maas/coding"


class TestDaemonGolemEnv:
    def test_includes_effectors_in_path(self):
        ns = _load_daemon()
        env = ns._golem_env()
        assert "effectors" in env["PATH"]

    def test_includes_venv_bin(self):
        ns = _load_daemon()
        env = ns._golem_env()
        assert ".venv" in env["PATH"]


class TestDaemonClean:
    def test_clean_removes_done_and_failed(self, tmp_queue):
        ns = _load_daemon()
        lock_path = tmp_queue.parent / "golem-queue.lock"
        with _patch_ns(ns, QUEUE_FILE=tmp_queue):
            ns["QueueLock"]._lock_path = lock_path
            ns.mark_done(4, "exit=0")
            ns.mark_failed(5, "exit=2 bad", exit_code=2)
            ret = ns.cmd_clean()
        assert ret == 0
        content = tmp_queue.read_text()
        assert "- [x]" not in content
        assert "- [!]" not in content

    def test_clean_missing_queue(self, tmp_path):
        ns = _load_daemon()
        with _patch_ns(ns, QUEUE_FILE=tmp_path / "nope.md"):
            ret = ns.cmd_clean()
        assert ret == 1


class TestDaemonRotateLogs:
    def test_rotate_no_files(self, tmp_path):
        ns = _load_daemon()
        with _patch_ns(ns, LOGFILE=tmp_path / "nope.log", JSONLFILE=tmp_path / "nope.jsonl"):
            ns.rotate_logs()

    def test_rotate_large_file(self, tmp_path):
        ns = _load_daemon()
        big_log = tmp_path / "golem-daemon.log"
        big_log.write_bytes(b"x" * (6 * 1024 * 1024))
        rotated = tmp_path / "golem-daemon.log.1"
        with _patch_ns(ns, LOGFILE=big_log, JSONLFILE=tmp_path / "nope.jsonl"):
            ns.rotate_logs()
        assert rotated.exists()
        assert not big_log.exists()

    def test_rotate_small_file_kept(self, tmp_path):
        ns = _load_daemon()
        small_log = tmp_path / "golem-daemon.log"
        small_log.write_text("small log\n")
        with _patch_ns(ns, LOGFILE=small_log, JSONLFILE=tmp_path / "nope.jsonl"):
            ns.rotate_logs()
        assert small_log.exists()


class TestDaemonAutoCommit:
    def test_nothing_to_commit(self):
        ns = _load_daemon()
        mock_result_quiet = MagicMock()
        mock_result_quiet.returncode = 0  # no staged changes
        with patch("subprocess.run", return_value=mock_result_quiet):
            result = ns.auto_commit()
        assert result == "nothing to commit"


# ===================================================================
# golem-dash tests
# ===================================================================


class TestDashFmtBytes:
    def test_bytes(self):
        ns = _load_dash()
        assert ns.fmt_bytes(500) == "500.0 B"

    def test_kilobytes(self):
        ns = _load_dash()
        result = ns.fmt_bytes(2048)
        assert "2.0 KB" == result

    def test_gigabytes(self):
        ns = _load_dash()
        result = ns.fmt_bytes(2 * 1024 * 1024 * 1024)
        assert "GB" in result

    def test_zero(self):
        ns = _load_dash()
        assert ns.fmt_bytes(0) == "0.0 B"

    def test_negative(self):
        ns = _load_dash()
        result = ns.fmt_bytes(-1)
        assert "B" in result


class TestDashLoadJsonl:
    def test_load_valid(self, tmp_jsonl):
        ns = _load_dash()
        records = ns.load_jsonl(tmp_jsonl)
        assert len(records) == 3
        assert records[0]["provider"] == "zhipu"

    def test_load_missing(self, tmp_path):
        ns = _load_dash()
        assert ns.load_jsonl(tmp_path / "nope.jsonl") == []

    def test_load_with_malformed(self, tmp_path):
        ns = _load_dash()
        j = tmp_path / "bad.jsonl"
        j.write_text('{"valid": true}\nnot json\n{"also": true}\n')
        records = ns.load_jsonl(j)
        assert len(records) == 2

    def test_load_empty_lines(self, tmp_path):
        ns = _load_dash()
        j = tmp_path / "empty_lines.jsonl"
        j.write_text('\n\n{"provider": "zhipu"}\n\n')
        records = ns.load_jsonl(j)
        assert len(records) == 1


class TestDashProviderStats:
    def test_basic_stats(self, tmp_jsonl):
        ns = _load_dash()
        records = ns.load_jsonl(tmp_jsonl)
        output = ns.provider_stats(records, use_color=False)
        assert "zhipu" in output
        assert "volcano" in output

    def test_empty_records(self):
        ns = _load_dash()
        output = ns.provider_stats([], use_color=False)
        assert "No task records" in output

    def test_with_color(self, tmp_jsonl):
        ns = _load_dash()
        records = ns.load_jsonl(tmp_jsonl)
        output = ns.provider_stats(records, use_color=True)
        assert "\033[" in output


class TestDashQueueStatus:
    def test_basic_status(self, tmp_queue):
        ns = _load_dash()
        status_text, last_done = ns.queue_status(tmp_queue, use_color=False)
        assert "Pending: 3" in status_text
        assert "Done: 0" in status_text

    def test_missing_queue(self, tmp_path):
        ns = _load_dash()
        output = ns.queue_status(tmp_path / "nope.md", use_color=False)
        assert "not found" in output.lower()

    def test_with_done_tasks(self, tmp_path):
        ns = _load_dash()
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
        ns = _load_dash()
        output = ns.disk_free(use_color=False)
        assert "Free:" in output


class TestDashMain:
    def test_help_flag(self, capsys):
        ns = _load_dash()
        ret = ns.main(["--help"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "golem-dash" in captured.out

    def test_no_color(self, capsys, tmp_jsonl, tmp_queue):
        ns = _load_dash()
        with _patch_ns(ns, JSONL_PATH=tmp_jsonl, QUEUE_PATH=tmp_queue):
            ret = ns.main(["--no-color"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "\033[" not in captured.out

    def test_dashboard_output(self, capsys, tmp_jsonl, tmp_queue):
        ns = _load_dash()
        with _patch_ns(ns, JSONL_PATH=tmp_jsonl, QUEUE_PATH=tmp_queue):
            ns.print_dashboard(use_color=False)
        captured = capsys.readouterr()
        assert "Provider Stats" in captured.out
        assert "Queue Status" in captured.out
        assert "Disk" in captured.out


class TestDashLastCompleted:
    def test_empty(self):
        ns = _load_dash()
        output = ns.last_completed_table([], use_color=False)
        assert "No completed" in output

    def test_with_entries(self):
        ns = _load_dash()
        entries = [('golem "Write tests"', "exit=0")]
        output = ns.last_completed_table(entries, use_color=False)
        assert "Write tests" in output


# ===================================================================
# golem-health tests
# ===================================================================


class TestHealthSourceEnv:
    def test_missing_file(self, tmp_path):
        ns = _load_health()
        result = ns.source_env_file(tmp_path / "nope")
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_parses_env_file(self, tmp_path):
        ns = _load_health()
        env_f = tmp_path / ".env.fly"
        env_f.write_text('export ZHIPU_API_KEY="sk-test-123"\nVOLCANO_API_KEY=sk-volc\n')
        result = ns.source_env_file(env_f)
        assert "ZHIPU_API_KEY" in result
        assert result["ZHIPU_API_KEY"] == "sk-test-123"
        assert result["VOLCANO_API_KEY"] == "sk-volc"


class TestHealthCheckProvider:
    def test_unknown_provider(self):
        ns = _load_health()
        env = os.environ.copy()
        golem_path = EFFECTORS_DIR / "golem"
        result = ns.check_provider("unknown_provider", env, golem_path)
        assert result.status == "ERROR"
        assert "Unknown provider" in result.error

    def test_missing_key(self):
        ns = _load_health()
        env = {}
        golem_path = EFFECTORS_DIR / "golem"
        result = ns.check_provider("zhipu", env, golem_path)
        assert result.status == "FAIL"
        assert "ZHIPU_API_KEY not set" in result.error


class TestHealthPrintTable:
    def test_print_results(self, capsys):
        ns = _load_health()
        result = ns.HealthResult(
            provider="zhipu", status="OK", latency_ms=150,
            model="GLM-5.1", exit_code=0, has_output=True,
        )
        ns.print_table([result])
        captured = capsys.readouterr()
        assert "zhipu" in captured.out
        assert "OK" in captured.out
        assert "150ms" in captured.out

    def test_print_with_error(self, capsys):
        ns = _load_health()
        result = ns.HealthResult(
            provider="infini", status="FAIL", latency_ms=0,
            model="glm-5", exit_code=1, has_output=False, error="timeout",
        )
        ns.print_table([result])
        captured = capsys.readouterr()
        assert "timeout" in captured.out


class TestHealthPrintJson:
    def test_print_json(self, capsys):
        ns = _load_health()
        result = ns.HealthResult(
            provider="zhipu", status="OK", latency_ms=100,
            model="GLM-5.1", exit_code=0, has_output=True,
        )
        ns.print_json([result])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["provider"] == "zhipu"
        assert data[0]["status"] == "OK"


class TestHealthMain:
    def test_help_flag(self):
        ns = _load_health()
        with pytest.raises(SystemExit) as exc_info:
            ns.main(["--help"])
        assert exc_info.value.code == 0


# ===================================================================
# golem-reviewer tests
# ===================================================================


class TestReviewerRun:
    def test_run_echo(self):
        ns = _load_reviewer()
        code, out = ns.run("echo hello")
        assert code == 0
        assert "hello" in out

    def test_run_failure(self):
        ns = _load_reviewer()
        code, out = ns.run("false")
        assert code != 0

    def test_run_timeout(self):
        ns = _load_reviewer()
        code, out = ns.run("sleep 10", cwd="/tmp")
        assert code == 124


class TestReviewerCheckDaemonStatus:
    def test_parses_running(self):
        ns = _load_reviewer()
        with patch.dict(ns, {}):
            with patch.object(ns, "run", return_value=(0, "Daemon running (PID 1234), 5 pending tasks (zhipu:3)")):
                status = ns.check_daemon_status()
        assert status["running"] is True
        assert status["pending"] == 5

    def test_parses_not_running(self):
        ns = _load_reviewer()
        with patch.dict(ns, {}):
            with patch.object(ns, "run", return_value=(1, "Daemon not running")):
                status = ns.check_daemon_status()
        assert status["running"] is False
        assert status["pending"] == 0


class TestReviewerFixCollectionErrors:
    def test_no_errors(self):
        ns = _load_reviewer()
        with _patch_ns(ns):
            with patch.object(ns, "run", return_value=(1, "")):
                fixed = ns.fix_collection_errors()
        assert fixed == 0

    def test_fixes_hardcoded_paths(self, tmp_path):
        ns = _load_reviewer()
        test_file = tmp_path / "assays" / "test_example.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(
            'import os\n'
            'path = "/Users/terry/germline/foo.py"\n'
            'def test_something():\n'
            '    assert True\n'
        )
        with _patch_ns(ns, GERMLINE=tmp_path):
            with patch.object(ns, "run", return_value=(0, f"ERROR {test_file}")):
                fixed = ns.fix_collection_errors()
        assert fixed == 1
        fixed_content = test_file.read_text()
        assert "/Users/terry/" not in fixed_content
        assert str(Path.home()) in fixed_content


class TestReviewerRunTestSnapshot:
    def test_parses_output(self):
        ns = _load_reviewer()
        with patch.object(ns, "run", return_value=(0, "10 passed, 2 failed, 1 error")):
            result = ns.run_test_snapshot()
        assert result["passed"] == 10
        assert result["failed"] == 2
        assert result["errors"] == 1

    def test_empty_output(self):
        ns = _load_reviewer()
        with patch.object(ns, "run", return_value=(1, "")):
            result = ns.run_test_snapshot()
        assert result["passed"] == 0
        assert result["failed"] == 0
        assert result["errors"] == 0


class TestReviewerCheckDaemonFailures:
    def test_with_failures(self):
        ns = _load_reviewer()
        with patch.object(ns, "run", return_value=(0, "FAILED task A\nFAILED task B\n")):
            failures = ns.check_daemon_failures()
        assert len(failures) == 2

    def test_no_failures(self):
        ns = _load_reviewer()
        with patch.object(ns, "run", return_value=(1, "")):
            failures = ns.check_daemon_failures()
        assert failures == []


class TestReviewerWriteProgressReport:
    def test_writes_report(self, tmp_path):
        ns = _load_reviewer()
        copia = tmp_path / "copia"
        copia.mkdir()
        ns["cycle_number"] = 1
        status = {"running": True, "pending": 5}
        output = {"new_tests": 3, "new_effectors": 1, "consulting_pieces": 2}
        tests = {"passed": 10, "failed": 1, "errors": 0}
        with _patch_ns(ns, GERMLINE=tmp_path):
            ns.write_progress_report(status, output, tests, [])
        report_file = copia / "reviewer-cycle-1.md"
        assert report_file.exists()
        content = report_file.read_text()
        assert "Cycle 1" in content
        assert "5 pending" in content


# ===================================================================
# golem-validate tests
# ===================================================================


class TestValidateFile:
    def test_valid_file(self, tmp_path):
        ns = _load_validate()
        good = tmp_path / "good.py"
        good.write_text("x = 1\ny = 2\n")
        status, issues = ns.validate_file(good)
        assert status == "PASS"
        assert issues == []

    def test_syntax_error(self, tmp_path):
        ns = _load_validate()
        bad = tmp_path / "bad.py"
        bad.write_text("def broken(\n")
        status, issues = ns.validate_file(bad)
        assert status == "FAIL"
        assert any("SyntaxError" in i for i in issues)

    def test_hardcoded_mac_path(self, tmp_path):
        ns = _load_validate()
        f = tmp_path / "path.py"
        f.write_text('p = "/Users/terry/germline"\n')
        status, issues = ns.validate_file(f)
        assert status == "FAIL"
        assert any("/Users/terry/" in i for i in issues)

    def test_todo_marker(self, tmp_path):
        ns = _load_validate()
        f = tmp_path / "todo.py"
        f.write_text("# TODO: fix this later\nx = 1\n")
        status, issues = ns.validate_file(f)
        assert status == "FAIL"
        assert any("TODO" in i for i in issues)

    def test_fixme_marker(self, tmp_path):
        ns = _load_validate()
        f = tmp_path / "fixme.py"
        f.write_text("# FIXME: broken\nx = 1\n")
        status, issues = ns.validate_file(f)
        assert status == "FAIL"
        assert any("FIXME" in i for i in issues)

    def test_stub_marker(self, tmp_path):
        ns = _load_validate()
        f = tmp_path / "stub.py"
        f.write_text("def stub():\n    pass\n")
        status, issues = ns.validate_file(f)
        assert status == "FAIL"
        assert any("stub" in i.lower() for i in issues)

    def test_unreadable_file(self, tmp_path):
        ns = _load_validate()
        f = tmp_path / "unreadable.py"
        f.write_text("x = 1\n")
        f.chmod(0o000)
        try:
            status, issues = ns.validate_file(f)
            assert status == "FAIL"
        finally:
            f.chmod(0o644)

    def test_test_file_collectability_pass(self, tmp_path):
        ns = _load_validate()
        f = tmp_path / "test_good.py"
        f.write_text("def test_ok():\n    assert True\n")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1 test collected"
        with patch("subprocess.run", return_value=mock_result):
            status, issues = ns.validate_file(f)
        assert status == "PASS"

    def test_test_file_collection_failure(self, tmp_path):
        ns = _load_validate()
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
        ns = _load_validate()
        ret = ns.main([])
        assert ret == 2

    def test_valid_file(self, tmp_path, capsys):
        ns = _load_validate()
        good = tmp_path / "good.py"
        good.write_text("x = 1\n")
        ret = ns.main([str(good)])
        assert ret == 0
        captured = capsys.readouterr()
        assert "PASS" in captured.out

    def test_invalid_file(self, tmp_path, capsys):
        ns = _load_validate()
        bad = tmp_path / "bad.py"
        bad.write_text("def (\n")
        ret = ns.main([str(bad)])
        assert ret == 1
        captured = capsys.readouterr()
        assert "FAIL" in captured.out

    def test_multiple_files(self, tmp_path, capsys):
        ns = _load_validate()
        good = tmp_path / "good.py"
        good.write_text("x = 1\n")
        bad = tmp_path / "bad.py"
        bad.write_text("def (\n")
        ret = ns.main([str(good), str(bad)])
        assert ret == 1
        captured = capsys.readouterr()
        assert "PASS" in captured.out
        assert "FAIL" in captured.out


# ===================================================================
# golem (bash script) tests via subprocess
# ===================================================================


class TestGolemBashHelp:
    def test_help_flag(self):
        result = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "golem" in result.stdout.lower()

    def test_summary_help(self):
        result = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0


class TestGolemBashSummary:
    def test_summary_no_log(self, tmp_path):
        log_file = tmp_path / "golem.jsonl"
        result = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert result.returncode != 0

    def test_summary_with_data(self, tmp_path):
        log_file = tmp_path / "golem.jsonl"
        records = [
            {"provider": "zhipu", "exit": 0, "duration": 120},
            {"provider": "zhipu", "exit": 1, "duration": 60},
        ]
        log_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        result = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert result.returncode == 0
        assert "zhipu" in result.stdout

    def test_summary_recent_flag(self, tmp_path):
        log_file = tmp_path / "golem.jsonl"
        records = [{"provider": "zhipu", "exit": 0, "duration": 10}]
        log_file.write_text(json.dumps(records[0]) + "\n")
        result = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", "--recent", "5"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(log_file)},
        )
        assert result.returncode == 0

    def test_summary_custom_log(self, tmp_path):
        log_file = tmp_path / "custom.jsonl"
        log_file.write_text(json.dumps({"provider": "volcano", "exit": 0, "duration": 200}) + "\n")
        result = subprocess.run(
            [str(EFFECTORS_DIR / "golem"), "summary", f"--log={log_file}"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GOLEM_LOG": str(tmp_path / "default.jsonl")},
        )
        assert result.returncode == 0
        assert "volcano" in result.stdout
