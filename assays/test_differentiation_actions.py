"""Tests for differentiation action-dispatch consolidation."""
from unittest.mock import patch, MagicMock
import pytest

from metabolon.enzymes.differentiation import differentiation


class TestUnknownAction:
    def test_unknown_action_returns_error_message(self):
        result = differentiation(action="nonexistent")
        assert isinstance(result, str)
        assert "unknown" in result.lower()
        assert "nonexistent" in result.lower()

    def test_unknown_action_suggests_valid_actions(self):
        result = differentiation(action="bad")
        assert "latest_log" in result or "readiness" in result or "write_log" in result


class TestLatestLogAction:
    @patch("metabolon.enzymes.differentiation.HEALTH_DIR")
    def test_no_logs_found(self, mock_dir):
        mock_dir.glob.return_value = []
        result = differentiation(action="latest_log")
        assert result == "No gym logs found."

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR")
    def test_single_log(self, mock_dir):
        mock_file = MagicMock()
        mock_file.name = "Gym Log - 2026-03-30.md"
        mock_file.read_text.return_value = "# Leg Day\n\nSquats: 3x5"
        mock_dir.glob.return_value = [mock_file]
        result = differentiation(action="latest_log")
        assert "Gym Log - 2026-03-30.md" in result
        assert "# Leg Day" in result
        assert "Squats: 3x5" in result

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR")
    def test_multiple_logs_returns_latest(self, mock_dir):
        # sorted() compares Path-like objects, need to mock name attribute for comparison
        # Create mock files with proper ordering - sorted by name string
        mock_old = MagicMock()
        mock_old.name = "Gym Log - 2026-03-28.md"
        mock_old.read_text.return_value = "old content"
        mock_old.__lt__ = lambda self, other: self.name < other.name

        mock_new = MagicMock()
        mock_new.name = "Gym Log - 2026-03-30.md"
        mock_new.read_text.return_value = "new content"
        mock_new.__lt__ = lambda self, other: self.name < other.name

        # glob returns unsorted, sorted() will order by __lt__
        mock_dir.glob.return_value = [mock_new, mock_old]
        result = differentiation(action="latest_log")
        assert "Gym Log - 2026-03-30.md" in result
        assert "new content" in result
        assert "old content" not in result


class TestReadinessAction:
    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_high_score_full_session(self, mock_readiness):
        mock_readiness.return_value = {
            "score": 85,
            "contributors": {"activity": 90, "sleep": 80},
            "temperature_deviation": 0.2,
        }
        result = differentiation(action="readiness")
        assert "Readiness: 85" in result
        assert "Full session" in result
        assert "Follow working weights" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_moderate_score_70(self, mock_readiness):
        mock_readiness.return_value = {
            "score": 70,
            "contributors": {},
            "temperature_deviation": 0.0,
        }
        result = differentiation(action="readiness")
        assert "Readiness: 70" in result
        assert "Moderate session" in result
        assert "Reduce volume" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_low_score_60(self, mock_readiness):
        mock_readiness.return_value = {
            "score": 60,
            "contributors": {"recovery": 50},
            "temperature_deviation": -0.5,
        }
        result = differentiation(action="readiness")
        assert "Readiness: 60" in result
        assert "Light only" in result
        assert "protect recovery" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_boundary_score_74(self, mock_readiness):
        mock_readiness.return_value = {
            "score": 74,
            "contributors": {},
            "temperature_deviation": None,
        }
        result = differentiation(action="readiness")
        assert "Readiness: 74" in result
        assert "Moderate session" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_boundary_score_75(self, mock_readiness):
        mock_readiness.return_value = {
            "score": 75,
            "contributors": {},
            "temperature_deviation": None,
        }
        result = differentiation(action="readiness")
        assert "Readiness: 75" in result
        assert "Full session" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_no_score_available(self, mock_readiness):
        mock_readiness.return_value = {"score": None}
        result = differentiation(action="readiness")
        assert "No readiness data available" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_api_error(self, mock_readiness):
        mock_readiness.side_effect = RuntimeError("API timeout")
        result = differentiation(action="readiness")
        assert "Error fetching readiness" in result
        assert "API timeout" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_contributors_formatted(self, mock_readiness):
        mock_readiness.return_value = {
            "score": 80,
            "contributors": {"activity": 85, "sleep": 75, "recovery": 90},
            "temperature_deviation": 0.1,
        }
        result = differentiation(action="readiness")
        assert "activity: 85" in result
        assert "sleep: 75" in result
        assert "recovery: 90" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_empty_contributors_shows_dash(self, mock_readiness):
        mock_readiness.return_value = {
            "score": 80,
            "contributors": {},
            "temperature_deviation": 0.0,
        }
        result = differentiation(action="readiness")
        # contributors line should show dash when empty
        assert "Contributors: —" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_temperature_deviation_displayed(self, mock_readiness):
        mock_readiness.return_value = {
            "score": 80,
            "contributors": {},
            "temperature_deviation": 0.35,
        }
        result = differentiation(action="readiness")
        assert "Temperature deviation: 0.35" in result


class TestWriteLogAction:
    @patch("metabolon.enzymes.differentiation.HEALTH_DIR")
    def test_invalid_date_format(self, mock_dir):
        result = differentiation(action="write_log", session_date="2026/03/30", content="test")
        assert "Invalid date format" in result
        assert "2026/03/30" in result
        assert "YYYY-MM-DD" in result

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR")
    def test_invalid_date_not_iso(self, mock_dir):
        result = differentiation(action="write_log", session_date="March 30, 2026", content="test")
        assert "Invalid date format" in result

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR")
    def test_new_file_created(self, mock_dir):
        mock_dir.__truediv__ = lambda self, name: MagicMock(
            exists=MagicMock(return_value=False),
            __str__=lambda self: f"/home/test/{name}",
        )
        mock_target = MagicMock()
        mock_target.exists.return_value = False
        mock_target.__str__ = lambda self: "/home/test/Gym Log - 2026-03-30.md"
        mock_dir.__truediv__ = lambda self, name: mock_target

        result = differentiation(action="write_log", session_date="2026-03-30", content="# Workout")

        mock_target.write_text.assert_called_once_with("# Workout")
        assert "Gym log written" in result

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR")
    def test_existing_file_replaced_atomically(self, mock_dir):
        mock_target = MagicMock()
        mock_target.exists.return_value = True
        mock_target.__str__ = lambda self: "/home/test/Gym Log - 2026-03-30.md"

        mock_tmp = MagicMock()
        mock_target.with_suffix.return_value = mock_tmp

        mock_dir.__truediv__ = lambda self, name: mock_target

        result = differentiation(action="write_log", session_date="2026-03-30", content="Updated content")

        mock_tmp.write_text.assert_called_once_with("Updated content")
        mock_tmp.replace.assert_called_once_with(mock_target)
        assert "Gym log written" in result
