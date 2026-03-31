"""Tests for golem summary subcommand."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


def create_test_log(entries: list[dict], tmp_path: Path) -> Path:
    """Create a test JSONL log file with given entries."""
    log_file = tmp_path / "golem.jsonl"
    with open(log_file, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return log_file


def run_summary(log_file: Path, recent: int = 0) -> tuple[str, int]:
    """Run golem summary with the given log file."""
    env = os.environ.copy()
    env["GOLEM_LOG"] = str(log_file)
    
    cmd = ["./effectors/golem", "summary"]
    if recent > 0:
        cmd.extend(["--recent", str(recent)])
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        cwd="/Users/terry/germline"
    )
    return result.stdout, result.returncode


class TestGolemSummary:
    """Test suite for golem summary subcommand."""

    def test_summary_basic_table_format(self, tmp_path):
        """Test that summary produces a properly formatted table."""
        entries = [
            {"provider": "zhipu", "duration": 100, "exit": 0, "tests_passed": 5, "tests_failed": 1},
            {"provider": "zhipu", "duration": 200, "exit": 1, "tests_passed": 3, "tests_failed": 2},
            {"provider": "volcano", "duration": 150, "exit": 0, "tests_passed": 4, "tests_failed": 0},
        ]
        log_file = create_test_log(entries, tmp_path)
        stdout, code = run_summary(log_file)
        
        assert code == 0
        assert "Provider" in stdout
        assert "Runs" in stdout
        assert "Pass" in stdout
        assert "Fail" in stdout
        assert "Avg Duration" in stdout
        assert "Tests Created" in stdout
        assert "zhipu" in stdout
        assert "volcano" in stdout

    def test_summary_counts_pass_fail(self, tmp_path):
        """Test that pass/fail counts are correct based on exit code."""
        entries = [
            {"provider": "zhipu", "duration": 100, "exit": 0},
            {"provider": "zhipu", "duration": 100, "exit": 0},
            {"provider": "zhipu", "duration": 100, "exit": 1},
            {"provider": "zhipu", "duration": 100, "exit": 2},
        ]
        log_file = create_test_log(entries, tmp_path)
        stdout, code = run_summary(log_file)
        
        assert code == 0
        # zhipu: 4 runs, 2 pass (exit=0), 2 fail (exit!=0)
        lines = stdout.strip().split("\n")
        zhipu_line = [l for l in lines if "zhipu" in l][0]
        # Check the line has correct values
        assert "| 4 |" in zhipu_line
        assert "| 2 |" in zhipu_line  # pass count
        # There should be two "| 2 |" - one for pass, one for fail
        parts = zhipu_line.split("|")
        assert parts[3].strip() == "2"  # Pass column
        assert parts[4].strip() == "2"  # Fail column

    def test_summary_average_duration(self, tmp_path):
        """Test that average duration is calculated correctly."""
        entries = [
            {"provider": "infini", "duration": 100, "exit": 0},
            {"provider": "infini", "duration": 200, "exit": 0},
            {"provider": "infini", "duration": 300, "exit": 0},
        ]
        log_file = create_test_log(entries, tmp_path)
        stdout, code = run_summary(log_file)
        
        assert code == 0
        # Average duration: (100+200+300)/3 = 200
        assert "200s" in stdout

    def test_summary_tests_created(self, tmp_path):
        """Test that tests_created sums tests_passed + tests_failed."""
        entries = [
            {"provider": "zhipu", "duration": 100, "exit": 0, "tests_passed": 5, "tests_failed": 2},
            {"provider": "zhipu", "duration": 100, "exit": 0, "tests_passed": 3, "tests_failed": 1},
        ]
        log_file = create_test_log(entries, tmp_path)
        stdout, code = run_summary(log_file)
        
        assert code == 0
        # Total tests created: (5+2) + (3+1) = 11
        lines = stdout.strip().split("\n")
        zhipu_line = [l for l in lines if "zhipu" in l][0]
        assert "11" in zhipu_line

    def test_summary_recent_flag(self, tmp_path):
        """Test that --recent N filters to last N entries."""
        entries = [
            {"provider": "zhipu", "duration": 100, "exit": 0},
            {"provider": "zhipu", "duration": 100, "exit": 0},
            {"provider": "volcano", "duration": 100, "exit": 0},
            {"provider": "infini", "duration": 100, "exit": 0},
        ]
        log_file = create_test_log(entries, tmp_path)
        stdout, code = run_summary(log_file, recent=2)
        
        assert code == 0
        # Only last 2 entries should be counted: volcano and infini
        assert "volcano" in stdout
        assert "infini" in stdout
        # zhipu should show 0 runs since last 2 don't include it
        lines = stdout.strip().split("\n")
        # Check that zhipu line has 0 runs or is not present
        zhipu_lines = [l for l in lines if "zhipu" in l]
        if zhipu_lines:
            # If zhipu is shown, it should have 0 runs
            assert "| 0 |" in zhipu_lines[0] or "zhipu" not in stdout

    def test_summary_missing_log_file(self, tmp_path):
        """Test that missing log file returns non-zero exit."""
        missing_log = tmp_path / "nonexistent.jsonl"
        stdout, code = run_summary(missing_log)
        
        assert code != 0

    def test_summary_empty_log_file(self, tmp_path):
        """Test that empty log file doesn't crash."""
        log_file = tmp_path / "golem.jsonl"
        log_file.write_text("")
        stdout, code = run_summary(log_file)
        
        assert code == 0
        # Should show headers but no data rows

    def test_summary_malformed_json_lines(self, tmp_path):
        """Test that malformed JSON lines are skipped gracefully."""
        log_content = """{"provider": "zhipu", "duration": 100, "exit": 0}
this is not valid json
{"provider": "zhipu", "duration": 200, "exit": 1}
"""
        log_file = tmp_path / "golem.jsonl"
        log_file.write_text(log_content)
        stdout, code = run_summary(log_file)
        
        assert code == 0
        # Should have 2 valid entries counted
        assert "zhipu" in stdout

    def test_summary_multiple_providers(self, tmp_path):
        """Test that multiple providers are all shown."""
        entries = [
            {"provider": "zhipu", "duration": 100, "exit": 0},
            {"provider": "volcano", "duration": 150, "exit": 0},
            {"provider": "infini", "duration": 200, "exit": 1},
        ]
        log_file = create_test_log(entries, tmp_path)
        stdout, code = run_summary(log_file)
        
        assert code == 0
        assert "zhipu" in stdout
        assert "volcano" in stdout
        assert "infini" in stdout

    def test_summary_missing_optional_fields(self, tmp_path):
        """Test that entries missing optional fields are handled."""
        entries = [
            {"provider": "zhipu", "exit": 0},  # missing duration
            {"provider": "zhipu"},  # missing exit, duration
        ]
        log_file = create_test_log(entries, tmp_path)
        stdout, code = run_summary(log_file)
        
        assert code == 0
        assert "zhipu" in stdout
        # Missing duration should be treated as 0
        # Missing exit should be treated as non-zero (fail)
        lines = stdout.strip().split("\n")
        zhipu_line = [l for l in lines if "zhipu" in l][0]
        assert "| 2 |" in zhipu_line  # 2 runs

    def test_summary_unknown_provider(self, tmp_path):
        """Test that unknown providers are shown as 'unknown'."""
        entries = [
            {"duration": 100, "exit": 0},  # missing provider
        ]
        log_file = create_test_log(entries, tmp_path)
        stdout, code = run_summary(log_file)
        
        assert code == 0
        assert "unknown" in stdout
