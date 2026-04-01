from __future__ import annotations

"""Tests for effectors/golem-top.

Effectors are scripts — load via exec, never import.
"""

import sys
import json
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

EFFECTOR = Path.home() / "germline" / "effectors" / "golem-tools"

# Load the effector into a namespace
NS = {"__name__": "golem_top", "__file__": str(EFFECTOR)}
exec(open(EFFECTOR).read(), NS)

# Pull functions into local scope
parse_ps_lines = NS["parse_ps_lines"]
classify_process = NS["classify_process"]
etime_to_seconds = NS["etime_to_seconds"]
format_duration = NS["format_duration"]
group_tasks = NS["group_tasks"]
render_table = NS["render_table"]
run = NS["top_run"]
truncate = NS["truncate"]


# ── etime_to_seconds ────────────────────────────────────────────

class TestEtimeToSeconds:
    def test_mm_ss(self):
        assert etime_to_seconds("14:30") == 870

    def test_hh_mm_ss(self):
        assert etime_to_seconds("03:38:56") == 13136

    def test_d_hh_mm_ss(self):
        assert etime_to_seconds("1-03:38:56") == 99536

    def test_zero(self):
        assert etime_to_seconds("00:00") == 0

    def test_single_minute(self):
        assert etime_to_seconds("01:00") == 60


# ── format_duration ────────────────────────────────────────────

class TestFormatDuration:
    def test_seconds_only(self):
        assert format_duration("00:45") == "45s"

    def test_minutes(self):
        assert format_duration("05:30") == "5m30s"

    def test_hours(self):
        assert format_duration("02:15:00") == "2h15m"

    def test_days(self):
        assert format_duration("1-03:00:00") == "1d3h"


# ── classify_process ──────────────────────────────────────────

class TestClassifyProcess:
    def test_shell_wrapper(self):
        args = '/bin/sh -c golem --provider zhipu --max-turns 30 "Write tests for rheotaxis"'
        result = classify_process(args)
        assert result is not None
        assert result["provider"] == "zhipu"
        assert result["max_turns"] == 30
        assert "Write tests for rheotaxis" in result["task"]
        assert result["kind"] == "golem"

    def test_bash_direct(self):
        args = "bash /home/terry/germline/effectors/golem --provider infini --max-turns 35 Create effectors/skill-search"
        result = classify_process(args)
        assert result is not None
        assert result["provider"] == "infini"
        assert result["max_turns"] == 35
        assert "Create effectors/skill-search" in result["task"]

    def test_golem_reviewer(self):
        args = "python3 /home/terry/germline/effectors/golem-reviewer"
        result = classify_process(args)
        assert result is not None
        assert result["provider"] == "reviewer"
        assert result["task"] == "reviewer daemon"

    def test_non_golem_process(self):
        args = "bash /usr/bin/something-else --foo bar"
        assert classify_process(args) is None

    def test_unknown_provider(self):
        args = "bash /home/terry/germline/effectors/golem --max-turns 10 Do something"
        result = classify_process(args)
        assert result is not None
        assert result["provider"] == "unknown"


# ── parse_ps_lines ────────────────────────────────────────────

class TestParsePsLines:
    def test_basic_parsing(self):
        raw = textwrap.dedent("""\
            PID     ELAPSED COMMAND
            369       14:30 /bin/sh -c golem --provider zhipu --max-turns 30 "Write tests"
            2256    03:38:56 python3 /home/terry/germline/effectors/golem-reviewer
        """)
        entries = parse_ps_lines(raw)
        assert len(entries) == 2
        assert entries[0]["pid"] == 369
        assert entries[0]["etime"] == "14:30"
        assert entries[1]["pid"] == 2256

    def test_skips_self(self):
        raw = "  100 01:00:00 /home/terry/germline/effectors/golem-top --watch\n"
        entries = parse_ps_lines(raw)
        assert len(entries) == 0

    def test_keeps_python3_golem_top(self):
        """python3 invoking golem-top passes parse (executable is python3)."""
        raw = "  100 01:00:00 python3 /home/terry/germline/effectors/golem-top\n"
        entries = parse_ps_lines(raw)
        assert len(entries) == 1

    def test_skips_header(self):
        raw = "  PID   ELAPSED COMMAND\n"
        entries = parse_ps_lines(raw)
        assert len(entries) == 0

    def test_keeps_golem_top_in_task_description(self):
        """A task *about* golem-top should still show up."""
        raw = '  2308 04:57 /bin/sh -c golem --provider zhipu --max-turns 35 "Create effectors/golem-top as Python"\n'
        entries = parse_ps_lines(raw)
        assert len(entries) == 1
        assert "golem-top" in entries[0]["args"]


# ── group_tasks ────────────────────────────────────────────────

class TestGroupTasks:
    def test_deduplicates_shell_and_bash(self):
        entries = [
            {"pid": 369, "etime": "14:30", "args": '/bin/sh -c golem --provider zhipu --max-turns 30 "Write tests for rheotaxis"', "raw_line": ""},
            {"pid": 370, "etime": "14:30", "args": "bash /home/terry/germline/effectors/golem --provider zhipu --max-turns 30 Write tests for rheotaxis", "raw_line": ""},
            {"pid": 378, "etime": "14:29", "args": "bash /home/terry/germline/effectors/golem --provider zhipu --max-turns 30 Write tests for rheotaxis", "raw_line": ""},
        ]
        tasks = group_tasks(entries)
        assert len(tasks) == 1
        assert tasks[0]["pid"] == 369  # lowest PID = parent
        assert tasks[0]["provider"] == "zhipu"
        assert tasks[0]["num_procs"] == 3
        assert "Write tests for rheotaxis" in tasks[0]["task"]

    def test_separates_different_tasks(self):
        entries = [
            {"pid": 369, "etime": "14:30", "args": "bash /home/terry/germline/effectors/golem --provider zhipu --max-turns 30 Task alpha", "raw_line": ""},
            {"pid": 418, "etime": "05:27", "args": "bash /home/terry/germline/effectors/golem --provider zhipu --max-turns 35 Task beta", "raw_line": ""},
        ]
        tasks = group_tasks(entries)
        assert len(tasks) == 2

    def test_reviewer_grouped(self):
        entries = [
            {"pid": 2256, "etime": "03:38:56", "args": "python3 /home/terry/germline/effectors/golem-reviewer", "raw_line": ""},
        ]
        tasks = group_tasks(entries)
        assert len(tasks) == 1
        assert tasks[0]["kind"] == "reviewer"
        assert tasks[0]["duration"] == "3h38m"


# ── render_table ───────────────────────────────────────────────

class TestRenderTable:
    def test_empty(self):
        assert render_table([]) == "No golem processes running."

    def test_header_and_rows(self):
        tasks = [{
            "pid": 369, "provider": "zhipu", "duration": "14m30s",
            "num_procs": 3, "task": "Write tests for rheotaxis-local",
            "kind": "golem",
        }]
        output = render_table(tasks)
        assert "PID" in output
        assert "PROVIDER" in output
        assert "369" in output
        assert "zhipu" in output
        assert "14m30s" in output

    def test_summary_footer(self):
        tasks = [
            {"pid": 100, "provider": "zhipu", "duration": "1m00s", "num_procs": 2, "task": "Task A", "kind": "golem"},
            {"pid": 200, "provider": "infini", "duration": "2m00s", "num_procs": 1, "task": "Task B", "kind": "golem"},
        ]
        output = render_table(tasks)
        assert "Total: 2 task(s)" in output
        assert "infini:1" in output
        assert "zhipu:1" in output


# ── truncate ──────────────────────────────────────────────────

class TestTruncate:
    def test_short_string(self):
        assert truncate("hello", 10) == "hello"

    def test_exact_length(self):
        assert truncate("hello", 5) == "hello"

    def test_truncated(self):
        result = truncate("hello world", 8)
        assert len(result) == 8
        assert result.endswith("…")


# ── run (integration with mocked ps) ─────────────────────────

class TestRun:
    def test_json_output(self):
        fake_ps = textwrap.dedent("""\
            PID     ELAPSED COMMAND
            369       14:30 /bin/sh -c golem --provider zhipu --max-turns 30 "Write tests for rheotaxis-local"
            370       14:30 bash /home/terry/germline/effectors/golem --provider zhipu --max-turns 30 Write tests for rheotaxis-local
            2256    03:38:56 python3 /home/terry/germline/effectors/golem-reviewer
        """)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_ps)
            output = run(json_output=True)

        data = json.loads(output)
        assert isinstance(data, list)
        # Should have 2 unique tasks: rheotaxis + reviewer
        assert len(data) == 2
        pids = [d["pid"] for d in data]
        assert 369 in pids
        assert 2256 in pids

    def test_no_golems_running(self):
        fake_ps = "  PID   ELAPSED COMMAND\n  1000    01:00:00 /usr/bin/sleep 999\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_ps)
            output = run(json_output=False)

        assert output == "No golem processes running."

    def test_table_output(self):
        fake_ps = textwrap.dedent("""\
            PID     ELAPSED COMMAND
            419       05:27 bash /home/terry/germline/effectors/golem --provider infini --max-turns 35 Create effectors/skill-search
        """)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_ps)
            output = run(json_output=False)

        assert "infini" in output
        assert "419" in output
        assert "skill-search" in output
