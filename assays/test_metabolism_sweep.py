"""Tests for metabolon/metabolism/sweep.py."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.metabolism.fitness import Emotion
from metabolon.metabolism.sweep import (
    SelectionParameters,
    _load_conf,
    mutate,
    recombine,
    select,
)


class TestSelectionParameters:
    """Tests for SelectionParameters dataclass."""

    def test_default_values(self):
        """Test that dataclass defaults are correct."""
        params = SelectionParameters()
        assert params.min_phenotypes == 3
        assert params.max_retries == 3
        assert params.fitness_plateau == 0.8
        assert params.offspring_per_generation == 2

    def test_custom_values(self):
        """Test that custom values override defaults."""
        params = SelectionParameters(
            min_phenotypes=5,
            max_retries=10,
            fitness_plateau=0.5,
            offspring_per_generation=4,
        )
        assert params.min_phenotypes == 5
        assert params.max_retries == 10
        assert params.fitness_plateau == 0.5
        assert params.offspring_per_generation == 4


class TestLoadConf:
    """Tests for _load_conf function."""

    def test_load_conf_defaults_when_no_file(self):
        """Test that defaults are returned when config file doesn't exist."""
        with patch("metabolon.metabolism.sweep._CONF_PATH", Path("/nonexistent/path.conf")):
            cfg = _load_conf()
            assert cfg.getint("selection", "min_phenotypes") == 3
            assert cfg.getint("selection", "max_retries") == 3
            assert cfg.getfloat("selection", "fitness_plateau") == 0.8
            assert cfg.getint("selection", "offspring_per_generation") == 2

    def test_load_conf_merges_existing_file(self):
        """Test that existing config file overrides defaults."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("[selection]\n")
            f.write("min_phenotypes = 10\n")
            f.write("max_retries = 5\n")
            f.flush()
            conf_path = Path(f.name)

        try:
            with patch("metabolon.metabolism.sweep._CONF_PATH", conf_path):
                cfg = _load_conf()
                assert cfg.getint("selection", "min_phenotypes") == 10
                assert cfg.getint("selection", "max_retries") == 5
                # Unchanged values keep defaults
                assert cfg.getfloat("selection", "fitness_plateau") == 0.8
        finally:
            conf_path.unlink()


class TestSelect:
    """Tests for select function."""

    def test_select_empty_emotions(self):
        """Test with empty emotions dict."""
        result = select({})
        assert result == []

    def test_select_low_valence_only(self):
        """Test selection based on low valence."""
        emotions = {
            "tool_a": Emotion(
                tool="tool_a", activations=5, success_rate=0.9, metabolic_cost=1.0, valence=0.8
            ),
            "tool_b": Emotion(
                tool="tool_b", activations=5, success_rate=0.5, metabolic_cost=1.0, valence=0.4
            ),
        }
        result = select(emotions)
        # median is 0.6, tool_b has valence 0.4 < 0.6
        assert result == ["tool_b"]

    def test_select_none_valence_flagged(self):
        """Test that tools with None valence are flagged."""
        emotions = {
            "tool_a": Emotion(
                tool="tool_a", activations=5, success_rate=0.9, metabolic_cost=1.0, valence=0.8
            ),
            "tool_b": Emotion(
                tool="tool_b", activations=1, success_rate=0.5, metabolic_cost=1.0, valence=None
            ),
        }
        result = select(emotions)
        # tool_b has None valence (insufficient data)
        assert result == ["tool_b"]

    def test_select_combines_low_and_none_valence(self):
        """Test that both low and None valence tools are selected."""
        emotions = {
            "tool_a": Emotion(
                tool="tool_a", activations=5, success_rate=0.9, metabolic_cost=1.0, valence=0.9
            ),
            "tool_b": Emotion(
                tool="tool_b", activations=5, success_rate=0.4, metabolic_cost=1.0, valence=0.3
            ),
            "tool_c": Emotion(
                tool="tool_c", activations=1, success_rate=0.5, metabolic_cost=1.0, valence=None
            ),
        }
        result = select(emotions)
        # median of [0.9, 0.3] is 0.6, tool_b has valence 0.3 < 0.6, tool_c has None
        assert result == ["tool_b", "tool_c"]

    def test_select_all_above_median(self):
        """Test that tool below median is selected even with high valences."""
        emotions = {
            "tool_a": Emotion(
                tool="tool_a", activations=5, success_rate=0.9, metabolic_cost=1.0, valence=0.9
            ),
            "tool_b": Emotion(
                tool="tool_b", activations=5, success_rate=0.8, metabolic_cost=1.0, valence=0.8
            ),
        }
        result = select(emotions)
        # median is 0.85, tool_b has valence 0.8 < 0.85 so is selected
        assert result == ["tool_b"]

    def test_select_all_equal_valence(self):
        """Test that no tools selected when all valence equal to median."""
        emotions = {
            "tool_a": Emotion(
                tool="tool_a", activations=5, success_rate=0.9, metabolic_cost=1.0, valence=0.9
            ),
            "tool_b": Emotion(
                tool="tool_b", activations=5, success_rate=0.9, metabolic_cost=1.0, valence=0.9
            ),
        }
        result = select(emotions)
        # median is 0.9, both tools have valence 0.9 = median (not < median)
        assert result == []

    def test_select_result_sorted(self):
        """Test that result is sorted alphabetically."""
        emotions = {
            "zebra": Emotion(
                tool="zebra", activations=1, success_rate=0.5, metabolic_cost=1.0, valence=None
            ),
            "alpha": Emotion(
                tool="alpha", activations=1, success_rate=0.5, metabolic_cost=1.0, valence=None
            ),
        }
        result = select(emotions)
        assert result == ["alpha", "zebra"]


class TestRecombine:
    """Tests for recombine async function."""

    @pytest.mark.asyncio
    async def test_recombine_calls_transduce(self):
        """Test that recombine calls transduce with correct prompt."""
        with patch("metabolon.symbiont.transduce") as mock_transduce:
            mock_transduce.return_value = "  new description  "

            result = await recombine(
                tool="test_tool",
                parent_a="desc A",
                parent_b="desc B",
                reference_phenotype="current best",
            )

            assert result == "new description"
            mock_transduce.assert_called_once()
            call_args = mock_transduce.call_args
            assert call_args[0][0] == "glm"
            prompt = call_args[0][1]
            assert "test_tool" in prompt
            assert "desc A" in prompt
            assert "desc B" in prompt
            assert "current best" in prompt

    @pytest.mark.asyncio
    async def test_recombine_strips_whitespace(self):
        """Test that recombine strips whitespace from result."""
        with patch("metabolon.symbiont.transduce") as mock_transduce:
            mock_transduce.return_value = "\n  trimmed result  \n"

            result = await recombine(
                tool="tool",
                parent_a="a",
                parent_b="b",
                reference_phenotype="ref",
            )

            assert result == "trimmed result"


class TestMutate:
    """Tests for mutate async function."""

    @pytest.mark.asyncio
    async def test_mutate_calls_transduce(self):
        """Test that mutate calls transduce with correct prompt."""
        with patch("metabolon.symbiont.transduce") as mock_transduce:
            mock_transduce.return_value = "revised description"

            result = await mutate(
                tool="test_tool",
                description="original description",
                selection_pressure="low success rate",
            )

            assert result == "revised description"
            mock_transduce.assert_called_once()
            call_args = mock_transduce.call_args
            assert call_args[0][0] == "glm"
            prompt = call_args[0][1]
            assert "original description" in prompt
            assert "low success rate" in prompt

    @pytest.mark.asyncio
    async def test_mutate_strips_whitespace(self):
        """Test that mutate strips whitespace from result."""
        with patch("metabolon.symbiont.transduce") as mock_transduce:
            mock_transduce.return_value = "  \n  revised  \n  "

            result = await mutate(
                tool="tool",
                description="desc",
                selection_pressure="pressure",
            )

            assert result == "revised"


class TestSelectionParametersFromConf:
    """Tests for SelectionParameters.from_conf class method."""

    def test_from_conf_uses_defaults(self):
        """Test from_conf loads defaults when no config file."""
        with patch("metabolon.metabolism.sweep._CONF_PATH", Path("/nonexistent/path.conf")):
            params = SelectionParameters.from_conf()
            assert params.min_phenotypes == 3
            assert params.max_retries == 3
            assert params.fitness_plateau == 0.8
            assert params.offspring_per_generation == 2

    def test_from_conf_loads_custom_values(self):
        """Test from_conf loads custom values from config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("[selection]\n")
            f.write("min_phenotypes = 7\n")
            f.write("max_retries = 5\n")
            f.write("fitness_plateau = 0.6\n")
            f.write("offspring_per_generation = 4\n")
            f.flush()
            conf_path = Path(f.name)

        try:
            with patch("metabolon.metabolism.sweep._CONF_PATH", conf_path):
                params = SelectionParameters.from_conf()
                assert params.min_phenotypes == 7
                assert params.max_retries == 5
                assert params.fitness_plateau == 0.6
                assert params.offspring_per_generation == 4
        finally:
            conf_path.unlink()
