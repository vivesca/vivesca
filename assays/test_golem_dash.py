#!/usr/bin/env python3
from __future__ import annotations
"""Tests for effectors/golem-dash — golem dashboard."""

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_dash():
    """Load golem-dash module via exec."""
    source = Path("/home/terry/germline/effectors/golem-dash").read_text()
    ns: dict = {"__name__": "golem_dash"}
    exec(source, ns)
    return ns


_mod = _load_dash()
load_jsonl = _mod["load_jsonl"]
provider_stats = _mod["provider_stats"]
queue_status = _mod["queue_status"]
last_completed_table = _mod["last_completed_table"]
disk_free = _mod["disk_free"]
fmt_bytes = _mod["fmt_bytes"]
main = _mod["main"]
print_dashboard = _mod["print_dashboard"]
JSONL_PATH = _mod["JSONL_PATH"]
QUEUE_PATH = _mod["QUEUE_PATH"]


# ── fmt_bytes ──────────────────────────────────────────────────────────────


class TestFmtBytes:
    def test_bytes(self):
        assert fmt_bytes(500) == "500.0 B"

    def test_kilobytes(self):
        assert fmt_bytes(2048) == "2.0 KB"

    def test_megabytes(self):
        assert fmt_bytes(5 * 1024 * 1024) == "5.0 MB"

    def test_gigabytes(self):
        assert fmt_bytes(50 * 1024 ** 3) == "50.0 GB"

    def test_zero(self):
        assert fmt_bytes(0) == "0.0 B"


# ── load_jsonl ────────────────────────────────────────────────────────────


class TestLoadJsonl:
    def test_missing_file(self, tmp_path):
        assert load_jsonl(tmp_path / "nope.jsonl") == []

    def test_empty_file(self, tmp_path):
        p = tmp_path / "golem.jsonl"
        p.write_text("")
        assert load_jsonl(p) == []

    def test_valid_records(self, tmp_path):
        p = tmp_path / "golem.jsonl"
        p.write_text(
            '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0}\n'
            '{"ts":"2026-01-02","provider":"volcano","duration":20,"exit":1}\n'
        )
        recs = load_jsonl(p)
        assert len(recs) == 2
        assert recs[0]["provider"] == "zhipu"
        assert recs[1]["exit"] == 1

    def test_skips_bad_lines(self, tmp_path):
        p = tmp_path / "golem.jsonl"
        p.write_text('{"ok":true}\nBADLINE\n{"ok":false}\n')
        recs = load_jsonl(p)
        assert len(recs) == 2

    def test_skips_blank_lines(self, tmp_path):
        p = tmp_path / "golem.jsonl"
        p.write_text('{"a":1}\n\n{"b":2}\n')
        recs = load_jsonl(p)
        assert len(recs) == 2


# ── provider_stats ────────────────────────────────────────────────────────


class TestProviderStats:
    def test_empty_records(self):
        result = provider_stats([], use_color=False)
        assert "No task records" in result

    def test_single_provider_pass(self):
        recs = [{"provider": "zhipu", "exit": 0, "duration": 10}]
        result = provider_stats(recs, use_color=False)
        assert "zhipu" in result
        assert "100%" in result
        assert "10s" in result

    def test_single_provider_fail(self):
        recs = [{"provider": "volcano", "exit": 1, "duration": 5}]
        result = provider_stats(recs, use_color=False)
        assert "volcano" in result
        assert "0%" in result

    def test_mixed_results(self):
        recs = [
            {"provider": "infini", "exit": 0, "duration": 20},
            {"provider": "infini", "exit": 0, "duration": 40},
            {"provider": "infini", "exit": 1, "duration": 10},
        ]
        result = provider_stats(recs, use_color=False)
        assert "67%" in result
        assert "23s" in result  # (20+40+10)/3

    def test_multiple_providers(self):
        recs = [
            {"provider": "zhipu", "exit": 0, "duration": 5},
            {"provider": "volcano", "exit": 1, "duration": 3},
        ]
        result = provider_stats(recs, use_color=False)
        assert "zhipu" in result
        assert "volcano" in result

    def test_color_mode_includes_ansi(self):
        recs = [{"provider": "zhipu", "exit": 0, "duration": 10}]
        result = provider_stats(recs, use_color=True)
        assert "\033[" in result

    def test_no_color_mode_excludes_ansi(self):
        recs = [{"provider": "zhipu", "exit": 0, "duration": 10}]
        result = provider_stats(recs, use_color=False)
        assert "\033[" not in result


# ── queue_status ───────────────────────────────────────────────────────────


class TestQueueStatus:
    def test_missing_file(self, tmp_path):
        result = queue_status(tmp_path / "nope.md", use_color=False)
        assert "not found" in result

    def test_empty_queue(self, tmp_path):
        p = tmp_path / "queue.md"
        p.write_text("# Golem Task Queue\n\n## Pending\n\n## Done\n")
        result, last = queue_status(p, use_color=False)
        assert "Pending: 0" in result
        assert "Done: 0" in result
        assert "Failed: 0" in result
        assert last == []

    def test_pending_tasks(self, tmp_path):
        p = tmp_path / "queue.md"
        p.write_text(textwrap.dedent("""\
            # Queue
            ## Pending
            - [ ] `golem --provider zhipu "task A"`
            - [ ] `golem --provider volcano "task B"`
        """))
        result, _ = queue_status(p, use_color=False)
        assert "Pending: 2" in result

    def test_done_tasks(self, tmp_path):
        p = tmp_path / "queue.md"
        p.write_text(textwrap.dedent("""\
            # Queue
            ## Pending
            ## Done
            - [x] `golem --provider zhipu "task A"` → exit=0
            - [x] `golem --provider volcano "task B"` → exit=0
        """))
        result, last = queue_status(p, use_color=False)
        assert "Done: 2" in result
        assert len(last) == 2

    def test_failed_tasks(self, tmp_path):
        p = tmp_path / "queue.md"
        p.write_text(textwrap.dedent("""\
            # Queue
            - [!] `golem --provider zhipu "task A"`
        """))
        result, _ = queue_status(p, use_color=False)
        assert "Failed: 1" in result

    def test_last_five_completed(self, tmp_path):
        p = tmp_path / "queue.md"
        lines = ["# Queue", "## Done"]
        for i in range(7):
            lines.append(f'- [x] `golem --provider zhipu "task {i}"` → exit=0')
        p.write_text("\n".join(lines) + "\n")
        result, last = queue_status(p, use_color=False)
        assert len(last) == 5
        # Should be the last 5 (indices 2..6)
        assert "task 6" in last[-1][0]
        assert "task 2" in last[0][0]


# ── last_completed_table ──────────────────────────────────────────────────


class TestLastCompletedTable:
    def test_empty(self):
        result = last_completed_table([], use_color=False)
        assert "No completed" in result

    def test_single_task(self):
        tasks = [('golem --provider zhipu "Say hello"', "exit=0")]
        result = last_completed_table(tasks, use_color=False)
        assert "Say hello" in result
        assert "exit=0" in result

    def test_color_mode(self):
        tasks = [('golem --provider zhipu "test"', "ok")]
        result = last_completed_table(tasks, use_color=True)
        assert "\033[" in result


# ── disk_free ─────────────────────────────────────────────────────────────


class TestDiskFree:
    def test_returns_string(self):
        result = disk_free(use_color=False)
        assert "Free:" in result
        assert "GB" in result or "MB" in result or "TB" in result

    def test_no_color_no_ansi(self):
        result = disk_free(use_color=False)
        assert "\033[" not in result

    def test_mocked_low_disk(self):
        usage = type("usage", (), {"free": 500_000_000, "total": 50_000_000_000})()
        with patch("shutil.disk_usage", return_value=usage):
            result = disk_free(use_color=True)
            assert "Free:" in result


# ── main / print_dashboard ────────────────────────────────────────────────


class TestMain:
    def test_main_no_color(self, tmp_path, capsys):
        # Point to empty temp files (mutate exec namespace directly)
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text("")
            (tmp_path / "queue.md").write_text("# Queue\n")
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        assert "Provider Stats" in captured.out
        assert "Queue Status" in captured.out
        assert "Last Completed" in captured.out
        assert "Disk" in captured.out

    def test_main_with_color(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text(
                '- [x] `golem --provider zhipu "hello"` → exit=0\n'
            )
            rc = main([])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        assert "\033[" in captured.out
        assert "zhipu" in captured.out

    def test_script_exists(self):
        assert Path("/home/terry/germline/effectors/golem-dash").exists()

    def test_script_executable(self):
        p = Path("/home/terry/germline/effectors/golem-dash")
        assert p.stat().st_mode & 0o111
