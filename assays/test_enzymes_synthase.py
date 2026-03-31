"""Tests for metabolon/enzymes/synthase.py — headless CC with full organism access."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import metabolon.enzymes.synthase as mod


# ── Constants ──────────────────────────────────────────────────────────────────


class TestChannel:
    def test_channel_path_under_home(self):
        assert mod.CHANNEL == str(Path.home() / "germline" / "effectors" / "channel")

    def test_timeout_value(self):
        assert mod._TIMEOUT == 300


# ── Tool metadata ──────────────────────────────────────────────────────────────


class TestToolMetadata:
    def test_tool_name(self):
        assert mod.synthase.name == "synthase"

    def test_tool_description_nonempty(self):
        assert isinstance(mod.synthase.description, str) and len(mod.synthase.description) > 0

    def test_tool_not_readonly(self):
        assert mod.synthase.annotations.readOnlyHint is False

    def test_tool_not_idempotent(self):
        assert mod.synthase.annotations.idempotentHint is False


# ── Model validation ──────────────────────────────────────────────────────────


class TestModelValidation:
    @pytest.mark.parametrize("bad_model", ["gpt4", "claude", "", "Sonnet", "HAIKU", "opus "])
    def test_invalid_model_raises(self, bad_model):
        with pytest.raises(ValueError, match="Unknown model"):
            mod.synthase(prompt="hello", model=bad_model)

    @pytest.mark.parametrize("valid_model", ["haiku", "sonnet", "opus"])
    def test_valid_models_accepted(self, valid_model):
        with patch.object(mod, "run_cli", return_value="ok"):
            result = mod.synthase(prompt="test", model=valid_model)
        assert result == "ok"


# ── run_cli delegation ─────────────────────────────────────────────────────────


class TestRunCliDelegation:
    def test_passes_organism_flag(self):
        with patch.object(mod, "run_cli", return_value="ok") as mock:
            mod.synthase(prompt="do stuff")
        assert "--organism" in mock.call_args[0][1]

    def test_passes_prompt_with_p_flag(self):
        with patch.object(mod, "run_cli", return_value="ok") as mock:
            mod.synthase(prompt="my prompt text")
        args = mock.call_args[0][1]
        p_idx = args.index("-p")
        assert args[p_idx + 1] == "my prompt text"

    def test_passes_channel_as_binary(self):
        with patch.object(mod, "run_cli", return_value="ok") as mock:
            mod.synthase(prompt="x")
        assert mock.call_args[0][0] == mod.CHANNEL

    def test_passes_timeout(self):
        with patch.object(mod, "run_cli", return_value="ok") as mock:
            mod.synthase(prompt="x")
        assert mock.call_args[1]["timeout"] == 300

    def test_model_is_first_arg(self):
        with patch.object(mod, "run_cli", return_value="ok") as mock:
            mod.synthase(prompt="x", model="opus")
        assert mock.call_args[0][1][0] == "opus"

    def test_default_model_is_sonnet(self):
        with patch.object(mod, "run_cli", return_value="sonnet result") as mock:
            result = mod.synthase(prompt="hello")
        assert result == "sonnet result"
        assert mock.call_args[0][1][0] == "sonnet"

    def test_returns_run_cli_output_verbatim(self):
        with patch.object(mod, "run_cli", return_value="  exact output  "):
            assert mod.synthase(prompt="x") == "  exact output  "

    def test_full_arg_order(self):
        """Args list should be: [model, '--organism', '-p', prompt]."""
        with patch.object(mod, "run_cli", return_value="ok") as mock:
            mod.synthase(prompt="hello world", model="haiku")
        args = mock.call_args[0][1]
        assert args == ["haiku", "--organism", "-p", "hello world"]


# ── Error propagation ─────────────────────────────────────────────────────────


class TestErrorPropagation:
    def test_binary_not_found_propagates(self):
        with patch.object(mod, "run_cli", side_effect=ValueError("Binary not found")):
            with pytest.raises(ValueError, match="Binary not found"):
                mod.synthase(prompt="x")

    def test_timeout_propagates(self):
        with patch.object(mod, "run_cli", side_effect=ValueError("timed out")):
            with pytest.raises(ValueError, match="timed out"):
                mod.synthase(prompt="x")

    def test_process_error_propagates(self):
        with patch.object(mod, "run_cli", side_effect=ValueError("error: boom")):
            with pytest.raises(ValueError, match="boom"):
                mod.synthase(prompt="x")
