from __future__ import annotations

"""Tests for metabolon/enzymes/pinocytosis.py — edge cases and supplementary coverage."""

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes import pinocytosis as pino


# ---------------------------------------------------------------------------
# _hkt_now
# ---------------------------------------------------------------------------


def test_hkt_now_offset_is_exactly_8_hours():
    result = pino._hkt_now()
    assert result.utcoffset() == timedelta(hours=8)


# ---------------------------------------------------------------------------
# _read_if_fresh
# ---------------------------------------------------------------------------


def test_read_if_fresh_strips_whitespace():
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True
    mock_path.stat.return_value.st_mtime = time.time() - 60
    mock_path.read_text.return_value = "  hello world  \n"
    assert pino._read_if_fresh(mock_path) == "hello world"


def test_read_if_fresh_custom_max_age():
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True
    # 2 hours old — should be fresh with max_age=3, stale with max_age=1
    mock_path.stat.return_value.st_mtime = time.time() - 7200
    mock_path.read_text.return_value = "ok"
    assert pino._read_if_fresh(mock_path, max_age_hours=3) == "ok"
    assert pino._read_if_fresh(mock_path, max_age_hours=1) is None


# ---------------------------------------------------------------------------
# _read_now_md
# ---------------------------------------------------------------------------


def test_read_now_md_skips_blank_lines():
    content = "- [ ] Task A\n\n   \n- [ ] Task B\n"
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.read_text", return_value=content):
            result = pino._read_now_md()
    assert "Task A" in result
    assert "Task B" in result
    # No double-spacing from blank lines
    assert "\n\n" not in result


def test_read_now_md_case_insensitive_done_markers():
    content = "- [DONE] upper\n- [done] lower\n- [Decided] mixed\n- [ ] open\n"
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.read_text", return_value=content):
            result = pino._read_now_md()
    assert "open" in result
    assert "upper" not in result
    assert "lower" not in result
    assert "mixed" not in result


def test_read_now_md_dash_x_marker_filtered():
    content = "- [x] completed\n- [ ] pending\n"
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.read_text", return_value=content):
            result = pino._read_now_md()
    assert "pending" in result
    assert "completed" not in result


# ---------------------------------------------------------------------------
# _count_job_alerts
# ---------------------------------------------------------------------------


def test_count_job_alerts_empty_file():
    """File exists but has no checkboxes."""
    now = datetime.now(pino.HKT)
    with patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=now):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value="No checkboxes here.\n"):
                with patch("pathlib.Path.glob", return_value=[]):
                    result = pino._count_job_alerts()
    assert "0/0 unchecked" in result


def test_count_job_alerts_includes_filename():
    now = datetime.now(pino.HKT)
    today_str = now.strftime("%Y-%m-%d")
    with patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=now):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value="- [ ] A\n"):
                with patch("pathlib.Path.glob", return_value=[]):
                    result = pino._count_job_alerts()
    assert today_str in result


def test_count_job_alerts_all_checked():
    now = datetime.now(pino.HKT)
    with patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=now):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value="- [x] A\n- [x] B\n"):
                with patch("pathlib.Path.glob", return_value=[]):
                    result = pino._count_job_alerts()
    assert "0/2 unchecked" in result


# ---------------------------------------------------------------------------
# _read_efferens
# ---------------------------------------------------------------------------


def test_read_efferens_body_truncation():
    mock_acta = MagicMock()
    long_body = "x" * 200
    mock_acta.read.return_value = [
        {"severity": "info", "from": "sys", "body": long_body},
    ]
    with patch.dict("sys.modules", {"acta": mock_acta}):
        result = pino._read_efferens()
    # Body should be truncated to 80 chars
    line = result.splitlines()[1]  # skip header
    assert len(line.split(": ", 1)[1]) <= 80


def test_read_efferens_newlines_in_body_replaced():
    mock_acta = MagicMock()
    mock_acta.read.return_value = [
        {"severity": "info", "from": "sys", "body": "line1\nline2\nline3"},
    ]
    with patch.dict("sys.modules", {"acta": mock_acta}):
        result = pino._read_efferens()
    # No literal newlines inside the body portion
    for line in result.splitlines()[1:]:
        assert "\n" not in line


def test_read_efferens_limits_to_5_messages():
    mock_acta = MagicMock()
    mock_acta.read.return_value = [
        {"severity": "info", "from": f"sender{i}", "body": f"msg{i}"}
        for i in range(10)
    ]
    with patch.dict("sys.modules", {"acta": mock_acta}):
        result = pino._read_efferens()
    # Header + 5 message lines
    assert result.count("[info]") == 5
    assert "10 message(s)" in result


def test_read_efferens_defaults_missing_fields():
    mock_acta = MagicMock()
    mock_acta.read.return_value = [{}]
    with patch.dict("sys.modules", {"acta": mock_acta}):
        result = pino._read_efferens()
    assert "[info]" in result  # default severity
    assert "?" in result       # default sender


# ---------------------------------------------------------------------------
# _count_goose_tasks
# ---------------------------------------------------------------------------


def test_count_goose_tasks_exception():
    with patch("pathlib.Path.exists", side_effect=PermissionError("denied")):
        result = pino._count_goose_tasks()
    assert "read error" in result.lower()


# ---------------------------------------------------------------------------
# _read_praxis_today
# ---------------------------------------------------------------------------


def test_read_praxis_today_uses_title_fallback():
    import metabolon.organelles

    mock_praxis = MagicMock()
    mock_praxis.today.return_value = {
        "overdue": [{"title": "Important task"}],
        "today": [],
    }
    with patch.dict("sys.modules", {"metabolon.organelles.praxis": mock_praxis}):
        with patch.object(metabolon.organelles, "praxis", mock_praxis):
            result = pino._read_praxis_today()
    assert "Important task" in result


def test_read_praxis_today_no_due_field():
    import metabolon.organelles

    mock_praxis = MagicMock()
    mock_praxis.today.return_value = {
        "overdue": [{"text": "Untitled task"}],
        "today": [],
    }
    with patch.dict("sys.modules", {"metabolon.organelles.praxis": mock_praxis}):
        with patch.object(metabolon.organelles, "praxis", mock_praxis):
            result = pino._read_praxis_today()
    assert "Untitled task" in result
    assert "(due " not in result


def test_read_praxis_today_limits_to_5():
    import metabolon.organelles

    mock_praxis = MagicMock()
    mock_praxis.today.return_value = {
        "overdue": [{"text": f"Task {i}"} for i in range(8)],
        "today": [],
    }
    with patch.dict("sys.modules", {"metabolon.organelles.praxis": mock_praxis}):
        with patch.object(metabolon.organelles, "praxis", mock_praxis):
            result = pino._read_praxis_today()
    assert result.count("[overdue]") == 5


# ---------------------------------------------------------------------------
# _day_snapshot
# ---------------------------------------------------------------------------


def test_day_snapshot_post_noon_includes_job_alerts():
    with patch("metabolon.enzymes.pinocytosis._hkt_now") as mock_now:
        mock_now.return_value = datetime(2024, 6, 1, 14, 0, tzinfo=pino.HKT)
        with patch("metabolon.enzymes.pinocytosis._read_now_md", return_value="N"):
            with patch("metabolon.enzymes.pinocytosis._read_praxis_today", return_value="P"):
                with patch("metabolon.enzymes.pinocytosis._read_efferens", return_value="E"):
                    with patch("metabolon.enzymes.pinocytosis._count_goose_tasks", return_value="G"):
                        with patch("metabolon.enzymes.pinocytosis._count_job_alerts", return_value="J") as mock_jobs:
                            result = pino._day_snapshot(json_output=True)
    mock_jobs.assert_called_once()
    data = json.loads(result.output)
    assert data["job_alerts"] == "J"


def test_day_snapshot_json_has_all_keys():
    with patch("metabolon.enzymes.pinocytosis._hkt_now") as mock_now:
        mock_now.return_value = datetime(2024, 6, 1, 14, 0, tzinfo=pino.HKT)
        with patch("metabolon.enzymes.pinocytosis._read_now_md", return_value="N"):
            with patch("metabolon.enzymes.pinocytosis._read_praxis_today", return_value="P"):
                with patch("metabolon.enzymes.pinocytosis._read_efferens", return_value="E"):
                    with patch("metabolon.enzymes.pinocytosis._count_goose_tasks", return_value="G"):
                        with patch("metabolon.enzymes.pinocytosis._count_job_alerts", return_value="J"):
                            result = pino._day_snapshot(json_output=True)
    data = json.loads(result.output)
    for key in ("time", "now_md", "praxis", "efferens", "goose_tasks", "job_alerts"):
        assert key in data


def test_day_snapshot_text_ordering():
    with patch("metabolon.enzymes.pinocytosis._hkt_now") as mock_now:
        mock_now.return_value = datetime(2024, 6, 1, 14, 0, tzinfo=pino.HKT)
        with patch("metabolon.enzymes.pinocytosis._read_now_md", return_value="NOW"):
            with patch("metabolon.enzymes.pinocytosis._read_praxis_today", return_value="PRAXIS"):
                with patch("metabolon.enzymes.pinocytosis._read_efferens", return_value="EFFERENS"):
                    with patch("metabolon.enzymes.pinocytosis._count_goose_tasks", return_value="GOOSE"):
                        with patch("metabolon.enzymes.pinocytosis._count_job_alerts", return_value="JOBS"):
                            result = pino._day_snapshot(json_output=False)
    # Ordering: now_md, praxis, efferens, job_alerts, goose_tasks
    pos = {k: result.output.index(k) for k in ("NOW", "PRAXIS", "EFFERENS", "JOBS", "GOOSE")}
    assert pos["NOW"] < pos["PRAXIS"] < pos["EFFERENS"] < pos["JOBS"] < pos["GOOSE"]


# ---------------------------------------------------------------------------
# _entrainment_brief — full Oura fields
# ---------------------------------------------------------------------------


def _make_entrainment_mocks(oura_data, kinesin_output="", health=None, flywheel=None):
    """Build mock modules for _entrainment_brief tests."""
    mock_chemo = MagicMock()
    mock_chemo.sense.return_value = oura_data

    mock_cyto = MagicMock()
    mock_cyto.invoke_organelle.return_value = kinesin_output
    mock_cyto.VIVESCA_ROOT = Path("/tmp/viv")

    return mock_chemo, mock_cyto, health, flywheel


def _run_entrainment(mock_chemo, mock_cyto, health, flywheel):
    with patch.dict("sys.modules", {
        "metabolon.organelles.chemoreceptor": mock_chemo,
        "metabolon.cytosol": mock_cyto,
    }):
        with patch("metabolon.enzymes.pinocytosis._read_if_fresh") as mock_fresh:
            def fresh_side_effect(path, **kw):
                s = str(path)
                if "nightly-health" in s:
                    return health
                if "skill-flywheel" in s:
                    return flywheel
                return None
            mock_fresh.side_effect = fresh_side_effect
            return pino._entrainment_brief()


def test_entrainment_brief_all_oura_fields():
    oura = {
        "sleep_score": 80,
        "readiness_score": 75,
        "spo2": {"average": 96},
        "resilience": {"level": "good"},
        "stress": {"day_summary": "low"},
        "total_sleep_duration": 27000,  # 7.5h
        "efficiency": 92,
        "average_heart_rate": 58,
        "average_hrv": 45,
        "lowest_heart_rate": 48,
        "activity": {"steps": 8500},
    }
    result = _run_entrainment(*_make_entrainment_mocks(oura))
    assert "Sleep: 80" in result.output
    assert "Readiness: 75" in result.output
    assert "SpO2: 96%" in result.output
    assert "Resilience: good" in result.output
    assert "Stress: low" in result.output
    assert "Total sleep: 7.5h" in result.output
    assert "Efficiency: 92%" in result.output
    assert "Avg HR: 58 bpm" in result.output
    assert "Avg HRV: 45 ms" in result.output
    assert "Lowest HR: 48 bpm" in result.output
    assert "Steps: 8500" in result.output


def test_entrainment_brief_sopor_error():
    oura = {"error": "api timeout"}
    result = _run_entrainment(*_make_entrainment_mocks(oura))
    assert "sopor error" in result.output.lower()


def test_entrainment_brief_no_oura_data():
    oura = {}
    result = _run_entrainment(*_make_entrainment_mocks(oura))
    assert "No Oura data" in result.output


def test_entrainment_brief_chemoreceptor_exception():
    mock_chemo = MagicMock()
    mock_chemo.sense.side_effect = Exception("conn refused")

    mock_cyto = MagicMock()
    mock_cyto.invoke_organelle.return_value = ""
    mock_cyto.VIVESCA_ROOT = Path("/tmp")

    with patch.dict("sys.modules", {
        "metabolon.organelles.chemoreceptor": mock_chemo,
        "metabolon.cytosol": mock_cyto,
    }):
        with patch("metabolon.enzymes.pinocytosis._read_if_fresh", return_value=None):
            result = pino._entrainment_brief()
    assert "sopor unavailable" in result.output.lower()


def test_entrainment_brief_health_warning_lines():
    oura = {}
    health = "system warning: disk at 90%\nall good\nred flag: cpu hot\n"
    result = _run_entrainment(*_make_entrainment_mocks(oura, health=health))
    assert "warning" in result.output.lower() or "red" in result.output.lower()


def test_entrainment_brief_health_all_green():
    oura = {}
    health = "everything is fine\nno issues\n"
    result = _run_entrainment(*_make_entrainment_mocks(oura, health=health))
    assert "all green" in result.output.lower()


def test_entrainment_brief_flywheel_miss_lines():
    oura = {}
    flywheel = "daily practice: 80%\nmiss: vocabulary drill\ncoverage: 100%\n"
    result = _run_entrainment(*_make_entrainment_mocks(oura, flywheel=flywheel))
    assert "miss" in result.output.lower()


def test_entrainment_brief_kinesin_needs_attention():
    oura = {}
    kinesin = "NEEDS_ATTENTION: disk full\nall good\nCRITICAL: memory low\n"
    result = _run_entrainment(*_make_entrainment_mocks(oura, kinesin_output=kinesin))
    assert "NEEDS_ATTENTION" in result.output
    assert "Alert" in result.output


def test_entrainment_brief_kinesin_normal_output():
    oura = {}
    kinesin = "backup completed successfully\nlog rotated\n"
    result = _run_entrainment(*_make_entrainment_mocks(oura, kinesin_output=kinesin))
    assert "backup completed" in result.output


def test_entrainment_brief_kinesin_empty():
    oura = {}
    result = _run_entrainment(*_make_entrainment_mocks(oura, kinesin_output="   "))
    assert "No overnight data" in result.output


def test_entrainment_brief_no_overnight_data():
    oura = {}
    result = _run_entrainment(*_make_entrainment_mocks(oura))
    assert "No overnight data" in result.output


def test_entrainment_brief_cytosol_exception():
    oura = {}
    mock_chemo, mock_cyto, health, flywheel = _make_entrainment_mocks(oura)
    mock_cyto.invoke_organelle.side_effect = Exception("broken")

    with patch.dict("sys.modules", {
        "metabolon.organelles.chemoreceptor": mock_chemo,
        "metabolon.cytosol": mock_cyto,
    }):
        with patch("metabolon.enzymes.pinocytosis._read_if_fresh", return_value=None):
            result = pino._entrainment_brief()
    # Should not crash, just skip kinesin section
    assert isinstance(result, pino.PinocytosisResult)


# ---------------------------------------------------------------------------
# _overnight_results — arg verification
# ---------------------------------------------------------------------------


def test_overnight_results_empty_task():
    mock_cytosol = MagicMock()
    mock_cytosol.invoke_organelle.return_value = "all results"
    mock_cytosol.VIVESCA_ROOT = Path("/tmp/viv")

    with patch.dict("sys.modules", {"metabolon.cytosol": mock_cytosol}):
        pino._overnight_results("")

    args = mock_cytosol.invoke_organelle.call_args[0][1]
    assert args == ["results"]


def test_overnight_results_with_task():
    mock_cytosol = MagicMock()
    mock_cytosol.invoke_organelle.return_value = "task results"
    mock_cytosol.VIVESCA_ROOT = Path("/tmp/viv")

    with patch.dict("sys.modules", {"metabolon.cytosol": mock_cytosol}):
        pino._overnight_results("deploy-check")

    args = mock_cytosol.invoke_organelle.call_args[0][1]
    assert args == ["results", "--task", "deploy-check"]


def test_overnight_list_args():
    mock_cytosol = MagicMock()
    mock_cytosol.invoke_organelle.return_value = "task-list"
    mock_cytosol.VIVESCA_ROOT = Path("/tmp/viv")

    with patch.dict("sys.modules", {"metabolon.cytosol": mock_cytosol}):
        pino._overnight_list()

    args = mock_cytosol.invoke_organelle.call_args[0][1]
    assert args == ["list"]


# ---------------------------------------------------------------------------
# pinocytosis main function — param forwarding
# ---------------------------------------------------------------------------


def test_pinocytosis_morning_forwards_params():
    mock_photo = MagicMock()
    mock_photo.intake.return_value = "weather data"

    with patch.dict("sys.modules", {"metabolon.pinocytosis.photoreception": mock_photo}):
        result = pino.pinocytosis(action="morning", json_output=False, send_weather=True)

    mock_photo.intake.assert_called_once_with(as_json=False, send_weather=True)
    assert isinstance(result, pino.PinocytosisResult)


def test_pinocytosis_evening_forwards_json():
    mock_interp = MagicMock()
    mock_interp.intake.return_value = "evening"

    with patch.dict("sys.modules", {"metabolon.pinocytosis.interphase": mock_interp}):
        pino.pinocytosis(action="evening", json_output=False)

    mock_interp.intake.assert_called_once_with(as_json=False)


def test_pinocytosis_weekly_forwards_json():
    mock_ecd = MagicMock()
    mock_ecd.intake.return_value = "weekly"

    with patch.dict("sys.modules", {"metabolon.pinocytosis.ecdysis": mock_ecd}):
        pino.pinocytosis(action="weekly", json_output=False)

    mock_ecd.intake.assert_called_once_with(as_json=False)


def test_pinocytosis_polarization_forwards_json():
    mock_pol = MagicMock()
    mock_pol.intake.return_value = "polar"

    with patch.dict("sys.modules", {"metabolon.pinocytosis.polarization": mock_pol}):
        pino.pinocytosis(action="polarization", json_output=False)

    mock_pol.intake.assert_called_once_with(as_json=False)


def test_pinocytosis_overnight_results_forwards_task():
    mock_cyto = MagicMock()
    mock_cyto.invoke_organelle.return_value = "res"
    mock_cyto.VIVESCA_ROOT = Path("/tmp")

    with patch.dict("sys.modules", {"metabolon.cytosol": mock_cyto}):
        result = pino.pinocytosis(action="overnight_results", task="build")

    assert isinstance(result, pino.PinocytosisResult)


def test_pinocytosis_action_strips_whitespace():
    with patch("metabolon.enzymes.pinocytosis._day_snapshot") as mock_snap:
        mock_snap.return_value = pino.PinocytosisResult(output="ok")
        result = pino.pinocytosis(action="  DAY  ")

    assert isinstance(result, pino.PinocytosisResult)


def test_pinocytosis_unknown_action_lists_valid():
    result = pino.pinocytosis(action="bogus")
    assert result.success is False
    for a in ("morning", "day", "evening", "weekly", "overnight",
              "overnight_results", "overnight_list", "polarization", "entrainment_status"):
        assert a in result.message


def test_pinocytosis_entrainment_status_returns_signals_and_recs():
    mock_ent = MagicMock()
    mock_ent.zeitgebers.return_value = {"light": 0.5, "caffeine": 0.3}
    mock_ent.optimal_schedule.return_value = {
        "recommendations": {"wind_down": "21:30"},
        "summary": "Moderate readiness",
    }

    with patch.dict("sys.modules", {"metabolon.organelles.entrainment": mock_ent}):
        result = pino.pinocytosis(action="entrainment_status")

    assert result.signals == {"light": 0.5, "caffeine": 0.3}
    assert result.recommendations == {"wind_down": "21:30"}
    assert result.summary == "Moderate readiness"


# ---------------------------------------------------------------------------
# Result class edge cases
# ---------------------------------------------------------------------------


def test_pinocytosis_result_inherits_secretion():
    from metabolon.morphology import Secretion
    result = pino.PinocytosisResult(output="x")
    assert isinstance(result, Secretion)


def test_entrainment_status_result_inherits_secretion():
    from metabolon.morphology import Secretion
    result = pino.EntrainmentStatusResult(signals={}, recommendations={}, summary="s")
    assert isinstance(result, Secretion)
