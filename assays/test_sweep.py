"""Tests for weekly DE sweep."""

from metabolon.metabolism.fitness import Emotion
from metabolon.metabolism.sweep import SelectionParameters, select


def test_select_below_median():
    emotions = {
        "a": Emotion("a", 10, 0.9, 100.0, 0.9),
        "b": Emotion("b", 10, 0.5, 200.0, 0.3),
        "c": Emotion("c", 10, 0.8, 150.0, 0.6),
    }
    candidates = select(emotions)
    assert "b" in candidates  # lowest valence
    assert "a" not in candidates  # highest valence


def test_select_includes_zero_invocations():
    emotions = {
        "a": Emotion("a", 10, 0.9, 100.0, 0.9),
        "b": Emotion("b", 0, 0.0, 0.0, None),
    }
    candidates = select(emotions)
    assert "b" in candidates  # zero activations = drift


def test_select_skips_insufficient_data():
    emotions = {
        "a": Emotion("a", 10, 0.9, 100.0, 0.9),
        "b": Emotion("b", 2, 0.5, 100.0, None),  # None = insufficient
    }
    candidates = select(emotions)
    # b has None valence — flagged as drift candidate
    assert "b" in candidates


def test_sweep_config_defaults():
    cfg = SelectionParameters()
    assert cfg.min_phenotypes == 3
    assert cfg.max_retries == 3
    assert cfg.fitness_plateau == 0.8
