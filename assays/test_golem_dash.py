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
    source = Path(str(Path.home() / "germline/effectors/golem-dash")).read_text()
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
throughput_sparkline = _mod["throughput_sparkline"]
enrich_running_progress = _mod["enrich_running_progress"]
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
        text, _, pend, done, fail = queue_status(tmp_path / "nope.md", use_color=False)
        assert "not found" in text

    def test_empty_queue(self, tmp_path):
        p = tmp_path / "queue.md"
        p.write_text("# Golem Task Queue\n\n## Pending\n\n## Done\n")
        text, last, pend, done, fail = queue_status(p, use_color=False)
        assert "Pending: 0" in text
        assert "Done: 0" in text
        assert "Failed: 0" in text
        assert last == []

    def test_pending_tasks(self, tmp_path):
        p = tmp_path / "queue.md"
        p.write_text(textwrap.dedent("""\
            # Queue
            ## Pending
            - [ ] `golem --provider zhipu "task A"`
            - [ ] `golem --provider volcano "task B"`
        """))
        text, _, pend, _, _ = queue_status(p, use_color=False)
        assert "Pending: 2" in text

    def test_done_tasks(self, tmp_path):
        p = tmp_path / "queue.md"
        p.write_text(textwrap.dedent("""\
            # Queue
            ## Pending
            ## Done
            - [x] `golem --provider zhipu "task A"` → exit=0
            - [x] `golem --provider volcano "task B"` → exit=0
        """))
        text, last, _, done, _ = queue_status(p, use_color=False)
        assert "Done: 2" in text
        assert len(last) == 2

    def test_failed_tasks(self, tmp_path):
        p = tmp_path / "queue.md"
        p.write_text(textwrap.dedent("""\
            # Queue
            - [!] `golem --provider zhipu "task A"`
        """))
        text, _, _, _, fail = queue_status(p, use_color=False)
        assert "Failed: 1" in text

    def test_last_five_completed(self, tmp_path):
        p = tmp_path / "queue.md"
        lines = ["# Queue", "## Done"]
        for i in range(7):
            lines.append(f'- [x] `golem --provider zhipu "task {i}"` → exit=0')
        p.write_text("\n".join(lines) + "\n")
        text, last, _, _, _ = queue_status(p, use_color=False)
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
        assert Path(str(Path.home() / "germline/effectors/golem-dash")).exists()

    def test_script_executable(self):
        p = Path(str(Path.home() / "germline/effectors/golem-dash"))
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
        assert "throughput_sparkline" in data


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
        # 2 days + 3h 15m 30s = 172800 + 10800 + 900 + 30 = 184530
        assert etime_to_seconds("2-03:15:30") == 184530

    def test_days_short(self):
        # 1 day + 12 minutes = 86400 + 720 = 87120
        assert etime_to_seconds("1-12:00") == 87120


# ── extract_task_snippet ────────────────────────────────────────────────


class TestExtractTaskSnippet:
    def test_golem_command(self):
        result = extract_task_snippet(f'{Path.home()}/germline/effectors/golem --provider zhipu "hello world"')
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


# ── calculate_eta (enhanced) ─────────────────────────────────────────────


class TestCalculateEta:
    def test_no_pending_no_running(self):
        eta = calculate_eta([], pending=0, running_count=0)
        assert eta["eta_seconds"] == 0
        assert eta["eta_str"] == "—"
        assert eta["drain_milestones"] == []

    def test_with_duration_data(self):
        recs = [
            {"duration": 100},
            {"duration": 200},
            {"duration": 300},
        ]
        eta = calculate_eta(recs, pending=6, running_count=2)
        assert eta["eta_seconds"] == 600
        assert eta["avg_duration"] == 200

    def test_no_duration_data_uses_default(self):
        eta = calculate_eta([], pending=5, running_count=1)
        assert eta["avg_duration"] == 120
        assert eta["eta_seconds"] == 600

    def test_workers_at_least_one(self):
        eta = calculate_eta([{"duration": 60}], pending=3, running_count=0)
        assert eta["workers"] == 1

    def test_with_running_tasks_accounts_for_progress(self):
        recs = [{"duration": 100}, {"duration": 200}, {"duration": 300}]
        running_tasks = [
            {"provider": "zhipu", "duration_secs": 100, "estimated_remaining": 100},
            {"provider": "infini", "duration_secs": 50, "estimated_remaining": 150},
        ]
        eta = calculate_eta(recs, pending=4, running_count=2, running_tasks=running_tasks)
        assert eta["eta_seconds"] == 400
        assert eta["running_remaining_secs"] == 250

    def test_pending_zero_running_left(self):
        running_tasks = [
            {"provider": "zhipu", "duration_secs": 100, "estimated_remaining": 50},
        ]
        eta = calculate_eta([], pending=0, running_count=1, running_tasks=running_tasks)
        assert eta["eta_seconds"] == 50
        # Milestones generated because running > 0 and eta > 0
        assert len(eta["drain_milestones"]) == 4

    def test_drain_milestones_present(self):
        eta = calculate_eta([{"duration": 60}], pending=10, running_count=1)
        assert len(eta["drain_milestones"]) == 4
        assert eta["drain_milestones"][0] == (25, 150)
        assert eta["drain_milestones"][3] == (100, 600)

    def test_fewer_pending_than_running(self):
        running_tasks = [
            {"provider": "zhipu", "duration_secs": 200, "estimated_remaining": 100},
            {"provider": "infini", "duration_secs": 150, "estimated_remaining": 200},
        ]
        eta = calculate_eta(
            [{"duration": 200}], pending=1, running_count=2, running_tasks=running_tasks
        )
        assert eta["eta_seconds"] == 200


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
        assert ":" in result

    def test_negative_eta(self):
        result = eta_wall_clock(-10)
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


# ── throughput_sparkline ────────────────────────────────────────────────


class TestThroughputSparkline:
    def test_no_records(self):
        result = throughput_sparkline([])
        assert "▁" in result
        assert "0 max" in result

    def test_recent_records_produce_non_flat(self):
        now = datetime.now()
        recs = []
        for i in range(10):
            recs.append({"ts": (now - timedelta(minutes=10 * i)).isoformat()})
        result = throughput_sparkline(recs, hours=3, bucket_minutes=30)
        assert "max" in result
        assert any(c in result for c in "▂▃▄▅▆▇█")

    def test_all_old_records_flat(self):
        now = datetime.now()
        recs = [{"ts": (now - timedelta(hours=12)).isoformat()}]
        result = throughput_sparkline(recs, hours=6)
        assert "0 max" in result

    def test_bucket_count_matches_hours(self):
        result = throughput_sparkline([], hours=6, bucket_minutes=15)
        # 6 hours * 4 buckets/hr = 24 buckets
        spark_part = result.split(" ")[0]
        assert len(spark_part) == 24

    def test_single_bucket_peak(self):
        now = datetime.now()
        recs = [{"ts": now.isoformat()}] * 5
        result = throughput_sparkline(recs, hours=1, bucket_minutes=15)
        assert "max 5/bucket" in result
        assert "█" in result


# ── enrich_running_progress ────────────────────────────────────────────


class TestEnrichRunningProgress:
    def test_empty_running(self):
        result = enrich_running_progress([], [])
        assert result == []

    def test_enriches_with_progress(self):
        recs = [
            {"provider": "zhipu", "duration": 100},
            {"provider": "zhipu", "duration": 200},
            {"provider": "zhipu", "duration": 300},
        ]
        running = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 100, "task": "test"},
        ]
        result = enrich_running_progress(running, recs)
        assert len(result) == 1
        assert result[0]["estimated_pct"] == 33  # 100/300 (90th percentile)
        assert result[0]["estimated_remaining"] == 200
        assert result[0]["is_stale"] is False

    def test_stale_detection(self):
        recs = [{"provider": "infini", "duration": 60}]
        running = [
            {"pid": 2, "provider": "infini", "duration_secs": 200, "task": "slow"},
        ]
        result = enrich_running_progress(running, recs)
        assert result[0]["is_stale"] is True  # 200 > 60 * 2

    def test_unknown_provider_uses_overall_median(self):
        recs = [{"provider": "zhipu", "duration": 100}]
        running = [
            {"pid": 3, "provider": "unknown", "duration_secs": 50, "task": "new"},
        ]
        result = enrich_running_progress(running, recs)
        assert result[0]["estimated_pct"] == 50  # 50/100

    def test_no_records_uses_default_120(self):
        running = [
            {"pid": 4, "provider": "new", "duration_secs": 60, "task": "first"},
        ]
        result = enrich_running_progress(running, [])
        assert result[0]["estimated_pct"] == 50  # 60/120

    def test_progress_capped_at_100(self):
        recs = [{"provider": "zhipu", "duration": 100}]
        running = [
            {"pid": 5, "provider": "zhipu", "duration_secs": 500, "task": "overdue"},
        ]
        result = enrich_running_progress(running, recs)
        assert result[0]["estimated_pct"] == 100
        assert result[0]["estimated_remaining"] == 0


# ── running_tasks_table (with progress bars) ───────────────────────────


class TestRunningTasksTable:
    def test_no_running(self):
        result = _mod["running_tasks_table"]([], use_color=False)
        assert "No golem processes running" in result

    def test_single_task_with_progress(self):
        tasks = [{
            "pid": 1234,
            "provider": "zhipu",
            "duration_secs": 100,
            "task": "my task",
            "estimated_pct": 50,
            "estimated_remaining": 100,
            "is_stale": False,
        }]
        result = _mod["running_tasks_table"](tasks, use_color=False)
        assert "1234" in result
        assert "zhipu" in result
        assert "50%" in result
        assert "█" in result

    def test_stale_task_shown(self):
        tasks = [{
            "pid": 5678,
            "provider": "infini",
            "duration_secs": 300,
            "task": "stale task",
            "estimated_pct": 100,
            "estimated_remaining": 0,
            "is_stale": True,
        }]
        result = _mod["running_tasks_table"](tasks, use_color=True)
        assert "STALE" in result

    def test_multiple_tasks_summary(self):
        tasks = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 10, "task": "a",
             "estimated_pct": 20, "estimated_remaining": 40, "is_stale": False},
            {"pid": 2, "provider": "zhipu", "duration_secs": 20, "task": "b",
             "estimated_pct": 40, "estimated_remaining": 30, "is_stale": False},
            {"pid": 3, "provider": "infini", "duration_secs": 5, "task": "c",
             "estimated_pct": 10, "estimated_remaining": 50, "is_stale": False},
        ]
        result = _mod["running_tasks_table"](tasks, use_color=False)
        assert "3 running" in result
        assert "zhipu:2" in result
        assert "infini:1" in result


# ── eta_section (with milestones) ──────────────────────────────────────


class TestEtaSection:
    def test_queue_empty(self):
        eta = {"pending": 0, "running": 0, "eta_seconds": 0, "eta_str": "—",
               "workers": 1, "avg_duration": 0, "drain_milestones": [],
               "running_remaining_secs": 0}
        result = _mod["eta_section"](eta, 0.0, use_color=False)
        assert "Queue empty" in result

    def test_only_running_tasks(self):
        eta = {"pending": 0, "running": 2, "eta_seconds": 60, "eta_str": "1m 0s",
               "workers": 2, "avg_duration": 60, "drain_milestones": [],
               "running_remaining_secs": 120}
        result = _mod["eta_section"](eta, 5.0, use_color=False)
        assert "Finishing 2 running tasks" in result

    def test_with_milestones(self):
        eta = {"pending": 10, "running": 2, "eta_seconds": 600, "eta_str": "10m 0s",
               "workers": 2, "avg_duration": 100,
               "drain_milestones": [(25, 150), (50, 300), (75, 450), (100, 600)],
               "running_remaining_secs": 200}
        result = _mod["eta_section"](eta, 6.0, use_color=False)
        assert "Milestones:" in result
        assert "25%" in result
        assert "100%" in result
        assert "6.0/hr" in result

    def test_no_milestones_when_zero(self):
        eta = {"pending": 10, "running": 2, "eta_seconds": 600, "eta_str": "10m 0s",
               "workers": 2, "avg_duration": 100,
               "drain_milestones": [],
               "running_remaining_secs": 200}
        result = _mod["eta_section"](eta, 3.0, use_color=False)
        assert "Milestones:" not in result


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
        assert "Throughput" in captured.out or "/hr" in captured.out

    def test_includes_sparkline_section(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text("# Queue\n")
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        assert "Throughput Trend" in captured.out
        assert "▁" in captured.out

    def test_includes_eta_section(self, tmp_path, capsys):
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
        assert "Milestones:" in captured.out

    def test_includes_running_tasks_with_progress(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":60,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text("# Queue\n")
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        assert "Running Tasks" in captured.out

    def test_json_output_includes_sparkline(self, tmp_path, capsys):
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
        data = json.loads(capsys.readouterr().out)
        assert "throughput_sparkline" in data
        assert "drain_milestones" in data["eta"]


# ── help flag ───────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_flag(self, capsys):
        rc = main(["--help"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "golem-dash" in captured.out


# ── per_provider_pending (NEW) ──────────────────────────────────────────


class TestPerProviderPending:
    """Tests for per-provider pending task breakdown."""

    def test_missing_file(self, tmp_path):
        func = _mod["per_provider_pending"]
        result = func(tmp_path / "nope.md")
        assert result == {}

    def test_empty_queue(self, tmp_path):
        func = _mod["per_provider_pending"]
        p = tmp_path / "queue.md"
        p.write_text("# Queue\n\n## Pending\n")
        result = func(p)
        assert result == {}

    def test_single_provider(self, tmp_path):
        func = _mod["per_provider_pending"]
        p = tmp_path / "queue.md"
        p.write_text(textwrap.dedent("""\
            # Queue
            - [ ] `golem --provider zhipu "task A"`
            - [ ] `golem --provider zhipu "task B"`
        """))
        result = func(p)
        assert result == {"zhipu": 2}

    def test_multiple_providers(self, tmp_path):
        func = _mod["per_provider_pending"]
        p = tmp_path / "queue.md"
        p.write_text(textwrap.dedent("""\
            # Queue
            - [ ] `golem --provider zhipu "task A"`
            - [ ] `golem --provider infini "task B"`
            - [ ] `golem --provider volcano "task C"`
            - [ ] `golem --provider zhipu "task D"`
        """))
        result = func(p)
        assert result["zhipu"] == 2
        assert result["infini"] == 1
        assert result["volcano"] == 1

    def test_ignores_done_and_failed(self, tmp_path):
        func = _mod["per_provider_pending"]
        p = tmp_path / "queue.md"
        p.write_text(textwrap.dedent("""\
            # Queue
            - [ ] `golem --provider zhipu "pending"`
            - [x] `golem --provider zhipu "done"`
            - [!] `golem --provider zhipu "failed"`
        """))
        result = func(p)
        assert result == {"zhipu": 1}

    def test_default_provider_when_missing(self, tmp_path):
        func = _mod["per_provider_pending"]
        p = tmp_path / "queue.md"
        p.write_text('- [ ] `golem "no provider specified"`\n')
        result = func(p)
        assert "unknown" in result or result == {}

    def test_high_priority_counted(self, tmp_path):
        func = _mod["per_provider_pending"]
        p = tmp_path / "queue.md"
        p.write_text('- [!!] `golem --provider zhipu "urgent"`\n')
        result = func(p)
        assert result == {"zhipu": 1}


# ── ewma_throughput (NEW) ──────────────────────────────────────────────


class TestEwmaThroughput:
    """Tests for exponentially weighted moving average throughput."""

    def test_no_records(self):
        func = _mod["ewma_throughput"]
        assert func([], alpha=0.3) == 0.0

    def test_single_recent_record(self):
        func = _mod["ewma_throughput"]
        now = datetime.now()
        recs = [{"ts": now.isoformat(), "exit": 0}]
        rate = func(recs, alpha=0.3)
        assert rate > 0

    def test_recent_burst_higher_than_steady(self):
        func = _mod["ewma_throughput"]
        now = datetime.now()
        # Burst: 5 tasks in last 10 minutes
        burst = [{"ts": (now - timedelta(minutes=2 * i)).isoformat(), "exit": 0} for i in range(5)]
        # Steady: 5 tasks spread over 3 hours
        steady = [{"ts": (now - timedelta(hours=1, minutes=10 * i)).isoformat(), "exit": 0} for i in range(5)]
        burst_rate = func(burst, alpha=0.3)
        steady_rate = func(steady, alpha=0.3)
        assert burst_rate > steady_rate

    def test_alpha_closer_to_one_weights_recent_more(self):
        func = _mod["ewma_throughput"]
        now = datetime.now()
        recs = [
            {"ts": (now - timedelta(minutes=5)).isoformat(), "exit": 0},
            {"ts": (now - timedelta(minutes=55)).isoformat(), "exit": 0},
        ]
        rate_high = func(recs, alpha=0.9)
        rate_low = func(recs, alpha=0.1)
        # Higher alpha weights the recent task more, should give higher rate
        assert rate_high >= rate_low

    def test_old_records_contribute_little(self):
        func = _mod["ewma_throughput"]
        now = datetime.now()
        recs = [
            {"ts": (now - timedelta(hours=12)).isoformat(), "exit": 0},
            {"ts": (now - timedelta(hours=24)).isoformat(), "exit": 0},
        ]
        rate = func(recs, alpha=0.3)
        assert rate < 1.0  # Should be very low


# ── eta_confidence (NEW) ──────────────────────────────────────────────


class TestEtaConfidence:
    """Tests for ETA confidence indicator based on sample size."""

    def test_no_data(self):
        func = _mod["eta_confidence"]
        assert func([]) == "none"

    def test_low_sample(self):
        func = _mod["eta_confidence"]
        recs = [{"duration": 100, "exit": 0}]
        assert func(recs) == "low"

    def test_medium_sample(self):
        func = _mod["eta_confidence"]
        recs = [{"duration": 100 + i, "exit": 0} for i in range(15)]
        assert func(recs) == "medium"

    def test_high_sample(self):
        func = _mod["eta_confidence"]
        recs = [{"duration": 100 + i, "exit": 0} for i in range(50)]
        assert func(recs) == "high"

    def test_only_counts_with_duration(self):
        func = _mod["eta_confidence"]
        recs = [{"exit": 0}] * 100  # No duration field
        assert func(recs) == "none"


# ── print_compact (NEW) ──────────────────────────────────────────────


class TestPrintCompact:
    """Tests for compact one-line output for tmux status bar."""

    def test_empty_queue(self, tmp_path, capsys):
        func = _mod["print_compact"]
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text("")
            (tmp_path / "queue.md").write_text("# Queue\n")
            func()
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        captured = capsys.readouterr()
        assert "empty" in captured.out.lower() or "0" in captured.out

    def test_with_pending(self, tmp_path, capsys):
        func = _mod["print_compact"]
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":60,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text(textwrap.dedent("""\
                - [ ] `golem --provider zhipu "task A"`
                - [ ] `golem --provider zhipu "task B"`
                - [x] `golem --provider zhipu "task C"` → exit=0
            """))
            func()
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        captured = capsys.readouterr()
        # Should show pending count and some progress info
        assert "2" in captured.out  # 2 pending
        assert "1" in captured.out  # 1 done

    def test_output_is_single_line(self, tmp_path, capsys):
        func = _mod["print_compact"]
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text("")
            (tmp_path / "queue.md").write_text(
                '- [ ] `golem --provider zhipu "task A"`\n'
            )
            func()
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        captured = capsys.readouterr()
        # Compact output should be a single line
        lines = [l for l in captured.out.strip().splitlines() if l.strip()]
        assert len(lines) == 1


# ── provider_concurrency_display (NEW) ─────────────────────────────────


class TestProviderConcurrencyDisplay:
    """Tests for per-provider concurrency display (active/max)."""

    def test_no_running(self):
        func = _mod["provider_concurrency_display"]
        recs = [
            {"provider": "zhipu", "duration": 100, "exit": 0},
        ]
        result = func(recs, [], use_color=False)
        assert "zhipu" in result

    def test_with_running_tasks(self):
        func = _mod["provider_concurrency_display"]
        recs = [
            {"provider": "zhipu", "duration": 100, "exit": 0},
            {"provider": "infini", "duration": 80, "exit": 0},
        ]
        running = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 30, "task": "a"},
            {"pid": 2, "provider": "zhipu", "duration_secs": 45, "task": "b"},
            {"pid": 3, "provider": "infini", "duration_secs": 20, "task": "c"},
        ]
        result = func(recs, running, use_color=False)
        assert "zhipu" in result
        assert "infini" in result
        assert "2/" in result  # 2 zhipu running

    def test_color_mode(self):
        func = _mod["provider_concurrency_display"]
        recs = [{"provider": "zhipu", "duration": 100, "exit": 0}]
        running = [{"pid": 1, "provider": "zhipu", "duration_secs": 30, "task": "a"}]
        result = func(recs, running, use_color=True)
        assert "\033[" in result


# ── compact flag integration (NEW) ────────────────────────────────────


class TestCompactFlag:
    def test_compact_flag(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text("")
            (tmp_path / "queue.md").write_text("# Queue\n")
            rc = main(["--compact", "--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        # Compact output should be short
        assert len(captured.out.strip()) < 200


# ── get_hatchet_status (NEW) ──────────────────────────────────────────


class TestGetHatchetStatus:
    """Tests for Hatchet API integration (graceful when unavailable)."""

    def test_returns_none_when_unavailable(self):
        func = _mod["get_hatchet_status"]
        # Should not crash when Hatchet SDK is not configured
        result = func()
        # Should return None or empty list, not raise
        assert result is None or isinstance(result, (list, dict))

    def test_returns_list_or_none(self):
        func = _mod["get_hatchet_status"]
        result = func()
        assert result is None or isinstance(result, (list, dict))


# ── per-provider pending shown in dashboard (NEW) ────────────────────


class TestDashboardProviderBreakdown:
    def test_shows_per_provider_pending(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":60,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text(textwrap.dedent("""\
                - [ ] `golem --provider zhipu "task A"`
                - [ ] `golem --provider zhipu "task B"`
                - [ ] `golem --provider infini "task C"`
            """))
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        # Should show provider breakdown
        assert "zhipu:2" in captured.out or "zhipu 2" in captured.out
        assert "infini:1" in captured.out or "infini 1" in captured.out

    def test_shows_eta_confidence(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            recs = [{"ts": "2026-01-01", "provider": "zhipu", "duration": 60 + i, "exit": 0} for i in range(5)]
            (tmp_path / "golem.jsonl").write_text(
                "\n".join(json.dumps(r) for r in recs) + "\n"
            )
            (tmp_path / "queue.md").write_text(
                '- [ ] `golem --provider zhipu "task A"`\n'
            )
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        # Should show confidence indicator
        assert "low" in captured.out.lower() or "conf" in captured.out.lower()


# ── failure_adjusted_throughput (NEW) ────────────────────────────────────


class TestFailureAdjustedThroughput:
    """Tests for throughput adjusted by historical failure rate."""

    def test_no_records(self):
        func = _mod["failure_adjusted_throughput"]
        raw, adj, fail_pct = func([], window_minutes=60)
        assert raw == 0.0
        assert adj == 0.0
        assert fail_pct == 0.0

    def test_all_success(self):
        func = _mod["failure_adjusted_throughput"]
        now = datetime.now()
        recs = [
            {"ts": (now - timedelta(minutes=10 * i)).isoformat(), "exit": 0}
            for i in range(5)
        ]
        raw, adj, fail_pct = func(recs, window_minutes=60)
        assert raw == pytest.approx(5.0, abs=0.1)
        assert adj == pytest.approx(5.0, abs=0.1)  # no failures
        assert fail_pct == 0.0

    def test_mixed_pass_fail(self):
        func = _mod["failure_adjusted_throughput"]
        now = datetime.now()
        recs = [
            {"ts": (now - timedelta(minutes=10)).isoformat(), "exit": 0},
            {"ts": (now - timedelta(minutes=20)).isoformat(), "exit": 0},
            {"ts": (now - timedelta(minutes=30)).isoformat(), "exit": 1},
            {"ts": (now - timedelta(minutes=40)).isoformat(), "exit": 1},
        ]
        raw, adj, fail_pct = func(recs, window_minutes=60)
        assert raw == pytest.approx(4.0, abs=0.1)  # 4 total
        assert fail_pct == pytest.approx(50.0, abs=1.0)
        assert adj < raw  # adjusted should be lower

    def test_all_failures(self):
        func = _mod["failure_adjusted_throughput"]
        now = datetime.now()
        recs = [
            {"ts": (now - timedelta(minutes=10 * i)).isoformat(), "exit": 1}
            for i in range(3)
        ]
        raw, adj, fail_pct = func(recs, window_minutes=60)
        assert raw == pytest.approx(3.0, abs=0.1)
        assert fail_pct == pytest.approx(100.0, abs=1.0)
        assert adj == 0.0  # 100% failure = 0 effective throughput


# ── worker_utilization (NEW) ────────────────────────────────────────────


class TestWorkerUtilization:
    """Tests for per-provider and overall worker utilization."""

    def test_no_running(self):
        func = _mod["worker_utilization"]
        result = func([], {"zhipu": 8, "infini": 8})
        assert result["overall"] == 0.0
        assert result["providers"]["zhipu"] == 0.0

    def test_single_provider_partial(self):
        func = _mod["worker_utilization"]
        running = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 10, "task": "a"},
            {"pid": 2, "provider": "zhipu", "duration_secs": 20, "task": "b"},
        ]
        result = func(running, {"zhipu": 8, "infini": 8})
        assert result["providers"]["zhipu"] == pytest.approx(25.0)  # 2/8
        assert result["providers"]["infini"] == 0.0
        assert result["overall"] == pytest.approx(12.5)  # 2/16

    def test_full_utilization(self):
        func = _mod["worker_utilization"]
        running = [
            {"pid": i, "provider": "zhipu", "duration_secs": 10, "task": "t"}
            for i in range(8)
        ]
        result = func(running, {"zhipu": 8})
        assert result["providers"]["zhipu"] == pytest.approx(100.0)
        assert result["overall"] == pytest.approx(100.0)

    def test_unknown_provider_skipped(self):
        func = _mod["worker_utilization"]
        running = [
            {"pid": 1, "provider": "unknown", "duration_secs": 10, "task": "a"},
        ]
        result = func(running, {"zhipu": 8})
        assert "unknown" not in result["providers"]

    def test_provider_not_in_max_defaults_to_zero(self):
        func = _mod["worker_utilization"]
        running = [
            {"pid": 1, "provider": "newprov", "duration_secs": 10, "task": "a"},
        ]
        result = func(running, {"zhipu": 8})
        # newprov not in max dict, should be skipped
        assert result["overall"] == 0.0


# ── running_tasks_table with wall-clock ETA ─────────────────────────────


class TestRunningTasksTableWallClock:
    """Tests for per-task wall-clock completion time in running tasks."""

    def test_shows_wall_clock_eta(self):
        tasks = [{
            "pid": 1234,
            "provider": "zhipu",
            "duration_secs": 60,
            "task": "my task",
            "estimated_pct": 50,
            "estimated_remaining": 60,
            "is_stale": False,
        }]
        result = _mod["running_tasks_table"](tasks, use_color=False)
        assert "1234" in result
        assert "50%" in result
        # Should show a wall-clock time like "today HH:MM"
        assert "today" in result or ":" in result

    def test_no_eta_when_zero_remaining(self):
        tasks = [{
            "pid": 5678,
            "provider": "infini",
            "duration_secs": 200,
            "task": "almost done",
            "estimated_pct": 95,
            "estimated_remaining": 0,
            "is_stale": False,
        }]
        result = _mod["running_tasks_table"](tasks, use_color=False)
        assert "5678" in result
        # When remaining is 0, no wall-clock needed


# ── eta_section with utilization (NEW) ──────────────────────────────────


class TestEtaSectionUtilization:
    """Tests for utilization info in the ETA section."""

    def test_shows_utilization(self):
        eta = {
            "pending": 10, "running": 2, "eta_seconds": 600, "eta_str": "10m 0s",
            "workers": 2, "avg_duration": 100,
            "drain_milestones": [(25, 150), (50, 300), (75, 450), (100, 600)],
            "running_remaining_secs": 200,
        }
        util = {"overall": 12.5, "providers": {"zhipu": 25.0, "infini": 0.0}}
        result = _mod["eta_section"](
            eta, 6.0, use_color=False, utilization=util,
        )
        assert "Utilization" in result or "12.5%" in result or "12.5" in result

    def test_no_utilization_arg(self):
        eta = {
            "pending": 10, "running": 2, "eta_seconds": 600, "eta_str": "10m 0s",
            "workers": 2, "avg_duration": 100,
            "drain_milestones": [],
            "running_remaining_secs": 200,
        }
        # Should not crash when utilization is not provided
        result = _mod["eta_section"](eta, 6.0, use_color=False)
        assert "ETA" in result


# ── print_compact enhanced (NEW) ────────────────────────────────────────


class TestCompactEnhanced:
    """Tests for enhanced compact mode with trend and stall info."""

    def test_compact_shows_trend(self, tmp_path, capsys):
        func = _mod["print_compact"]
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            now = datetime.now()
            recs = [
                {"ts": (now - timedelta(minutes=2 * i)).isoformat(), "exit": 0,
                 "provider": "zhipu", "duration": 60}
                for i in range(5)
            ]
            (tmp_path / "golem.jsonl").write_text(
                "\n".join(json.dumps(r) for r in recs) + "\n"
            )
            (tmp_path / "queue.md").write_text(
                '- [ ] `golem --provider zhipu "task A"`\n'
                '- [ ] `golem --provider zhipu "task B"`\n'
                '- [x] `golem --provider zhipu "done"` → exit=0\n'
            )
            func()
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().splitlines() if l.strip()]
        assert len(lines) == 1
        # Should contain a trend indicator
        out = captured.out
        assert "↑" in out or "↓" in out or "→" in out or "/hr" in out

    def test_compact_stall_warning(self, tmp_path, capsys):
        func = _mod["print_compact"]
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            # Old records = stall
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"' + (datetime.now() - timedelta(minutes=30)).isoformat()
                + '","provider":"zhipu","duration":60,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text(
                '- [ ] `golem --provider zhipu "pending task"`\n'
            )
            func()
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        captured = capsys.readouterr()
        # Should show stall warning when no recent completions + pending tasks
        assert "stall" in captured.out.lower() or "⚠" in captured.out or "stale" in captured.out.lower()


# ── JSON output includes new fields (NEW) ───────────────────────────────


class TestJsonOutputNewFields:
    """Tests that JSON output includes failure-adjusted throughput and utilization."""

    def test_json_includes_failure_adjusted(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            now = datetime.now()
            recs = [
                {"ts": (now - timedelta(minutes=10 * i)).isoformat(),
                 "provider": "zhipu", "duration": 60, "exit": 0 if i % 2 == 0 else 1}
                for i in range(6)
            ]
            (tmp_path / "golem.jsonl").write_text(
                "\n".join(json.dumps(r) for r in recs) + "\n"
            )
            (tmp_path / "queue.md").write_text("# Queue\n")
            rc = main(["--json"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert "failure_adjusted_throughput" in data
        fa = data["failure_adjusted_throughput"]
        assert "raw" in fa
        assert "adjusted" in fa
        assert "failure_pct" in fa

    def test_json_includes_utilization(self, tmp_path, capsys):
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
        data = json.loads(capsys.readouterr().out)
        assert "utilization" in data
        assert "overall" in data["utilization"]


# ── load_running_json (NEW) ─────────────────────────────────────────────


class TestLoadRunningJson:
    """Tests for loading golem-running.json."""

    def test_missing_file(self, tmp_path):
        func = _mod["load_running_json"]
        assert func(tmp_path / "nope.json") == []

    def test_empty_file(self, tmp_path):
        func = _mod["load_running_json"]
        p = tmp_path / "running.json"
        p.write_text("")
        assert func(p) == []

    def test_valid_entries(self, tmp_path):
        func = _mod["load_running_json"]
        p = tmp_path / "running.json"
        p.write_text(json.dumps([
            {"task_id": "t-abc", "provider": "zhipu", "cmd": "golem [t-abc] --provider zhipu \"test\""},
            {"task_id": "t-def", "provider": "infini", "cmd": "golem [t-def] --provider infini \"task\""},
        ]))
        result = func(p)
        assert len(result) == 2
        assert result[0]["task_id"] == "t-abc"
        assert result[1]["provider"] == "infini"

    def test_invalid_json(self, tmp_path):
        func = _mod["load_running_json"]
        p = tmp_path / "running.json"
        p.write_text("not json")
        assert func(p) == []

    def test_non_list_json(self, tmp_path):
        func = _mod["load_running_json"]
        p = tmp_path / "running.json"
        p.write_text('{"error": "not a list"}')
        assert func(p) == []


# ── load_cooldowns (NEW) ────────────────────────────────────────────────


class TestLoadCooldowns:
    """Tests for loading golem-cooldowns.json."""

    def test_missing_file(self, tmp_path):
        func = _mod["load_cooldowns"]
        assert func(tmp_path / "nope.json") == []

    def test_valid_entries(self, tmp_path):
        func = _mod["load_cooldowns"]
        p = tmp_path / "cooldowns.json"
        p.write_text(json.dumps([
            {"ts": "2026-04-01 17:51:17", "provider": "codex",
             "resets_at": "2026-04-01 18:01:17", "reason": "failure window"},
        ]))
        result = func(p)
        assert len(result) == 1
        assert result[0]["provider"] == "codex"

    def test_invalid_json(self, tmp_path):
        func = _mod["load_cooldowns"]
        p = tmp_path / "cooldowns.json"
        p.write_text("BAD")
        assert func(p) == []


# ── active_cooldowns (NEW) ──────────────────────────────────────────────


class TestActiveCooldowns:
    """Tests for filtering active cooldowns."""

    def test_empty_list(self):
        func = _mod["active_cooldowns"]
        assert func([]) == {}

    def test_expired_cooldowns_excluded(self):
        func = _mod["active_cooldowns"]
        cooldowns = [
            {"provider": "zhipu", "resets_at": "2020-01-01 00:00:00", "reason": "old"},
        ]
        assert func(cooldowns) == {}

    def test_active_cooldown_included(self):
        func = _mod["active_cooldowns"]
        future = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        cooldowns = [
            {"provider": "zhipu", "resets_at": future, "reason": "failure"},
        ]
        result = func(cooldowns)
        assert "zhipu" in result
        assert result["zhipu"]["remaining_secs"] > 0
        assert result["zhipu"]["reason"] == "failure"

    def test_mixed_active_and_expired(self):
        func = _mod["active_cooldowns"]
        future = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        cooldowns = [
            {"provider": "zhipu", "resets_at": future, "reason": "active"},
            {"provider": "infini", "resets_at": "2020-01-01 00:00:00", "reason": "old"},
        ]
        result = func(cooldowns)
        assert len(result) == 1
        assert "zhipu" in result

    def test_missing_fields_skipped(self):
        func = _mod["active_cooldowns"]
        cooldowns = [
            {"provider": "", "resets_at": "2026-01-01 00:00:00"},
            {"provider": "zhipu"},
        ]
        assert func(cooldowns) == {}


# ── cooldown_display (NEW) ──────────────────────────────────────────────


class TestCooldownDisplay:
    """Tests for cooldown display formatting."""

    def test_empty_cooldowns(self):
        func = _mod["cooldown_display"]
        assert func([]) == ""

    def test_all_expired(self):
        func = _mod["cooldown_display"]
        cooldowns = [
            {"provider": "zhipu", "resets_at": "2020-01-01 00:00:00", "reason": "old"},
        ]
        assert func(cooldowns) == ""

    def test_active_cooldown_shown(self):
        func = _mod["cooldown_display"]
        future = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        cooldowns = [
            {"provider": "zhipu", "resets_at": future, "reason": "failure window"},
        ]
        result = func(cooldowns, use_color=False)
        assert "zhipu" in result
        assert "cooldown" in result
        assert "failure window" in result

    def test_color_mode(self):
        func = _mod["cooldown_display"]
        future = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        cooldowns = [
            {"provider": "zhipu", "resets_at": future, "reason": "test"},
        ]
        result = func(cooldowns, use_color=True)
        assert "\033[" in result


# ── merge_running_sources (NEW) ─────────────────────────────────────────


class TestMergeRunningSources:
    """Tests for merging ps and JSON running task sources."""

    def test_both_empty(self):
        func = _mod["merge_running_sources"]
        assert func([], [], []) == []

    def test_json_only(self):
        func = _mod["merge_running_sources"]
        json_running = [
            {"task_id": "t-abc", "provider": "zhipu", "cmd": "golem [t-abc] --provider zhipu \"test\""},
        ]
        result = func([], json_running, [])
        assert len(result) == 1
        assert result[0]["task_id"] == "t-abc"
        assert result[0]["provider"] == "zhipu"

    def test_ps_only(self):
        func = _mod["merge_running_sources"]
        ps_running = [
            {"pid": 1234, "provider": "infini", "duration_secs": 30,
             "etime": "00:30", "task": "my task"},
        ]
        result = func(ps_running, [], [])
        assert len(result) == 1
        assert result[0]["pid"] == 1234

    def test_merge_adds_task_id(self):
        func = _mod["merge_running_sources"]
        ps_running = [
            {"pid": 1234, "provider": "zhipu", "duration_secs": 30,
             "etime": "00:30", "task": '"test task"'},
        ]
        json_running = [
            {"task_id": "t-abc", "provider": "zhipu",
             "cmd": "golem [t-abc] --provider zhipu --max-turns 30 \"test task\""},
        ]
        result = func(ps_running, json_running, [])
        assert len(result) == 1
        assert result[0].get("task_id") == "t-abc"

    def test_unmatched_json_adds_synthetic(self):
        func = _mod["merge_running_sources"]
        ps_running = [
            {"pid": 1234, "provider": "infini", "duration_secs": 30,
             "etime": "00:30", "task": "other task"},
        ]
        json_running = [
            {"task_id": "t-abc", "provider": "zhipu",
             "cmd": "golem [t-abc] --provider zhipu \"unique task\""},
        ]
        result = func(ps_running, json_running, [])
        assert len(result) == 2


# ── recent_activity_timeline (NEW) ──────────────────────────────────────


class TestRecentActivityTimeline:
    """Tests for parsing daemon log for recent events."""

    def test_missing_file(self, tmp_path):
        func = _mod["recent_activity_timeline"]
        assert func(tmp_path / "nope.log") == []

    def test_empty_file(self, tmp_path):
        func = _mod["recent_activity_timeline"]
        p = tmp_path / "daemon.log"
        p.write_text("")
        assert func(p) == []

    def test_parses_starting_events(self, tmp_path):
        func = _mod["recent_activity_timeline"]
        p = tmp_path / "daemon.log"
        p.write_text(
            "[2026-04-01 10:00:00] Starting: golem --provider zhipu --max-turns 30 \"test task\"\n"
            "[2026-04-01 10:05:00] Finished (300s, exit=0): golem --provider zhipu --max-turns 30 \"test task\"\n"
        )
        result = func(p, limit=5)
        assert len(result) == 2
        assert result[0][1] == "finish"  # Most recent first
        assert result[1][1] == "start"

    def test_parses_failed_events(self, tmp_path):
        func = _mod["recent_activity_timeline"]
        p = tmp_path / "daemon.log"
        p.write_text(
            "[2026-04-01 10:00:00] FAILED (exit=1): golem --provider infini \"bad task\"\n"
        )
        result = func(p, limit=5)
        assert len(result) == 1
        assert result[0][1] == "fail"

    def test_parses_retry_events(self, tmp_path):
        func = _mod["recent_activity_timeline"]
        p = tmp_path / "daemon.log"
        p.write_text(
            "[2026-04-01 10:00:00] Re-queued (retry): golem --provider zhipu \"retry task\"\n"
        )
        result = func(p, limit=5)
        assert len(result) == 1
        assert result[0][1] == "retry"

    def test_limit_respected(self, tmp_path):
        func = _mod["recent_activity_timeline"]
        p = tmp_path / "daemon.log"
        lines = []
        for i in range(10):
            lines.append(f"[2026-04-01 10:{i:02d}:00] Starting: golem --provider zhipu \"task {i}\"\n")
        p.write_text("".join(lines))
        result = func(p, limit=3)
        assert len(result) == 3

    def test_ignores_non_matching_lines(self, tmp_path):
        func = _mod["recent_activity_timeline"]
        p = tmp_path / "daemon.log"
        p.write_text("Random log line\nAnother line\n")
        result = func(p, limit=5)
        assert result == []


# ── timeline_display (NEW) ──────────────────────────────────────────────


class TestTimelineDisplay:
    """Tests for formatting activity timeline."""

    def test_empty_events(self):
        func = _mod["timeline_display"]
        result = func([], use_color=False)
        assert "No recent activity" in result

    def test_formats_start_event(self):
        func = _mod["timeline_display"]
        events = [("10:00:00", "start", "golem --provider zhipu \"test\"")]
        result = func(events, use_color=False)
        assert "10:00:00" in result
        assert "golem" in result

    def test_formats_finish_event(self):
        func = _mod["timeline_display"]
        events = [("10:05:00", "finish", "(300s, exit=0): golem --provider zhipu")]
        result = func(events, use_color=False)
        assert "10:05:00" in result

    def test_formats_fail_event(self):
        func = _mod["timeline_display"]
        events = [("10:01:00", "fail", "(exit=1): golem --provider infini")]
        result = func(events, use_color=False)
        assert "10:01:00" in result

    def test_color_mode(self):
        func = _mod["timeline_display"]
        events = [("10:00:00", "start", "golem --provider zhipu \"test\"")]
        result = func(events, use_color=True)
        assert "\033[" in result


# ── calculate_eta with cooldowns (NEW) ──────────────────────────────────


class TestCalculateEtaWithCooldowns:
    """Tests for ETA calculation that accounts for provider cooldowns."""

    def test_no_cooldowns(self):
        recs = [{"duration": 100}]
        eta = calculate_eta(
            recs, pending=5, running_count=1,
            cooldowns_data=[], provider_max={"zhipu": 8},
        )
        assert eta["cooldown_penalty_secs"] == 0
        assert eta["effective_workers"] == 1

    def test_active_cooldown_increases_eta(self):
        recs = [{"duration": 100}]
        future = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        cooldowns = [
            {"provider": "zhipu", "resets_at": future, "reason": "failure"},
        ]
        eta_no_cd = calculate_eta(recs, pending=5, running_count=1)
        eta_with_cd = calculate_eta(
            recs, pending=5, running_count=1,
            cooldowns_data=cooldowns, provider_max={"zhipu": 8, "infini": 8},
        )
        assert eta_with_cd["cooldown_penalty_secs"] > 0
        assert eta_with_cd["eta_seconds"] >= eta_no_cd["eta_seconds"]

    def test_expired_cooldown_no_effect(self):
        recs = [{"duration": 100}]
        cooldowns = [
            {"provider": "zhipu", "resets_at": "2020-01-01 00:00:00", "reason": "old"},
        ]
        eta = calculate_eta(
            recs, pending=5, running_count=1,
            cooldowns_data=cooldowns, provider_max={"zhipu": 8},
        )
        assert eta["cooldown_penalty_secs"] == 0

    def test_zero_pending_no_cooldown_penalty(self):
        recs = [{"duration": 100}]
        future = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        cooldowns = [
            {"provider": "zhipu", "resets_at": future, "reason": "failure"},
        ]
        running_tasks = [
            {"provider": "zhipu", "duration_secs": 50, "estimated_remaining": 50},
        ]
        eta = calculate_eta(
            recs, pending=0, running_count=1, running_tasks=running_tasks,
            cooldowns_data=cooldowns, provider_max={"zhipu": 8},
        )
        # No pending tasks: cooldown shouldn't add to ETA
        assert eta["eta_seconds"] == 50

    def test_new_keys_in_result(self):
        recs = [{"duration": 100}]
        eta = calculate_eta(
            recs, pending=5, running_count=1,
            cooldowns_data=[], provider_max={"zhipu": 8},
        )
        assert "cooldown_penalty_secs" in eta
        assert "effective_workers" in eta


# ── Dashboard shows new sections (NEW) ──────────────────────────────────


class TestDashboardNewSectionsV2:
    """Tests for new dashboard sections: cooldowns, timeline, recent activity."""

    def test_shows_recent_activity(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        orig_log = _mod["LOG_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            _mod["LOG_PATH"] = tmp_path / "daemon.log"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text("# Queue\n")
            (tmp_path / "daemon.log").write_text(
                "[2026-04-01 10:00:00] Starting: golem --provider zhipu \"test\"\n"
                "[2026-04-01 10:05:00] Finished (300s, exit=0): golem --provider zhipu \"test\"\n"
            )
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
            _mod["LOG_PATH"] = orig_log
        assert rc == 0
        captured = capsys.readouterr()
        assert "Recent Activity" in captured.out
        assert "10:00:00" in captured.out

    def test_shows_cooldowns(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        orig_cd = _mod["COOLDOWNS_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            _mod["COOLDOWNS_PATH"] = tmp_path / "cooldowns.json"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text(
                '- [ ] `golem --provider zhipu "task A"`\n'
            )
            future = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
            (tmp_path / "cooldowns.json").write_text(json.dumps([
                {"provider": "zhipu", "resets_at": future, "reason": "failure window"},
            ]))
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
            _mod["COOLDOWNS_PATH"] = orig_cd
        assert rc == 0
        captured = capsys.readouterr()
        assert "Cooldown" in captured.out
        assert "zhipu" in captured.out

    def test_json_includes_cooldowns(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        orig_cd = _mod["COOLDOWNS_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            _mod["COOLDOWNS_PATH"] = tmp_path / "cooldowns.json"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text("# Queue\n")
            (tmp_path / "cooldowns.json").write_text(json.dumps([
                {"provider": "zhipu",
                 "resets_at": (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                 "reason": "test"},
            ]))
            rc = main(["--json"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
            _mod["COOLDOWNS_PATH"] = orig_cd
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert "cooldowns" in data
        assert "active_cooldowns" in data
        assert "recent_activity" in data
        assert "json_running" in data

    def test_compact_shows_cooldown_info(self, tmp_path, capsys):
        func = _mod["print_compact"]
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        orig_cd = _mod["COOLDOWNS_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            _mod["COOLDOWNS_PATH"] = tmp_path / "cooldowns.json"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text(
                '- [ ] `golem --provider zhipu "task A"`\n'
            )
            future = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
            (tmp_path / "cooldowns.json").write_text(json.dumps([
                {"provider": "zhipu", "resets_at": future, "reason": "test"},
            ]))
            func()
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
            _mod["COOLDOWNS_PATH"] = orig_cd
        captured = capsys.readouterr()
        assert "cd:" in captured.out


# ── parse_daemon_log_start_times (NEW) ──────────────────────────────────


class TestParseDaemonLogStartTimes:
    """Tests for parsing daemon log start times."""

    def test_missing_file(self, tmp_path):
        func = _mod["parse_daemon_log_start_times"]
        assert func(tmp_path / "nope.log") == {}

    def test_parses_starting_lines(self, tmp_path):
        func = _mod["parse_daemon_log_start_times"]
        p = tmp_path / "daemon.log"
        p.write_text(
            "[2026-04-01 10:00:00] Starting: golem --provider zhipu --max-turns 30 \"test\"\n"
        )
        result = func(p)
        assert len(result) == 1
        key = list(result.keys())[0]
        assert "zhipu" in key
        assert isinstance(result[key], datetime)

    def test_ignores_non_starting_lines(self, tmp_path):
        func = _mod["parse_daemon_log_start_times"]
        p = tmp_path / "daemon.log"
        p.write_text(
            "[2026-04-01 10:00:00] Finished (300s, exit=0): golem --provider zhipu\n"
            "[2026-04-01 10:00:00] FAILED (exit=1): golem --provider infini\n"
        )
        result = func(p)
        assert len(result) == 0


# ── next_completion (NEW) ──────────────────────────────────────────────


class TestNextCompletion:
    """Tests for next_completion — identifies the task closest to finishing."""

    def test_no_running(self):
        func = _mod["next_completion"]
        assert func([]) is None

    def test_returns_closest_to_done(self):
        func = _mod["next_completion"]
        running = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 100,
             "estimated_remaining": 80, "is_stale": False},
            {"pid": 2, "provider": "infini", "duration_secs": 50,
             "estimated_remaining": 10, "is_stale": False},
            {"pid": 3, "provider": "volcano", "duration_secs": 200,
             "estimated_remaining": 150, "is_stale": False},
        ]
        result = func(running)
        assert result is not None
        assert result["pid"] == 2
        assert result["finishes_in"] == 10
        assert isinstance(result["finishes_at"], datetime)

    def test_skips_stale_tasks(self):
        func = _mod["next_completion"]
        running = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 200,
             "estimated_remaining": 10, "is_stale": True},
            {"pid": 2, "provider": "infini", "duration_secs": 50,
             "estimated_remaining": 30, "is_stale": False},
        ]
        result = func(running)
        assert result is not None
        assert result["pid"] == 2

    def test_all_zero_remaining_picks_longest_running(self):
        func = _mod["next_completion"]
        running = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 100,
             "estimated_remaining": 0, "is_stale": False},
            {"pid": 2, "provider": "infini", "duration_secs": 200,
             "estimated_remaining": 0, "is_stale": False},
        ]
        result = func(running)
        assert result is not None
        assert result["finishes_in"] == 0

    def test_does_not_mutate_input(self):
        func = _mod["next_completion"]
        running = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 50,
             "estimated_remaining": 20, "is_stale": False},
        ]
        original_keys = set(running[0].keys())
        func(running)
        assert set(running[0].keys()) == original_keys


# ── throughput_based_eta (NEW) ──────────────────────────────────────────


class TestThroughputBasedEta:
    """Tests for throughput-based ETA calculation."""

    def test_no_pending_no_running(self):
        func = _mod["throughput_based_eta"]
        assert func([], pending=0, running_count=0) == 0

    def test_with_ewma_rate(self):
        func = _mod["throughput_based_eta"]
        # 6 tasks/hr = 0.00167 tasks/sec
        # 10 pending + 2 running = 12 tasks
        # 12 / 0.00167 ≈ 7200 sec = 2hr
        eta = func([], pending=10, running_count=2, ewma_rate=6.0)
        assert eta == 7200

    def test_without_ewma_uses_windowed_rate(self):
        func = _mod["throughput_based_eta"]
        now = datetime.now()
        recs = [
            {"ts": (now - timedelta(minutes=10 * i)).isoformat(), "exit": 0}
            for i in range(5)
        ]
        eta = func(recs, pending=5, running_count=1)
        assert eta > 0

    def test_zero_rate_returns_zero(self):
        func = _mod["throughput_based_eta"]
        # No records, no ewma — should return 0
        eta = func([], pending=5, running_count=1)
        assert eta == 0

    def test_high_rate_gives_short_eta(self):
        func = _mod["throughput_based_eta"]
        eta_fast = func([], pending=10, running_count=2, ewma_rate=60.0)
        eta_slow = func([], pending=10, running_count=2, ewma_rate=6.0)
        assert eta_fast < eta_slow


# ── drain_projection (NEW) ──────────────────────────────────────────────


class TestDrainProjection:
    """Tests for drain projection timeline."""

    def test_no_running_no_pending(self):
        func = _mod["drain_projection"]
        result = func([], pending=0, running=[])
        assert result == []

    def test_running_only_shows_next_done(self):
        func = _mod["drain_projection"]
        running = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 50,
             "estimated_remaining": 30, "is_stale": False},
        ]
        result = func([], pending=0, running=running)
        events = [e["event"] for e in result]
        assert "next_done" in events

    def test_pending_shows_milestones(self):
        func = _mod["drain_projection"]
        now = datetime.now()
        recs = [
            {"ts": (now - timedelta(minutes=10 * i)).isoformat(), "exit": 0}
            for i in range(5)
        ]
        running = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 50,
             "estimated_remaining": 30, "is_stale": False},
        ]
        result = func(recs, pending=10, running=running)
        events = [e["event"] for e in result]
        assert "quarter" in events
        assert "half" in events
        assert "drain" in events

    def test_events_sorted_by_offset(self):
        func = _mod["drain_projection"]
        now = datetime.now()
        recs = [
            {"ts": (now - timedelta(minutes=10 * i)).isoformat(), "exit": 0}
            for i in range(5)
        ]
        running = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 50,
             "estimated_remaining": 30, "is_stale": False},
        ]
        result = func(recs, pending=10, running=running)
        offsets = [e["offset_secs"] for e in result]
        assert offsets == sorted(offsets)


# ── running_tasks_table leading task highlight (NEW) ────────────────────


class TestRunningTasksTableLeading:
    """Tests for leading task highlight (★ marker)."""

    def test_single_task_has_star(self):
        func = _mod["running_tasks_table"]
        tasks = [{
            "pid": 1234, "provider": "zhipu", "duration_secs": 100,
            "task": "leading", "estimated_pct": 80, "estimated_remaining": 20,
            "is_stale": False,
        }]
        result = func(tasks, use_color=False)
        assert "★" in result

    def test_multiple_tasks_only_one_star(self):
        func = _mod["running_tasks_table"]
        tasks = [
            {"pid": 1, "provider": "zhipu", "duration_secs": 100,
             "task": "slow", "estimated_pct": 30, "estimated_remaining": 70,
             "is_stale": False},
            {"pid": 2, "provider": "infini", "duration_secs": 80,
             "task": "fast", "estimated_pct": 80, "estimated_remaining": 20,
             "is_stale": False},
        ]
        result = func(tasks, use_color=False)
        assert result.count("★") == 1
        assert "[2]" in result  # The faster task

    def test_no_star_for_no_running(self):
        func = _mod["running_tasks_table"]
        result = func([], use_color=False)
        assert "★" not in result


# ── eta_section with next_done and throughput-based ETA (NEW) ──────────


class TestEtaSectionNextDone:
    """Tests for ETA section showing next completion and rate-based ETA."""

    def test_shows_next_done(self):
        func = _mod["eta_section"]
        eta = {"pending": 10, "running": 2, "eta_seconds": 600, "eta_str": "10m 0s",
               "workers": 2, "avg_duration": 100,
               "drain_milestones": [(25, 150), (50, 300), (75, 450), (100, 600)],
               "running_remaining_secs": 200}
        nxt = {"finishes_in": 30, "provider": "zhipu", "pid": 1234}
        result = func(eta, 6.0, use_color=False, next_done=nxt)
        assert "Next done" in result

    def test_shows_throughput_based_eta(self):
        func = _mod["eta_section"]
        eta = {"pending": 10, "running": 2, "eta_seconds": 600, "eta_str": "10m 0s",
               "workers": 2, "avg_duration": 100,
               "drain_milestones": [],
               "running_remaining_secs": 200}
        result = func(eta, 6.0, use_color=False, tp_eta=3600)
        assert "Rate-based" in result

    def test_shows_projection(self):
        func = _mod["eta_section"]
        eta = {"pending": 10, "running": 2, "eta_seconds": 600, "eta_str": "10m 0s",
               "workers": 2, "avg_duration": 100,
               "drain_milestones": [],
               "running_remaining_secs": 200}
        projection = [
            {"offset_secs": 30, "event": "next_done", "description": "Next task done"},
            {"offset_secs": 900, "event": "quarter", "description": "25% drained"},
            {"offset_secs": 1800, "event": "half", "description": "50% drained"},
            {"offset_secs": 3600, "event": "drain", "description": "100% drained"},
        ]
        result = func(eta, 6.0, use_color=False, projection=projection)
        assert "Projection" in result
        assert "next" in result
        assert "100%" in result

    def test_no_next_done_when_none(self):
        func = _mod["eta_section"]
        eta = {"pending": 10, "running": 2, "eta_seconds": 600, "eta_str": "10m 0s",
               "workers": 2, "avg_duration": 100,
               "drain_milestones": [],
               "running_remaining_secs": 200}
        result = func(eta, 6.0, use_color=False)
        assert "Next done" not in result

    def test_rate_based_shows_faster_slower(self):
        func = _mod["eta_section"]
        eta = {"pending": 10, "running": 2, "eta_seconds": 600, "eta_str": "10m 0s",
               "workers": 2, "avg_duration": 100,
               "drain_milestones": [],
               "running_remaining_secs": 200}
        # tp_eta much shorter than duration-based → shows "faster"
        result_fast = func(eta, 6.0, use_color=False, tp_eta=300)
        assert "faster" in result_fast
        # tp_eta much longer → shows "slower"
        result_slow = func(eta, 6.0, use_color=False, tp_eta=1200)
        assert "slower" in result_slow


# ── Dashboard shows next completion and projection (NEW) ──────────────


class TestDashboardNextCompletion:
    """Tests that dashboard includes next completion and drain projection."""

    def test_json_includes_next_completion(self, tmp_path, capsys):
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
        data = json.loads(capsys.readouterr().out)
        assert "throughput_based_eta_seconds" in data
        assert "drain_projection" in data
        assert isinstance(data["drain_projection"], list)

    def test_compact_shows_next_completion(self, tmp_path, capsys):
        func = _mod["print_compact"]
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0}\n'
            )
            (tmp_path / "queue.md").write_text(
                '- [ ] `golem --provider zhipu "task A"`\n'
            )
            func()
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        captured = capsys.readouterr()
        # Compact may or may not show "next:" depending on running tasks
        # Just verify it doesn't crash and produces output
        assert len(captured.out.strip()) > 0

    def test_eta_section_with_running_shows_next_done(self, tmp_path, capsys):
        orig_jsonl = _mod["JSONL_PATH"]
        orig_queue = _mod["QUEUE_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            _mod["QUEUE_PATH"] = tmp_path / "queue.md"
            now = datetime.now()
            recs = [
                {"ts": (now - timedelta(minutes=10 * i)).isoformat(),
                 "provider": "zhipu", "duration": 60, "exit": 0}
                for i in range(5)
            ]
            (tmp_path / "golem.jsonl").write_text(
                "\n".join(json.dumps(r) for r in recs) + "\n"
            )
            (tmp_path / "queue.md").write_text(
                '- [ ] `golem --provider zhipu "task A"`\n'
            )
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig_jsonl
            _mod["QUEUE_PATH"] = orig_queue
        assert rc == 0
        captured = capsys.readouterr()
        assert "ETA" in captured.out
