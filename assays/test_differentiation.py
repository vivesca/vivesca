"""Tests for differentiation.py gym coaching tool."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from metabolon.enzymes.differentiation import differentiation


def test_latest_log_no_logs():
    """Test latest_log when no gym logs exist."""
    with patch("metabolon.enzymes.differentiation.HEALTH_DIR") as mock_dir:
        mock_dir.glob.return_value = []
        result = differentiation("latest_log")
        assert result == "No gym logs found."


def test_latest_log_with_logs():
    """Test latest_log returns the most recent log content."""
    with patch("metabolon.enzymes.differentiation.HEALTH_DIR") as mock_dir:
        # Create mock log files sorted by name (date order)
        mock_old = MagicMock()
        mock_old.name = "Gym Log - 2026-03-25.md"
        mock_old.read_text.return_value = "Old workout"

        mock_new = MagicMock()
        mock_new.name = "Gym Log - 2026-03-30.md"
        mock_new.read_text.return_value = "New workout"

        mock_dir.glob.return_value = [mock_old, mock_new]

        result = differentiation("latest_log")
        assert "Gym Log - 2026-03-30.md" in result
        assert "New workout" in result


def test_readiness_error_fetching():
    """Test readiness handles exceptions from chemoreceptor."""
    with patch("metabolon.enzymes.differentiation.chemoreceptor") as mock_chemo:
        mock_chemo.readiness.side_effect = RuntimeError("API down")
        result = differentiation("readiness")
        assert "Error fetching readiness: API down" in result


def test_readiness_no_score():
    """Test readiness when no score is available."""
    with patch("metabolon.enzymes.differentiation.chemoreceptor") as mock_chemo:
        mock_chemo.readiness.return_value = {}
        result = differentiation("readiness")
        assert "No readiness data available for today." in result


def test_readiness_low_score():
    """Test readiness guidance for low score (<70)."""
    with patch("metabolon.enzymes.differentiation.chemoreceptor") as mock_chemo:
        mock_chemo.readiness.return_value = {"score": 65}
        result = differentiation("readiness")
        assert "Readiness: 65" in result
        assert "Light only — protect recovery. Skip heavy compounds." in result


def test_readiness_moderate_score():
    """Test readiness guidance for moderate score (70-74)."""
    with patch("metabolon.enzymes.differentiation.chemoreceptor") as mock_chemo:
        mock_chemo.readiness.return_value = {"score": 72}
        result = differentiation("readiness")
        assert "Readiness: 72" in result
        assert "Moderate session OK. Reduce volume or weight by ~10%." in result


def test_readiness_full_score():
    """Test readiness guidance for full score (>=75)."""
    with patch("metabolon.enzymes.differentiation.chemoreceptor") as mock_chemo:
        mock_chemo.readiness.return_value = {"score": 80}
        result = differentiation("readiness")
        assert "Readiness: 80" in result
        assert "Full session. Follow working weights from last log." in result


def test_readiness_with_contributors():
    """Test readiness includes contributor details."""
    with patch("metabolon.enzymes.differentiation.chemoreceptor") as mock_chemo:
        mock_chemo.readiness.return_value = {
            "score": 78,
            "contributors": {"hrv": 85, "activity": 70},
            "temperature_deviation": -0.3
        }
        result = differentiation("readiness")
        assert "hrv: 85" in result
        assert "activity: 70" in result
        assert "Temperature deviation: -0.3" in result


def test_unknown_action():
    """Test unknown action returns error message."""
    result = differentiation("invalid_action")
    assert "Unknown action: 'invalid_action'" in result


def test_write_log_invalid_date():
    """Test write_log rejects invalid date format."""
    result = differentiation("write_log", session_date="invalid-date", content="test")
    assert "Invalid date format: 'invalid-date'" in result


def test_write_log_new_file(tmp_path):
    """Test write_log creates a new file."""
    from unittest.mock import patch
    with patch("metabolon.enzymes.differentiation.HEALTH_DIR", tmp_path):
        session_date = "2026-04-01"
        content = "# Gym Log\n- Squat: 100kg x 5"

        result = differentiation("write_log", session_date=session_date, content=content)
        assert f"Gym log written to {tmp_path}/Gym Log - 2026-04-01.md" in result

        # Verify file was created with correct content
        output_file = tmp_path / f"Gym Log - {session_date}.md"
        assert output_file.exists()
        assert output_file.read_text() == content


def test_write_log_overwrite_existing(tmp_path):
    """Test write_log overwrites an existing file."""
    from unittest.mock import patch
    with patch("metabolon.enzymes.differentiation.HEALTH_DIR", tmp_path):
        session_date = "2026-04-01"
        old_content = "Old content"
        new_content = "New content"

        # Create existing file
        existing_file = tmp_path / f"Gym Log - {session_date}.md"
        existing_file.write_text(old_content)

        result = differentiation("write_log", session_date=session_date, content=new_content)
        assert f"Gym log written to {tmp_path}/Gym Log - 2026-04-01.md" in result

        # Verify content was updated
        assert existing_file.exists()
        assert existing_file.read_text() == new_content
