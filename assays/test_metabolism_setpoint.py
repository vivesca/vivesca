from __future__ import annotations

"""Tests for metabolon.metabolism.setpoint — autonomic thresholds with calibration."""

import json
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.metabolism.setpoint import SETPOINTS_DIR, SetpointStatus, Threshold


# ── helpers ──────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect SETPOINTS_DIR to a temp directory for every test."""
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    return tmp_path


def _make_threshold(tmp_dir: Path, **kw) -> Threshold:
    """Create a Threshold whose store lives under *tmp_dir*."""
    t = Threshold(**kw)
    # Point persistence paths at the temp directory
    t._state_store = tmp_dir / f"{t.name}.json"
    t._events = tmp_dir / f"{t.name}-events.jsonl"
    return t


def _write_events(events_path: Path, events: list[dict]) -> None:
    """Append JSONL event records."""
    with events_path.open("a") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


# ── __init__ / validation ────────────────────────────────────────────


class TestInit:
    def test_default_attributes(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="disk", default=15.0)
        assert t.name == "disk"
        assert t.default == 15.0
        assert t.clamp == (0.0, 1000.0)
        assert t.window == 5
        assert t.min_samples == 2
        assert t.hysteresis == 0.0
        assert t._gate_open is None

    def test_custom_attributes(self, tmp_dir: Path):
        t = _make_threshold(
            tmp_dir,
            name="cpu",
            default=80.0,
            clamp=(10.0, 100.0),
            window=3,
            min_samples=1,
            hysteresis=0.3,
        )
        assert t.clamp == (10.0, 100.0)
        assert t.window == 3
        assert t.min_samples == 1
        assert t.hysteresis == 0.3

    def test_hysteresis_zero_ok(self, tmp_dir: Path):
        _make_threshold(tmp_dir, name="x", default=5, hysteresis=0.0)

    def test_hysteresis_rejects_negative(self):
        with pytest.raises(ValueError, match="hysteresis must be in"):
            Threshold(name="x", default=5, hysteresis=-0.1)

    def test_hysteresis_rejects_one(self):
        with pytest.raises(ValueError, match="hysteresis must be in"):
            Threshold(name="x", default=5, hysteresis=1.0)

    def test_hysteresis_rejects_above_one(self):
        with pytest.raises(ValueError, match="hysteresis must be in"):
            Threshold(name="x", default=5, hysteresis=1.5)


# ── read() ───────────────────────────────────────────────────────────


class TestRead:
    def test_returns_default_when_no_file(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="disk", default=15.0)
        assert t.read() == 15.0

    def test_reads_persisted_value(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="disk", default=15.0)
        t._state_store.write_text(json.dumps({"value": 22.5}))
        assert t.read() == 22.5

    def test_returns_default_on_corrupt_file(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="disk", default=15.0)
        t._state_store.write_text("NOT JSON!!!")
        assert t.read() == 15.0

    def test_returns_default_when_missing_key(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="disk", default=15.0)
        t._state_store.write_text(json.dumps({"other": 99}))
        assert t.read() == 15.0


# ── activation / deactivation thresholds ─────────────────────────────


class TestThresholdPoles:
    def test_activation_equals_read(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=20.0)
        t._state_store.write_text(json.dumps({"value": 30.0}))
        assert t.activation_threshold == 30.0

    def test_deactivation_no_hysteresis(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=20.0, hysteresis=0.0)
        assert t.deactivation_threshold == 20.0

    def test_deactivation_with_hysteresis(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=100.0, hysteresis=0.25)
        assert t.activation_threshold == 100.0
        assert t.deactivation_threshold == 75.0

    def test_deactivation_with_persisted_value(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=100.0, hysteresis=0.25)
        t._state_store.write_text(json.dumps({"value": 80.0}))
        assert t.activation_threshold == 80.0
        assert t.deactivation_threshold == 60.0


# ── is_activated — bistable gate ─────────────────────────────────────


class TestIsActivated:
    def test_binary_above_activates(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0)
        assert t.is_activated(15.0) is True

    def test_binary_below_does_not(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0)
        assert t.is_activated(5.0) is False

    def test_binary_exact_activates(self, tmp_dir: Path):
        """value == threshold counts as activated (>=)."""
        t = _make_threshold(tmp_dir, name="x", default=10.0)
        assert t.is_activated(10.0) is True

    def test_hysteresis_stays_open_in_dead_band(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=100.0, hysteresis=0.25)
        # activation=100, deactivation=75
        assert t.is_activated(110.0) is True  # open gate
        assert t.is_activated(80.0) is True  # in dead-band → stays open

    def test_hysteresis_closes_below_deactivation(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=100.0, hysteresis=0.25)
        # activation=100, deactivation=75
        assert t.is_activated(110.0) is True  # open
        assert t.is_activated(70.0) is False  # below deactivation → close

    def test_hysteresis_stays_closed_in_dead_band(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=100.0, hysteresis=0.25)
        # activation=100, deactivation=75
        assert t.is_activated(60.0) is False  # closed
        assert t.is_activated(80.0) is False  # in dead-band → stays closed

    def test_hysteresis_opens_at_activation(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=100.0, hysteresis=0.25)
        assert t.is_activated(60.0) is False
        assert t.is_activated(100.0) is True  # at activation → open

    def test_refractory_gate_resets(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0)
        t.is_activated(15.0)
        assert t._gate_open is True
        t.refractory_gate()
        assert t._gate_open is None

    def test_first_eval_below_stays_closed(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=50.0)
        assert t.is_activated(30.0) is False
        assert t._gate_open is False

    def test_first_eval_above_opens(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=50.0)
        assert t.is_activated(60.0) is True
        assert t._gate_open is True


# ── record() ─────────────────────────────────────────────────────────


class TestRecord:
    def test_appends_event(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0)
        with patch("metabolon.metabolism.setpoint.datetime") as mock_dt:
            mock_dt.now.return_value.isoformat.return_value = "2026-01-01T00:00:00"
            t.record(prior_load=20.0, post_response=10.0)

        lines = t._events.read_text().strip().splitlines()
        assert len(lines) == 1
        ev = json.loads(lines[0])
        assert ev["before"] == 20.0
        assert ev["after"] == 10.0
        assert ev["ts"] == "2026-01-01T00:00:00"

    def test_extra_kwargs_in_event(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0)
        with patch("metabolon.metabolism.setpoint.datetime") as mock_dt:
            mock_dt.now.return_value.isoformat.return_value = "2026-01-01T00:00:00"
            t.record(prior_load=20.0, post_response=10.0, action="clean_disk")

        ev = json.loads(t._events.read_text().strip())
        assert ev["action"] == "clean_disk"

    def test_triggers_acclimatisation(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0, window=3, min_samples=2)
        # Pre-seed 1 event so the record adds a 2nd → triggers acclimatisation
        _write_events(t._events, [{"before": 12.0, "after": 8.0}])
        with patch("metabolon.metabolism.setpoint.datetime") as mock_dt:
            mock_dt.now.return_value.isoformat.return_value = "2026-01-01T00:00:00"
            t.record(prior_load=18.0, post_response=9.0)

        # Acclimatised value = mean(12.0, 18.0) = 15.0
        data = json.loads(t._state_store.read_text())
        assert data["value"] == 15.0


# ── _acclimatise() ───────────────────────────────────────────────────


class TestAcclimatise:
    def test_no_change_below_min_samples(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0, min_samples=3)
        _write_events(t._events, [{"before": 20.0}, {"before": 25.0}])
        t._acclimatise()
        # File should not exist — no write happened
        assert not t._state_store.exists()

    def test_adapts_to_mean(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0, window=5, min_samples=2)
        _write_events(
            t._events,
            [{"before": 10.0}, {"before": 20.0}, {"before": 30.0}],
        )
        t._acclimatise()
        assert t.read() == 20.0  # mean(10,20,30)

    def test_respects_window(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0, window=2, min_samples=2)
        _write_events(
            t._events,
            [{"before": 100.0}, {"before": 10.0}, {"before": 20.0}],
        )
        t._acclimatise()
        # Only last 2 → mean(10,20)=15.0
        assert t.read() == 15.0

    def test_clamps_lower(self, tmp_dir: Path):
        t = _make_threshold(
            tmp_dir, name="x", default=10.0, clamp=(5.0, 100.0), min_samples=1
        )
        _write_events(t._events, [{"before": 1.0}])
        t._acclimatise()
        assert t.read() == 5.0

    def test_clamps_upper(self, tmp_dir: Path):
        t = _make_threshold(
            tmp_dir, name="x", default=10.0, clamp=(0.0, 50.0), min_samples=1
        )
        _write_events(t._events, [{"before": 200.0}])
        t._acclimatise()
        assert t.read() == 50.0

    def test_ignores_corrupt_events_file(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0, min_samples=1)
        t._events.write_text("BAD LINE\n")
        t._acclimatise()
        # Should not crash; no state file written
        assert not t._state_store.exists()

    def test_skips_events_without_before_key(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0, min_samples=2)
        _write_events(t._events, [{"after": 5.0}, {"before": 20.0}])
        t._acclimatise()
        assert not t._state_store.exists()

    def test_rounds_to_one_decimal(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0, min_samples=2)
        _write_events(t._events, [{"before": 10.0}, {"before": 15.0}])
        t._acclimatise()
        assert t.read() == 12.5

    def test_rounds_third_decimal(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0, min_samples=3)
        _write_events(t._events, [{"before": 10.0}, {"before": 11.0}, {"before": 12.0}])
        t._acclimatise()
        assert t.read() == 11.0


# ── _write() ─────────────────────────────────────────────────────────


class TestWrite:
    def test_writes_json(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0)
        with patch("metabolon.metabolism.setpoint.date") as mock_date:
            mock_date.today.return_value.isoformat.return_value = "2026-04-01"
            t._write(25.0, "test reason")

        data = json.loads(t._state_store.read_text())
        assert data["value"] == 25.0
        assert data["reason"] == "test reason"
        assert data["updated"] == "2026-04-01"

    def test_creates_setpoints_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        new_dir = tmp_path / "setpoints"
        monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", new_dir)
        t = Threshold(name="x", default=10.0)
        assert not new_dir.exists()
        t._write(5.0, "init")
        assert new_dir.is_dir()
        assert json.loads((new_dir / "x.json").read_text())["value"] == 5.0


# ── status() ─────────────────────────────────────────────────────────


class TestStatus:
    def test_returns_setpoint_status(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="disk", default=15.0, hysteresis=0.2)
        t.is_activated(10.0)  # initialise gate
        s = t.status()
        assert isinstance(s, SetpointStatus)
        assert s.name == "disk"
        assert s.value == 15.0
        assert s.default == 15.0
        assert s.observations == 0
        assert s.acclimatised is False
        assert s.hysteresis == 0.2
        assert s.activation_threshold == 15.0
        assert s.deactivation_threshold == pytest.approx(12.0)
        assert s.gate_open is False

    def test_counts_events(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="x", default=10.0, min_samples=2)
        _write_events(
            t._events,
            [{"before": 10.0}, {"before": 20.0}, {"before": 30.0}],
        )
        s = t.status()
        assert s.observations == 3
        assert s.acclimatised is True

    def test_zero_events_when_no_file(self, tmp_dir: Path):
        t = _make_threshold(tmp_dir, name="y", default=5.0)
        s = t.status()
        assert s.observations == 0
        assert s.acclimatised is False


# ── SetpointStatus model ────────────────────────────────────────────


class TestSetpointStatusModel:
    def test_defaults(self):
        s = SetpointStatus(
            name="x", value=10.0, default=10.0, observations=0, acclimatised=False
        )
        assert s.hysteresis == 0.0
        assert s.activation_threshold is None
        assert s.deactivation_threshold is None
        assert s.gate_open is None

    def test_serializable(self):
        s = SetpointStatus(
            name="x",
            value=10.0,
            default=10.0,
            observations=5,
            acclimatised=True,
            hysteresis=0.1,
            activation_threshold=10.0,
            deactivation_threshold=9.0,
            gate_open=True,
        )
        d = s.model_dump()
        assert d["name"] == "x"
        assert d["gate_open"] is True
        json_str = s.model_dump_json()
        assert "x" in json_str
