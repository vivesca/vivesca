"""Tests for metabolon.enzymes.differentiation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestLatestLog:
    """Tests for the latest_log action."""

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR", new_callable=lambda: Path("/fake/health"))
    def test_no_logs_found(self, mock_health_dir: Path) -> None:
        """Return message when no gym logs exist."""
        from metabolon.enzymes.differentiation import differentiation

        with patch.object(Path, "glob", return_value=[]):
            result = differentiation(action="latest_log")

        assert result == "No gym logs found."

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR", new_callable=lambda: Path("/fake/health"))
    def test_returns_latest_log(self, mock_health_dir: Path) -> None:
        """Return the most recent gym log file."""
        from metabolon.enzymes.differentiation import differentiation

        # Use actual Path objects which are sortable by string comparison
        log1 = Path("/fake/health/Gym Log - 2026-03-28.md")
        log2 = Path("/fake/health/Gym Log - 2026-03-30.md")

        with patch.object(Path, "glob", return_value=[log1, log2]):
            with patch.object(Path, "read_text", return_value="# Push Day\nBench: 95x5"):
                result = differentiation(action="latest_log")

        assert "Gym Log - 2026-03-30.md" in result
        assert "# Push Day" in result
        assert "Bench: 95x5" in result


class TestReadiness:
    """Tests for the readiness action."""

    @patch("metabolon.enzymes.differentiation.chemoreceptor")
    def test_error_fetching_readiness(self, mock_chemoreceptor: MagicMock) -> None:
        """Handle exceptions from chemoreceptor gracefully."""
        from metabolon.enzymes.differentiation import differentiation

        mock_chemoreceptor.readiness.side_effect = RuntimeError("API down")

        result = differentiation(action="readiness")

        assert "Error fetching readiness: API down" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor")
    def test_no_readiness_score(self, mock_chemoreceptor: MagicMock) -> None:
        """Handle missing score gracefully."""
        from metabolon.enzymes.differentiation import differentiation

        mock_chemoreceptor.readiness.return_value = {"score": None}

        result = differentiation(action="readiness")

        assert "No readiness data available" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor")
    def test_low_readiness_light_only(self, mock_chemoreceptor: MagicMock) -> None:
        """Score below 70 recommends light session only."""
        from metabolon.enzymes.differentiation import differentiation

        mock_chemoreceptor.readiness.return_value = {
            "score": 65,
            "contributors": {"activity": 80, "sleep": 60},
            "temperature_deviation": 0.3,
        }

        result = differentiation(action="readiness")

        assert "Readiness: 65" in result
        assert "Light only" in result
        assert "protect recovery" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor")
    def test_moderate_readiness_reduce_volume(self, mock_chemoreceptor: MagicMock) -> None:
        """Score 70-74 recommends moderate session with reduced volume."""
        from metabolon.enzymes.differentiation import differentiation

        mock_chemoreceptor.readiness.return_value = {
            "score": 72,
            "contributors": {"activity": 75, "sleep": 70},
            "temperature_deviation": -0.1,
        }

        result = differentiation(action="readiness")

        assert "Readiness: 72" in result
        assert "Moderate session OK" in result
        assert "Reduce volume" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor")
    def test_high_readiness_full_session(self, mock_chemoreceptor: MagicMock) -> None:
        """Score 75+ allows full session."""
        from metabolon.enzymes.differentiation import differentiation

        mock_chemoreceptor.readiness.return_value = {
            "score": 82,
            "contributors": {"activity": 90, "sleep": 85},
            "temperature_deviation": 0.0,
        }

        result = differentiation(action="readiness")

        assert "Readiness: 82" in result
        assert "Full session" in result
        assert "Follow working weights" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor")
    def test_contributors_formatted(self, mock_chemoreceptor: MagicMock) -> None:
        """Contributors are formatted as key: value pairs."""
        from metabolon.enzymes.differentiation import differentiation

        mock_chemoreceptor.readiness.return_value = {
            "score": 80,
            "contributors": {"activity": 90, "sleep": 75, "recovery": 85},
            "temperature_deviation": 0.2,
        }

        result = differentiation(action="readiness")

        assert "activity: 90" in result
        assert "sleep: 75" in result
        assert "recovery: 85" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor")
    def test_missing_contributors_shows_dash(self, mock_chemoreceptor: MagicMock) -> None:
        """Missing contributors shows dash."""
        from metabolon.enzymes.differentiation import differentiation

        mock_chemoreceptor.readiness.return_value = {
            "score": 80,
            "contributors": {},
            "temperature_deviation": None,
        }

        result = differentiation(action="readiness")

        assert "Contributors: —" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor")
    def test_temperature_deviation_displayed(self, mock_chemoreceptor: MagicMock) -> None:
        """Temperature deviation is included in output."""
        from metabolon.enzymes.differentiation import differentiation

        mock_chemoreceptor.readiness.return_value = {
            "score": 78,
            "contributors": {},
            "temperature_deviation": -0.5,
        }

        result = differentiation(action="readiness")

        assert "Temperature deviation: -0.5" in result


class TestWriteLog:
    """Tests for the write_log action."""

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR", new_callable=lambda: Path("/fake/health"))
    def test_invalid_date_format(self, mock_health_dir: Path) -> None:
        """Reject invalid date format."""
        from metabolon.enzymes.differentiation import differentiation

        result = differentiation(
            action="write_log",
            session_date="not-a-date",
            content="# Test",
        )

        assert "Invalid date format" in result
        assert "Use YYYY-MM-DD" in result

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR", new_callable=lambda: Path("/fake/health"))
    def test_writes_new_log(self, mock_health_dir: Path) -> None:
        """Write a new gym log file."""
        from metabolon.enzymes.differentiation import differentiation

        mock_target = MagicMock(spec=Path)
        mock_target.exists.return_value = False
        mock_target.__str__ = lambda self: "/fake/health/Gym Log - 2026-04-01.md"

        with patch.object(Path, "__truediv__", return_value=mock_target):
            result = differentiation(
                action="write_log",
                session_date="2026-04-01",
                content="# Push Day\nBench: 100x5",
            )

        mock_target.write_text.assert_called_once_with("# Push Day\nBench: 100x5")
        assert "Gym log written" in result

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR", new_callable=lambda: Path("/fake/health"))
    def test_overwrites_existing_log_safely(self, mock_health_dir: Path) -> None:
        """Overwrite existing log using temp file for safety."""
        from metabolon.enzymes.differentiation import differentiation

        mock_target = MagicMock(spec=Path)
        mock_target.exists.return_value = True
        mock_target.__str__ = lambda self: "/fake/health/Gym Log - 2026-04-01.md"

        mock_tmp = MagicMock(spec=Path)
        mock_target.with_suffix.return_value = mock_tmp

        with patch.object(Path, "__truediv__", return_value=mock_target):
            result = differentiation(
                action="write_log",
                session_date="2026-04-01",
                content="# Updated Log",
            )

        mock_tmp.write_text.assert_called_once_with("# Updated Log")
        mock_tmp.replace.assert_called_once_with(mock_target)
        assert "Gym log written" in result


class TestUnknownAction:
    """Tests for unknown/invalid actions."""

    def test_unknown_action_message(self) -> None:
        """Unknown action returns helpful error message."""
        from metabolon.enzymes.differentiation import differentiation

        result = differentiation(action="invalid_action")

        assert "Unknown action" in result
        assert "invalid_action" in result
        assert "latest_log" in result
        assert "readiness" in result
        assert "write_log" in result
