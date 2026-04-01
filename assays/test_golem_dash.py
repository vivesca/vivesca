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
        assert result[0]["estimated_pct"] == 50  # 100/200 (median)
        assert result[0]["estimated_remaining"] == 100
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
