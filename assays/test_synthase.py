#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/synthase — Slim LLM CLI routing through channel.

Synthase is a script (effectors/synthase), not an importable module.
It is loaded via exec() into isolated namespaces.
"""


import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

SYNTHASE_PATH = Path(__file__).resolve().parents[1] / "effectors" / "synthase"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def synth(tmp_path):
    """Load synthase via exec into an isolated namespace dict."""
    ns: dict = {"__name__": "test_synthase", "__doc__": ""}
    source = SYNTHASE_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    # Redirect config path to tmp_path so tests don't read real config
    config_path = str(tmp_path / "config.yaml")
    ns["CONFIG_PATH"] = config_path
    return ns


# ── _load_config ────────────────────────────────────────────────────────────


class TestLoadConfig:
    def test_config_exists_with_llm_section(self, synth):
        """Should return llm section when config has it."""
        mock_yaml = {"llm": {"default_model": "sonnet"}}
        config_path = synth["CONFIG_PATH"]
        with patch("builtins.open", mock_open(read_data="llm:\n  default_model: sonnet\n")):
            with patch("yaml.safe_load", return_value=mock_yaml):
                cfg = synth["_load_config"]()
        assert cfg == {"default_model": "sonnet"}

    def test_config_not_found(self, synth):
        """Should return empty dict when config file not found."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            cfg = synth["_load_config"]()
        assert cfg == {}

    def test_config_empty_yaml(self, synth):
        """Should return empty dict when YAML is None."""
        with patch("builtins.open", mock_open(read_data="")):
            with patch("yaml.safe_load", return_value=None):
                cfg = synth["_load_config"]()
        assert cfg == {}

    def test_config_no_llm_key(self, synth):
        """Should return empty dict when config has no llm key."""
        with patch("builtins.open", mock_open(read_data="other: true\n")):
            with patch("yaml.safe_load", return_value={"other": True}):
                cfg = synth["_load_config"]()
        assert cfg == {}

    def test_config_read_error(self, synth, capsys):
        """Should return empty dict and print warning on read errors."""
        with patch("builtins.open", side_effect=PermissionError("denied")):
            cfg = synth["_load_config"]()
        assert cfg == {}
        err = capsys.readouterr().err
        assert "Warning" in err


# ── _which ──────────────────────────────────────────────────────────────────


class TestWhich:
    def test_found(self, synth, monkeypatch):
        """Should return path when executable is found."""
        import shutil
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/channel")
        result = synth["_which"]("channel")
        assert result == "/usr/bin/channel"

    def test_not_found(self, synth, monkeypatch):
        """Should return None when executable not found."""
        import shutil
        monkeypatch.setattr(shutil, "which", lambda _: None)
        result = synth["_which"]("nonexistent")
        assert result is None


# ── _backend_channel ───────────────────────────────────────────────────────


class TestBackendChannel:
    def test_success(self, synth, monkeypatch):
        """Should return stdout when channel succeeds."""
        mock_result = MagicMock(stdout="test output\n", stderr="")
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        synth["_which"] = lambda _: "/usr/bin/channel"
        result = synth["_backend_channel"]("test prompt", "haiku", 60)
        assert result == "test output"

    def test_empty_stdout_raises(self, synth, monkeypatch):
        """Should raise RuntimeError when channel returns empty output."""
        mock_result = MagicMock(stdout="  \n", stderr="something went wrong")
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        synth["_which"] = lambda _: "/usr/bin/channel"
        with pytest.raises(RuntimeError, match="channel error: something went wrong"):
            synth["_backend_channel"]("test", "haiku", 60)

    def test_no_stderr_message(self, synth, monkeypatch):
        """Should raise with 'no output' when both stdout and stderr are empty."""
        mock_result = MagicMock(stdout="", stderr="")
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        synth["_which"] = lambda _: "/usr/bin/channel"
        with pytest.raises(RuntimeError, match="no output"):
            synth["_backend_channel"]("test", "haiku", 60)

    def test_channel_not_found(self, synth, monkeypatch):
        """Should raise RuntimeError when channel not on PATH."""
        synth["_which"] = lambda _: None
        with pytest.raises(RuntimeError, match="channel not found"):
            synth["_backend_channel"]("test", "haiku", 60)

    def test_passes_model_and_prompt(self, synth, monkeypatch):
        """Should pass model and -p prompt to channel."""
        calls = []
        def mock_run(args, **kwargs):
            calls.append(args)
            return MagicMock(stdout="result", stderr="")
        monkeypatch.setattr(subprocess, "run", mock_run)
        synth["_which"] = lambda _: "/usr/bin/channel"
        synth["_backend_channel"]("my prompt", "sonnet", 120)
        assert calls[0][1] == "sonnet"
        assert "-p" in calls[0]
        assert calls[0][-1] == "my prompt"


# ── main ────────────────────────────────────────────────────────────────────


class TestMain:
    def test_prompt_as_argument(self, synth, capsys):
        """Should pass the prompt argument to _backend_channel."""
        mock_bc = MagicMock(return_value="response")
        synth["_backend_channel"] = mock_bc
        synth["_load_config"] = lambda: {}
        with patch.object(sys, "argv", ["synthase", "hello world"]), \
             patch.object(sys, "stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            synth["main"]()
        mock_bc.assert_called_once_with("hello world", "haiku", 60)
        assert capsys.readouterr().out.strip() == "response"

    def test_model_override(self, synth, capsys):
        """Should use --model flag value."""
        mock_bc = MagicMock(return_value="ok")
        synth["_backend_channel"] = mock_bc
        synth["_load_config"] = lambda: {}
        with patch.object(sys, "argv", ["synthase", "--model", "opus", "test"]), \
             patch.object(sys, "stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            synth["main"]()
        mock_bc.assert_called_once_with("test", "opus", 60)

    def test_default_model_from_config(self, synth, capsys):
        """Should use default_model from config when --model not specified."""
        mock_bc = MagicMock(return_value="ok")
        synth["_backend_channel"] = mock_bc
        synth["_load_config"] = lambda: {"default_model": "sonnet"}
        with patch.object(sys, "argv", ["synthase", "test"]), \
             patch.object(sys, "stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            synth["main"]()
        mock_bc.assert_called_once_with("test", "sonnet", 60)

    def test_stdin_prompt(self, synth, capsys):
        """Should read prompt from stdin when not a tty."""
        mock_bc = MagicMock(return_value="ok")
        synth["_backend_channel"] = mock_bc
        synth["_load_config"] = lambda: {}
        with patch.object(sys, "argv", ["synthase"]), \
             patch.object(sys, "stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            mock_stdin.read.return_value = "  stdin prompt  \n"
            synth["main"]()
        mock_bc.assert_called_once_with("stdin prompt", "haiku", 60)

    def test_no_prompt_exits(self, synth):
        """Should exit 1 when no prompt provided and stdin is a tty."""
        with patch.object(sys, "argv", ["synthase"]), \
             patch.object(sys, "stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            with pytest.raises(SystemExit) as exc_info:
                synth["main"]()
        assert exc_info.value.code == 1

    def test_empty_prompt_exits(self, synth):
        """Should exit 1 when prompt is empty."""
        with patch.object(sys, "argv", ["synthase", ""]), \
             patch.object(sys, "stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            with pytest.raises(SystemExit) as exc_info:
                synth["main"]()
        assert exc_info.value.code == 1

    def test_backend_error_exits(self, synth, capsys):
        """Should exit 1 and print error when _backend_channel raises."""
        synth["_backend_channel"] = MagicMock(side_effect=RuntimeError("boom"))
        synth["_load_config"] = lambda: {}
        with patch.object(sys, "argv", ["synthase", "test"]), \
             patch.object(sys, "stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            with pytest.raises(SystemExit) as exc_info:
                synth["main"]()
        assert exc_info.value.code == 1
        assert "boom" in capsys.readouterr().err

    def test_custom_timeout(self, synth, capsys):
        """Should pass custom timeout to _backend_channel."""
        mock_bc = MagicMock(return_value="ok")
        synth["_backend_channel"] = mock_bc
        synth["_load_config"] = lambda: {}
        with patch.object(sys, "argv", ["synthase", "--timeout", "120", "test"]), \
             patch.object(sys, "stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            synth["main"]()
        mock_bc.assert_called_once_with("test", "haiku", 120)


# ── CLI subprocess ──────────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_no_args_exits_nonzero(self):
        """Running synthase with no args and tty should exit nonzero."""
        r = subprocess.run(
            [str(SYNTHASE_PATH)],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode != 0

    def test_help_flag(self):
        """Running synthase --help should exit 0."""
        r = subprocess.run(
            [str(SYNTHASE_PATH), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0
        assert "synthase" in r.stdout.lower() or "llm" in r.stdout.lower()
