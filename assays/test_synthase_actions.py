"""Tests for metabolon.enzymes.synthase — headless CC enzyme."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import metabolon.enzymes.synthase as mod


# ── Module constants ────────────────────────────────────────────────────────


class TestConstants:
    def test_channel_path(self):
        """CHANNEL should point to ~/germline/effectors/channel."""
        assert mod.CHANNEL == str(Path.home() / "germline" / "effectors" / "channel")

    def test_timeout_value(self):
        """_TIMEOUT should be 300 seconds."""
        assert mod._TIMEOUT == 300


# ── Model validation ───────────────────────────────────────────────────────


class TestModelValidation:
    @pytest.mark.parametrize("model", ["gpt4", "claude", "GPT", "", "haiku "])
    def test_invalid_model_raises(self, model):
        """Should reject unknown model names."""
        with pytest.raises(ValueError, match="Unknown model"):
            mod.synthase(prompt="hello", model=model)

    @pytest.mark.parametrize("model", ["haiku", "sonnet", "opus"])
    def test_valid_models_accepted(self, model):
        """Should accept all three valid model names."""
        with patch("metabolon.enzymes.synthase.run_cli", return_value="ok"):
            result = mod.synthase(prompt="test", model=model)
        assert result == "ok"


# ── run_cli call structure ─────────────────────────────────────────────────


class TestRunCliCall:
    def test_args_include_model(self):
        """Args list should start with the model name."""
        with patch("metabolon.enzymes.synthase.run_cli", return_value="ok") as mock:
            mod.synthase(prompt="do it", model="haiku")
        args_list = mock.call_args[0][1]
        assert args_list[0] == "haiku"

    def test_args_include_organism_flag(self):
        """Args list should contain --organism."""
        with patch("metabolon.enzymes.synthase.run_cli", return_value="ok") as mock:
            mod.synthase(prompt="do it")
        args_list = mock.call_args[0][1]
        assert "--organism" in args_list

    def test_args_include_prompt_flag(self):
        """Args list should contain -p followed by the prompt."""
        with patch("metabolon.enzymes.synthase.run_cli", return_value="ok") as mock:
            mod.synthase(prompt="my task")
        args_list = mock.call_args[0][1]
        assert "-p" in args_list
        assert args_list[-1] == "my task"

    def test_full_args_structure(self):
        """Args should be [model, --organism, -p, prompt]."""
        with patch("metabolon.enzymes.synthase.run_cli", return_value="ok") as mock:
            mod.synthase(prompt="hello world", model="opus")
        binary = mock.call_args[0][0]
        args = mock.call_args[0][1]
        assert binary == mod.CHANNEL
        assert args == ["opus", "--organism", "-p", "hello world"]

    def test_timeout_passed_as_keyword(self):
        """timeout=300 should be passed as keyword argument to run_cli."""
        with patch("metabolon.enzymes.synthase.run_cli", return_value="ok") as mock:
            mod.synthase(prompt="x")
        assert mock.call_args.kwargs["timeout"] == 300

    def test_default_model_is_sonnet(self):
        """When model is not specified, sonnet should be used."""
        with patch("metabolon.enzymes.synthase.run_cli", return_value="ok") as mock:
            mod.synthase(prompt="hi")
        assert mock.call_args[0][1][0] == "sonnet"


# ── Return value and error propagation ─────────────────────────────────────


class TestReturnAndErrors:
    def test_return_value_passthrough(self):
        """Should return whatever run_cli returns."""
        with patch("metabolon.enzymes.synthase.run_cli", return_value="Done."):
            assert mod.synthase(prompt="x") == "Done."

    def test_run_cli_valueerror_propagates(self):
        """ValueError from run_cli should bubble up (binary not found, etc)."""
        with patch(
            "metabolon.enzymes.synthase.run_cli",
            side_effect=ValueError("Binary not found"),
        ):
            with pytest.raises(ValueError, match="Binary not found"):
                mod.synthase(prompt="x")

    def test_run_cli_timeout_propagates(self):
        """Timeout errors from run_cli should propagate as ValueError."""
        with patch(
            "metabolon.enzymes.synthase.run_cli",
            side_effect=ValueError("channel timed out"),
        ):
            with pytest.raises(ValueError, match="timed out"):
                mod.synthase(prompt="x")

    def test_run_cli_error_propagates(self):
        """CalledProcessError wrapping from run_cli should propagate."""
        with patch(
            "metabolon.enzymes.synthase.run_cli",
            side_effect=ValueError("channel error: something failed"),
        ):
            with pytest.raises(ValueError, match="something failed"):
                mod.synthase(prompt="x")
