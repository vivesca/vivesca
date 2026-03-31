from __future__ import annotations

"""Tests for fitness computation."""

import pytest

from metabolon.metabolism.fitness import sense_affect
from metabolon.metabolism.signals import Outcome, Stimulus


def _signal(tool: str, outcome: str | Outcome, tokens: int = 100) -> Stimulus:
    return Stimulus(
        tool=tool,
        outcome=Outcome(outcome),
        substrate_consumed=tokens,
        product_released=tokens,
        response_latency=100,
    )


def test_perfect_fitness():
    signals = [_signal("t", "success") for _ in range(10)]
    result = sense_affect(signals)
    assert "t" in result
    assert result["t"].success_rate == 1.0
    assert result["t"].activations == 10


def test_mixed_outcomes():
    signals = [
        _signal("t", "success"),
        _signal("t", "success"),
        _signal("t", "error"),
    ]
    result = sense_affect(signals)
    assert result["t"].success_rate == pytest.approx(2 / 3, rel=0.01)
    assert result["t"].activations == 3


def test_multiple_tools():
    signals = [
        _signal("a", "success"),
        _signal("b", "error"),
        _signal("a", "success"),
    ]
    result = sense_affect(signals)
    assert len(result) == 2
    assert result["a"].success_rate == 1.0
    assert result["b"].success_rate == 0.0


def test_token_efficiency_rewards_parsimony():
    cheap = [_signal("a", "success", tokens=50) for _ in range(5)]
    expensive = [_signal("b", "success", tokens=5000) for _ in range(5)]
    result = sense_affect(cheap + expensive)
    assert result["a"].valence is not None
    assert result["b"].valence is not None
    assert result["a"].valence > result["b"].valence


def test_empty_signals():
    result = sense_affect([])
    assert result == {}


def test_minimum_signal_threshold():
    """Tools with < min_stimuli get valence=None."""

    signals = [_signal("t", "success"), _signal("t", "success")]
    result = sense_affect(signals, min_stimuli=3)
    assert result["t"].valence is None
