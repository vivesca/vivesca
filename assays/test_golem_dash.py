#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/golem-dash — golem dashboard."""

import json
import textwrap
from datetime import datetime, timedelta
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
fmt_duration = _mod["fmt_duration"]
etime_to_seconds = _mod["etime_to_seconds"]
extract_task_snippet = _mod["extract_task_snippet"]
calculate_eta = _mod["calculate_eta"]
throughput_rate = _mod["throughput_rate"]
progress_bar = _mod["progress_bar"]
eta_wall_clock = _mod["eta_wall_clock"]
completion_burst = _mod["completion_burst"]
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

    def test_main_json_output(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text("# Queue\n")
            rc = main(["--json"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "timestamp" in data
        assert "running" in data
        assert "queue" in data
        assert "eta" in data


# ── fmt_duration ──────────────────────────────────────────────────────────


class TestFmtDuration:
    def test_seconds_only(self):
        assert fmt_duration(45) == "45s"

    def test_minutes_and_seconds(self):
        assert fmt_duration(125) == "2m 5s"

    def test_hours_and_minutes(self):
        assert fmt_duration(3665) == "1h 1m"

    def test_days_and_hours(self):
        assert fmt_duration(90000) == "1d 1h"

    def test_zero(self):
        assert fmt_duration(0) == "0s"


# ── etime_to_seconds ─────────────────────────────────────────────────────


class TestEtimeToSeconds:
    def test_simple_seconds(self):
        assert etime_to_seconds("00:45") == 45

    def test_minutes_seconds(self):
        assert etime_to_seconds("05:30") == 330

    def test_hours_minutes_seconds(self):
        assert etime_to_seconds("01:02:03") == 3723

    def test_days(self):
        assert etime_to_seconds("1-00:00:00") == 86400

    def test_days_with_time(self):
        assert etime_to_seconds("2-03:15:30") == 183330

    def test_days_short(self):
        assert etime_to_seconds("1-12:00") == 129600


# ── extract_task_snippet ────────────────────────────────────────────────


class TestExtractTaskSnippet:
    def test_golem_command(self):
        result = extract_task_snippet('/home/terry/germline/effectors/golem --provider zhipu "hello world"')
        assert "hello world" in result

    def test_shell_prefix(self):
        result = extract_task_snippet('/bin/sh -c golem --provider volcano "test task"')
        assert "test task" in result

    def test_strips_flags(self):
        result = extract_task_snippet(
            'effectors/golem --provider infini --max-turns 30 "do stuff"'
        )
        assert "do stuff" in result
        assert "--provider" not in result
        assert "--max-turns" not in result

    def test_truncates_long_task(self):
        long_task = "x" * 100
        result = extract_task_snippet(f'effectors/golem --provider zhipu "{long_task}"')
        assert len(result) <= 70  # 60 chars + ellipsis char
        assert "…" in result


# ── calculate_eta ────────────────────────────────────────────────────────


class TestCalculateEta:
    def test_no_pending(self):
        eta = calculate_eta([], pending=0, running_count=0)
        assert eta["eta_seconds"] == 0
        assert eta["eta_str"] == "—"

    def test_with_duration_data(self):
        recs = [
            {"duration": 100},
            {"duration": 200},
            {"duration": 300},
        ]
        eta = calculate_eta(recs, pending=6, running_count=2)
        # median duration = 200, workers=2, tasks=6 → 6*200/2 = 600s
        assert eta["eta_seconds"] == 600
        assert eta["avg_duration"] == 200

    def test_no_duration_data_uses_default(self):
        eta = calculate_eta([], pending=5, running_count=1)
        assert eta["avg_duration"] == 120
        assert eta["eta_seconds"] == 600  # 5*120/1

    def test_workers_at_least_one(self):
        eta = calculate_eta([{"duration": 60}], pending=3, running_count=0)
        assert eta["workers"] == 1


# ── throughput_rate ──────────────────────────────────────────────────────


class TestThroughputRate:
    def test_no_records(self):
        rate = throughput_rate([], window_minutes=60)
        assert rate == 0.0

    def test_recent_records(self):
        now = datetime.now()
        recs = []
        for i in range(5):
            recs.append({"ts": (now - timedelta(minutes=10 * i)).isoformat(), "exit": 0})
        rate = throughput_rate(recs, window_minutes=60)
        assert rate == pytest.approx(5.0, abs=0.1)

    def test_old_records_excluded(self):
        now = datetime.now()
        recs = [
            {"ts": (now - timedelta(hours=2)).isoformat(), "exit": 0},
            {"ts": (now - timedelta(hours=3)).isoformat(), "exit": 0},
        ]
        rate = throughput_rate(recs, window_minutes=60)
        assert rate == 0.0

    def test_mixed_old_and_new(self):
        now = datetime.now()
        recs = [
            {"ts": (now - timedelta(minutes=5)).isoformat(), "exit": 0},
            {"ts": (now - timedelta(minutes=15)).isoformat(), "exit": 0},
            {"ts": (now - timedelta(hours=2)).isoformat(), "exit": 0},
        ]
        rate = throughput_rate(recs, window_minutes=60)
        assert rate == pytest.approx(2.0, abs=0.1)

    def test_iso_format_with_z(self):
        now = datetime.now()
        recs = [{"ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "exit": 0}]
        rate = throughput_rate(recs, window_minutes=60)
        assert rate == pytest.approx(1.0, abs=0.1)


# ── progress_bar ────────────────────────────────────────────────────────


class TestProgressBar:
    def test_zero_percent(self):
        bar = progress_bar(0, 10)
        assert "0%" in bar

    def test_fifty_percent(self):
        bar = progress_bar(5, 10)
        assert "50%" in bar

    def test_one_hundred_percent(self):
        bar = progress_bar(10, 10)
        assert "100%" in bar

    def test_empty_queue(self):
        bar = progress_bar(0, 0)
        assert "0%" in bar or "—" in bar

    def test_has_visual_bar(self):
        bar = progress_bar(3, 10, width=20)
        assert "█" in bar or "|" in bar or "#" in bar

    def test_width_parameter(self):
        bar10 = progress_bar(5, 10, width=10)
        bar30 = progress_bar(5, 10, width=30)
        assert len(bar30) > len(bar10)


# ── eta_wall_clock ──────────────────────────────────────────────────────


class TestEtaWallClock:
    def test_zero_eta(self):
        result = eta_wall_clock(0)
        assert result == "—"

    def test_positive_eta(self):
        result = eta_wall_clock(3600)
        # Should contain a time in HH:MM format
        assert ":" in result

    def test_format_contains_now_marker(self):
        result = eta_wall_clock(0)
        assert result == "—"


# ── completion_burst ────────────────────────────────────────────────────


class TestCompletionBurst:
    def test_no_records(self):
        m15, m60 = completion_burst([])
        assert m15 == 0
        assert m60 == 0

    def test_recent_completions(self):
        now = datetime.now()
        recs = []
        for i in range(3):
            recs.append({"ts": (now - timedelta(minutes=5 * i)).isoformat(), "exit": 0})
        for i in range(2):
            recs.append({"ts": (now - timedelta(minutes=45 + 5 * i)).isoformat(), "exit": 0})
        m15, m60 = completion_burst(recs)
        assert m15 == 3
        assert m60 == 5

    def test_old_records_only(self):
        now = datetime.now()
        recs = [{"ts": (now - timedelta(hours=3)).isoformat(), "exit": 0}]
        m15, m60 = completion_burst(recs)
        assert m15 == 0
        assert m60 == 0


# ── print_dashboard includes new sections ───────────────────────────────


class TestDashboardNewSections:
    def test_includes_progress_bar(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0}\n'
                '{"ts":"2026-01-01","provider":"zhipu","duration":20,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text(textwrap.dedent("""\
                # Queue
                - [x] `golem --provider zhipu "task A"` → exit=0
                - [x] `golem --provider zhipu "task B"` → exit=0
                - [ ] `golem --provider zhipu "task C"`
            """))
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        assert "Progress" in captured.out
        assert "2/3" in captured.out or "67%" in captured.out

    def test_includes_throughput(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            now_iso = datetime.now().isoformat()
            (tmp_path / "golem.jsonl").write_text(
                f'{{"ts":"{now_iso}","provider":"zhipu","duration":10,"exit":0}}\n'
            )
            (tmp_path / "queue.md").write_text("# Queue\n")
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        assert "Throughput" in captured.out or "Rate" in captured.out or "/hr" in captured.out

    def test_includes_eta_wall_clock(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":120,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text(
                '- [ ] `golem --provider zhipu "task A"`\n'
                '- [ ] `golem --provider zhipu "task B"`\n'
            )
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        assert "ETA" in captured.out


# ── watch mode argument parsing ─────────────────────────────────────────


class TestWatchMode:
    def test_watch_flag_parsed(self):
        """Verify --watch is recognized without crashing."""
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        tmp = Path("/tmp")
        try:
            _mod["JSONL_PATH"] = tmp / "_golem_dash_test.jsonl"
            _mod["QUEUE_PATH"] = tmp / "_golem_dash_queue.md"
            (tmp / "_golem_dash_test.jsonl").write_text("")
            (tmp / "_golem_dash_queue.md").write_text("# Queue\n")
            # Run once (no loop) — the --watch flag should be accepted
            rc = main(["--no-color", "--watch", "0"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
            for f in ["_golem_dash_test.jsonl", "_golem_dash_queue.md"]:
                p = tmp / f
                if p.exists():
                    p.unlink()
        assert rc == 0

    def test_help_flag(self, capsys):
        rc = main(["--help"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "golem-dash" in captured.out
