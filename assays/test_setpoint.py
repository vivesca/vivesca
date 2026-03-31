from __future__ import annotations

"""Tests for autonomic thresholds."""


import pytest

from metabolon.metabolism.setpoint import Threshold


def test_default_when_no_data(tmp_path, monkeypatch):
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    sp = Threshold(name="test", default=15.0)
    assert sp.read() == 15.0


def test_acclimatises_after_min_samples(tmp_path, monkeypatch):
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    sp = Threshold(name="test", default=15.0, clamp=(5, 50), min_samples=2)

    # First observation — not enough to acclimatise
    sp.record(prior_load=20.0, post_response=30.0)
    assert sp.read() == 15.0  # still default

    # Second observation — acclimatises to average of before values
    sp.record(prior_load=24.0, post_response=35.0)
    assert sp.read() == 22.0  # avg(20, 24)


def test_clamp_prevents_drift(tmp_path, monkeypatch):
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    sp = Threshold(name="test", default=15.0, clamp=(10, 30), min_samples=2)

    sp.record(prior_load=50.0, post_response=60.0)
    sp.record(prior_load=50.0, post_response=60.0)
    assert sp.read() == 30.0  # clamped to max


def test_status_reports_acclimatisation(tmp_path, monkeypatch):
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    sp = Threshold(name="test", default=15.0, min_samples=2)

    status = sp.status()
    assert not status.acclimatised
    assert status.observations == 0

    sp.record(prior_load=20.0, post_response=30.0)
    sp.record(prior_load=20.0, post_response=30.0)
    status = sp.status()
    assert status.acclimatised
    assert status.observations == 2


def test_window_limits_observations(tmp_path, monkeypatch):
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    sp = Threshold(name="test", default=15.0, clamp=(5, 50), window=3, min_samples=2)

    # Old observations that should fall out of window
    sp.record(prior_load=10.0, post_response=20.0)
    sp.record(prior_load=10.0, post_response=20.0)
    sp.record(prior_load=10.0, post_response=20.0)
    assert sp.read() == 10.0

    # New observations shift the window
    sp.record(prior_load=30.0, post_response=40.0)
    sp.record(prior_load=30.0, post_response=40.0)
    sp.record(prior_load=30.0, post_response=40.0)
    assert sp.read() == 30.0  # old 10s fell out of window=3


# ---------------------------------------------------------------------------
# Bistable switch — hysteresis tests
# The lac operon and CDK1/Cdc25 patterns: separate activation and
# deactivation thresholds create a dead-band that prevents oscillation
# at the switching boundary.
# ---------------------------------------------------------------------------


def test_no_hysteresis_is_binary(tmp_path, monkeypatch):
    """Without hysteresis the gate is a simple comparator — original behaviour."""
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    sp = Threshold(name="test", default=10.0)  # hysteresis=0 by default

    assert sp.activation_threshold == 10.0
    assert sp.deactivation_threshold == 10.0

    # Crosses above threshold → opens
    assert sp.is_activated(11.0) is True
    # Drops to threshold value → still open (value >= activation pole only at exactly 10)
    assert sp.is_activated(10.0) is True
    # Drops below threshold → closes immediately (no dead-band)
    assert sp.is_activated(9.9) is False


def test_hysteresis_keeps_gate_open_inside_dead_band(tmp_path, monkeypatch):
    """Gate stays open inside the dead-band — bistable latch behaviour."""
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    # activation=10.0, hysteresis=0.3 → deactivation=7.0
    sp = Threshold(name="test", default=10.0, hysteresis=0.3)

    assert sp.activation_threshold == pytest.approx(10.0)
    assert sp.deactivation_threshold == pytest.approx(7.0)

    # Rise above activation pole → gate opens
    assert sp.is_activated(12.0) is True
    # Value drops into dead-band (7.0 < value < 10.0) — gate must stay open
    assert sp.is_activated(8.5) is True
    # Value reaches exactly deactivation threshold — still open (> deactivate is False now)
    assert sp.is_activated(7.0) is True
    # Value falls below deactivation pole → gate closes
    assert sp.is_activated(6.9) is False


def test_hysteresis_keeps_gate_closed_inside_dead_band(tmp_path, monkeypatch):
    """Gate stays closed inside the dead-band when approaching from below."""
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    # activation=10.0, hysteresis=0.3 → deactivation=7.0
    sp = Threshold(name="test", default=10.0, hysteresis=0.3)

    # Start below both thresholds → gate is closed
    assert sp.is_activated(5.0) is False
    # Rise into dead-band (7 <= value < 10) — gate must stay closed
    assert sp.is_activated(8.5) is False
    # Cross activation pole → gate opens
    assert sp.is_activated(10.0) is True


def test_hysteresis_prevents_oscillation_at_boundary(tmp_path, monkeypatch):
    """Rapid toggling near a single threshold is silenced by the dead-band."""
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    # Without hysteresis a value hovering at 10 would flip with every call.
    # With hysteresis=0.3 (dead-band 7-10) it stays in its current state.
    sp = Threshold(name="test", default=10.0, hysteresis=0.3)

    # Open the gate first
    sp.is_activated(11.0)
    assert sp._gate_open is True

    # Rapid oscillation at activation boundary — must not flip
    for _ in range(5):
        assert sp.is_activated(9.8) is True  # inside dead-band, stays open
        assert sp.is_activated(10.2) is True  # above activation, stays open


def test_hysteresis_example_from_spec(tmp_path, monkeypatch):
    """Reproduces the concrete example from the task specification.

    activation=0.7, deactivation=0.5 (hysteresis = 1 - 0.5/0.7 ≈ 0.2857).
    A value at 0.65 must keep its previous state.
    """
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    hysteresis = 1.0 - (0.5 / 0.7)  # ≈ 0.2857
    sp = Threshold(name="test", default=0.7, hysteresis=hysteresis)

    assert sp.activation_threshold == pytest.approx(0.7)
    assert sp.deactivation_threshold == pytest.approx(0.5, abs=1e-9)

    # Gate closed; value at 0.65 (inside dead-band) — should stay closed
    sp.is_activated(0.4)  # below deactivation — start closed
    assert sp.is_activated(0.65) is False  # dead-band, closed state preserved

    # Now open the gate and verify 0.65 keeps it open
    sp.is_activated(0.75)  # above activation — open
    assert sp.is_activated(0.65) is True  # dead-band, open state preserved


def test_refractory_gate_clears_latch(tmp_path, monkeypatch):
    """refractory_gate() discards the in-memory latch for fresh evaluation."""
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    sp = Threshold(name="test", default=10.0, hysteresis=0.3)

    sp.is_activated(15.0)  # open
    assert sp._gate_open is True

    sp.refractory_gate()
    assert sp._gate_open is None

    # Next evaluation initialises from current signal (8.0 < activation 10 → closed)
    assert sp.is_activated(8.0) is False


def test_status_includes_hysteresis_metadata(tmp_path, monkeypatch):
    """SetpointStatus carries bistable switch metadata."""
    monkeypatch.setattr("metabolon.metabolism.setpoint.SETPOINTS_DIR", tmp_path)
    sp = Threshold(name="test", default=20.0, hysteresis=0.25)

    sp.is_activated(25.0)  # open the gate
    status = sp.status()

    assert status.hysteresis == pytest.approx(0.25)
    assert status.activation_threshold == pytest.approx(20.0)
    assert status.deactivation_threshold == pytest.approx(15.0)
    assert status.gate_open is True


def test_invalid_hysteresis_raises():
    """Hysteresis must be in [0, 1) — reject values that invert the thresholds."""
    with pytest.raises(ValueError, match="hysteresis"):
        Threshold(name="test", default=10.0, hysteresis=1.0)
    with pytest.raises(ValueError, match="hysteresis"):
        Threshold(name="test", default=10.0, hysteresis=-0.1)
