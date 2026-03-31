"""Tests for vasomotor.py — pure functions and data transformations.

Mock all external I/O and subprocess calls to test core logic in isolation.
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import patch, mock_open
import datetime

from metabolon.vasomotor import (
    _migrate_path,
    oxygen_debt,
    effective_burn,
    _hours_to_reset,
    vasomotor_snapshot,
    _migrated,
    SATURATION_PENALTY,
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
        with patch('metabolon.vasomotor.vasomotor_genome', return_value={'saturation_penalty': 2.0}):
            # 10 total, 3 saturated, penalty 2.0 → (7 + 3×2) × 1.0 = 13
            assert effective_burn(10, 3, 1.0) == 13.0

    def test_effective_burn_default_penalty_when_genome_empty(self):
        """When genome is empty, default SATURATION_PENALTY used."""
        with patch('metabolon.vasomotor.vasomotor_genome', return_value={}):
            expected = (7 + (3 * SATURATION_PENALTY)) * 1.0
            assert effective_burn(10, 3, 1.0) == pytest.approx(expected)


class TestHoursToReset:
    """Tests for _hours_to_reset with telemetry and fallback persistence."""

    def test_hours_to_reset_uses_telemetry_when_available(self):
        """When telemetry provides resets_at, use it and persist to file."""
        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        telemetry = {
            "seven_day": {
                "resets_at": future.isoformat()
            }
        }
        
        with patch('metabolon.vasomotor._RESETS_AT_FILE') as mock_file:
            mock_file.write_text = lambda x: None
            result = _hours_to_reset(telemetry)
            assert result is not None
            assert 23 < result < 25  # ~24h left

    def test_hours_to_reset_fallback_to_file(self):
        """When telemetry doesn't have resets_at, read from file fallback."""
        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=12)
        cached_content = future.isoformat()
        
        with patch('metabolon.vasomotor._RESETS_AT_FILE') as mock_file:
            mock_file.read_text = lambda: cached_content
            result = _hours_to_reset(None)
            assert result is not None
            assert 11 < result < 13

    def test_hours_to_reset_returns_none_when_no_data(self):
        """When neither telemetry nor cached file has data, return None."""
        def raise_file_not_found():
            raise FileNotFoundError()
        with patch('metabolon.vasomotor._RESETS_AT_FILE') as mock_file:
            mock_file.read_text = raise_file_not_found
            result = _hours_to_reset(None)
            assert result is None

    def test_hours_to_reset_returns_min_half_hour(self):
        """Never returns less than 0.5 hours."""
        past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        telemetry = {
            "seven_day": {
                "resets_at": past.isoformat()
            }
        }
        
        with patch('metabolon.vasomotor._RESETS_AT_FILE') as mock_file:
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
        with patch('metabolon.vasomotor._fetch_telemetry', return_value=telemetry):
            snapshot = vasomotor_snapshot()
            assert snapshot == {"weekly": 45, "sonnet": 60}

    def test_vasomotor_snapshot_defaults_zero_when_missing(self):
        """When fields are missing, defaults to 0."""
        telemetry = {"seven_day": {}}
        with patch('metabolon.vasomotor._fetch_telemetry', return_value=telemetry):
            snapshot = vasomotor_snapshot()
            assert snapshot == {"weekly": 0, "sonnet": 0}

    def test_vasomotor_snapshot_returns_none_when_telemetry_none(self):
        """When telemetry fetch fails, returns None."""
        with patch('metabolon.vasomotor._fetch_telemetry', return_value=None):
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

        with patch('metabolon.vasomotor._load_circadian_state', return_value=empty_state):
            with patch('metabolon.vasomotor._save_circadian_state') as mock_save:
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

        with patch('metabolon.vasomotor._load_circadian_state', return_value=state):
            with patch('metabolon.vasomotor._save_circadian_state'):
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

        with patch('metabolon.vasomotor._load_circadian_state', return_value=empty_state):
            with patch('metabolon.vasomotor._save_circadian_state') as mock_save:
                breathe(saturated=False, wave_delta=0.5)
                saved_state = mock_save.call_args[0][0]
                assert saved_state["systole_deltas"] == [0.5]


class TestTidalVolume:
    """Tests for tidal_volume calculation blends interactive pressure."""

    def test_tidal_volume_reduces_with_high_pressure(self):
        """Higher interactive pressure reduces tidal volume (pulse share)."""
        from metabolon.vasomotor import tidal_volume

        with patch('metabolon.vasomotor.vasomotor_genome', return_value={
            'basal_rate': 0.5,
            'min_basal_rate': 0.15,
        }):
            with patch('metabolon.vasomotor.interactive_pressure', return_value=0.0):
                # 0 pressure → full basal rate
                assert tidal_volume() == pytest.approx(0.5)

            with patch('metabolon.vasomotor.interactive_pressure', return_value=1.0):
                # 1 pressure → min basal rate
                assert tidal_volume() == pytest.approx(0.15)

            with patch('metabolon.vasomotor.interactive_pressure', return_value=0.5):
                # 0.5 pressure → midpoint
                expected = 0.5 - 0.5 * (0.5 - 0.15)
                assert tidal_volume() == pytest.approx(expected)


class TestVasomotorGenome:
    """Tests for vasomotor_genome config reading."""

    def test_vasomotor_genome_returns_empty_dict_when_file_missing(self):
        """When config file doesn't exist, returns empty dict."""
        from metabolon.vasomotor import vasomotor_genome
        with patch('metabolon.vasomotor.CONF_PATH') as mock_path:
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
        with patch('metabolon.vasomotor.CONF_PATH') as mock_path:
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

        with patch('metabolon.vasomotor.SKIP_UNTIL_FILE') as mock_file:
            mock_file.read_text = raise_file_not_found
            apneic, reason = is_apneic()
            assert not apneic
            assert reason == ""

    def test_apneic_when_now_before_skip_until(self):
        """When current time is before skip_until, returns apneic."""
        from metabolon.vasomotor import is_apneic

        future = datetime.datetime.now() + datetime.timedelta(minutes=30)
        with patch('metabolon.vasomotor.SKIP_UNTIL_FILE') as mock_file:
            mock_file.read_text = lambda: future.isoformat()
            apneic, reason = is_apneic()
            assert apneic
            assert "skip_until" in reason
            assert "remaining" in reason

    def test_not_apneic_when_now_after_skip_until(self):
        """When current time is past skip_until, not apneic."""
        from metabolon.vasomotor import is_apneic

        past = datetime.datetime.now() - datetime.timedelta(minutes=10)
        with patch('metabolon.vasomotor.SKIP_UNTIL_FILE') as mock_file:
            mock_file.read_text = lambda: past.isoformat()
            apneic, reason = is_apneic()
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
        with patch('metabolon.vasomotor._load_circadian_state', return_value=circadian_state):
            with patch('metabolon.vasomotor.vasomotor_genome', return_value={}):
                cost = measured_cost_per_systole()
                assert cost == pytest.approx(0.4)

    def test_falls_back_to_default_when_few_samples_no_history(self):
        """When too few samples today and no historical data, uses default."""
        from metabolon.vasomotor import measured_cost_per_systole, DEFAULT_COST_PER_SYSTOLE

        circadian_state = {
            "systole_deltas": [0.0, 1.0],  # only 2 samples (<3 required)
        }
        with patch('metabolon.vasomotor._load_circadian_state', return_value=circadian_state):
            with patch('builtins.open', mock_open(read_data="")):
                with patch('metabolon.vasomotor.EVENT_LOG') as mock_log:
                    mock_log.read_text = lambda: ""
                    with patch('metabolon.vasomotor.vasomotor_genome', return_value={}):
                        cost = measured_cost_per_systole()
                        assert cost == DEFAULT_COST_PER_SYSTOLE

    def test_never_drops_below_minimum(self):
        """Average is never lower than 0.1 minimum."""
        from metabolon.vasomotor import measured_cost_per_systole

        circadian_state = {
            "systole_deltas": [0.0, 0.0, 0.0],  # average 0.0
        }
        with patch('metabolon.vasomotor._load_circadian_state', return_value=circadian_state):
            with patch('metabolon.vasomotor.vasomotor_genome', return_value={}):
                cost = measured_cost_per_systole()
                assert cost == 0.1  # clamped to minimum


# Run with: pytest assays/test_vasomotor_core.py -v
