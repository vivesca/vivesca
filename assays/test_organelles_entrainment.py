from __future__ import annotations

"""Tests for metabolon/organelles/entrainment.py — zeitgebers, optimal_schedule, entrain."""

import datetime
import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

HKT = datetime.timezone(datetime.timedelta(hours=8))
UTC = datetime.UTC

# Module under test
_MOD = "metabolon.organelles.entrainment"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_now(h: int, m: int = 0, day: int = 30, month: int = 3, year: int = 2026):
    """Build a fixed HKT datetime and the matching mock_dt patch dict."""
    now = datetime.datetime(year, month, day, h, m, tzinfo=HKT)
    return now


def _patch_dt(now):
    """Return a dict suitable for patching the datetime module inside entrainment."""
    mock_dt = MagicMock()
    mock_dt.datetime.now.return_value = now
    mock_dt.timezone = datetime.timezone
    mock_dt.timedelta = datetime.timedelta
    # datetime.datetime is also used as a constructor (fromisoformat) inside zeitgebers
    mock_dt.datetime.fromisoformat = datetime.datetime.fromisoformat
    mock_dt.datetime.UTC = UTC
    return mock_dt


def _mock_module(name: str, **attrs):
    """Create a mock module and inject it (and parents) into sys.modules."""
    mod = MagicMock()
    for k, v in attrs.items():
        setattr(mod, k, v)
    parts = name.split(".")
    for i in range(len(parts)):
        partial = ".".join(parts[: i + 1])
        if partial not in sys.modules:
            sys.modules[partial] = MagicMock()
    sys.modules[name] = mod
    return mod


# ---------------------------------------------------------------------------
# TestZeitgebers
# ---------------------------------------------------------------------------

class TestZeitgebers:
    """Tests for zeitgebers() signal collection."""

    def test_basic_keys_present(self):
        from metabolon.organelles.entrainment import zeitgebers

        now = _fake_now(14)
        with patch(f"{_MOD}.datetime", _patch_dt(now)):
            result = zeitgebers()
        for key in (
            "hkt_hour", "weekday", "is_weekend", "is_night",
            "asleep", "readiness", "budget_status", "rss_stale",
            "pending_signals",
        ):
            assert key in result, f"missing key: {key}"

    def test_night_boundary_start_23(self):
        from metabolon.organelles.entrainment import zeitgebers

        now = _fake_now(23, 0)
        with patch(f"{_MOD}.datetime", _patch_dt(now)):
            assert zeitgebers()["is_night"] is True

    def test_night_boundary_end_5(self):
        from metabolon.organelles.entrainment import zeitgebers

        now = _fake_now(5, 59)
        with patch(f"{_MOD}.datetime", _patch_dt(now)):
            assert zeitgebers()["is_night"] is True

    def test_daytime_hour_6(self):
        from metabolon.organelles.entrainment import zeitgebers

        now = _fake_now(6, 0)
        with patch(f"{_MOD}.datetime", _patch_dt(now)):
            assert zeitgebers()["is_night"] is False

    def test_daytime_hour_22(self):
        from metabolon.organelles.entrainment import zeitgebers

        now = _fake_now(22, 59)
        with patch(f"{_MOD}.datetime", _patch_dt(now)):
            assert zeitgebers()["is_night"] is False

    def test_weekend_saturday(self):
        from metabolon.organelles.entrainment import zeitgebers

        # 2026-03-28 is a Saturday
        now = _fake_now(10, 0, day=28)
        with patch(f"{_MOD}.datetime", _patch_dt(now)):
            result = zeitgebers()
        assert result["is_weekend"] is True

    def test_weekday_monday(self):
        from metabolon.organelles.entrainment import zeitgebers

        # 2026-03-30 is a Monday
        now = _fake_now(10, 0, day=30)
        with patch(f"{_MOD}.datetime", _patch_dt(now)):
            result = zeitgebers()
        assert result["is_weekend"] is False

    def test_readiness_from_chemoreceptor(self):
        from metabolon.organelles.entrainment import zeitgebers

        fake_sense = MagicMock(return_value={"readiness_score": 72})
        now = _fake_now(10)
        with (
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch.dict(sys.modules, {
                "metabolon.organelles.chemoreceptor": MagicMock(sense=fake_sense),
            }),
        ):
            result = zeitgebers()
        assert result["readiness"] == 72

    def test_readiness_none_on_error(self):
        from metabolon.organelles.entrainment import zeitgebers

        fake_sense = MagicMock(side_effect=RuntimeError("no ring"))
        now = _fake_now(10)
        with (
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch.dict(sys.modules, {
                "metabolon.organelles.chemoreceptor": MagicMock(sense=fake_sense),
            }),
        ):
            result = zeitgebers()
        assert result["readiness"] is None

    def test_readiness_none_when_error_key(self):
        from metabolon.organelles.entrainment import zeitgebers

        fake_sense = MagicMock(return_value={"error": "timeout"})
        now = _fake_now(10)
        with (
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch.dict(sys.modules, {
                "metabolon.organelles.chemoreceptor": MagicMock(sense=fake_sense),
            }),
        ):
            result = zeitgebers()
        assert result["readiness"] is None

    def test_budget_from_vasomotor(self):
        from metabolon.organelles.entrainment import zeitgebers

        now = _fake_now(10)
        with (
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch.dict(sys.modules, {
                "metabolon.vasomotor": MagicMock(vasomotor_status=MagicMock(return_value="green")),
            }),
        ):
            result = zeitgebers()
        assert result["budget_status"] == "green"

    def test_budget_unknown_on_error(self):
        from metabolon.organelles.entrainment import zeitgebers

        now = _fake_now(10)
        with (
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch.dict(sys.modules, {
                "metabolon.vasomotor": MagicMock(vasomotor_status=MagicMock(side_effect=ImportError)),
            }),
        ):
            result = zeitgebers()
        assert result["budget_status"] == "unknown"

    def test_rss_stale_true(self):
        from metabolon.organelles.entrainment import zeitgebers

        # last fetch was 6 hours ago → stale
        six_hours_ago = (datetime.datetime.now(tz=UTC) - datetime.timedelta(hours=6)).isoformat()
        fake_state = {"feed1": six_hours_ago}
        fake_cfg = MagicMock(state_path="/fake/state.json")

        now = _fake_now(10)
        mock_dt = _patch_dt(now)
        # zeitgebers also calls datetime.datetime.now(tz=utc) internally
        # The mock_dt.datetime.now handles the first call; we need fromisoformat to work
        with (
            patch(f"{_MOD}.datetime", mock_dt),
            patch.dict(sys.modules, {
                "metabolon.organelles.endocytosis_rss.config": MagicMock(restore_config=MagicMock(return_value=fake_cfg)),
                "metabolon.organelles.endocytosis_rss.state": MagicMock(restore_state=MagicMock(return_value=fake_state)),
            }),
        ):
            result = zeitgebers()
        assert result["rss_stale"] is True

    def test_rss_stale_false(self):
        from metabolon.organelles.entrainment import zeitgebers

        # last fetch was 1 hour ago → not stale
        one_hour_ago = (datetime.datetime.now(tz=UTC) - datetime.timedelta(hours=1)).isoformat()
        fake_state = {"feed1": one_hour_ago}
        fake_cfg = MagicMock(state_path="/fake/state.json")

        now = _fake_now(10)
        mock_dt = _patch_dt(now)
        with (
            patch(f"{_MOD}.datetime", mock_dt),
            patch.dict(sys.modules, {
                "metabolon.organelles.endocytosis_rss.config": MagicMock(restore_config=MagicMock(return_value=fake_cfg)),
                "metabolon.organelles.endocytosis_rss.state": MagicMock(restore_state=MagicMock(return_value=fake_state)),
            }),
        ):
            result = zeitgebers()
        assert result["rss_stale"] is False

    def test_rss_stale_none_on_error(self):
        from metabolon.organelles.entrainment import zeitgebers

        now = _fake_now(10)
        with (
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch.dict(sys.modules, {
                "metabolon.organelles.endocytosis_rss.config": MagicMock(
                    restore_config=MagicMock(side_effect=FileNotFoundError),
                ),
            }),
        ):
            result = zeitgebers()
        assert result["rss_stale"] is None

    def test_pending_signals_from_demethylase(self):
        from metabolon.organelles.entrainment import zeitgebers

        signals = [{"type": "alert", "msg": "wake up"}]
        now = _fake_now(10)
        with (
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch.dict(sys.modules, {
                "metabolon.organelles.demethylase": MagicMock(read_signals=MagicMock(return_value=signals)),
            }),
        ):
            result = zeitgebers()
        assert result["pending_signals"] == signals

    def test_pending_signals_empty_on_error(self):
        from metabolon.organelles.entrainment import zeitgebers

        now = _fake_now(10)
        with (
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch.dict(sys.modules, {
                "metabolon.organelles.demethylase": MagicMock(
                    read_signals=MagicMock(side_effect=ImportError),
                ),
            }),
        ):
            result = zeitgebers()
        assert result["pending_signals"] == []


# ---------------------------------------------------------------------------
# TestOptimalSchedule
# ---------------------------------------------------------------------------

class TestOptimalSchedule:
    """Tests for optimal_schedule() advisory logic."""

    def test_budget_red_suppresses_pulse(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "red", "rss_stale": False,
               "hkt_hour": 12, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        rec = result["recommendations"]["pulse"]
        assert rec["action"] == "suppress"
        assert rec["reason"] == "budget_red"

    def test_night_suppresses_pulse(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": True, "budget_status": "green", "rss_stale": False,
               "hkt_hour": 1, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        rec = result["recommendations"]["pulse"]
        assert rec["action"] == "suppress"
        assert rec["reason"] == "night_hours"

    def test_green_daytime_accelerates_pulse(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "green", "rss_stale": False,
               "hkt_hour": 10, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        rec = result["recommendations"]["pulse"]
        assert rec["action"] == "accelerate"
        assert rec["reason"] == "green_daytime"

    def test_green_but_weekend_normal_pulse(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "green", "rss_stale": False,
               "hkt_hour": 10, "is_weekend": True}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        rec = result["recommendations"]["pulse"]
        assert rec["action"] == "normal"

    def test_green_but_holiday_normal_pulse(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "green", "rss_stale": False,
               "hkt_hour": 10, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=True)),
        }):
            result = optimal_schedule(sig)
        rec = result["recommendations"]["pulse"]
        assert rec["action"] == "normal"

    def test_yellow_budget_normal_pulse(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "yellow", "rss_stale": False,
               "hkt_hour": 12, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        rec = result["recommendations"]["pulse"]
        assert rec["action"] == "normal"

    def test_rss_stale_triggers_endocytosis(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "green", "rss_stale": True,
               "hkt_hour": 12, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        rec = result["recommendations"]["endocytosis"]
        assert rec["action"] == "trigger"
        assert rec["reason"] == "rss_stale_gt_4h"

    def test_night_suppresses_endocytosis(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": True, "budget_status": "green", "rss_stale": True,
               "hkt_hour": 1, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        rec = result["recommendations"]["endocytosis"]
        assert rec["action"] == "suppress"
        assert rec["reason"] == "night_hours"

    def test_transduction_suppressed_at_night(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": True, "budget_status": "green", "rss_stale": False,
               "hkt_hour": 1, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        rec = result["recommendations"]["transduction"]
        assert rec["action"] == "suppress"
        assert rec["reason"] == "night_hours"

    def test_transduction_normal_daytime(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "green", "rss_stale": False,
               "hkt_hour": 14, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        rec = result["recommendations"]["transduction"]
        assert rec["action"] == "normal"
        assert rec["reason"] == "nominal"

    def test_summary_string_present(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "green", "rss_stale": False,
               "hkt_hour": 10, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        assert "summary" in result
        assert isinstance(result["summary"], str)

    def test_no_signals_calls_zeitgebers(self):
        """optimal_schedule(None) should call zeitgebers() internally."""
        from metabolon.organelles.entrainment import optimal_schedule

        with patch(f"{_MOD}.zeitgebers", return_value={
            "is_night": False, "budget_status": "green", "rss_stale": False,
            "hkt_hour": 10, "is_weekend": False,
        }), patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(None)
        assert result["recommendations"]["pulse"]["action"] == "accelerate"

    def test_green_daytime_boundary_9am(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "green", "rss_stale": False,
               "hkt_hour": 9, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        assert result["recommendations"]["pulse"]["action"] == "accelerate"

    def test_green_daytime_boundary_18(self):
        """Hour 18 (6pm) is still within 9 <= hour < 19."""
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "green", "rss_stale": False,
               "hkt_hour": 18, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        assert result["recommendations"]["pulse"]["action"] == "accelerate"

    def test_green_daytime_boundary_19(self):
        """Hour 19 is NOT in 9 <= hour < 19."""
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "green", "rss_stale": False,
               "hkt_hour": 19, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        assert result["recommendations"]["pulse"]["action"] == "normal"

    def test_three_agents_always_present(self):
        from metabolon.organelles.entrainment import optimal_schedule

        sig = {"is_night": False, "budget_status": "green", "rss_stale": False,
               "hkt_hour": 14, "is_weekend": False}
        with patch.dict(sys.modules, {
            "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
        }):
            result = optimal_schedule(sig)
        assert set(result["recommendations"].keys()) == {"pulse", "endocytosis", "transduction"}


# ---------------------------------------------------------------------------
# TestEntrain
# ---------------------------------------------------------------------------

class TestEntrain:
    """Tests for entrain() — the action-dispatch function."""

    def _night_signals(self):
        return {
            "is_night": True, "budget_status": "green", "rss_stale": False,
            "hkt_hour": 1, "is_weekend": False, "pending_signals": [],
        }

    def _day_signals(self):
        return {
            "is_night": False, "budget_status": "green", "rss_stale": False,
            "hkt_hour": 10, "is_weekend": False, "pending_signals": [],
        }

    def test_dry_run_returns_structure(self):
        from metabolon.organelles.entrainment import entrain

        now = _fake_now(1)
        with (
            patch(f"{_MOD}.zeitgebers", return_value=self._night_signals()),
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch.dict(sys.modules, {
                "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
            }),
            patch("builtins.open", mock_open()),
        ):
            result = entrain(dry_run=True)
        assert "dry_run" in result
        assert result["dry_run"] is True
        assert "signals" in result
        assert "schedule" in result
        assert "actions_taken" in result
        assert "actions_deferred" in result

    def test_dry_run_defers_suppress(self):
        from metabolon.organelles.entrainment import entrain

        now = _fake_now(1)
        with (
            patch(f"{_MOD}.zeitgebers", return_value=self._night_signals()),
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch.dict(sys.modules, {
                "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
            }),
            patch("builtins.open", mock_open()),
        ):
            result = entrain(dry_run=True)
        # At night, pulse+transduction are suppressed, so deferred should mention suppress
        assert len(result["actions_deferred"]) > 0
        assert any("WOULD suppress" in d for d in result["actions_deferred"])

    def test_live_suppress_writes_skip_file(self, tmp_path):
        from metabolon.organelles.entrainment import entrain, _SKIP_FILE

        skip_file = tmp_path / ".entrainment-suppress"
        now = _fake_now(1)
        mock_skip = MagicMock()
        mock_vasomotor_skip = MagicMock()

        with (
            patch(f"{_MOD}.zeitgebers", return_value=self._night_signals()),
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch(f"{_MOD}._SKIP_FILE", skip_file),
            patch.dict(sys.modules, {
                "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
                "metabolon.vasomotor": MagicMock(SKIP_UNTIL_FILE=mock_vasomotor_skip),
            }),
            patch("builtins.open", mock_open()),
        ):
            result = entrain(dry_run=False)
        assert skip_file.exists()
        payload = json.loads(skip_file.read_text())
        assert "pulse" in payload["suppress"]
        assert result["dry_run"] is False

    def test_live_night_sets_vasomotor_skip_until(self, tmp_path):
        from metabolon.organelles.entrainment import entrain

        skip_file = tmp_path / ".entrainment-suppress"
        vaso_skip = tmp_path / "skip-until"
        now = _fake_now(1)

        with (
            patch(f"{_MOD}.zeitgebers", return_value=self._night_signals()),
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch(f"{_MOD}._SKIP_FILE", skip_file),
            patch.dict(sys.modules, {
                "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
                "metabolon.vasomotor": MagicMock(SKIP_UNTIL_FILE=vaso_skip),
            }),
            patch("builtins.open", mock_open()),
        ):
            result = entrain(dry_run=False)
        assert vaso_skip.exists()
        wake = datetime.datetime.fromisoformat(vaso_skip.read_text())
        # Night suppression → wake at 06:00 next day
        assert wake.hour == 6
        assert wake.minute == 0

    def test_live_budget_red_skip_until_1_hour(self, tmp_path):
        from metabolon.organelles.entrainment import entrain

        skip_file = tmp_path / ".entrainment-suppress"
        vaso_skip = tmp_path / "skip-until"
        signals = {
            "is_night": False, "budget_status": "red", "rss_stale": False,
            "hkt_hour": 14, "is_weekend": False, "pending_signals": [],
        }
        now = _fake_now(14)

        with (
            patch(f"{_MOD}.zeitgebers", return_value=signals),
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch(f"{_MOD}._SKIP_FILE", skip_file),
            patch.dict(sys.modules, {
                "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
                "metabolon.vasomotor": MagicMock(SKIP_UNTIL_FILE=vaso_skip),
            }),
            patch("builtins.open", mock_open()),
        ):
            result = entrain(dry_run=False)
        assert vaso_skip.exists()
        wake = datetime.datetime.fromisoformat(vaso_skip.read_text())
        # Budget red → 1 hour from now
        assert wake.hour == 15

    def test_trigger_endocytosis_when_rss_stale(self, tmp_path):
        from metabolon.organelles.entrainment import entrain

        skip_file = tmp_path / ".entrainment-suppress"
        signals = {
            "is_night": False, "budget_status": "green", "rss_stale": True,
            "hkt_hour": 12, "is_weekend": False, "pending_signals": [],
        }
        now = _fake_now(12)

        with (
            patch(f"{_MOD}.zeitgebers", return_value=signals),
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch(f"{_MOD}._SKIP_FILE", skip_file),
            patch.dict(sys.modules, {
                "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
            }),
            patch("builtins.open", mock_open()),
        ):
            result = entrain(dry_run=True)
        # endocytosis trigger should appear in deferred for dry_run
        assert any("trigger" in d and "endocytosis" in d for d in result["actions_deferred"])

    def test_logging_writes_jsonl(self, tmp_path):
        from metabolon.organelles.entrainment import entrain

        log_file = tmp_path / "events.jsonl"
        now = _fake_now(10)

        with (
            patch(f"{_MOD}.zeitgebers", return_value=self._day_signals()),
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch(f"{_MOD}._LOG", log_file),
            patch.dict(sys.modules, {
                "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
            }),
        ):
            result = entrain(dry_run=True)

        assert log_file.exists()
        line = log_file.read_text().strip()
        entry = json.loads(line)
        assert entry["event"] == "entrainment"
        assert entry["dry_run"] is True

    def test_all_nominal_daytime(self, tmp_path):
        from metabolon.organelles.entrainment import entrain

        log_file = tmp_path / "events.jsonl"
        now = _fake_now(10)

        with (
            patch(f"{_MOD}.zeitgebers", return_value=self._day_signals()),
            patch(f"{_MOD}.datetime", _patch_dt(now)),
            patch(f"{_MOD}._LOG", log_file),
            patch.dict(sys.modules, {
                "metabolon.organelles.circadian_clock": MagicMock(is_holiday=MagicMock(return_value=False)),
            }),
        ):
            result = entrain(dry_run=True)
        sched = result["schedule"]
        # daytime green weekday → pulse accelerate, endocytosis normal, transduction normal
        assert sched["recommendations"]["pulse"]["action"] == "accelerate"
        assert sched["recommendations"]["endocytosis"]["action"] == "normal"
        assert sched["recommendations"]["transduction"]["action"] == "normal"
        # No suppress → no skip file actions
        assert not any("suppress" in a for a in result["actions_deferred"])
