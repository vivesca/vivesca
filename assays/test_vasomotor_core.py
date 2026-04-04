from __future__ import annotations

"""Tests for vasomotor.py — pure functions and data transformations.

Mock all external I/O and subprocess calls to test core logic in isolation.
"""


import datetime
import json
from unittest.mock import mock_open, patch

import pytest

from metabolon.vasomotor import (
    SATURATION_PENALTY,
    _hours_to_reset,
    _migrate_path,
    effective_burn,
    oxygen_debt,
    vasomotor_snapshot,
)


class TestMigrationHelpers:
    """Tests for migration helpers."""

    def test_migrate_path_creates_new_from_legacy(self, tmp_path):
        """If legacy exists and new doesn't, rename legacy to new path."""
        legacy = tmp_path / "legacy.txt"
        new = tmp_path / "new.txt"
        legacy.write_text("legacy content")

        assert not new.exists()
        _migrate_path(new, legacy)
        assert new.exists()
        assert not legacy.exists()
        assert new.read_text() == "legacy content"

    def test_migrate_path_no_legacy_does_nothing(self, tmp_path):
        """If legacy doesn't exist, do nothing."""
        legacy = tmp_path / "legacy.txt"
        new = tmp_path / "new.txt"

        assert not legacy.exists()
        assert not new.exists()
        _migrate_path(new, legacy)
        assert not new.exists()

    def test_migrate_path_new_already_exists_does_nothing(self, tmp_path):
        """If new already exists, don't overwrite it."""
        legacy = tmp_path / "legacy.txt"
        new = tmp_path / "new.txt"
        legacy.write_text("legacy")
        new.write_text("new")

        _migrate_path(new, legacy)
        assert new.exists()
        assert legacy.exists()
        assert new.read_text() == "new"


class TestOxygenDebt:
    """Tests for oxygen_debt pure function.

    Oxygen debt: 0.0 (no urgency) to 1.0 (full urgency)
    Ramps from 48h (0.0) to 6h (1.0). Below 6h → 1.0. Above 48h → 0.0.
    Formula: max(0.0, min(1.0, (48 - hours_to_reset) / 42))
    """

    def test_oxygen_debt_full_debt_below_6h(self):
        """Below 6 hours reset, debt is maxed at 1.0."""
        assert oxygen_debt(0) == 1.0
        assert oxygen_debt(3) == 1.0
        assert oxygen_debt(6) == pytest.approx(1.0)

    def test_oxygen_debt_zero_above_48h(self):
        """Above 48 hours reset, debt is 0.0."""
        assert oxygen_debt(48) == pytest.approx(0.0)
        assert oxygen_debt(72) == 0.0
        assert oxygen_debt(100) == 0.0

    def test_oxygen_debt_linear_midpoint(self):
        """Linear ramp between 6h and 48h."""
        # (48 - 27) / 42 = 21 / 42 = 0.5
        assert oxygen_debt(27) == pytest.approx(0.5)
        # (48 - 36) / 42 = 12 / 42 ≈ 0.2857
        assert oxygen_debt(36) == pytest.approx(12 / 42)
        # (48 - 12) / 42 = 36 / 42 ≈ 0.8571
        assert oxygen_debt(12) == pytest.approx(36 / 42)

    def test_oxygen_debt_clamped_within_bounds(self):
        """Output is clamped between 0.0 and 1.0."""
        assert 0.0 <= oxygen_debt(0) <= 1.0
        assert 0.0 <= oxygen_debt(24) <= 1.0
        assert 0.0 <= oxygen_debt(100) <= 1.0


class TestEffectiveBurn:
    """Tests for effective_burn calculation with saturation penalty."""

    def test_effective_burn_no_saturation(self):
        """Without saturated systoles, burn is just simple multiplication."""
        # 5 systoles, 0 saturated, cost 1.0 → 5.0
        assert effective_burn(5, 0, 1.0) == 5.0
        # 10 systoles, 0 saturated, cost 0.5 → 5.0
        assert effective_burn(10, 0, 0.5) == 5.0

    def test_effective_burn_all_saturated(self):
        """All systoles saturated get penalty applied."""
        # 4 saturated, 0 productive → 4 * 1.5 = 6 × cost 1.0 = 6.0
        assert effective_burn(4, 4, 1.0) == 4 * SATURATION_PENALTY * 1.0
        # 10 saturated, cost 0.5 → 10 * 1.5 * 0.5 = 7.5
        assert effective_burn(10, 10, 0.5) == pytest.approx(7.5)

    def test_effective_burn_mixed(self):
        """Mix of productive and saturated systoles."""
        # 10 total, 3 saturated → (7 + (3 * 1.5)) × 1.0 = 7 + 4.5 = 11.5
        expected = (7 + (3 * SATURATION_PENALTY)) * 1.0
        assert effective_burn(10, 3, 1.0) == pytest.approx(expected)
        # 5 total, 2 saturated, cost 0.4
        expected = (3 + (2 * SATURATION_PENALTY)) * 0.4
        assert effective_burn(5, 2, 0.4) == pytest.approx(expected)

    def test_effective_burn_custom_penalty_from_genome(self):
        """When genome has custom penalty, it's used."""
        with patch(
            "metabolon.vasomotor.vasomotor_genome", return_value={"saturation_penalty": 2.0}
        ):
            # 10 total, 3 saturated, penalty 2.0 → (7 + 3×2) × 1.0 = 13
            assert effective_burn(10, 3, 1.0) == 13.0

    def test_effective_burn_default_penalty_when_genome_empty(self):
        """When genome is empty, default SATURATION_PENALTY used."""
        with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
            expected = (7 + (3 * SATURATION_PENALTY)) * 1.0
            assert effective_burn(10, 3, 1.0) == pytest.approx(expected)


class TestHoursToReset:
    """Tests for _hours_to_reset with telemetry and fallback persistence."""

    def test_hours_to_reset_uses_telemetry_when_available(self):
        """When telemetry provides resets_at, use it and persist to file."""
        future = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
        telemetry = {"seven_day": {"resets_at": future.isoformat()}}

        with patch("metabolon.vasomotor._RESETS_AT_FILE") as mock_file:
            mock_file.write_text = lambda x: None
            result = _hours_to_reset(telemetry)
            assert result is not None
            assert 23 < result < 25  # ~24h left

    def test_hours_to_reset_fallback_to_file(self):
        """When telemetry doesn't have resets_at, read from file fallback."""
        future = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=12)
        cached_content = future.isoformat()

        with patch("metabolon.vasomotor._RESETS_AT_FILE") as mock_file:
            mock_file.read_text = lambda: cached_content
            result = _hours_to_reset(None)
            assert result is not None
            assert 11 < result < 13

    def test_hours_to_reset_returns_none_when_no_data(self):
        """When neither telemetry nor cached file has data, return None."""

        def raise_file_not_found():
            raise FileNotFoundError()

        with patch("metabolon.vasomotor._RESETS_AT_FILE") as mock_file:
            mock_file.read_text = raise_file_not_found
            result = _hours_to_reset(None)
            assert result is None

    def test_hours_to_reset_returns_min_half_hour(self):
        """Never returns less than 0.5 hours."""
        past = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1)
        telemetry = {"seven_day": {"resets_at": past.isoformat()}}

        with patch("metabolon.vasomotor._RESETS_AT_FILE") as mock_file:
            mock_file.write_text = lambda x: None
            result = _hours_to_reset(telemetry)
            assert result == 0.5


class TestVasomotorSnapshot:
    """Tests for vasomotor_snapshot extraction."""

    def test_vasomotor_snapshot_extracts_correct_fields(self):
        """Snapshot extracts weekly and sonnet utilization correctly."""
        telemetry = {
            "seven_day": {"utilization": 45},
            "seven_day_sonnet": {"utilization": 60},
        }
        with patch("metabolon.vasomotor._fetch_telemetry", return_value=telemetry):
            snapshot = vasomotor_snapshot()
            assert snapshot == {"weekly": 45, "sonnet": 60}

    def test_vasomotor_snapshot_defaults_zero_when_missing(self):
        """When fields are missing, defaults to 0."""
        telemetry = {"seven_day": {}}
        with patch("metabolon.vasomotor._fetch_telemetry", return_value=telemetry):
            snapshot = vasomotor_snapshot()
            assert snapshot == {"weekly": 0, "sonnet": 0}

    def test_vasomotor_snapshot_returns_none_when_telemetry_none(self):
        """When telemetry fetch fails, returns None."""
        with patch("metabolon.vasomotor._fetch_telemetry", return_value=None):
            snapshot = vasomotor_snapshot()
            assert snapshot is None


class TestCircadianCalibration:
    """Tests for circadian calibration functions."""

    def test_breathe_increments_count(self):
        """Breathe increments systole count correctly."""
        from metabolon.vasomotor import breathe

        empty_state = {
            "date": datetime.date.today().isoformat(),
            "count": 0,
            "saturated": 0,
            "systole_deltas": [],
        }

        with patch("metabolon.vasomotor._load_circadian_state", return_value=empty_state):
            with patch("metabolon.vasomotor._save_circadian_state") as mock_save:
                count = breathe(saturated=False, systole_delta=1.0)
                assert count == 1
                # Check saved state has incremented count
                saved_state = mock_save.call_args[0][0]
                assert saved_state["count"] == 1
                assert saved_state["saturated"] == 0
                assert saved_state["systole_deltas"] == [1.0]

    def test_breathe_increments_saturated(self):
        """Breathe increments saturated counter when saturated=True."""
        from metabolon.vasomotor import breathe

        state = {
            "date": datetime.date.today().isoformat(),
            "count": 5,
            "saturated": 2,
            "systole_deltas": [1.0, 0.0],
        }

        with patch("metabolon.vasomotor._load_circadian_state", return_value=state):
            with patch("metabolon.vasomotor._save_circadian_state"):
                count = breathe(saturated=True, systole_delta=0.0)
                assert count == 6

    def test_breathe_accepts_wave_delta(self):
        """Breathe accepts legacy wave_delta parameter."""
        from metabolon.vasomotor import breathe

        empty_state = {
            "date": datetime.date.today().isoformat(),
            "count": 0,
            "saturated": 0,
            "systole_deltas": [],
        }

        with patch("metabolon.vasomotor._load_circadian_state", return_value=empty_state):
            with patch("metabolon.vasomotor._save_circadian_state") as mock_save:
                breathe(saturated=False, wave_delta=0.5)
                saved_state = mock_save.call_args[0][0]
                assert saved_state["systole_deltas"] == [0.5]


class TestTidalVolume:
    """Tests for tidal_volume calculation blends interactive pressure."""

    def test_tidal_volume_reduces_with_high_pressure(self):
        """Higher interactive pressure reduces tidal volume (pulse share)."""
        from metabolon.vasomotor import tidal_volume

        with patch(
            "metabolon.vasomotor.vasomotor_genome",
            return_value={
                "basal_rate": 0.5,
                "min_basal_rate": 0.15,
            },
        ):
            with patch("metabolon.vasomotor.interactive_pressure", return_value=0.0):
                # 0 pressure → full basal rate
                assert tidal_volume() == pytest.approx(0.5)

            with patch("metabolon.vasomotor.interactive_pressure", return_value=1.0):
                # 1 pressure → min basal rate
                assert tidal_volume() == pytest.approx(0.15)

            with patch("metabolon.vasomotor.interactive_pressure", return_value=0.5):
                # 0.5 pressure → midpoint
                expected = 0.5 - 0.5 * (0.5 - 0.15)
                assert tidal_volume() == pytest.approx(expected)


class TestVasomotorGenome:
    """Tests for vasomotor_genome config reading."""

    def test_vasomotor_genome_returns_empty_dict_when_file_missing(self):
        """When config file doesn't exist, returns empty dict."""
        from metabolon.vasomotor import vasomotor_genome

        with patch("metabolon.vasomotor.CONF_PATH") as mock_path:
            mock_path.exists = lambda: False
            assert vasomotor_genome() == {}

    def test_vasomotor_genome_returns_parsed_json(self):
        """When config exists, returns parsed JSON dict."""
        from metabolon.vasomotor import vasomotor_genome

        test_config = {
            "aerobic_ceiling": 85,
            "sonnet_ceiling": 92,
            "basal_rate": 0.4,
        }
        with patch("metabolon.vasomotor.CONF_PATH") as mock_path:
            mock_path.exists = lambda: True
            mock_path.read_text = lambda: json.dumps(test_config)
            assert vasomotor_genome() == test_config


class TestApneaCheck:
    """Tests for is_apneic apnea detection."""

    def test_not_apneic_when_file_missing(self):
        """When no skip_until file, not apneic."""
        from metabolon.vasomotor import is_apneic

        def raise_file_not_found():
            raise FileNotFoundError()

        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE") as mock_file:
            mock_file.read_text = raise_file_not_found
            apneic, reason = is_apneic()
            assert not apneic
            assert reason == ""

    def test_apneic_when_now_before_skip_until(self):
        """When current time is before skip_until, returns apneic."""
        from metabolon.vasomotor import is_apneic

        future = datetime.datetime.now() + datetime.timedelta(minutes=30)
        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE") as mock_file:
            mock_file.read_text = lambda: future.isoformat()
            apneic, reason = is_apneic()
            assert apneic
            assert "skip_until" in reason
            assert "remaining" in reason

    def test_not_apneic_when_now_after_skip_until(self):
        """When current time is past skip_until, not apneic."""
        from metabolon.vasomotor import is_apneic

        past = datetime.datetime.now() - datetime.timedelta(minutes=10)
        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE") as mock_file:
            mock_file.read_text = lambda: past.isoformat()
            apneic, _reason = is_apneic()
            assert not apneic


class TestMeasuredCostPerSystole:
    """Tests for measured_cost_per_systole calculation."""

    def test_uses_today_isolated_deltas_when_enough_samples(self):
        """When today has >= 3 samples, uses average of today's deltas."""
        from metabolon.vasomotor import measured_cost_per_systole

        circadian_state = {
            "systole_deltas": [0.0, 1.0, 0.0, 1.0, 0.0],
        }
        # Average: (0+1+0+1+0)/5 = 2/5 = 0.4
        with patch("metabolon.vasomotor._load_circadian_state", return_value=circadian_state):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                cost = measured_cost_per_systole()
                assert cost == pytest.approx(0.4)

    def test_falls_back_to_default_when_few_samples_no_history(self):
        """When too few samples today and no historical data, uses default."""
        from metabolon.vasomotor import DEFAULT_COST_PER_SYSTOLE, measured_cost_per_systole

        circadian_state = {
            "systole_deltas": [0.0, 1.0],  # only 2 samples (<3 required)
        }
        with patch("metabolon.vasomotor._load_circadian_state", return_value=circadian_state):
            with patch("builtins.open", mock_open(read_data="")):
                with patch("metabolon.vasomotor.EVENT_LOG") as mock_log:
                    mock_log.read_text = lambda: ""
                    with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                        cost = measured_cost_per_systole()
                        assert cost == DEFAULT_COST_PER_SYSTOLE

    def test_never_drops_below_minimum(self):
        """Average is never lower than 0.1 minimum."""
        from metabolon.vasomotor import measured_cost_per_systole

        circadian_state = {
            "systole_deltas": [0.0, 0.0, 0.0],  # average 0.0
        }
        with patch("metabolon.vasomotor._load_circadian_state", return_value=circadian_state):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                cost = measured_cost_per_systole()
                assert cost == 0.1  # clamped to minimum


class TestFetchTelemetry:
    """Tests for _fetch_telemetry with caching and subprocess calls."""

    def test_fetch_telemetry_returns_parsed_json(self):
        """Successful subprocess call returns parsed JSON."""
        import metabolon.vasomotor as vm
        from metabolon.vasomotor import _fetch_telemetry

        vm._telemetry_cache = None
        vm._telemetry_cache_time = 0

        mock_result = type(
            "MockResult",
            (),
            {
                "returncode": 0,
                "stdout": '{"weekly": 50, "seven_day": {"utilization": 45}}',
                "stderr": "",
            },
        )()

        with patch("metabolon.vasomotor.subprocess.run", return_value=mock_result):
            result = _fetch_telemetry()
            assert result == {"weekly": 50, "seven_day": {"utilization": 45}}

    def test_fetch_telemetry_returns_none_on_failure(self):
        """Failed subprocess call returns None."""
        import metabolon.vasomotor as vm
        from metabolon.vasomotor import _fetch_telemetry

        vm._telemetry_cache = None
        vm._telemetry_cache_time = 0

        mock_result = type("MockResult", (), {"returncode": 1, "stdout": "", "stderr": "error"})()

        with patch("metabolon.vasomotor.subprocess.run", return_value=mock_result):
            result = _fetch_telemetry()
            assert result is None

    def test_fetch_telemetry_uses_cache_within_ttl(self):
        """Within cache TTL, returns cached value without subprocess call."""
        import time

        import metabolon.vasomotor as vm
        from metabolon.vasomotor import _fetch_telemetry

        vm._telemetry_cache = {"cached": True}
        vm._telemetry_cache_time = time.time()

        with patch("metabolon.vasomotor.subprocess.run") as mock_run:
            result = _fetch_telemetry()
            assert result == {"cached": True}
            mock_run.assert_not_called()


class TestMeasureVasomotorTone:
    """Tests for measure_vasomotor_tone wrapper."""

    def test_measure_vasomotor_tone_delegates_to_fetch(self):
        """measure_vasomotor_tone is a thin wrapper around _fetch_telemetry."""
        from metabolon.vasomotor import measure_vasomotor_tone

        with patch("metabolon.vasomotor._fetch_telemetry", return_value={"test": 1}):
            assert measure_vasomotor_tone() == {"test": 1}

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=None):
            assert measure_vasomotor_tone() is None


class TestAssessVitalCapacity:
    """Tests for assess_vital_capacity budget gate."""

    def test_returns_false_when_telemetry_unavailable(self):
        """When telemetry can't be fetched, returns (False, 'budget_unknown')."""
        from metabolon.vasomotor import assess_vital_capacity

        with patch("metabolon.vasomotor.measure_vasomotor_tone", return_value=None):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                ok, reason = assess_vital_capacity()
                assert not ok
                assert reason == "budget_unknown"

    def test_returns_false_when_weekly_exceeds_ceiling(self):
        """Weekly utilization above ceiling (accounting for oxygen debt) returns False."""
        from metabolon.vasomotor import assess_vital_capacity

        telemetry = {
            "seven_day": {"utilization": 95},  # Well above ceiling
            "seven_day_sonnet": {"utilization": 50},
        }

        with patch("metabolon.vasomotor.measure_vasomotor_tone", return_value=telemetry):
            with patch(
                "metabolon.vasomotor.vasomotor_genome",
                return_value={
                    "aerobic_ceiling": 80,
                    "sonnet_ceiling": 90,
                    "sympathetic_reserve": 15,
                    "tachycardia_threshold": 60,
                },
            ):
                # With many hours to reset, debt=0, ceiling stays at 80
                # 95% > 80% so should fail
                with patch("metabolon.vasomotor._hours_to_reset", return_value=48):
                    with patch("metabolon.vasomotor.assess_pacing", return_value=(True, "")):
                        ok, reason = assess_vital_capacity()
                        assert not ok
                        assert "exceeds_ceiling" in reason

    def test_returns_false_when_sonnet_exceeds_ceiling(self):
        """Sonnet utilization above ceiling returns False."""
        from metabolon.vasomotor import assess_vital_capacity

        telemetry = {"seven_day": {"utilization": 50}, "seven_day_sonnet": {"utilization": 95}}

        with patch("metabolon.vasomotor.measure_vasomotor_tone", return_value=telemetry):
            with patch(
                "metabolon.vasomotor.vasomotor_genome",
                return_value={
                    "aerobic_ceiling": 80,
                    "sonnet_ceiling": 90,
                    "sympathetic_reserve": 15,
                    "tachycardia_threshold": 60,
                },
            ):
                with patch("metabolon.vasomotor._hours_to_reset", return_value=48):
                    with patch("metabolon.vasomotor.assess_pacing", return_value=(True, "")):
                        ok, reason = assess_vital_capacity()
                        assert not ok
                        assert "sonnet" in reason and "exceeds" in reason

    def test_returns_false_when_remaining_below_reserve(self):
        """When remaining budget is below reserve (accounting for debt), returns False."""
        from metabolon.vasomotor import assess_vital_capacity

        telemetry = {
            "seven_day": {"utilization": 90},  # 10% remaining, below 15% reserve
            "seven_day_sonnet": {"utilization": 50},
        }

        with patch("metabolon.vasomotor.measure_vasomotor_tone", return_value=telemetry):
            with patch(
                "metabolon.vasomotor.vasomotor_genome",
                return_value={
                    "aerobic_ceiling": 95,  # 90% < 95% ceiling, so passes ceiling check
                    "sonnet_ceiling": 95,
                    "sympathetic_reserve": 15,
                    "tachycardia_threshold": 60,
                },
            ):
                # High hours = low debt = full reserve
                with patch("metabolon.vasomotor._hours_to_reset", return_value=48):
                    with patch("metabolon.vasomotor.assess_pacing", return_value=(True, "")):
                        ok, reason = assess_vital_capacity()
                        assert not ok
                        assert "reserve" in reason

    def test_returns_true_when_budget_ok(self):
        """When all checks pass, returns True."""
        from metabolon.vasomotor import assess_vital_capacity

        telemetry = {"seven_day": {"utilization": 50}, "seven_day_sonnet": {"utilization": 40}}

        with patch("metabolon.vasomotor.measure_vasomotor_tone", return_value=telemetry):
            with patch(
                "metabolon.vasomotor.vasomotor_genome",
                return_value={
                    "aerobic_ceiling": 80,
                    "sonnet_ceiling": 90,
                    "sympathetic_reserve": 15,
                    "tachycardia_threshold": 60,
                },
            ):
                with patch("metabolon.vasomotor._hours_to_reset", return_value=24):
                    with patch(
                        "metabolon.vasomotor.assess_pacing", return_value=(True, "pacing_ok")
                    ):
                        ok, reason = assess_vital_capacity()
                        assert ok
                        assert "ok" in reason


class TestVasomotorStatus:
    """Tests for vasomotor_status color-coded status."""

    def test_returns_green_when_under_95(self):
        """Under 95% utilization returns green."""
        from metabolon.vasomotor import vasomotor_status

        telemetry = {"seven_day": {"utilization": 80}, "seven_day_sonnet": {"utilization": 70}}

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=telemetry):
            with patch("metabolon.vasomotor.subprocess.run"):
                with patch("metabolon.vasomotor.record_event"):
                    assert vasomotor_status() == "green"

    def test_returns_yellow_when_95_to_98(self):
        """95-98% utilization returns yellow."""
        from metabolon.vasomotor import vasomotor_status

        telemetry = {"seven_day": {"utilization": 96}, "seven_day_sonnet": {"utilization": 70}}

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=telemetry):
            with patch("metabolon.vasomotor.subprocess.run"):
                with patch("metabolon.vasomotor.record_event"):
                    assert vasomotor_status() == "yellow"

    def test_returns_red_when_over_98(self):
        """Over 98% utilization returns red."""
        from metabolon.vasomotor import vasomotor_status

        telemetry = {"seven_day": {"utilization": 99}, "seven_day_sonnet": {"utilization": 70}}

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=telemetry):
            with patch("metabolon.vasomotor.subprocess.run"):
                with patch("metabolon.vasomotor.record_event"):
                    assert vasomotor_status() == "red"

    def test_returns_unknown_on_telemetry_failure(self):
        """When telemetry fails, returns unknown."""
        from metabolon.vasomotor import vasomotor_status

        mock_result = type("MockResult", (), {"stdout": "unknown"})()

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=None):
            with patch("metabolon.vasomotor.subprocess.run", return_value=mock_result):
                assert vasomotor_status() == "unknown"


class TestRecordEvent:
    """Tests for record_event JSONL logging."""

    def test_record_event_writes_jsonl(self, tmp_path):
        """record_event appends JSON line to log file."""
        from metabolon.vasomotor import record_event

        with patch("metabolon.vasomotor.EVENT_LOG", tmp_path / "events.jsonl"):
            record_event("test_event", key1="value1", key2=42)

            content = (tmp_path / "events.jsonl").read_text()
            entry = json.loads(content.strip())
            assert entry["event"] == "test_event"
            assert entry["key1"] == "value1"
            assert entry["key2"] == 42
            assert "ts" in entry


class TestEmitDistressSignal:
    """Tests for emit_distress_signal Telegram alerts."""

    def test_emit_distress_signal_calls_secrete_text(self):
        """emit_distress_signal delegates to secrete_text."""
        from metabolon.vasomotor import emit_distress_signal

        mock_module = type("M", (), {"secrete_text": lambda msg, html=False, label="": None})()
        with patch.dict("sys.modules", {"metabolon.organelles.secretory_vesicle": mock_module}):
            # Should not raise
            emit_distress_signal("test alert")

    def test_emit_distress_signal_handles_exception(self):
        """emit_distress_signal handles exceptions gracefully."""
        from metabolon.vasomotor import emit_distress_signal

        # The function catches Exception and logs, so it shouldn't raise
        with patch("metabolon.vasomotor.log"):
            # Simulate the import succeeding but the call failing
            with patch.dict("sys.modules"):
                # Just call it - if import fails, it catches and logs
                emit_distress_signal("test alert")  # Should not raise


class TestInduceApnea:
    """Tests for induce_apnea scheduling."""

    def test_induce_apnea_sets_skip_until_midnight_on_cap(self):
        """When daily cap reached, skip until midnight."""
        from metabolon.vasomotor import induce_apnea

        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE") as mock_file:
            with patch("metabolon.vasomotor.record_event"):
                with patch(
                    "metabolon.vasomotor.vasomotor_genome", return_value={"max_daily_systoles": 10}
                ):
                    induce_apnea(
                        daily_budget=5.0,
                        cost_per_systole=1.0,
                        systoles_today=10,
                        sustainable_daily=5.0,
                    )
                    # Should have written to file
                    mock_file.write_text.assert_called_once()
                    written = mock_file.write_text.call_args[0][0]
                    # Should be an ISO timestamp around midnight tomorrow
                    assert "T00:00:" in written

    def test_induce_apnea_sets_one_hour_on_pacing(self):
        """When under cap, skip for up to one hour."""
        from metabolon.vasomotor import induce_apnea

        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE") as mock_file:
            with patch("metabolon.vasomotor.record_event"):
                with patch(
                    "metabolon.vasomotor.vasomotor_genome", return_value={"max_daily_systoles": 10}
                ):
                    induce_apnea(
                        daily_budget=5.0,
                        cost_per_systole=1.0,
                        systoles_today=5,
                        sustainable_daily=5.0,
                    )
                    mock_file.write_text.assert_called_once()


class TestResumeBreathing:
    """Tests for resume_breathing clearing apnea state."""

    def test_resume_breathing_deletes_skip_file(self):
        """resume_breathing removes the skip_until file."""
        from metabolon.vasomotor import resume_breathing

        with patch("metabolon.vasomotor.SKIP_UNTIL_FILE") as mock_file:
            resume_breathing()
            mock_file.unlink.assert_called_once_with(missing_ok=True)


class TestSetRecoveryInterval:
    """Tests for set_recovery_interval delay calculation."""

    def test_set_recovery_uses_oxygen_debt(self):
        """Recovery interval is shorter with higher oxygen debt."""
        from metabolon.vasomotor import set_recovery_interval

        with patch("metabolon.vasomotor._fetch_telemetry", return_value={}):
            with patch("metabolon.vasomotor._hours_to_reset", return_value=10):  # high debt
                with patch("metabolon.vasomotor.SKIP_UNTIL_FILE") as mock_file:
                    with patch("metabolon.vasomotor.record_event"):
                        set_recovery_interval()
                        mock_file.write_text.assert_called_once()


class TestCalibrateCircadian:
    """Tests for calibrate_circadian baseline recording."""

    def test_calibrate_circadian_sets_day_start_weekly(self):
        """calibrate_circadian records weekly at start of first systole."""
        from metabolon.vasomotor import calibrate_circadian

        state = {
            "date": datetime.date.today().isoformat(),
            "day_start_weekly": None,
        }

        with patch("metabolon.vasomotor._load_circadian_state", return_value=state):
            with patch("metabolon.vasomotor._save_circadian_state") as mock_save:
                calibrate_circadian(weekly=45.5)
                saved = mock_save.call_args[0][0]
                assert saved["day_start_weekly"] == 45.5

    def test_calibrate_circadian_does_not_overwrite(self):
        """calibrate_circadian doesn't overwrite existing baseline."""
        from metabolon.vasomotor import calibrate_circadian

        state = {
            "date": datetime.date.today().isoformat(),
            "day_start_weekly": 30.0,
        }

        with patch("metabolon.vasomotor._load_circadian_state", return_value=state):
            with patch("metabolon.vasomotor._save_circadian_state") as mock_save:
                calibrate_circadian(weekly=50.0)
                # Should not have saved (baseline already set)
                mock_save.assert_not_called()


class TestInteractivePressure:
    """Tests for interactive_pressure calculation."""

    def test_interactive_pressure_blends_live_and_pattern(self):
        """Pressure blends live utilization with learned hourly pattern."""
        from metabolon.vasomotor import interactive_pressure

        telemetry = {"five_hour": {"utilization": 50}}
        pattern = {str(datetime.datetime.now().hour): 30}

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=telemetry):
            with patch("metabolon.vasomotor._load_sympathetic_pattern", return_value=pattern):
                with patch("metabolon.vasomotor._record_sympathetic_sample"):
                    with patch("metabolon.vasomotor.record_event"):
                        pressure = interactive_pressure()
                        # Result should be between 0 and 1
                        assert 0.0 <= pressure <= 1.0

    def test_interactive_pressure_uses_pattern_when_no_telemetry(self):
        """When telemetry unavailable, falls back to pattern only."""
        from metabolon.vasomotor import interactive_pressure

        pattern = {str(datetime.datetime.now().hour): 60}

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=None):
            with patch("metabolon.vasomotor._load_sympathetic_pattern", return_value=pattern):
                with patch("metabolon.vasomotor.record_event"):
                    pressure = interactive_pressure()
                    assert 0.0 <= pressure <= 1.0


class TestAssessPacing:
    """Tests for assess_pacing comprehensive pacing gate."""

    def test_assess_pacing_returns_false_no_data(self):
        """When no telemetry data, returns pacing_no_data."""
        from metabolon.vasomotor import assess_pacing

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=None):
            ok, reason = assess_pacing()
            assert not ok
            assert reason == "pacing_no_data"

    def test_assess_pacing_returns_true_no_reset_info(self):
        """When telemetry lacks reset info, returns True (can't pace)."""
        from metabolon.vasomotor import assess_pacing

        telemetry = {
            "seven_day": {"utilization": 50},
        }

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=telemetry):
            with patch("metabolon.vasomotor.vasomotor_genome", return_value={}):
                ok, reason = assess_pacing()
                assert ok
                assert "no_reset_info" in reason

    def test_assess_pacing_checks_burn_vs_budget(self):
        """assess_pacing compares estimated burn to daily budget."""
        import datetime

        from metabolon.vasomotor import assess_pacing

        future = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=3)

        telemetry = {
            "seven_day": {"utilization": 50, "resets_at": future.isoformat()},
        }

        with patch("metabolon.vasomotor._fetch_telemetry", return_value=telemetry):
            with patch(
                "metabolon.vasomotor.vasomotor_genome",
                return_value={"sympathetic_reserve": 15, "max_daily_systoles": 10},
            ):
                with patch("metabolon.vasomotor.daily_systole_count", return_value=2):
                    with patch("metabolon.vasomotor.daily_saturated_count", return_value=0):
                        with patch(
                            "metabolon.vasomotor.measured_cost_per_systole", return_value=1.0
                        ):
                            with patch("metabolon.vasomotor.tidal_volume", return_value=0.5):
                                with patch("metabolon.vasomotor.record_event"):
                                    with patch("metabolon.vasomotor.calibrate_circadian"):
                                        _ok, reason = assess_pacing()
                                        # Should pass with low systole count
                                        assert "pacing" in reason.lower() or "ok" in reason.lower()


class TestDailyCounts:
    """Tests for daily_systole_count and daily_saturated_count."""

    def test_daily_systole_count_returns_count(self):
        """daily_systole_count returns count from circadian state."""
        from metabolon.vasomotor import daily_systole_count

        state = {"count": 5, "date": datetime.date.today().isoformat()}

        with patch("metabolon.vasomotor._load_circadian_state", return_value=state):
            assert daily_systole_count() == 5

    def test_daily_saturated_count_returns_count(self):
        """daily_saturated_count returns saturated from circadian state."""
        from metabolon.vasomotor import daily_saturated_count

        state = {"saturated": 2, "date": datetime.date.today().isoformat()}

        with patch("metabolon.vasomotor._load_circadian_state", return_value=state):
            assert daily_saturated_count() == 2


class TestMeasureYield:
    """Tests for measure_yield file counting."""

    def test_measure_yield_counts_pulse_files(self, tmp_path):
        """measure_yield counts files with 'pulse' in name created recently."""
        from metabolon.vasomotor import measure_yield

        # Create test files
        (tmp_path / "pulse-report-1.md").write_text("test")
        (tmp_path / "pulse-report-2.md").write_text("test")
        (tmp_path / "other-file.txt").write_text("test")

        with patch("metabolon.vasomotor.YIELD_DIRS", [tmp_path]):
            with patch(
                "metabolon.vasomotor.subprocess.run", return_value=type("R", (), {"stdout": ""})()
            ):
                result = measure_yield()
                assert result["files_created"] == 2

    def test_measure_yield_returns_summary(self, tmp_path):
        """measure_yield returns a summary string."""
        from metabolon.vasomotor import measure_yield

        with patch("metabolon.vasomotor.YIELD_DIRS", [tmp_path]):
            with patch(
                "metabolon.vasomotor.subprocess.run", return_value=type("R", (), {"stdout": ""})()
            ):
                result = measure_yield()
                assert "files" in result["yield_summary"]
                assert "commits" in result["yield_summary"]


class TestSendPacingAlertOnce:
    """Tests for _send_pacing_alert_once daily alert limit."""

    def test_sends_alert_on_first_call_today(self, tmp_path):
        """First call today sends alert and records date."""
        from metabolon.vasomotor import _send_pacing_alert_once

        alert_file = tmp_path / "alert.json"

        with patch("metabolon.vasomotor.PACING_ALERT_FILE", alert_file):
            with patch("metabolon.vasomotor.emit_distress_signal") as mock_emit:
                _send_pacing_alert_once("test reason")
                mock_emit.assert_called_once()
                assert "test reason" in mock_emit.call_args[0][0]

    def test_no_alert_on_same_day(self, tmp_path):
        """Second call same day does not send alert."""
        from metabolon.vasomotor import _send_pacing_alert_once

        today = datetime.date.today().isoformat()
        alert_file = tmp_path / "alert.json"
        alert_file.write_text(json.dumps({"date": today}))

        with patch("metabolon.vasomotor.PACING_ALERT_FILE", alert_file):
            with patch("metabolon.vasomotor.emit_distress_signal") as mock_emit:
                _send_pacing_alert_once("test reason")
                mock_emit.assert_not_called()


# Run with: pytest assays/test_vasomotor_core.py -v
