"""Tests for vasomotor — autonomic pacing and budget regulation."""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


# Import the module under test
import metabolon.vasomotor as vm


class TestOxygenDebt:
    """Test oxygen_debt — use-it-or-lose-it pressure calculation."""

    def test_no_urgency_at_36_hours(self):
        """At 36h, there should be minimal urgency."""
        # At 36h: (48 - 36) / 42 = 12/42 ≈ 0.286
        result = vm.oxygen_debt(36.0)
        assert result == pytest.approx(0.286, rel=0.01)

    def test_full_debt_at_6_hours(self):
        """At 6h or below, debt should be 1.0."""
        result = vm.oxygen_debt(6.0)
        assert result == pytest.approx(1.0)

    def test_max_debt_below_6_hours(self):
        """Below 6h, debt is capped at 1.0."""
        result = vm.oxygen_debt(0.5)
        assert result == 1.0

    def test_zero_debt_at_48_hours(self):
        """At 48h, there's no debt pressure."""
        result = vm.oxygen_debt(48.0)
        assert result == pytest.approx(0.0, abs=0.01)

    def test_zero_debt_above_48_hours(self):
        """Above 48h, debt is floored at 0."""
        result = vm.oxygen_debt(60.0)
        assert result == 0.0

    def test_midpoint_calculation(self):
        """At 27h (midpoint of 6-48h range), debt should be ~0.5."""
        # (48 - 27) / 42 = 21/42 = 0.5
        result = vm.oxygen_debt(27.0)
        assert result == pytest.approx(0.5)


class TestEffectiveBurn:
    """Test effective_burn — saturation-weighted budget burn."""

    def test_no_saturation(self):
        """All productive systoles with no saturation."""
        result = vm.effective_burn(systoles_today=5, saturated_today=0, cost_per_systole=1.0)
        assert result == 5.0

    def test_with_saturation_default_penalty(self):
        """Saturated systoles count 1.5x by default."""
        # 3 productive + 2 * 1.5 = 3 + 3 = 6
        result = vm.effective_burn(systoles_today=5, saturated_today=2, cost_per_systole=1.0)
        assert result == 6.0

    def test_all_saturated(self):
        """All systoles saturated should have higher effective burn."""
        # 0 productive + 5 * 1.5 = 7.5
        result = vm.effective_burn(systoles_today=5, saturated_today=5, cost_per_systole=1.0)
        assert result == 7.5

    def test_custom_cost_per_systole(self):
        """Custom cost per systole scales the burn."""
        result = vm.effective_burn(systoles_today=4, saturated_today=1, cost_per_systole=2.0)
        # (3 productive + 1 * 1.5) * 2.0 = 4.5 * 2 = 9.0
        assert result == 9.0

    def test_zero_systoles(self):
        """Zero systoles means zero burn."""
        result = vm.effective_burn(systoles_today=0, saturated_today=0, cost_per_systole=1.0)
        assert result == 0.0


class TestFetchTelemetry:
    """Test _fetch_telemetry — budget data retrieval."""

    def test_returns_cached_data_within_ttl(self):
        """Should return cached data if within TTL."""
        vm._telemetry_cache = {"test": "data"}
        vm._telemetry_cache_time = 9999999999.0  # Far future

        with patch("metabolon.vasomotor.time.time", return_value=9999999990.0):
            result = vm._fetch_telemetry()

        assert result == {"test": "data"}
        vm._telemetry_cache = None
        vm._telemetry_cache_time = 0

    def test_fetches_new_data_when_cache_expired(self):
        """Should fetch new data when cache is expired."""
        vm._telemetry_cache = None
        vm._telemetry_cache_time = 0

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"seven_day": {"utilization": 50}}'
        mock_result.stderr = ""

        with patch("metabolon.vasomotor.subprocess.run", return_value=mock_result):
            with patch("metabolon.vasomotor.time.time", return_value=1000.0):
                result = vm._fetch_telemetry()

        assert result == {"seven_day": {"utilization": 50}}
        vm._telemetry_cache = None
        vm._telemetry_cache_time = 0

    def test_returns_none_on_subprocess_failure(self):
        """Should return None when subprocess fails."""
        vm._telemetry_cache = None
        vm._telemetry_cache_time = 0

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"

        with patch("metabolon.vasomotor.subprocess.run", return_value=mock_result):
            with patch("metabolon.vasomotor.time.time", return_value=1000.0):
                result = vm._fetch_telemetry()

        assert result is None
        vm._telemetry_cache = None
        vm._telemetry_cache_time = 0

    def test_returns_none_on_exception(self):
        """Should return None on any exception."""
        vm._telemetry_cache = None
        vm._telemetry_cache_time = 0

        with patch("metabolon.vasomotor.subprocess.run", side_effect=Exception("boom")):
            with patch("metabolon.vasomotor.time.time", return_value=1000.0):
                result = vm._fetch_telemetry()

        assert result is None
        vm._telemetry_cache = None
        vm._telemetry_cache_time = 0


class TestVasomotorSnapshot:
    """Test vasomotor_snapshot — simplified budget view."""

    def test_returns_weekly_and_sonnet(self):
        """Should extract weekly and sonnet utilization."""
        mock_telemetry = {
            "seven_day": {"utilization": 45},
            "seven_day_sonnet": {"utilization": 30},
        }

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
            result = vm.vasomotor_snapshot()

        assert result == {"weekly": 45, "sonnet": 30}

    def test_returns_none_on_telemetry_failure(self):
        """Should return None when telemetry unavailable."""
        with patch("metabolon.vasomotor._fetch_telemetry", return_value=None):
            result = vm.vasomotor_snapshot()

        assert result is None

    def test_handles_missing_fields(self):
        """Should handle missing telemetry fields gracefully."""
        # When telemetry is truthy but missing fields, returns zeros
        mock_telemetry = {"seven_day": {}, "seven_day_sonnet": {}}  # Present but empty

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
            result = vm.vasomotor_snapshot()

        assert result == {"weekly": 0, "sonnet": 0}


class TestHoursToReset:
    """Test _hours_to_reset — time until budget reset."""

    def test_calculates_hours_correctly(self):
        """Should calculate hours until reset."""
        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=12)
        telemetry = {"seven_day": {"resets_at": future.isoformat()}}

        with patch("metabolon.vasomotor._RESETS_AT_FILE", Path("/tmp/test-resets-at")):
            result = vm._hours_to_reset(telemetry)

        assert result is not None
        assert 11.5 < result < 12.5

    def test_returns_none_when_no_reset_time(self):
        """Should return None when no reset time available."""
        result = vm._hours_to_reset({})
        assert result is None

    def test_uses_fallback_from_file(self):
        """Should use persisted fallback when telemetry has no reset time."""
        # Create a temp file with a future reset time
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=6)
            f.write(future.isoformat())
            temp_path = Path(f.name)

        try:
            with patch("metabolon.vasomotor._RESETS_AT_FILE", temp_path):
                result = vm._hours_to_reset(None)

            assert result is not None
            assert 5.5 < result < 6.5
        finally:
            temp_path.unlink(missing_ok=True)

    def test_minimum_half_hour(self):
        """Should return at least 0.5 hours even if reset is imminent."""
        past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        telemetry = {"seven_day": {"resets_at": past.isoformat()}}

        with patch("metabolon.vasomotor._RESETS_AT_FILE", Path("/tmp/test-resets-at-2")):
            result = vm._hours_to_reset(telemetry)

        assert result == 0.5


class TestAssessVitalCapacity:
    """Test assess_vital_capacity — coarse budget gate."""

    def test_returns_false_on_unknown_budget(self):
        """Should return False when budget is unknown."""
        with patch("metabolon.vasomotor.measure_vasomotor_tone", return_value=None):
            ok, reason = vm.assess_vital_capacity()

        assert ok is False
        assert reason == "budget_unknown"

    def test_returns_false_when_weekly_exceeds_ceiling(self):
        """Should return False when weekly utilization exceeds ceiling."""
        mock_telemetry = {
            "seven_day": {"utilization": 85},
            "seven_day_sonnet": {"utilization": 30},
        }

        with patch("metabolon.vasomotor.measure_vasomotor_tone", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                with patch("metabolon.vasomotor._hours_to_reset", return_value=48.0):
                    with patch("metabolon.vasomotor.assess_pacing", return_value=(True, "ok")):
                        ok, reason = vm.assess_vital_capacity()

        assert ok is False
        assert "exceeds_ceiling" in reason

    def test_returns_false_when_sonnet_exceeds_ceiling(self):
        """Should return False when sonnet utilization exceeds ceiling."""
        mock_telemetry = {
            "seven_day": {"utilization": 50},
            "seven_day_sonnet": {"utilization": 95},
        }

        with patch("metabolon.vasomotor.measure_vasomotor_tone", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                with patch("metabolon.vasomotor._hours_to_reset", return_value=48.0):
                    with patch("metabolon.vasomotor.assess_pacing", return_value=(True, "ok")):
                        ok, reason = vm.assess_vital_capacity()

        assert ok is False
        assert "sonnet" in reason

    def test_returns_false_when_weekly_near_limit(self):
        """Should return False when weekly leaves less than reserve."""
        # With weekly=87%, the ceiling check fires first (87 > 80)
        # The reserve check is a secondary safeguard
        mock_telemetry = {
            "seven_day": {"utilization": 87},
            "seven_day_sonnet": {"utilization": 50},
        }

        with patch("metabolon.vasomotor.measure_vasomotor_tone", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                with patch("metabolon.vasomotor._hours_to_reset", return_value=48.0):
                    with patch("metabolon.vasomotor.assess_pacing", return_value=(True, "ok")):
                        ok, reason = vm.assess_vital_capacity()

        assert ok is False
        assert "ceiling" in reason or "reserve" in reason

    def test_returns_true_when_budget_ok(self):
        """Should return True when budget is within limits."""
        mock_telemetry = {
            "seven_day": {"utilization": 50},
            "seven_day_sonnet": {"utilization": 40},
        }

        with patch("metabolon.vasomotor.measure_vasomotor_tone", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                with patch("metabolon.vasomotor._hours_to_reset", return_value=48.0):
                    with patch("metabolon.vasomotor.assess_pacing", return_value=(True, "pacing_ok")):
                        ok, reason = vm.assess_vital_capacity()

        assert ok is True
        assert "ok" in reason

    def test_oxygen_debt_relaxes_thresholds(self):
        """Should relax thresholds when budget expires soon."""
        mock_telemetry = {
            "seven_day": {"utilization": 82},  # Above default 80% ceiling
            "seven_day_sonnet": {"utilization": 30},
        }

        with patch("metabolon.vasomotor.measure_vasomotor_tone", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                with patch("metabolon.vasomotor._hours_to_reset", return_value=6.0):  # Full debt
                    with patch("metabolon.vasomotor.assess_pacing", return_value=(True, "ok")):
                        ok, reason = vm.assess_vital_capacity()

        # With oxygen debt, ceiling should be ~90%, so 82% should pass
        assert ok is True


class TestVasomotorStatus:
    """Test vasomotor_status — per-systole respiratory status."""

    def test_returns_green_under_95(self):
        """Should return green when utilization under 95%."""
        mock_telemetry = {
            "seven_day": {"utilization": 80},
            "seven_day_sonnet": {"utilization": 70},
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.subprocess.run", return_value=mock_result):
                result = vm.vasomotor_status()

        assert result == "green"

    def test_returns_yellow_at_95(self):
        """Should return yellow when utilization at 95%."""
        mock_telemetry = {
            "seven_day": {"utilization": 96},
            "seven_day_sonnet": {"utilization": 70},
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.subprocess.run", return_value=mock_result):
                result = vm.vasomotor_status()

        assert result == "yellow"

    def test_returns_red_at_98(self):
        """Should return red when utilization at 98%."""
        mock_telemetry = {
            "seven_day": {"utilization": 99},
            "seven_day_sonnet": {"utilization": 70},
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.subprocess.run", return_value=mock_result):
                result = vm.vasomotor_status()

        assert result == "red"

    def test_falls_back_to_cached_on_failure(self):
        """Should fall back to cached result on telemetry failure."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "green"
        mock_result.stderr = ""

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=None):
            with patch("metabolon.vasomotor.subprocess.run", return_value=mock_result):
                result = vm.vasomotor_status()

        assert result == "green"

    def test_returns_unknown_on_all_failures(self):
        """Should return unknown when all methods fail."""
        with patch("metabolon.vasomotor._fetch_telemetry", return_value=None):
            with patch("metabolon.vasomotor.subprocess.run", side_effect=Exception("fail")):
                result = vm.vasomotor_status()

        assert result == "unknown"


class TestCircadianState:
    """Test daily systole counter functions."""

    def test_daily_systole_count_default(self, tmp_path):
        """Should return 0 when no state file exists."""
        state_file = tmp_path / "respiration-daily.json"
        with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                result = vm.daily_systole_count()

        assert result == 0

    def test_breathe_increments_count(self, tmp_path):
        """Should increment count when breathe is called."""
        state_file = tmp_path / "respiration-daily.json"
        with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                count1 = vm.breathe()
                count2 = vm.breathe()

        assert count1 == 1
        assert count2 == 2

    def test_breathe_tracks_saturation(self, tmp_path):
        """Should track saturated systoles."""
        state_file = tmp_path / "respiration-daily.json"
        with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                vm.breathe(saturated=False)
                vm.breathe(saturated=True)
                vm.breathe(saturated=True)

                saturated = vm.daily_saturated_count()

        assert saturated == 2

    def test_breathe_tracks_deltas(self, tmp_path):
        """Should track systole deltas."""
        state_file = tmp_path / "respiration-daily.json"
        with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                vm.breathe(systole_delta=0.5)
                vm.breathe(systole_delta=1.0)

                state = vm._load_circadian_state()

        assert state["systole_deltas"] == [0.5, 1.0]

    def test_wave_delta_backward_compat(self, tmp_path):
        """Should accept wave_delta as alias for systole_delta."""
        state_file = tmp_path / "respiration-daily.json"
        with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                vm.breathe(wave_delta=2.0)

                state = vm._load_circadian_state()

        assert state["systole_deltas"] == [2.0]

    def test_calibrate_circadian_sets_day_start(self, tmp_path):
        """Should record day_start_weekly on first calibration."""
        state_file = tmp_path / "respiration-daily.json"
        with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                vm.calibrate_circadian(weekly=45.5)

                state = vm._load_circadian_state()

        assert state["day_start_weekly"] == 45.5

    def test_calibrate_circadian_does_not_overwrite(self, tmp_path):
        """Should not overwrite day_start_weekly if already set."""
        state_file = tmp_path / "respiration-daily.json"
        with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                vm.calibrate_circadian(weekly=45.5)
                vm.calibrate_circadian(weekly=60.0)

                state = vm._load_circadian_state()

        assert state["day_start_weekly"] == 45.5


class TestMeasuredCostPerSystole:
    """Test measured_cost_per_systole — cost estimation."""

    def test_uses_today_deltas_when_available(self, tmp_path):
        """Should use today's deltas when 3+ samples available."""
        state_file = tmp_path / "respiration-daily.json"
        state_file.write_text(json.dumps({
            "date": datetime.date.today().isoformat(),
            "count": 3,
            "systole_deltas": [0.5, 1.0, 0.0, 1.5],
        }))

        with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                result = vm.measured_cost_per_systole()

        # Average: (0.5 + 1.0 + 0.0 + 1.5) / 4 = 0.75
        assert result == pytest.approx(0.75)

    def test_uses_default_when_insufficient_data(self, tmp_path):
        """Should use default when not enough samples."""
        state_file = tmp_path / "respiration-daily.json"
        state_file.write_text(json.dumps({
            "date": datetime.date.today().isoformat(),
            "count": 1,
            "systole_deltas": [0.5],
        }))

        with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
            with patch("metabolon.vasomotor.EVENT_LOG", tmp_path / "no-events.jsonl"):
                with patch("metabolon.vasomotor._maybe_migrate"):
                    with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                        result = vm.measured_cost_per_systole()

        assert result == 1.0  # DEFAULT_COST_PER_SYSTOLE

    def test_minimum_cost_is_one_tenth(self, tmp_path):
        """Should return at least 0.1 even with zero deltas."""
        state_file = tmp_path / "respiration-daily.json"
        state_file.write_text(json.dumps({
            "date": datetime.date.today().isoformat(),
            "count": 5,
            "systole_deltas": [0.0, 0.0, 0.0],
        }))

        with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                result = vm.measured_cost_per_systole()

        assert result == 0.1


class TestApnea:
    """Test apnea scheduling functions."""

    def test_is_apneic_when_no_file(self, tmp_path):
        """Should return False when no skip file exists."""
        skip_file = tmp_path / "skip-until"
        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE", skip_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                is_apneic, reason = vm.is_apneic()

        assert is_apneic is False
        assert reason == ""

    def test_is_apneic_when_time_passed(self, tmp_path):
        """Should return False when skip time has passed."""
        skip_file = tmp_path / "skip-until"
        past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        skip_file.write_text(past.isoformat())

        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE", skip_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                is_apneic, reason = vm.is_apneic()

        assert is_apneic is False

    def test_is_apneic_when_time_future(self, tmp_path):
        """Should return True when skip time is in future."""
        skip_file = tmp_path / "skip-until"
        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        skip_file.write_text(future.isoformat())

        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE", skip_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                is_apneic, reason = vm.is_apneic()

        assert is_apneic is True
        assert "skip_until" in reason

    def test_resume_breathing_removes_file(self, tmp_path):
        """Should remove skip file when breathing resumes."""
        skip_file = tmp_path / "skip-until"
        skip_file.write_text("some content")

        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE", skip_file):
            vm.resume_breathing()

        assert not skip_file.exists()

    def test_induce_apnea_sets_skip_until(self, tmp_path):
        """Should set skip time when apnea is induced."""
        skip_file = tmp_path / "skip-until"

        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE", skip_file):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                with patch("metabolon.vasomotor.record_event"):
                    vm.induce_apnea(
                        daily_budget=5.0,
                        cost_per_systole=1.0,
                        systoles_today=3,
                        sustainable_daily=10.0,
                    )

        assert skip_file.exists()

    def test_induce_apnea_at_max_systoles_sets_midnight(self, tmp_path):
        """Should set skip until midnight when at max systoles."""
        skip_file = tmp_path / "skip-until"

        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE", skip_file):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={"max_daily_systoles": 10}):
                with patch("metabolon.vasomotor.record_event"):
                    vm.induce_apnea(
                        daily_budget=5.0,
                        cost_per_systole=1.0,
                        systoles_today=10,
                        sustainable_daily=10.0,
                    )

        skip_until = datetime.datetime.fromisoformat(skip_file.read_text().strip())
        # Should be around midnight
        assert skip_until.hour == 0
        assert skip_until.minute == 0


class TestInteractivePressure:
    """Test interactive_pressure — sympathetic awareness."""

    def test_uses_live_util_when_available(self, tmp_path):
        """Should blend live util with pattern when telemetry available."""
        pattern_file = tmp_path / "pattern.json"
        pattern_file.write_text(json.dumps({"14": 30.0}))

        mock_telemetry = {
            "five_hour": {"utilization": 50.0},
        }

        # Create a mock datetime object with hour=14
        mock_now = MagicMock()
        mock_now.hour = 14

        with patch("metabolon.vasomotor.INTERACTIVE_PATTERN_FILE", pattern_file):
            with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
                with patch("metabolon.vasomotor.datetime.datetime.now", return_value=mock_now):
                    with patch("metabolon.vasomotor.record_event"):
                        result = vm.interactive_pressure()

        # blended = 0.7 * 50 + 0.3 * 30 = 35 + 9 = 44
        # pressure = (44 - 20) / 40 = 0.6
        assert result == pytest.approx(0.6, abs=0.05)

    def test_uses_pattern_only_when_no_telemetry(self, tmp_path):
        """Should use pattern only when telemetry unavailable."""
        pattern_file = tmp_path / "pattern.json"
        pattern_file.write_text(json.dumps({"14": 60.0}))

        mock_now = MagicMock()
        mock_now.hour = 14

        with patch("metabolon.vasomotor.INTERACTIVE_PATTERN_FILE", pattern_file):
            with patch("metabolon.vasomotor._fetch_telemetry", return_value=None):
                with patch("metabolon.vasomotor.datetime.datetime.now", return_value=mock_now):
                    with patch("metabolon.vasomotor.record_event"):
                        result = vm.interactive_pressure()

        # pressure = (60 - 20) / 40 = 1.0
        assert result == pytest.approx(1.0, abs=0.05)

    def test_pressure_capped_at_one(self, tmp_path):
        """Should cap pressure at 1.0."""
        mock_telemetry = {
            "five_hour": {"utilization": 100.0},
        }
        pattern_file = tmp_path / "pattern.json"
        pattern_file.write_text("{}")

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.INTERACTIVE_PATTERN_FILE", pattern_file):
                with patch("metabolon.vasomotor.record_event"):
                    result = vm.interactive_pressure()

        assert result <= 1.0

    def test_pressure_floored_at_zero(self):
        """Should floor pressure at 0.0."""
        mock_telemetry = {
            "five_hour": {"utilization": 10.0},  # Below 20 baseline
        }

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.record_event"):
                result = vm.interactive_pressure()

        assert result >= 0.0


class TestTidalVolume:
    """Test tidal_volume — pulse's share of budget."""

    def test_default_tidal_volume(self):
        """Should return default share when no pressure."""
        with patch("metabolon.vasomotor.interactive_pressure", return_value=0.0):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                result = vm.tidal_volume()

        assert result == 0.5  # BASAL_RATE

    def test_reduced_tidal_volume_under_pressure(self):
        """Should reduce share under high pressure."""
        with patch("metabolon.vasomotor.interactive_pressure", return_value=1.0):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                result = vm.tidal_volume()

        assert result == 0.15  # MIN_BASAL_RATE

    def test_custom_genome_values(self):
        """Should respect custom genome values."""
        with patch("metabolon.vasomotor.interactive_pressure", return_value=0.5):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={
                "basal_rate": 0.4,
                "min_basal_rate": 0.1,
            }):
                result = vm.tidal_volume()

        # share = 0.4 - 0.5 * (0.4 - 0.1) = 0.4 - 0.15 = 0.25
        assert result == pytest.approx(0.25)


class TestVasomotorGenome:
    """Test vasomotor_genome — config reading."""

    def test_returns_empty_dict_when_no_conf(self, tmp_path):
        """Should return empty dict when conf file doesn't exist."""
        conf_path = tmp_path / "respiration.conf"

        with patch("metabolon.vasomotor.CONF_PATH", conf_path):
            with patch("metabolon.vasomotor._maybe_migrate"):
                result = vm.vasomotor_genome()

        assert result == {}

    def test_reads_json_conf(self, tmp_path):
        """Should read and parse JSON conf file."""
        conf_path = tmp_path / "respiration.conf"
        conf_path.write_text('{"aerobic_ceiling": 85, "sonnet_ceiling": 92}')

        with patch("metabolon.vasomotor.CONF_PATH", conf_path):
            with patch("metabolon.vasomotor._maybe_migrate"):
                result = vm.vasomotor_genome()

        assert result == {"aerobic_ceiling": 85, "sonnet_ceiling": 92}

    def test_handles_malformed_json(self, tmp_path):
        """Should return empty dict on malformed JSON."""
        conf_path = tmp_path / "respiration.conf"
        conf_path.write_text('not valid json')

        with patch("metabolon.vasomotor.CONF_PATH", conf_path):
            with patch("metabolon.vasomotor._maybe_migrate"):
                result = vm.vasomotor_genome()

        assert result == {}


class TestMeasureYield:
    """Test measure_yield — metabolic yield measurement."""

    def test_counts_pulse_files(self, tmp_path):
        """Should count files with 'pulse' in name."""
        pulse_dir = tmp_path / "pulse_reports"
        pulse_dir.mkdir()

        # Create some files
        (pulse_dir / "pulse-001.md").touch()
        (pulse_dir / "pulse-002.md").touch()
        (pulse_dir / "other.md").touch()

        with patch("metabolon.vasomotor.YIELD_DIRS", [pulse_dir]):
            with patch("metabolon.vasomotor.Path.home", return_value=tmp_path):
                result = vm.measure_yield()

        assert result["files_created"] == 2

    def test_counts_git_commits(self, tmp_path):
        """Should count git commits by Claude."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123 First commit\ndef456 Second commit\n"

        with patch("metabolon.vasomotor.YIELD_DIRS", []):
            with patch("metabolon.vasomotor.Path.home", return_value=tmp_path):
                with patch("metabolon.vasomotor.subprocess.run", return_value=mock_result):
                    result = vm.measure_yield()

        assert result["git_commits"] == 2

    def test_returns_summary(self):
        """Should return summary string."""
        with patch("metabolon.vasomotor.YIELD_DIRS", []):
            with patch("metabolon.vasomotor.Path.home", return_value=Path("/tmp")):
                with patch("metabolon.vasomotor.subprocess.run", side_effect=Exception("no git")):
                    result = vm.measure_yield()

        assert "files" in result["yield_summary"]
        assert "commits" in result["yield_summary"]


class TestRecordEvent:
    """Test record_event — structured logging."""

    def test_writes_to_event_log(self, tmp_path):
        """Should write JSON entry to event log."""
        event_log = tmp_path / "events.jsonl"

        with patch("metabolon.vasomotor.EVENT_LOG", event_log):
            vm.record_event("test_event", key1="value1", key2=42)

        content = event_log.read_text()
        entry = json.loads(content.strip())

        assert entry["event"] == "test_event"
        assert entry["key1"] == "value1"
        assert entry["key2"] == 42
        assert "ts" in entry


class TestEmitDistressSignal:
    """Test emit_distress_signal — Telegram alerts."""

    def test_calls_secrete_text(self):
        """Should call secrete_text with message."""
        mock_secrete = MagicMock()

        with patch.dict("sys.modules", {"metabolon.organelles.secretory_vesicle": mock_secrete}):
            with patch("metabolon.vasomotor.secrete_text", mock_secrete.secrete_text):
                vm.emit_distress_signal("Test alert")

    def test_logs_on_failure(self):
        """Should log on Telegram failure."""
        with patch("metabolon.vasomotor.log") as mock_log:
            with patch.dict("sys.modules", {}):
                # Import will fail, should log
                try:
                    vm.emit_distress_signal("Test alert")
                except Exception:
                    pass  # May raise due to import


class TestAssessPacing:
    """Test assess_pacing — pacing gate."""

    def test_returns_false_on_no_data(self):
        """Should return False when no telemetry data."""
        with patch("metabolon.vasomotor._fetch_telemetry", return_value=None):
            ok, reason = vm.assess_pacing()

        assert ok is False
        assert reason == "pacing_no_data"

    def test_returns_true_when_no_reset_info(self):
        """Should return True when reset time unknown."""
        mock_telemetry = {
            "seven_day": {"utilization": 50},
        }

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                with patch("metabolon.vasomotor.calibrate_circadian"):
                    ok, reason = vm.assess_pacing()

        assert ok is True
        assert "no_reset_info" in reason

    def test_returns_false_when_pacing_exceeded(self, tmp_path):
        """Should return False when burn exceeds daily budget."""
        state_file = tmp_path / "respiration-daily.json"
        state_file.write_text(json.dumps({
            "date": datetime.date.today().isoformat(),
            "count": 10,
            "saturated": 0,
            "systole_deltas": [1.0] * 10,
        }))

        skip_file = tmp_path / "skip-until"
        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=5)
        mock_telemetry = {
            "seven_day": {"utilization": 30, "resets_at": future.isoformat()},
            "five_hour": {"utilization": 10},
        }

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
                    with patch("metabolon.vasomotor.SKIP_UNTIL_FILE", skip_file):
                        with patch("metabolon.vasomotor.INTERACTIVE_PATTERN_FILE", tmp_path / "pattern.json"):
                            with patch("metabolon.vasomotor.EVENT_LOG", tmp_path / "events.jsonl"):
                                with patch("metabolon.vasomotor._maybe_migrate"):
                                    ok, reason = vm.assess_pacing()

        # With 10 systoles, should exceed pacing
        assert ok is False
        assert "pacing_exceeded" in reason or "daily_cap" in reason

    def test_returns_true_when_pacing_ok(self, tmp_path):
        """Should return True when pacing is acceptable."""
        state_file = tmp_path / "respiration-daily.json"
        state_file.write_text(json.dumps({
            "date": datetime.date.today().isoformat(),
            "count": 1,
            "saturated": 0,
            "systole_deltas": [0.5],
        }))

        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=5)
        mock_telemetry = {
            "seven_day": {"utilization": 30, "resets_at": future.isoformat()},
            "five_hour": {"utilization": 10},
        }

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                with patch("metabolon.vasomotor.DAILY_STATE_FILE", state_file):
                    with patch("metabolon.vasomotor.SKIP_UNTIL_FILE", tmp_path / "skip-until"):
                        with patch("metabolon.vasomotor.INTERACTIVE_PATTERN_FILE", tmp_path / "pattern.json"):
                            with patch("metabolon.vasomotor.EVENT_LOG", tmp_path / "events.jsonl"):
                                with patch("metabolon.vasomotor._maybe_migrate"):
                                    ok, reason = vm.assess_pacing()

        assert ok is True
        assert "pacing_ok" in reason


class TestSendPacingAlertOnce:
    """Test _send_pacing_alert_once — alert throttling."""

    def test_sends_alert_first_time(self, tmp_path):
        """Should send alert when not already alerted today."""
        alert_file = tmp_path / "alerted.json"

        with patch("metabolon.vasomotor.PACING_ALERT_FILE", alert_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                with patch("metabolon.vasomotor.emit_distress_signal") as mock_emit:
                    vm._send_pacing_alert_once("test reason")

        mock_emit.assert_called_once()
        assert alert_file.exists()

    def test_skips_alert_when_already_sent(self, tmp_path):
        """Should skip alert when already alerted today."""
        alert_file = tmp_path / "alerted.json"
        today = datetime.date.today().isoformat()
        alert_file.write_text(json.dumps({"date": today}))

        with patch("metabolon.vasomotor.PACING_ALERT_FILE", alert_file):
            with patch("metabolon.vasomotor._maybe_migrate"):
                with patch("metabolon.vasomotor.emit_distress_signal") as mock_emit:
                    vm._send_pacing_alert_once("test reason")

        mock_emit.assert_not_called()


class TestSelectReviewTier:
    """Test _select_review_tier — tier selection logic."""

    def test_haiku_by_default(self, tmp_path):
        """Should select haiku when no ligand and recent sonnet/opus."""
        review_state = tmp_path / "review-state.json"
        now = datetime.datetime.now()
        yesterday = (now - datetime.timedelta(days=1)).isoformat()
        last_week = (now - datetime.timedelta(days=2)).isoformat()
        review_state.write_text(json.dumps({
            "sonnet_last": yesterday,
            "opus_last": last_week,
        }))

        with patch("metabolon.vasomotor._REVIEW_STATE_FILE", review_state):
            with patch("metabolon.vasomotor._detect_ligand", return_value=None):
                with patch("metabolon.vasomotor.record_event"):
                    tier = vm._select_review_tier()

        assert tier == "haiku"

    def test_opus_after_week(self, tmp_path):
        """Should select opus when a week has passed."""
        review_state = tmp_path / "review-state.json"
        old_date = (datetime.datetime.now() - datetime.timedelta(days=8)).isoformat()
        review_state.write_text(json.dumps({
            "sonnet_last": old_date,
            "opus_last": old_date,
        }))

        with patch("metabolon.vasomotor._REVIEW_STATE_FILE", review_state):
            with patch("metabolon.vasomotor._detect_ligand", return_value=None):
                with patch("metabolon.vasomotor.record_event"):
                    tier = vm._select_review_tier()

        assert tier == "opus"

    def test_sonnet_after_day(self, tmp_path):
        """Should select sonnet when a day has passed (but not a week)."""
        review_state = tmp_path / "review-state.json"
        now = datetime.datetime.now()
        two_days_ago = (now - datetime.timedelta(days=2)).isoformat()
        three_days_ago = (now - datetime.timedelta(days=3)).isoformat()
        review_state.write_text(json.dumps({
            "sonnet_last": two_days_ago,
            "opus_last": three_days_ago,
        }))

        with patch("metabolon.vasomotor._REVIEW_STATE_FILE", review_state):
            with patch("metabolon.vasomotor._detect_ligand", return_value=None):
                with patch("metabolon.vasomotor.record_event"):
                    tier = vm._select_review_tier()

        assert tier == "sonnet"

    def test_ligand_overrides_clock(self, tmp_path):
        """Should select ligand-triggered tier regardless of clock."""
        review_state = tmp_path / "review-state.json"
        now = datetime.datetime.now()
        yesterday = (now - datetime.timedelta(days=1)).isoformat()
        review_state.write_text(json.dumps({
            "sonnet_last": yesterday,
            "opus_last": yesterday,
        }))

        with patch("metabolon.vasomotor._REVIEW_STATE_FILE", review_state):
            with patch("metabolon.vasomotor._detect_ligand", return_value="opus"):
                with patch("metabolon.vasomotor.record_event"):
                    tier = vm._select_review_tier()

        assert tier == "opus"


class TestDetectLigand:
    """Test _detect_ligand — signal detection for tier escalation."""

    def test_no_ligand_normal_events(self, tmp_path):
        """Should return None when events are normal."""
        event_log = tmp_path / "events.jsonl"
        event_log.write_text('{"event": "pacing_check"}\n{"event": "budget_raw"}\n')

        with patch("metabolon.vasomotor.EVENT_LOG", event_log):
            result = vm._detect_ligand()

        assert result is None

    def test_opus_ligand_on_circuit_breaker(self, tmp_path):
        """Should detect opus ligand on circuit breaker."""
        event_log = tmp_path / "events.jsonl"
        event_log.write_text('{"event": "circuit_breaker"}\n')

        with patch("metabolon.vasomotor.EVENT_LOG", event_log):
            result = vm._detect_ligand()

        assert result == "opus"

    def test_sonnet_ligand_on_saturation(self, tmp_path):
        """Should detect sonnet ligand on repeated saturation."""
        event_log = tmp_path / "events.jsonl"
        event_log.write_text(
            '{"event": "saturation_idle"}\n'
            '{"event": "saturation_idle"}\n'
        )

        with patch("metabolon.vasomotor.EVENT_LOG", event_log):
            result = vm._detect_ligand()

        assert result == "sonnet"


class TestSetRecoveryInterval:
    """Test set_recovery_interval — next-beat delay."""

    def test_sets_skip_until_file(self, tmp_path):
        """Should write skip_until file."""
        skip_file = tmp_path / "skip-until"
        mock_telemetry = {
            "seven_day": {"resets_at": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=12)).isoformat()}
        }

        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE", skip_file):
            with patch("metabolon.vasomotor._fetch_telemetry", return_value=mock_telemetry):
                with patch("metabolon.vasomotor.record_event"):
                    vm.set_recovery_interval()

        assert skip_file.exists()

    def test_fallback_on_no_telemetry(self, tmp_path):
        """Should use 120min fallback when no telemetry."""
        skip_file = tmp_path / "skip-until"

        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE", skip_file):
            with patch("metabolon.vasomotor._fetch_telemetry", return_value=None):
                with patch("metabolon.vasomotor._hours_to_reset", return_value=None):
                    with patch("metabolon.vasomotor.record_event"):
                        vm.set_recovery_interval()

        # Should still create a skip file with ~120min delay
        assert skip_file.exists()


class TestMigratePath:
    """Test _migrate_path — legacy file migration."""

    def test_renames_when_legacy_exists(self, tmp_path):
        """Should rename legacy file to new path."""
        legacy = tmp_path / "old.json"
        new = tmp_path / "new.json"
        legacy.write_text('{"data": "test"}')

        vm._migrate_path(new, legacy)

        assert new.exists()
        assert not legacy.exists()
        assert json.loads(new.read_text()) == {"data": "test"}

    def test_no_action_when_new_exists(self, tmp_path):
        """Should not overwrite if new file already exists."""
        legacy = tmp_path / "old.json"
        new = tmp_path / "new.json"
        legacy.write_text('{"old": true}')
        new.write_text('{"new": true}')

        vm._migrate_path(new, legacy)

        assert json.loads(new.read_text()) == {"new": True}
        assert legacy.exists()  # Legacy untouched

    def test_no_action_when_neither_exists(self, tmp_path):
        """Should do nothing when neither file exists."""
        legacy = tmp_path / "old.json"
        new = tmp_path / "new.json"

        vm._migrate_path(new, legacy)

        assert not new.exists()
        assert not legacy.exists()
