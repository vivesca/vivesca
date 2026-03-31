"""Tests for sortase CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from metabolon.sortase.cli import main, _percentile


# ---------------------------------------------------------------------------
# _percentile unit tests
# ---------------------------------------------------------------------------

class TestPercentile:
    def test_empty_list(self) -> None:
        assert _percentile([], 50) == 0.0

    def test_single_value(self) -> None:
        assert _percentile([10.0], 50) == 10.0
        assert _percentile([10.0], 0) == 10.0
        assert _percentile([10.0], 100) == 10.0

    def test_two_values_p50(self) -> None:
        assert _percentile([10.0, 20.0], 50) == 15.0

    def test_three_values_p50(self) -> None:
        assert _percentile([10.0, 20.0, 30.0], 50) == 20.0

    def test_p95(self) -> None:
        values = sorted([float(i) for i in range(1, 101)])
        result = _percentile(values, 95)
        assert 95.0 < result < 96.0


# ---------------------------------------------------------------------------
# speed --percentiles integration test
# ---------------------------------------------------------------------------

SAMPLE_LOG_ENTRIES = [
    {
        "timestamp": "2026-03-31T07:00:00",
        "plan": "task_a.md",
        "tool": "droid",
        "duration_s": 50.0,
        "success": True,
        "files_changed": 1,
    },
    {
        "timestamp": "2026-03-31T06:00:00",
        "plan": "task_b.md",
        "tool": "goose",
        "duration_s": 42.0,
        "success": True,
        "files_changed": 2,
    },
]


class TestSpeedPercentiles:
    @patch("metabolon.sortase.cli.read_logs")
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_speed_percentiles_flag(self, mock_tach_read: object, mock_cli_read: object) -> None:
        """The --percentiles flag is accepted by the speed command."""
        # Both callers need sample data so tachometer metrics don't crash.
        mock_tach_read.return_value = SAMPLE_LOG_ENTRIES
        mock_cli_read.return_value = SAMPLE_LOG_ENTRIES

        runner = CliRunner()
        result = runner.invoke(main, ["speed", "--percentiles", "--days", "1"])
        assert result.exit_code == 0, f"exit_code={result.exit_code}\noutput:\n{result.output}"
        assert "Backend Percentiles" in result.output
        assert "droid" in result.output
        assert "goose" in result.output

    @patch("metabolon.sortase.cli.read_logs")
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_speed_without_percentiles(self, mock_tach_read: object, mock_cli_read: object) -> None:
        """Speed command works without --percentiles (no Backend Percentiles output)."""
        mock_tach_read.return_value = SAMPLE_LOG_ENTRIES
        mock_cli_read.return_value = SAMPLE_LOG_ENTRIES

        runner = CliRunner()
        result = runner.invoke(main, ["speed", "--days", "1"])
        assert result.exit_code == 0, f"exit_code={result.exit_code}\noutput:\n{result.output}"
        assert "Backend Percentiles" not in result.output

    @patch("metabolon.sortase.cli.read_logs")
    def test_log_json_flag(self, mock_read: object) -> None:
        """--json-output returns valid JSON array."""
        mock_read.return_value = SAMPLE_LOG_ENTRIES

        runner = CliRunner()
        result = runner.invoke(main, ["log", "--json-output", "--last", "1"])
        assert result.exit_code == 0, f"exit_code={result.exit_code}\noutput:\n{result.output}"
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["plan"] == "task_b.md"

    @patch("metabolon.sortase.logger.read_logs")
    @patch("metabolon.sortase.cli.read_logs")
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_speed_percentiles_empty_log(self, mock_tach_read: object, mock_cli_read: object, mock_logger_read: object) -> None:
        """Percentiles with empty log does not crash."""
        mock_tach_read.return_value = []
        mock_cli_read.return_value = []
        mock_logger_read.return_value = []

        runner = CliRunner()
        result = runner.invoke(main, ["speed", "--percentiles", "--days", "1"])
        assert result.exit_code == 0, f"exit_code={result.exit_code}\noutput:\n{result.output}"
