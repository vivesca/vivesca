"""Tests for effectors/queue-stats."""
from __future__ import annotations

import json
import re
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

QUEUE_STATS_SCRIPT = Path(__file__).parent.parent / "effectors" / "queue-stats"


# ── Unit tests: parse_task ──────────────────────────────────────────────


class TestParseTask:
    """Test parse_task line-by-line parsing."""

    def _exec(self, src: str, fn: str, *args, **kwargs):
        """Load a function from the script via exec."""
        ns: dict = {"__name__": "queue_stats_test"}
        exec(src, ns)
        return ns[fn](*args, **kwargs)

    @pytest.fixture(autouse=True)
    def _load_module(self):
        self.src = QUEUE_STATS_SCRIPT.read_text()

    def test_pending_task(self):
        result = self._exec(
            self.src,
            "parse_task",
            '- [ ] `golem --provider zhipu --max-turns 30 "Do something"`',
        )
        assert result["status"] == "pending"
        assert result["provider"] == "zhipu"
        assert result["max_turns"] == 30

    def test_done_task(self):
        result = self._exec(
            self.src,
            "parse_task",
            '- [x] `golem --provider volcano --max-turns 50 "Write tests"`',
        )
        assert result["status"] == "done"
        assert result["provider"] == "volcano"
        assert result["max_turns"] == 50

    def test_failed_task(self):
        result = self._exec(
            self.src,
            "parse_task",
            '- [!] `golem --provider infini --max-turns 40 "Fix stuff" (retry)`',
        )
        assert result["status"] == "failed"
        assert result["provider"] == "infini"
        assert result["max_turns"] == 40

    def test_task_without_max_turns(self):
        result = self._exec(
            self.src,
            "parse_task",
            '- [ ] `golem --provider zhipu "Short task"`',
        )
        assert result["status"] == "pending"
        assert result["provider"] == "zhipu"
        assert result["max_turns"] == 20  # default

    def test_non_task_line_returns_none(self):
        result = self._exec(self.src, "parse_task", "## Some header")
        assert result is None

    def test_task_without_provider(self):
        result = self._exec(
            self.src,
            "parse_task",
            '- [x] `golem --max-turns 30 "Something"`',
        )
        assert result["provider"] == "unknown"

    def test_empty_line_returns_none(self):
        result = self._exec(self.src, "parse_task", "")
        assert result is None

    def test_full_flag_task(self):
        result = self._exec(
            self.src,
            "parse_task",
            '- [ ] `golem --provider zhipu --full --max-turns 50 "Research"`',
        )
        assert result["provider"] == "zhipu"
        assert result["max_turns"] == 50


# ── Unit tests: parse_queue ─────────────────────────────────────────────


class TestParseQueue:
    """Test parse_queue on full markdown."""

    @pytest.fixture(autouse=True)
    def _load_module(self):
        self.src = QUEUE_STATS_SCRIPT.read_text()

    def _exec(self, fn, *args, **kwargs):
        ns: dict = {"__name__": "queue_stats_test"}
        exec(self.src, ns)
        return ns[fn](*args, **kwargs)

    def test_mixed_statuses(self):
        md = textwrap.dedent("""\
            # Golem Task Queue
            ## Pending
            - [ ] `golem --provider zhipu --max-turns 30 "Task A"`
            - [x] `golem --provider volcano --max-turns 20 "Task B"`
            - [!] `golem --provider infini --max-turns 40 "Task C"`
        """)
        tasks = self._exec("parse_queue", md)
        assert len(tasks) == 3
        statuses = [t["status"] for t in tasks]
        assert "pending" in statuses
        assert "done" in statuses
        assert "failed" in statuses

    def test_empty_queue(self):
        tasks = self._exec("parse_queue", "# Empty\n")
        assert tasks == []

    def test_ignores_headers_and_prose(self):
        md = textwrap.dedent("""\
            # Queue
            Some prose here
            ## Pending
            More text
            - [ ] `golem --provider zhipu --max-turns 10 "Task"`
        """)
        tasks = self._exec("parse_queue", md)
        assert len(tasks) == 1


# ── Unit tests: parse_concurrency_header ────────────────────────────────


class TestParseConcurrencyHeader:
    @pytest.fixture(autouse=True)
    def _load_module(self):
        self.src = QUEUE_STATS_SCRIPT.read_text()

    def _exec(self, fn, *args, **kwargs):
        ns: dict = {"__name__": "queue_stats_test"}
        exec(self.src, ns)
        return ns[fn](*args, **kwargs)

    def test_parses_header(self):
        text = "ZhiPu(4) + Infini(6) + Volcano(8) = 18 concurrent."
        result = self._exec("parse_concurrency_header", text)
        assert result["zhipu"] == 4
        assert result["infini"] == 6
        assert result["volcano"] == 8

    def test_missing_header_returns_defaults(self):
        result = self._exec("parse_concurrency_header", "no concurrency info")
        assert all(isinstance(v, int) and v > 0 for v in result.values())


# ── Unit tests: compute_turn_durations ──────────────────────────────────


class TestComputeTurnDurations:
    @pytest.fixture(autouse=True)
    def _load_module(self):
        self.src = QUEUE_STATS_SCRIPT.read_text()

    def _exec(self, fn, *args, **kwargs):
        ns: dict = {"__name__": "queue_stats_test"}
        exec(self.src, ns)
        return ns[fn](*args, **kwargs)

    def test_computes_median(self):
        entries = [
            {"provider": "zhipu", "duration": 100, "turns": 10},  # 10 s/turn
            {"provider": "zhipu", "duration": 200, "turns": 10},  # 20 s/turn
            {"provider": "zhipu", "duration": 150, "turns": 10},  # 15 s/turn
        ]
        result = self._exec("compute_turn_durations", entries)
        assert result["zhipu"] == 15.0  # median of [10, 15, 20]

    def test_empty_entries_returns_defaults(self):
        result = self._exec("compute_turn_durations", [])
        assert "zhipu" in result
        assert result["zhipu"] > 0

    def test_multiple_providers(self):
        entries = [
            {"provider": "zhipu", "duration": 30, "turns": 3},
            {"provider": "infini", "duration": 20, "turns": 2},
        ]
        result = self._exec("compute_turn_durations", entries)
        assert result["zhipu"] == 10.0
        assert result["infini"] == 10.0

    def test_skips_zero_turns(self):
        entries = [
            {"provider": "zhipu", "duration": 30, "turns": 0},
        ]
        result = self._exec("compute_turn_durations", entries)
        # Should not include zero-turn entries
        assert "zhipu" not in result or result["zhipu"] > 0

    def test_skips_missing_fields(self):
        entries = [
            {"provider": "zhipu"},  # no duration or turns
            {"duration": 30, "turns": 3},  # no provider
        ]
        result = self._exec("compute_turn_durations", entries)
        # Should handle gracefully
        assert isinstance(result, dict)


# ── Unit tests: estimate_completion ─────────────────────────────────────


class TestEstimateCompletion:
    @pytest.fixture(autouse=True)
    def _load_module(self):
        self.src = QUEUE_STATS_SCRIPT.read_text()

    def _exec(self, fn, *args, **kwargs):
        ns: dict = {"__name__": "queue_stats_test"}
        exec(self.src, ns)
        return ns[fn](*args, **kwargs)

    def test_basic_estimation(self):
        tasks = [
            {"status": "pending", "provider": "zhipu", "max_turns": 30},
            {"status": "pending", "provider": "zhipu", "max_turns": 30},
            {"status": "done", "provider": "zhipu", "max_turns": 20},
        ]
        concurrency = {"zhipu": 4}
        sec_per_turn = {"zhipu": 10.0}
        result = self._exec("estimate_completion", tasks, concurrency, sec_per_turn)
        assert "zhipu" in result
        assert result["zhipu"]["tasks"] == 2
        assert result["zhipu"]["slots"] == 4
        assert result["zhipu"]["waves"] == 1  # 2 tasks, 4 slots = 1 wave
        assert result["zhipu"]["est_seconds"] > 0

    def test_includes_failed_tasks(self):
        tasks = [
            {"status": "failed", "provider": "infini", "max_turns": 40},
            {"status": "pending", "provider": "infini", "max_turns": 30},
        ]
        concurrency = {"infini": 6}
        sec_per_turn = {"infini": 12.0}
        result = self._exec("estimate_completion", tasks, concurrency, sec_per_turn)
        assert result["infini"]["tasks"] == 2

    def test_excludes_done_tasks(self):
        tasks = [
            {"status": "done", "provider": "volcano", "max_turns": 50},
        ]
        concurrency = {"volcano": 8}
        sec_per_turn = {"volcano": 8.0}
        result = self._exec("estimate_completion", tasks, concurrency, sec_per_turn)
        assert "volcano" not in result

    def test_multiple_waves(self):
        # 10 tasks, 2 slots = 5 waves
        tasks = [
            {"status": "pending", "provider": "zhipu", "max_turns": 30}
        ] * 10
        concurrency = {"zhipu": 2}
        sec_per_turn = {"zhipu": 10.0}
        result = self._exec("estimate_completion", tasks, concurrency, sec_per_turn)
        assert result["zhipu"]["waves"] == 5


# ── Unit tests: format_duration ─────────────────────────────────────────


class TestFormatDuration:
    @pytest.fixture(autouse=True)
    def _load_module(self):
        self.src = QUEUE_STATS_SCRIPT.read_text()

    def _exec(self, fn, *args, **kwargs):
        ns: dict = {"__name__": "queue_stats_test"}
        exec(self.src, ns)
        return ns[fn](*args, **kwargs)

    def test_seconds(self):
        assert self._exec("format_duration", 45) == "45s"

    def test_minutes(self):
        assert self._exec("format_duration", 120) == "2.0min"

    def test_hours(self):
        assert self._exec("format_duration", 7200) == "2.0h"

    def test_days(self):
        assert self._exec("format_duration", 172800) == "2.0d"

    def test_zero(self):
        assert self._exec("format_duration", 0) == "0s"

    def test_boundary_under_60(self):
        assert self._exec("format_duration", 59) == "59s"

    def test_boundary_60(self):
        result = self._exec("format_duration", 60)
        assert "min" in result


# ── Unit tests: read_golem_log ──────────────────────────────────────────


class TestReadGolemLog:
    @pytest.fixture(autouse=True)
    def _load_module(self):
        self.src = QUEUE_STATS_SCRIPT.read_text()

    def test_reads_valid_log(self, tmp_path):
        log = tmp_path / "golem.jsonl"
        entries_data = [
            {"ts": "t1", "provider": "zhipu", "exit": 0, "duration": 100, "turns": 10},
            {"ts": "t2", "provider": "infini", "exit": 1, "duration": 50, "turns": 5},
        ]
        log.write_text("\n".join(json.dumps(e) for e in entries_data) + "\n")

        ns: dict = {"__name__": "queue_stats_test"}
        ns["GOLEM_LOG"] = log
        exec(self.src, ns)
        result = ns["read_golem_log"]()
        assert len(result) == 2
        assert result[0]["provider"] == "zhipu"

    def test_handles_missing_file(self, tmp_path):
        ns: dict = {"__name__": "queue_stats_test"}
        ns["GOLEM_LOG"] = tmp_path / "nonexistent.jsonl"
        exec(self.src, ns)
        result = ns["read_golem_log"]()
        assert result == []

    def test_skips_malformed_lines(self, tmp_path):
        log = tmp_path / "golem.jsonl"
        log.write_text('{"valid": true}\nbad json\n{"also": "valid"}\n')
        ns: dict = {"__name__": "queue_stats_test"}
        ns["GOLEM_LOG"] = log
        exec(self.src, ns)
        result = ns["read_golem_log"]()
        assert len(result) == 2


# ── Integration test ────────────────────────────────────────────────────


class TestQueueStatsIntegration:
    """Integration test: run the script against real queue."""

    def test_runs_successfully(self):
        result = subprocess.run(
            [str(QUEUE_STATS_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Golem Queue Stats" in result.stdout
        assert "Pending:" in result.stdout
        assert "Done:" in result.stdout
        assert "Failed:" in result.stdout

    def test_has_provider_table(self):
        result = subprocess.run(
            [str(QUEUE_STATS_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "Tasks per provider" in result.stdout
        assert "zhipu" in result.stdout or "infini" in result.stdout or "volcano" in result.stdout

    def test_has_concurrency_section(self):
        result = subprocess.run(
            [str(QUEUE_STATS_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "Concurrency" in result.stdout
        assert "slots" in result.stdout

    def test_has_estimated_completion(self):
        result = subprocess.run(
            [str(QUEUE_STATS_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "Estimated completion" in result.stdout

    def test_total_tasks_positive(self):
        result = subprocess.run(
            [str(QUEUE_STATS_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        m = re.search(r"Total tasks: (\d+)", result.stdout)
        assert m is not None
        assert int(m.group(1)) > 0
