"""Tests for metabolon.enzymes.differentiation — gym coaching tool.

Covers all four dispatch branches: latest_log, readiness, write_log, and
the unknown-action fallback. External calls (chemoreceptor.readiness) and
filesystem paths (HEALTH_DIR) are mocked so tests are hermetic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from metabolon.enzymes.differentiation import differentiation

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# latest_log
# ---------------------------------------------------------------------------


class TestLatestLog:
    """Tests for action='latest_log'."""

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR")
    def test_no_logs_returns_message(self, mock_dir: MagicMock) -> None:
        mock_dir.glob.return_value = []
        assert differentiation("latest_log") == "No gym logs found."

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR")
    def test_single_log(self, mock_dir: MagicMock) -> None:
        mock_file = MagicMock()
        mock_file.name = "Gym Log - 2026-03-28.md"
        mock_file.read_text.return_value = "# Push day"
        mock_dir.glob.return_value = [mock_file]

        result = differentiation("latest_log")
        assert "Gym Log - 2026-03-28.md" in result
        assert "# Push day" in result

    @patch("metabolon.enzymes.differentiation.HEALTH_DIR")
    def test_multiple_logs_returns_latest(self, mock_dir: MagicMock) -> None:
        old = MagicMock(name="old_log")
        old.name = "Gym Log - 2026-03-25.md"
        old.read_text.return_value = "old content"
        old.__lt__ = lambda self, other: self.name < other.name  # type: ignore[attr-defined]

        new = MagicMock(name="new_log")
        new.name = "Gym Log - 2026-03-30.md"
        new.read_text.return_value = "new content"
        new.__lt__ = lambda self, other: self.name < other.name  # type: ignore[attr-defined]

        # Return unsorted; sorted() inside the function will order them
        mock_dir.glob.return_value = [new, old]

        result = differentiation("latest_log")
        assert "Gym Log - 2026-03-30.md" in result
        assert "new content" in result
        assert "old content" not in result


# ---------------------------------------------------------------------------
# readiness
# ---------------------------------------------------------------------------


class TestReadiness:
    """Tests for action='readiness'."""

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_api_exception(self, mock_ready: MagicMock) -> None:
        mock_ready.side_effect = ConnectionError("network unreachable")
        result = differentiation("readiness")
        assert "Error fetching readiness: network unreachable" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_missing_score(self, mock_ready: MagicMock) -> None:
        mock_ready.return_value = {"score": None}
        assert differentiation("readiness") == "No readiness data available for today."

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_empty_dict_no_score_key(self, mock_ready: MagicMock) -> None:
        mock_ready.return_value = {}
        assert differentiation("readiness") == "No readiness data available for today."

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_low_score_under_70(self, mock_ready: MagicMock) -> None:
        mock_ready.return_value = {"score": 60, "contributors": {}, "temperature_deviation": -0.5}
        result = differentiation("readiness")
        assert "Readiness: 60" in result
        assert "Light only" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_boundary_69_light(self, mock_ready: MagicMock) -> None:
        mock_ready.return_value = {"score": 69, "contributors": {}, "temperature_deviation": 0}
        result = differentiation("readiness")
        assert "Light only" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_boundary_70_moderate(self, mock_ready: MagicMock) -> None:
        mock_ready.return_value = {"score": 70, "contributors": {}, "temperature_deviation": 0}
        result = differentiation("readiness")
        assert "Moderate session" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_boundary_74_still_moderate(self, mock_ready: MagicMock) -> None:
        mock_ready.return_value = {"score": 74, "contributors": {}, "temperature_deviation": 0}
        result = differentiation("readiness")
        assert "Moderate session" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_boundary_75_full(self, mock_ready: MagicMock) -> None:
        mock_ready.return_value = {"score": 75, "contributors": {}, "temperature_deviation": 0}
        result = differentiation("readiness")
        assert "Full session" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_high_score_full(self, mock_ready: MagicMock) -> None:
        mock_ready.return_value = {"score": 89, "contributors": {}, "temperature_deviation": 0.2}
        result = differentiation("readiness")
        assert "Full session" in result
        assert "Temperature deviation: 0.2" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_contributors_formatted(self, mock_ready: MagicMock) -> None:
        mock_ready.return_value = {
            "score": 80,
            "contributors": {"hrv": 90, "activity": 75},
            "temperature_deviation": None,
        }
        result = differentiation("readiness")
        assert "hrv: 90" in result
        assert "activity: 75" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_empty_contributors_shows_dash(self, mock_ready: MagicMock) -> None:
        mock_ready.return_value = {
            "score": 80,
            "contributors": {},
            "temperature_deviation": None,
        }
        result = differentiation("readiness")
        assert "Contributors: —" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_temperature_key_absent_shows_dash(self, mock_ready: MagicMock) -> None:
        """When key is missing, data.get returns the '—' default."""
        mock_ready.return_value = {
            "score": 80,
            "contributors": {},
        }
        result = differentiation("readiness")
        assert "Temperature deviation: —" in result

    @patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
    def test_temperature_none_displayed_as_none(self, mock_ready: MagicMock) -> None:
        """When key is present with value None, it renders as 'None'."""
        mock_ready.return_value = {
            "score": 80,
            "contributors": {},
            "temperature_deviation": None,
        }
        result = differentiation("readiness")
        assert "Temperature deviation: None" in result


# ---------------------------------------------------------------------------
# write_log
# ---------------------------------------------------------------------------


class TestWriteLog:
    """Tests for action='write_log'."""

    def test_invalid_date_format(self) -> None:
        result = differentiation("write_log", session_date="03/30/2026", content="x")
        assert "Invalid date format" in result
        assert "03/30/2026" in result
        assert "YYYY-MM-DD" in result

    def test_non_iso_date_rejected(self) -> None:
        result = differentiation("write_log", session_date="March 1", content="x")
        assert "Invalid date format" in result

    def test_new_file_created(self, tmp_path: Path) -> None:
        session_date = "2026-04-01"
        content = "# Squats\n5x100 kg"
        target = tmp_path / f"Gym Log - {session_date}.md"

        with patch("metabolon.enzymes.differentiation.HEALTH_DIR", tmp_path):
            result = differentiation("write_log", session_date=session_date, content=content)

        assert "Gym log written" in result
        assert target.exists()
        assert target.read_text() == content

    def test_overwrite_existing_file(self, tmp_path: Path) -> None:
        session_date = "2026-03-30"
        target = tmp_path / f"Gym Log - {session_date}.md"
        target.write_text("old content")

        new_content = "# Updated session"
        with patch("metabolon.enzymes.differentiation.HEALTH_DIR", tmp_path):
            result = differentiation("write_log", session_date=session_date, content=new_content)

        assert "Gym log written" in result
        assert target.read_text() == new_content

    def test_empty_content_allowed(self, tmp_path: Path) -> None:
        session_date = "2026-01-15"
        with patch("metabolon.enzymes.differentiation.HEALTH_DIR", tmp_path):
            differentiation("write_log", session_date=session_date, content="")

        target = tmp_path / f"Gym Log - {session_date}.md"
        assert target.exists()
        assert target.read_text() == ""


# ---------------------------------------------------------------------------
# unknown action
# ---------------------------------------------------------------------------


class TestUnknownAction:
    """Tests for unrecognised action values."""

    def test_returns_error_with_action_name(self) -> None:
        result = differentiation("bicep_curls")
        assert "Unknown action" in result
        assert "bicep_curls" in result

    def test_suggests_valid_actions(self) -> None:
        result = differentiation("nope")
        assert "latest_log" in result
        assert "readiness" in result
        assert "write_log" in result

    def test_empty_action(self) -> None:
        result = differentiation("")
        assert "Unknown action" in result
