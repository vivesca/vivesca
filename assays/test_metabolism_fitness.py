from __future__ import annotations

import math
from metabolon.metabolism.fitness import Emotion, sense_affect
from metabolon.metabolism.signals import Stimulus, Outcome


def test_empty_stimuli():
    """Test sense_affect returns empty dict when given no stimuli."""
    result = sense_affect([])
    assert result == {}


def test_single_stimulus_below_min():
    """Test valence is None when fewer than min_stimuli."""
    stimulus = Stimulus(
        tool="test_tool",
        outcome=Outcome.success,
        substrate_consumed=10,
        product_released=20,
    )
    result = sense_affect([stimulus], min_stimuli=3)
    assert "test_tool" in result
    emotion = result["test_tool"]
    assert emotion.activations == 1
    assert emotion.success_rate == 1.0
    assert emotion.metabolic_cost == (10 + 20) / 1 == 30.0
    assert emotion.valence is None


def test_multiple_stimuli_all_success():
    """Test all successes with various costs."""
    stimuli = [
        Stimulus(tool="tool1", outcome=Outcome.success, substrate_consumed=0, product_released=10),
        Stimulus(tool="tool1", outcome=Outcome.success, substrate_consumed=0, product_released=10),
        Stimulus(tool="tool1", outcome=Outcome.success, substrate_consumed=0, product_released=10),
    ]
    result = sense_affect(stimuli, min_stimuli=3)
    emotion = result["tool1"]
    assert emotion.activations == 3
    assert emotion.success_rate == 1.0
    assert emotion.metabolic_cost == 10.0  # (0+10) *3 /3 = 10
    # valence = 1.0 * (1/log2(10+2)) = 1/log2(12) ≈ 1 / 3.58496 ≈ 0.2789
    expected_valence = 1.0 * (1.0 / math.log2(10 + 2))
    assert abs(emotion.valence - expected_valence) < 1e-6


def test_mixed_success_and_failure():
    """Test mixed outcomes calculate correct success_rate."""
    stimuli = [
        Stimulus(tool="tool2", outcome=Outcome.success, substrate_consumed=5, product_released=5),
        Stimulus(tool="tool2", outcome=Outcome.error, substrate_consumed=5, product_released=0),
        Stimulus(tool="tool2", outcome=Outcome.success, substrate_consumed=5, product_released=5),
        Stimulus(tool="tool2", outcome=Outcome.correction, substrate_consumed=10, product_released=0),
    ]
    result = sense_affect(stimuli, min_stimuli=3)
    emotion = result["tool2"]
    assert emotion.activations == 4
    assert emotion.success_rate == 0.5  # 2/4
    avg_cost = ((5+5) + (5+0) + (5+5) + (10+0)) / 4
    assert emotion.metabolic_cost == avg_cost
    assert emotion.valence is not None
    expected_valence = 0.5 * (1.0 / math.log2(avg_cost + 2))
    assert abs(emotion.valence - expected_valence) < 1e-6


def test_zero_metabolic_cost():
    """Test zero cost doesn't break log calculation (adds +2 safety)."""
    stimuli = [
        Stimulus(tool="free_tool", outcome=Outcome.success),
        Stimulus(tool="free_tool", outcome=Outcome.success),
        Stimulus(tool="free_tool", outcome=Outcome.success),
    ]
    result = sense_affect(stimuli, min_stimuli=3)
    emotion = result["free_tool"]
    assert emotion.metabolic_cost == 0.0
    assert emotion.valence == 1.0 * (1.0 / math.log2(0 + 2))  # log2(2) = 1, so valence = 1.0
    assert abs(emotion.valence - 1.0) < 1e-6


def test_multiple_enzymes():
    """Test correct grouping by enzyme tool name."""
    stimuli = [
        Stimulus(tool="tool_a", outcome=Outcome.success),
        Stimulus(tool="tool_b", outcome=Outcome.error),
        Stimulus(tool="tool_a", outcome=Outcome.success),
        Stimulus(tool="tool_b", outcome=Outcome.success),
        Stimulus(tool="tool_a", outcome=Outcome.success),
    ]
    result = sense_affect(stimuli, min_stimuli=3)
    assert len(result) == 2
    assert "tool_a" in result
    assert "tool_b" in result

    emotion_a = result["tool_a"]
    assert emotion_a.activations == 3
    assert emotion_a.success_rate == 1.0
    assert emotion_a.valence is not None

    emotion_b = result["tool_b"]
    assert emotion_b.activations == 2
    assert emotion_b.success_rate == 0.5
    assert emotion_b.valence is None
