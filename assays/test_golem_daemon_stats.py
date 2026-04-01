"""Tests for golem-daemon cmd_stats command."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest


@pytest.fixture
def daemon_ns():
    """Load golem-daemon into a namespace for testing."""
    ns = {"__name__": "golem_daemon_test", "__file__": str(Path.home() / "germline" / "effectors" / "golem-daemon")}
    exec(open(Path.home() / "germline" / "effectors" / "golem-daemon").read(), ns)
    return ns


@pytest.fixture
def jsonl_file(tmp_path):
    """Create a temp JSONL file path."""
    return tmp_path / "golem.jsonl"


@pytest.fixture
def queue_file(tmp_path):
    """Create a temp queue file path."""
    return tmp_path / "golem-queue.md"


def _write_jsonl(path: Path, records: list[dict]):
    """Write JSONL records to a file."""
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _sample_records(today: str) -> list[dict]:
    """Create sample JSONL records for testing."""
    return [
        {"ts": f"{today}T10:00:00Z", "provider": "zhipu", "duration": 120, "exit": 0, "turns": 30,
         "prompt": "task1", "tail": "", "files_created": 1, "tests_passed": 5, "tests_failed": 0, "pytest_exit": 0},
        {"ts": f"{today}T10:05:00Z", "provider": "zhipu", "duration": 180, "exit": 1, "turns": 30,
         "prompt": "task2", "tail": "error", "files_created": 0, "tests_passed": 0, "tests_failed": 2, "pytest_exit": 1},
        {"ts": f"{today}T10:10:00Z", "provider": "infini", "duration": 60, "exit": 0, "turns": 25,
         "prompt": "task3", "tail": "", "files_created": 2, "tests_passed": 3, "tests_failed": 0, "pytest_exit": 0},
        {"ts": f"{today}T10:15:00Z", "provider": "volcano", "duration": 300, "exit": 0, "turns": 30,
         "prompt": "task4", "tail": "", "files_created": 3, "tests_passed": 10, "tests_failed": 0, "pytest_exit": 0},
        {"ts": f"{today}T10:20:00Z", "provider": "volcano", "duration": 90, "exit": 1, "turns": 30,
         "prompt": "task5", "tail": "fail", "files_created": 0, "tests_passed": 0, "tests_failed": 1, "pytest_exit": 1},
        # Yesterday
        {"ts": "2000-01-01T10:00:00Z", "provider": "zhipu", "duration": 200, "exit": 0, "turns": 30,
         "prompt": "old", "tail": "", "files_created": 0, "tests_passed": 0, "tests_failed": 0, "pytest_exit": 0},
    ]


class TestCmdStatsBasic:
    def test_no_jsonl_file(self, daemon_ns, tmp_path, capsys):
        """Stats with no JSONL file should report no history."""
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        assert "No task history found" in out

    def test_totals(self, daemon_ns, tmp_path, capsys):
        """Stats should show correct total pass/fail counts."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n## Done\n")
        _write_jsonl(jsonl, _sample_records(today))

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        # 6 records total: 4 passed (exit=0), 2 failed (exit=1)
        assert "Total tasks: 6" in out
        assert "passed: 4" in out
        assert "failed: 2" in out

    def test_today_counts(self, daemon_ns, tmp_path, capsys):
        """Stats should filter today's tasks correctly."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n## Done\n")
        _write_jsonl(jsonl, _sample_records(today))

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        # 5 records today (the 6th is from 2000-01-01): 3 passed, 2 failed
        assert f"Tasks today ({today}): 5" in out
        assert "passed: 3" in out or "passed: 3" in out

    def test_retry_count_from_queue(self, daemon_ns, tmp_path, capsys):
        """Stats should count permanently failed ([!]) from queue."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n- [!] `golem cmd1`\n- [!] `golem cmd2`\n- [ ] `golem cmd3`\n## Done\n")
        _write_jsonl(jsonl, _sample_records(today))

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        assert "Permanently failed (retries exhausted): 2" in out

    def test_provider_stats(self, daemon_ns, tmp_path, capsys):
        """Stats should show per-provider breakdown with avg duration."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n## Done\n")
        _write_jsonl(jsonl, _sample_records(today))

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        assert "By provider:" in out
        # zhipu: 3 tasks (2 today + 1 old), durations 120+180+200=500, avg=166.7s=2m46s
        assert "zhipu" in out
        assert "infini" in out
        assert "volcano" in out

    def test_provider_avg_duration(self, daemon_ns, tmp_path, capsys):
        """Avg duration should be computed correctly per provider."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n## Done\n")
        _write_jsonl(jsonl, _sample_records(today))

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        # infini: 1 task, 60s → avg 1m00s
        assert "infini" in out
        # Check avg duration format (e.g., "avg 1m00s")
        lines = out.splitlines()
        for line in lines:
            if "infini" in line:
                assert "avg 1m00s" in line

    def test_returns_zero(self, daemon_ns, tmp_path, capsys):
        """cmd_stats should return 0 on success."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n## Done\n")
        _write_jsonl(jsonl, _sample_records(today))

        with _patch_constants(daemon_ns, jsonl, queue):
            ret = daemon_ns["cmd_stats"]()

        assert ret == 0

    def test_returns_zero_no_history(self, daemon_ns, tmp_path, capsys):
        """cmd_stats should return 0 even with no history."""
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"

        with _patch_constants(daemon_ns, jsonl, queue):
            ret = daemon_ns["cmd_stats"]()

        assert ret == 0


class TestCmdStatsRotatedLog:
    def test_reads_rotated_jsonl(self, daemon_ns, tmp_path, capsys):
        """Stats should also read from .1 rotated file."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        rotated = tmp_path / "golem.jsonl.1"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n## Done\n")

        # Only rotated file has data
        _write_jsonl(rotated, [
            {"ts": f"{today}T08:00:00Z", "provider": "zhipu", "duration": 90, "exit": 0, "turns": 30,
             "prompt": "old1", "tail": "", "files_created": 0, "tests_passed": 0, "tests_failed": 0, "pytest_exit": 0},
        ])

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        assert "Total tasks: 1" in out
        assert "passed: 1" in out

    def test_merges_both_jsonl_files(self, daemon_ns, tmp_path, capsys):
        """Stats should merge records from both jsonl and jsonl.1."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        rotated = tmp_path / "golem.jsonl.1"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n## Done\n")

        _write_jsonl(jsonl, [
            {"ts": f"{today}T10:00:00Z", "provider": "zhipu", "duration": 100, "exit": 0, "turns": 30,
             "prompt": "new", "tail": "", "files_created": 0, "tests_passed": 0, "tests_failed": 0, "pytest_exit": 0},
        ])
        _write_jsonl(rotated, [
            {"ts": f"{today}T08:00:00Z", "provider": "volcano", "duration": 200, "exit": 1, "turns": 30,
             "prompt": "old", "tail": "", "files_created": 0, "tests_passed": 0, "tests_failed": 0, "pytest_exit": 0},
        ])

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        assert "Total tasks: 2" in out


class TestCmdStatsEdgeCases:
    def test_malformed_jsonl_lines(self, daemon_ns, tmp_path, capsys):
        """Malformed JSONL lines should be skipped."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n## Done\n")

        jsonl.write_text(
            '{"ts":"' + today + 'T10:00:00Z","provider":"zhipu","duration":60,"exit":0,"turns":30,"prompt":"ok","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}\n'
            "NOT JSON\n"
            '{"ts":"' + today + 'T10:01:00Z","provider":"zhipu","duration":90,"exit":0,"turns":30,"prompt":"ok2","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}\n'
        )

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        assert "Total tasks: 2" in out

    def test_empty_jsonl(self, daemon_ns, tmp_path, capsys):
        """Empty JSONL file should report no history."""
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        jsonl.write_text("")

        with _patch_constants(daemon_ns, jsonl, queue):
            ret = daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        assert "No task history found" in out
        assert ret == 0

    def test_no_queue_file(self, daemon_ns, tmp_path, capsys):
        """Stats should work even if queue file doesn't exist."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "nonexistent" / "queue.md"
        _write_jsonl(jsonl, _sample_records(today))

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        assert "Permanently failed (retries exhausted): 0" in out

    def test_all_passed(self, daemon_ns, tmp_path, capsys):
        """All-passed scenario."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n## Done\n")
        _write_jsonl(jsonl, [
            {"ts": f"{today}T10:00:00Z", "provider": "zhipu", "duration": 60, "exit": 0, "turns": 30,
             "prompt": "ok", "tail": "", "files_created": 0, "tests_passed": 0, "tests_failed": 0, "pytest_exit": 0},
        ])

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        assert "passed: 1, failed: 0" in out

    def test_all_failed(self, daemon_ns, tmp_path, capsys):
        """All-failed scenario."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n- [!] `golem fail1`\n## Done\n")
        _write_jsonl(jsonl, [
            {"ts": f"{today}T10:00:00Z", "provider": "zhipu", "duration": 10, "exit": 1, "turns": 30,
             "prompt": "fail", "tail": "err", "files_created": 0, "tests_passed": 0, "tests_failed": 0, "pytest_exit": 1},
            {"ts": f"{today}T10:01:00Z", "provider": "volcano", "duration": 5, "exit": 2, "turns": 30,
             "prompt": "fail2", "tail": "err", "files_created": 0, "tests_passed": 0, "tests_failed": 0, "pytest_exit": 1},
        ])

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        assert "Total tasks: 2" in out
        assert "passed: 0, failed: 2" in out
        assert "Permanently failed (retries exhausted): 1" in out


class TestCmdStatsMainIntegration:
    def test_stats_dispatch(self, daemon_ns, tmp_path, capsys, monkeypatch):
        """'golem-daemon stats' should dispatch to cmd_stats."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n## Done\n")
        _write_jsonl(jsonl, [
            {"ts": f"{today}T10:00:00Z", "provider": "zhipu", "duration": 60, "exit": 0, "turns": 30,
             "prompt": "ok", "tail": "", "files_created": 0, "tests_passed": 0, "tests_failed": 0, "pytest_exit": 0},
        ])

        with _patch_constants(daemon_ns, jsonl, queue):
            monkeypatch.setattr("sys.argv", ["golem-daemon", "stats"])
            ret = daemon_ns["main"]()

        out = capsys.readouterr().out
        assert ret == 0
        assert "Total tasks: 1" in out


class TestCmdStatsProviderBreakdown:
    def test_provider_passed_failed_counts(self, daemon_ns, tmp_path, capsys):
        """Per-provider passed/failed should be correct."""
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "golem-queue.md"
        queue.write_text("## Queue\n## Done\n")
        _write_jsonl(jsonl, [
            {"ts": f"{today}T10:00:00Z", "provider": "zhipu", "duration": 120, "exit": 0, "turns": 30,
             "prompt": "a", "tail": "", "files_created": 0, "tests_passed": 0, "tests_failed": 0, "pytest_exit": 0},
            {"ts": f"{today}T10:01:00Z", "provider": "zhipu", "duration": 180, "exit": 1, "turns": 30,
             "prompt": "b", "tail": "", "files_created": 0, "tests_passed": 0, "tests_failed": 0, "pytest_exit": 0},
            {"ts": f"{today}T10:02:00Z", "provider": "zhipu", "duration": 60, "exit": 0, "turns": 30,
             "prompt": "c", "tail": "", "files_created": 0, "tests_passed": 0, "tests_failed": 0, "pytest_exit": 0},
        ])

        with _patch_constants(daemon_ns, jsonl, queue):
            daemon_ns["cmd_stats"]()

        out = capsys.readouterr().out
        # zhipu: 3 tasks, 2 passed, 1 failed, avg=(120+180+60)/3=120s=2m00s
        lines = out.splitlines()
        for line in lines:
            if "zhipu" in line:
                assert "3 tasks" in line
                assert "2 passed" in line
                assert "1 failed" in line
                assert "avg 2m00s" in line


def _patch_constants(ns, jsonl_path: Path, queue_path: Path):
    """Return a context manager that patches JSONLFILE and QUEUE_FILE in the namespace."""
    from contextlib import contextmanager
    from unittest.mock import patch as _patch

    @contextmanager
    def _ctx():
        # Patch the module-level constants in the exec'd namespace
        orig_jsonl = ns.get("JSONLFILE")
        orig_queue = ns.get("QUEUE_FILE")
        ns["JSONLFILE"] = jsonl_path
        ns["QUEUE_FILE"] = queue_path
        # Also patch the cmd_stats closure globals by replacing the function
        # Re-exec cmd_stats with the patched constants
        import types

        # Since cmd_stats reads JSONLFILE and QUEUE_FILE at call time from
        # the namespace globals, we need to patch them in the exec namespace
        # which is the module globals for the loaded code.
        try:
            yield
        finally:
            if orig_jsonl is not None:
                ns["JSONLFILE"] = orig_jsonl
            else:
                ns.pop("JSONLFILE", None)
            if orig_queue is not None:
                ns["QUEUE_FILE"] = orig_queue
            else:
                ns.pop("QUEUE_FILE", None)

    return _ctx()
