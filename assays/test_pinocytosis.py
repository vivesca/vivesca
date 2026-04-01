from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.pinocytosis import (
    EntrainmentStatusResult,
    PinocytosisResult,
    _count_job_alerts,
    _count_goose_tasks,
    _day_snapshot,
    _entrainment_brief,
    _hkt_now,
    _read_efferens,
    _read_if_fresh,
    _read_now_md,
    _read_praxis_today,
    pinocytosis,
)


def test_hkt_now_exists():
    """Test that _hkt_now returns a datetime with HKT timezone (UTC+8)."""
    result = _hkt_now()
    assert result.tzinfo is not None
    # Check that the offset is +8 hours
    offset = result.utcoffset()
    assert offset is not None
    assert offset == timedelta(hours=8)


def test_read_if_fresh_nonexistent():
    """Test _read_if_fresh returns None for non-existent file."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = False
    result = _read_if_fresh(mock_path)
    assert result is None


def test_read_if_fresh_fresh_file():
    """Test _read_if_fresh returns content for fresh file."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True
    mock_path.stat.return_value.st_mtime = 1000000000
    mock_path.read_text.return_value = "  test content  "

    with patch("time.time", return_value=1000000000 + 3600):  # 1 hour later
        result = _read_if_fresh(mock_path, max_age_hours=24)
        assert result == "test content"


def test_pinocytosis_read_if_fresh_stale_file():
    """Test _read_if_fresh returns None for stale file."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True
    mock_path.stat.return_value.st_mtime = 1000000000
    mock_path.read_text.return_value = "test content"

    with patch("time.time", return_value=1000000000 + (25 * 3600)):  # 25 hours later
        result = _read_if_fresh(mock_path, max_age_hours=24)
        assert result is None


def test_pinocytosis_read_now_md_not_exists():
    """Test _read_now_md when file doesn't exist."""
    from metabolon.enzymes import pinocytosis as module
    original = module.NOW_MD
    try:
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        module.NOW_MD = mock_path
        result = _read_now_md()
        assert "not found" in result
    finally:
        module.NOW_MD = original


def test_read_now_md_filters_completed():
    """Test _read_now_md filters out completed items."""
    from metabolon.enzymes import pinocytosis as module
    original = module.NOW_MD
    try:
        content = """- [ ] Open item 1
- [x] Done item 1
[decided] Decided item
- [ ] Open item 2
[done] Another done
"""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = content
        module.NOW_MD = mock_path
        result = _read_now_md()
        assert "Open item 1" in result
        assert "Open item 2" in result
        assert "Done item 1" not in result
        assert "Decided item" not in result
    finally:
        module.NOW_MD = original


def test_pinocytosis_count_job_alerts_no_files():
    """Test _count_job_alerts when no files exist."""
    from metabolon.enzymes import pinocytosis as module
    original = module.JOB_HUNT_DIR
    try:
        # Create a proper mock that handles glob and returns empty list
        mock_dir = MagicMock()
        mock_dir.glob = MagicMock(return_value=[])
        module.JOB_HUNT_DIR = mock_dir
        with patch("metabolon.enzymes.pinocytosis._hkt_now") as mock_hkt:
            mock_dt = MagicMock()
            mock_dt.strftime.return_value = "2026-04-01"
            mock_hkt.return_value = mock_dt
            result = _count_job_alerts()
            assert "No job alert" in result
    finally:
        module.JOB_HUNT_DIR = original


def test_pinocytosis_read_efferens_import_error():
    """Test _read_efferens handles import error."""
    with patch("builtins.__import__", side_effect=ImportError("No acta")):
        result = _read_efferens()
        assert "unavailable" in result.lower()


def test_count_goose_tasks_no_dir():
    """Test _count_goose_tasks when done dir doesn't exist."""
    result = _count_goose_tasks()
    assert "0 ready" in result


def test_pinocytosis_read_praxis_today_import_error():
    """Test _read_praxis_today handles import error."""
    with patch("builtins.__import__", side_effect=ImportError("No praxis")):
        result = _read_praxis_today()
        assert "unavailable" in result.lower()


def test_day_snapshot_json():
    """Test _day_snapshot with json_output=True."""
    with patch("metabolon.enzymes.pinocytosis._hkt_now") as mock_hkt:
        mock_dt = MagicMock()
        mock_dt.strftime.return_value = "10:30AM Monday 2026-04-01 HKT"
        mock_hkt.return_value = mock_dt
        mock_dt.hour = 10

        with patch("metabolon.enzymes.pinocytosis._read_now_md") as mock_read_now:
            mock_read_now.return_value = "Test now md"
            with patch("metabolon.enzymes.pinocytosis._read_praxis_today") as mock_praxis:
                mock_praxis.return_value = "Test praxis"
                with patch("metabolon.enzymes.pinocytosis._read_efferens") as mock_eff:
                    mock_eff.return_value = "Test efferens"
                    with patch("metabolon.enzymes.pinocytosis._count_goose_tasks") as mock_goose:
                        mock_goose.return_value = "Goose tasks: 2 ready for review."

                        result = _day_snapshot(json_output=True)
                        assert isinstance(result, PinocytosisResult)
                        parsed = json.loads(result.output)
                        assert "time" in parsed
                        assert "now_md" in parsed
                        assert "praxis" in parsed
                        assert "efferens" in parsed
                        assert "goose_tasks" in parsed
                        assert "job_alerts" in parsed


def test_entrainment_brief_chemoreceptor_error():
    """Test _entrainment_brief handles chemoreceptor error."""
    with patch("metabolon.enzymes.pinocytosis._read_if_fresh") as mock_read:
        mock_read.return_value = None
        with patch("builtins.__import__", side_effect=ImportError("No chemoreceptor")):
            result = _entrainment_brief()
            assert isinstance(result, PinocytosisResult)
            assert "unavailable" in result.output


def test_pinocytosis_pinocytosis_unknown_action():
    """Test pinocytosis returns error for unknown action."""
    result = pinocytosis(action="invalid_action")
    assert not result.success
    assert "Unknown action" in result.message


def test_pinocytosis_pinocytosis_day_action():
    """Test pinocytosis with day action."""
    with patch("metabolon.enzymes.pinocytosis._day_snapshot") as mock_snapshot:
        mock_snapshot.return_value = PinocytosisResult(output="test")
        result = pinocytosis(action="day")
        assert isinstance(result, PinocytosisResult)
        mock_snapshot.assert_called_once()


def test_pinocytosis_entrainment_status():
    """Test pinocytosis with entrainment_status action."""
    # The imports are inside the function, so we need to patch builtins.__import__
    # and mock the imported module properly
    mock_zeitgebers_func = MagicMock(return_value={"some": "signal"})
    mock_optimal_func = MagicMock(return_value={
        "recommendations": {"rec": "test"},
        "summary": "test summary"
    })

    mock_module = MagicMock()
    mock_module.optimal_schedule = mock_optimal_func
    mock_module.zeitgebers = mock_zeitgebers_func

    def mock_import(name, *args, **kwargs):
        if name == "metabolon.organelles.entrainment":
            return mock_module
        raise ImportError("Not what we're looking for")

    with patch("builtins.__import__", side_effect=mock_import):
        result = pinocytosis(action="entrainment_status")
        assert isinstance(result, EntrainmentStatusResult)
        assert result.signals == {"some": "signal"}
        assert result.summary == "test summary"
