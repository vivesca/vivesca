"""Tests for metabolon/enzymes/pinocytosis.py — deterministic context gathering."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from metabolon.enzymes import pinocytosis as pino

# ---------------------------------------------------------------------------
# Test _hkt_now
# ---------------------------------------------------------------------------


def test_hkt_now_returns_datetime():
    """Test _hkt_now returns a datetime object."""
    result = pino._hkt_now()
    assert isinstance(result, datetime)


def test_hkt_now_has_hkt_timezone():
    """Test _hkt_now returns time in HKT timezone (UTC+8)."""
    result = pino._hkt_now()
    assert result.tzinfo is not None
    # HKT is UTC+8
    offset = result.tzinfo.utcoffset(result)
    assert offset == timedelta(hours=8)


# ---------------------------------------------------------------------------
# Test _read_if_fresh
# ---------------------------------------------------------------------------


def test_read_if_fresh_file_not_exists():
    """Test _read_if_fresh returns None when file doesn't exist."""
    with patch.object(Path, 'exists', return_value=False):
        result = pino._read_if_fresh(Path("/nonexistent/file.md"))
    assert result is None


def test_read_if_fresh_file_too_old():
    """Test _read_if_fresh returns None when file is too old."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True
    mock_path.stat.return_value.st_mtime = time.time() - (25 * 3600)  # 25 hours old
    result = pino._read_if_fresh(mock_path, max_age_hours=24)
    assert result is None


def test_read_if_fresh_file_fresh():
    """Test _read_if_fresh returns content when file is fresh."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True
    mock_path.stat.return_value.st_mtime = time.time() - 3600  # 1 hour old
    mock_path.read_text.return_value = "  test content  "
    result = pino._read_if_fresh(mock_path, max_age_hours=24)
    assert result == "test content"


def test_read_if_fresh_file_exception():
    """Test _read_if_fresh returns None on exception."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True
    mock_path.stat.side_effect = PermissionError("no access")
    result = pino._read_if_fresh(mock_path)
    assert result is None


# ---------------------------------------------------------------------------
# Test _read_now_md
# ---------------------------------------------------------------------------


def test_read_now_md_not_exists():
    """Test _read_now_md when file doesn't exist."""
    with patch('pathlib.Path.exists', return_value=False):
        result = pino._read_now_md()
    assert result == "NOW.md not found."


def test_read_now_md_read_error():
    """Test _read_now_md when file read fails."""
    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', side_effect=PermissionError("no access")):
            result = pino._read_now_md()
    assert "read error" in result.lower()


def test_read_now_md_filters_done_items():
    """Test _read_now_md filters out done items."""
    content = """- [ ] Task 1
- [x] Task 2 (done)
- [Decided] Task 3
- [Done] Task 4
- Regular item
"""
    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', return_value=content):
            result = pino._read_now_md()
    assert "Task 1" in result
    assert "Task 2" not in result
    assert "Task 3" not in result
    assert "Task 4" not in result
    assert "Regular item" in result


def test_read_now_md_empty_result():
    """Test _read_now_md when all items are done."""
    content = "- [x] Done\n- [Decided] Done too\n"
    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', return_value=content):
            result = pino._read_now_md()
    assert "no open items" in result.lower()


def test_read_now_md_limits_to_20_items():
    """Test _read_now_md limits output to 20 items."""
    lines = [f"- [ ] Task {i}" for i in range(30)]
    content = "\n".join(lines)
    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', return_value=content):
            result = pino._read_now_md()
    # Should have 20 items in output
    assert result.count("Task") == 20


# ---------------------------------------------------------------------------
# Test _count_job_alerts
# ---------------------------------------------------------------------------


def test_count_job_alerts_no_files():
    """Test _count_job_alerts when no alert files exist."""
    with patch('pathlib.Path.exists', return_value=False):
        with patch('pathlib.Path.glob', return_value=[]):
            result = pino._count_job_alerts()
    assert "No job alert files" in result


def test_count_job_alerts_today_file():
    """Test _count_job_alerts uses today's file."""
    today = datetime.now(pino.HKT).strftime("%Y-%m-%d")

    with patch('metabolon.enzymes.pinocytosis._hkt_now') as mock_now:
        mock_now.return_value = datetime.now(pino.HKT)
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.read_text', return_value="- [ ] Job 1\n- [x] Job 2\n- [ ] Job 3\n"):
                with patch('pathlib.Path.glob', return_value=[]):
                    result = pino._count_job_alerts()

    assert "2/3 unchecked" in result


def test_count_job_alerts_uses_latest():
    """Test _count_job_alerts uses latest file when today's doesn't exist."""
    mock_latest = MagicMock(spec=Path)
    mock_latest.name = "Job Alerts 2024-03-15.md"
    mock_latest.read_text.return_value = "- [ ] Job A\n- [ ] Job B\n"

    with patch('metabolon.enzymes.pinocytosis._hkt_now') as mock_now:
        mock_now.return_value = datetime.now(pino.HKT)
        with patch('pathlib.Path.exists', return_value=False):
            with patch('pathlib.Path.glob', return_value=[mock_latest]):
                result = pino._count_job_alerts()

    assert "2/2 unchecked" in result


def test_count_job_alerts_read_error():
    """Test _count_job_alerts handles read errors."""
    with patch('metabolon.enzymes.pinocytosis._hkt_now') as mock_now:
        mock_now.return_value = datetime.now(pino.HKT)
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.read_text', side_effect=PermissionError("no access")):
                with patch('pathlib.Path.glob', return_value=[]):
                    result = pino._count_job_alerts()

    assert "read error" in result.lower()


# ---------------------------------------------------------------------------
# Test _read_efferens
# ---------------------------------------------------------------------------


def test_read_efferens_empty():
    """Test _read_efferens when board is empty."""
    mock_acta = MagicMock()
    mock_acta.read.return_value = []

    with patch.dict('sys.modules', {'acta': mock_acta}):
        result = pino._read_efferens()

    assert "board empty" in result.lower()


def test_read_efferens_with_messages():
    """Test _read_efferens with messages."""
    mock_acta = MagicMock()
    mock_acta.read.return_value = [
        {"severity": "high", "from": "system", "body": "Test message"},
        {"severity": "info", "from": "user", "body": "Another message"},
    ]

    with patch.dict('sys.modules', {'acta': mock_acta}):
        result = pino._read_efferens()

    assert "2 message(s)" in result
    assert "high" in result
    assert "system" in result


def test_read_efferens_import_error():
    """Test _read_efferens when acta import fails."""
    with patch.dict('sys.modules', {}):
        with patch('builtins.__import__', side_effect=ImportError("no acta")):
            result = pino._read_efferens()

    assert "unavailable" in result.lower()


# ---------------------------------------------------------------------------
# Test _count_goose_tasks
# ---------------------------------------------------------------------------


def test_count_goose_tasks_no_done_dir():
    """Test _count_goose_tasks when done directory doesn't exist."""
    with patch('pathlib.Path.exists', return_value=False):
        result = pino._count_goose_tasks()
    assert "0 ready for review" in result


def test_count_goose_tasks_with_files():
    """Test _count_goose_tasks counts markdown files."""
    mock_files = [MagicMock(spec=Path), MagicMock(spec=Path), MagicMock(spec=Path)]
    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.glob', return_value=mock_files):
            result = pino._count_goose_tasks()
    assert "3 ready for review" in result


def test_count_goose_tasks_empty():
    """Test _count_goose_tasks when no done files."""
    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.glob', return_value=[]):
            result = pino._count_goose_tasks()
    assert "0 ready for review" in result


# ---------------------------------------------------------------------------
# Test _read_praxis_today
# ---------------------------------------------------------------------------


def test_read_praxis_today_nothing_due():
    """Test _read_praxis_today when nothing due."""
    mock_praxis = MagicMock()
    mock_praxis.today.return_value = {"overdue": [], "today": []}

    with patch.dict('sys.modules', {'metabolon.organelles.praxis': mock_praxis}):
        result = pino._read_praxis_today()

    assert "nothing due" in result.lower()


def test_read_praxis_today_with_items():
    """Test _read_praxis_today with items due."""
    mock_praxis = MagicMock()
    mock_praxis.today.return_value = {
        "overdue": [{"text": "Overdue task", "due": "2024-03-10"}],
        "today": [{"text": "Today task", "due": "2024-03-15"}],
    }

    with patch.dict('sys.modules', {'metabolon.organelles.praxis': mock_praxis}):
        result = pino._read_praxis_today()

    assert "Overdue task" in result
    assert "Today task" in result
    assert "[overdue]" in result
    assert "[today]" in result


def test_read_praxis_today_import_error():
    """Test _read_praxis_today when import fails."""
    with patch.dict('sys.modules', {}):
        with patch('builtins.__import__', side_effect=ImportError("no praxis")):
            result = pino._read_praxis_today()

    assert "unavailable" in result.lower()


# ---------------------------------------------------------------------------
# Test _day_snapshot
# ---------------------------------------------------------------------------


def test_day_snapshot_json_output():
    """Test _day_snapshot returns valid JSON."""
    with patch('metabolon.enzymes.pinocytosis._hkt_now') as mock_now:
        mock_now.return_value = datetime(2024, 3, 15, 14, 30, tzinfo=pino.HKT)
        with patch('metabolon.enzymes.pinocytosis._read_now_md', return_value="NOW items"):
            with patch('metabolon.enzymes.pinocytosis._read_praxis_today', return_value="Praxis"):
                with patch('metabolon.enzymes.pinocytosis._read_efferens', return_value="Efferens"):
                    with patch('metabolon.enzymes.pinocytosis._count_goose_tasks', return_value="Goose"):
                        with patch('metabolon.enzymes.pinocytosis._count_job_alerts', return_value="Jobs"):
                            result = pino._day_snapshot(json_output=True)

    assert isinstance(result, pino.PinocytosisResult)
    data = json.loads(result.output)
    assert data["now_md"] == "NOW items"
    assert data["praxis"] == "Praxis"


def test_day_snapshot_text_output():
    """Test _day_snapshot returns formatted text."""
    with patch('metabolon.enzymes.pinocytosis._hkt_now') as mock_now:
        mock_now.return_value = datetime(2024, 3, 15, 14, 30, tzinfo=pino.HKT)
        with patch('metabolon.enzymes.pinocytosis._read_now_md', return_value="NOW items"):
            with patch('metabolon.enzymes.pinocytosis._read_praxis_today', return_value="Praxis"):
                with patch('metabolon.enzymes.pinocytosis._read_efferens', return_value="Efferens"):
                    with patch('metabolon.enzymes.pinocytosis._count_goose_tasks', return_value="Goose"):
                        with patch('metabolon.enzymes.pinocytosis._count_job_alerts', return_value="Jobs"):
                            result = pino._day_snapshot(json_output=False)

    assert isinstance(result, pino.PinocytosisResult)
    assert "snapshot" in result.output.lower()
    assert "NOW items" in result.output


def test_day_snapshot_pre_noon_skips_jobs():
    """Test _day_snapshot skips job alerts before noon."""
    with patch('metabolon.enzymes.pinocytosis._hkt_now') as mock_now:
        mock_now.return_value = datetime(2024, 3, 15, 10, 30, tzinfo=pino.HKT)  # 10:30 AM
        with patch('metabolon.enzymes.pinocytosis._read_now_md', return_value="NOW"):
            with patch('metabolon.enzymes.pinocytosis._read_praxis_today', return_value="Praxis"):
                with patch('metabolon.enzymes.pinocytosis._read_efferens', return_value="Efferens"):
                    with patch('metabolon.enzymes.pinocytosis._count_goose_tasks', return_value="Goose"):
                        result = pino._day_snapshot(json_output=True)

    data = json.loads(result.output)
    assert "skipped" in data["job_alerts"].lower()


# ---------------------------------------------------------------------------
# Test _entrainment_brief
# ---------------------------------------------------------------------------


def test_entrainment_brief_basic():
    """Test _entrainment_brief returns valid output."""
    mock_sense = MagicMock()
    mock_sense.sense.return_value = {"error": "no data"}

    with patch.dict('sys.modules', {'metabolon.organelles.chemoreceptor': mock_sense}):
        with patch('metabolon.enzymes.pinocytosis._read_if_fresh', return_value=None):
            with patch.dict('sys.modules', {'metabolon.cytosol': MagicMock()}):
                result = pino._entrainment_brief()

    assert isinstance(result, pino.PinocytosisResult)
    assert "Sleep" in result.output


def test_entrainment_brief_with_oura_data():
    """Test _entrainment_brief with Oura data."""
    mock_sense = MagicMock()
    mock_sense.sense.return_value = {
        "sleep_score": 85,
        "readiness_score": 70,
        "spo2": {"average": 97},
    }

    with patch.dict('sys.modules', {'metabolon.organelles.chemoreceptor': mock_sense}):
        with patch('metabolon.enzymes.pinocytosis._read_if_fresh', return_value=None):
            with patch.dict('sys.modules', {'metabolon.cytosol': MagicMock()}):
                result = pino._entrainment_brief()

    assert "Sleep: 85" in result.output
    assert "Readiness: 70" in result.output


def test_entrainment_brief_low_readiness_alert():
    """Test _entrainment_brief alerts on low readiness."""
    mock_sense = MagicMock()
    mock_sense.sense.return_value = {
        "sleep_score": 60,
        "readiness_score": 50,  # Low!
    }

    with patch.dict('sys.modules', {'metabolon.organelles.chemoreceptor': mock_sense}):
        with patch('metabolon.enzymes.pinocytosis._read_if_fresh', return_value=None):
            with patch.dict('sys.modules', {'metabolon.cytosol': MagicMock()}):
                result = pino._entrainment_brief()

    assert "Low readiness" in result.output
    assert "Alert" in result.output


# ---------------------------------------------------------------------------
# Test _overnight_results and _overnight_list
# ---------------------------------------------------------------------------


def test_overnight_results():
    """Test _overnight_results invokes organelle."""
    mock_cytosol = MagicMock()
    mock_cytosol.invoke_organelle.return_value = "overnight results output"
    mock_cytosol.VIVESCA_ROOT = Path("/tmp/vivesca")

    with patch.dict('sys.modules', {'metabolon.cytosol': mock_cytosol}):
        result = pino._overnight_results("test_task")

    assert isinstance(result, pino.PinocytosisResult)
    assert result.output == "overnight results output"
    mock_cytosol.invoke_organelle.assert_called_once()


def test_overnight_list():
    """Test _overnight_list invokes organelle."""
    mock_cytosol = MagicMock()
    mock_cytosol.invoke_organelle.return_value = "task1\ntask2\n"
    mock_cytosol.VIVESCA_ROOT = Path("/tmp/vivesca")

    with patch.dict('sys.modules', {'metabolon.cytosol': mock_cytosol}):
        result = pino._overnight_list()

    assert isinstance(result, pino.PinocytosisResult)
    assert "task1" in result.output


# ---------------------------------------------------------------------------
# Test pinocytosis main function
# ---------------------------------------------------------------------------


def test_pinocytosis_day_action():
    """Test pinocytosis with day action."""
    with patch('metabolon.enzymes.pinocytosis._day_snapshot') as mock_snapshot:
        mock_snapshot.return_value = pino.PinocytosisResult(output="day output")
        result = pino.pinocytosis(action="day", json_output=True)

    assert isinstance(result, pino.PinocytosisResult)
    assert result.output == "day output"


def test_pinocytosis_overnight_action():
    """Test pinocytosis with overnight action."""
    with patch('metabolon.enzymes.pinocytosis._entrainment_brief') as mock_brief:
        mock_brief.return_value = pino.PinocytosisResult(output="brief output")
        result = pino.pinocytosis(action="overnight")

    assert isinstance(result, pino.PinocytosisResult)


def test_pinocytosis_overnight_results_action():
    """Test pinocytosis with overnight_results action."""
    mock_cytosol = MagicMock()
    mock_cytosol.invoke_organelle.return_value = "results"
    mock_cytosol.VIVESCA_ROOT = Path("/tmp")

    with patch.dict('sys.modules', {'metabolon.cytosol': mock_cytosol}):
        result = pino.pinocytosis(action="overnight_results", task="mytask")

    assert isinstance(result, pino.PinocytosisResult)


def test_pinocytosis_overnight_list_action():
    """Test pinocytosis with overnight_list action."""
    mock_cytosol = MagicMock()
    mock_cytosol.invoke_organelle.return_value = "list"
    mock_cytosol.VIVESCA_ROOT = Path("/tmp")

    with patch.dict('sys.modules', {'metabolon.cytosol': mock_cytosol}):
        result = pino.pinocytosis(action="overnight_list")

    assert isinstance(result, pino.PinocytosisResult)


def test_pinocytosis_morning_action():
    """Test pinocytosis with morning action."""
    mock_photoreception = MagicMock()
    mock_photoreception.intake.return_value = "morning intake"

    with patch.dict('sys.modules', {'metabolon.pinocytosis.photoreception': mock_photoreception}):
        result = pino.pinocytosis(action="morning")

    assert isinstance(result, pino.PinocytosisResult)


def test_pinocytosis_evening_action():
    """Test pinocytosis with evening action."""
    mock_interphase = MagicMock()
    mock_interphase.intake.return_value = "evening intake"

    with patch.dict('sys.modules', {'metabolon.pinocytosis.interphase': mock_interphase}):
        result = pino.pinocytosis(action="evening")

    assert isinstance(result, pino.PinocytosisResult)


def test_pinocytosis_weekly_action():
    """Test pinocytosis with weekly action."""
    mock_ecdysis = MagicMock()
    mock_ecdysis.intake.return_value = "weekly intake"

    with patch.dict('sys.modules', {'metabolon.pinocytosis.ecdysis': mock_ecdysis}):
        result = pino.pinocytosis(action="weekly")

    assert isinstance(result, pino.PinocytosisResult)


def test_pinocytosis_polarization_action():
    """Test pinocytosis with polarization action."""
    mock_polarization = MagicMock()
    mock_polarization.intake.return_value = "polarization intake"

    with patch.dict('sys.modules', {'metabolon.pinocytosis.polarization': mock_polarization}):
        result = pino.pinocytosis(action="polarization")

    assert isinstance(result, pino.PinocytosisResult)


def test_pinocytosis_entrainment_status_action():
    """Test pinocytosis with entrainment_status action."""
    mock_entrainment = MagicMock()
    mock_entrainment.zeitgebers.return_value = {"light": 0.8}
    mock_entrainment.optimal_schedule.return_value = {
        "recommendations": {"sleep": "22:00"},
        "summary": "Good schedule",
    }

    with patch.dict('sys.modules', {'metabolon.organelles.entrainment': mock_entrainment}):
        result = pino.pinocytosis(action="entrainment_status")

    assert isinstance(result, pino.EntrainmentStatusResult)
    assert result.signals == {"light": 0.8}
    assert result.summary == "Good schedule"


def test_pinocytosis_unknown_action():
    """Test pinocytosis with unknown action returns error."""
    from metabolon.morphology import EffectorResult

    result = pino.pinocytosis(action="unknown_action")

    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "Unknown action" in result.message


def test_pinocytosis_action_case_insensitive():
    """Test pinocytosis action is case insensitive."""
    with patch('metabolon.enzymes.pinocytosis._day_snapshot') as mock_snapshot:
        mock_snapshot.return_value = pino.PinocytosisResult(output="day output")
        result = pino.pinocytosis(action="DAY")

    assert isinstance(result, pino.PinocytosisResult)


# ---------------------------------------------------------------------------
# Test result classes
# ---------------------------------------------------------------------------


def test_pinocytosis_result_creation():
    """Test PinocytosisResult can be created."""
    result = pino.PinocytosisResult(output="test output")
    assert result.output == "test output"


def test_entrainment_status_result_creation():
    """Test EntrainmentStatusResult can be created."""
    result = pino.EntrainmentStatusResult(
        signals={"test": 1},
        recommendations={"rec": "value"},
        summary="test summary",
    )
    assert result.signals == {"test": 1}
    assert result.summary == "test summary"
