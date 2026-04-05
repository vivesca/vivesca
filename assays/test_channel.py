#!/usr/bin/env python3
from __future__ import annotations

"""Tests for channel effector — mocks all external subprocess calls."""


from pathlib import Path
from typing import ClassVar
from unittest.mock import MagicMock, patch

import pytest

# Execute the channel file directly into the namespace
channel_path = Path(str(Path.home() / "germline/effectors/channel"))
channel_code = channel_path.read_text()
_channel_dict = {}
exec(channel_code, _channel_dict)


# Make attributes accessible via dot notation
class ChannelModule:
    _original_keys: ClassVar[set] = set(
        _channel_dict.keys()
    )  # Track what was originally in the module

    def __getattr__(self, name):
        return _channel_dict[name]

    def __setattr__(self, name, value):
        # Allow patch.object to work by writing to _channel_dict
        _channel_dict[name] = value

    def __delattr__(self, name):
        # patch.object tries to delattr on exit - restore original or remove
        if name in ChannelModule._original_keys:
            # Can't delete original keys - they'll be restored by patch.object's setattr
            pass
        elif name in _channel_dict:
            del _channel_dict[name]


channel = ChannelModule()

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------


def test_models_defined():
    """Test all expected models are defined."""
    assert "glm" in channel.MODELS
    assert "sonnet" in channel.MODELS
    assert "haiku" in channel.MODELS
    assert "opus" in channel.MODELS
    assert channel.MODELS["glm"] == "GLM-5.1"


def test_zhipu_models():
    """Test glm is in ZHIPU_MODELS."""
    assert "glm" in channel._ZHIPU_MODELS


def test_claude_path():
    """Test CLAUDE path is set."""
    assert str(Path.home() / ".local" / "bin" / "claude") == channel.CLAUDE


# ---------------------------------------------------------------------------
# Test _gate function
# ---------------------------------------------------------------------------


def test_gate_returns_true_on_success():
    """Test _gate returns True when claude --version succeeds."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result):
        assert channel._gate() is True


def test_gate_returns_false_on_failure():
    """Test _gate returns False when claude --version fails."""
    mock_result = MagicMock()
    mock_result.returncode = 1

    with patch("subprocess.run", return_value=mock_result):
        assert channel._gate() is False


def test_gate_returns_false_on_exception():
    """Test _gate returns False on exception."""
    with patch("subprocess.run", side_effect=Exception("command not found")):
        assert channel._gate() is False


def test_gate_removes_claude_env_vars():
    """Test _gate removes problematic environment variables."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch.dict("os.environ", {"CLAUDECODE": "1", "ANTHROPIC_API_KEY": "key"}, clear=True):
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            channel._gate()
            # Check that env doesn't contain the removed vars
            called_env = mock_run.call_args[1]["env"]
            assert "CLAUDECODE" not in called_env
            assert "ANTHROPIC_API_KEY" not in called_env


# ---------------------------------------------------------------------------
# Test _tissue_default function
# ---------------------------------------------------------------------------


def test_tissue_default_works_with_or_without_module():
    """Test _tissue_default doesn't crash and returns either None or a model name."""
    result = channel._tissue_default()
    # If import succeeds, we should get a model that's in MODELS
    if result is not None:
        assert result in channel.MODELS
    assert True  # just verify it doesn't crash


# ---------------------------------------------------------------------------
# Test _record function
# ---------------------------------------------------------------------------


def test_record_silently_fails_on_import_error():
    """Test _record doesn't raise when mitophagy import fails."""
    # Should not raise
    channel._record("sonnet", True, 1000)
    assert True  # we just need to verify it doesn't crash


# ---------------------------------------------------------------------------
# Test argument parsing - help
# ---------------------------------------------------------------------------


def test_main_prints_help_on_no_args():
    """Test main exits with help when no arguments."""
    with patch("sys.argv", ["channel"]):
        with patch("builtins.print"):
            with pytest.raises(SystemExit):
                channel.main()


def test_main_prints_help_on_help():
    """Test main exits with help when -h is given."""
    for flag in ["-h", "--help"]:
        with patch("sys.argv", ["channel", flag]):
            with patch("builtins.print"):
                with pytest.raises(SystemExit):
                    channel.main()


# ---------------------------------------------------------------------------
# Test model detection
# ---------------------------------------------------------------------------


def test_main_parses_explicit_model():
    """Test main parses explicit model argument."""
    with patch("sys.argv", ["channel", "sonnet", "-p", "test prompt"]):
        with patch.object(channel, "_gate", return_value=True):
            with patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run:
                with patch("time.monotonic", side_effect=[0, 0.1]):
                    with patch.object(channel, "_record"):
                        with pytest.raises(SystemExit) as exc_info:
                            channel.main()
                        assert exc_info.value.code == 0
                        # Check that correct model is used
                        called_args = mock_run.call_args[0][0]
                        assert "--model" in called_args
                        idx = called_args.index("--model")
                        assert called_args[idx + 1] == channel.MODELS["sonnet"]


def test_main_parses_organism_flag():
    """Test main handles --organism flag."""
    with patch("sys.argv", ["channel", "--organism", "sonnet", "-p", "test"]):
        with patch.object(channel, "_gate", return_value=True):
            with patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run:
                with patch("time.monotonic", side_effect=[0, 0.1]):
                    with patch.object(channel, "_record"):
                        with pytest.raises(SystemExit) as exc_info:
                            channel.main()
                        assert exc_info.value.code == 0
                        called_args = mock_run.call_args[0][0]
                        assert "--permission-mode" in called_args
                        assert "bypassPermissions" in called_args


def test_main_uses_glm_fallback_when_model_not_recognized():
    """Test main falls back to glm when model not in MODELS."""
    with patch("sys.argv", ["channel", "-p", "test prompt"]):
        with patch.object(channel, "_tissue_default", return_value=None):
            with patch.object(channel, "_gate", return_value=True):
                with patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run:
                    with patch("time.monotonic", side_effect=[0, 0.1]):
                        with patch.object(channel, "_record"):
                            with pytest.raises(SystemExit) as exc_info:
                                channel.main()
                            assert exc_info.value.code == 0
                            called_args = mock_run.call_args[0][0]
                            assert "--model" in called_args
                            idx = called_args.index("--model")
                            assert called_args[idx + 1] == channel.MODELS["glm"]


def test_main_uses_routed_model_from_tissue_routing():
    """Test main uses model from tissue routing when available."""
    with patch("sys.argv", ["channel", "-p", "test"]):
        with patch.object(channel, "_tissue_default", return_value="sonnet"):
            with patch.object(channel, "_gate", return_value=True):
                with patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run:
                    with patch("time.monotonic", side_effect=[0, 0.1]):
                        with patch.object(channel, "_record"):
                            with patch("builtins.print"):
                                with pytest.raises(SystemExit) as exc_info:
                                    channel.main()
                                assert exc_info.value.code == 0
                                called_args = mock_run.call_args[0][0]
                                assert "--model" in called_args
                                idx = called_args.index("--model")
                                assert called_args[idx + 1] == channel.MODELS["sonnet"]


# ---------------------------------------------------------------------------
# Test Zhipu model handling
# ---------------------------------------------------------------------------


def test_zhipu_exits_when_no_api_key():
    """Test glm model exits with error when ZHIPU_API_KEY not set."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("sys.argv", ["channel", "glm", "-p", "test"]):
            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc_info:
                    channel.main()
                assert exc_info.value.code == 2


def test_zhipu_sets_correct_env_vars():
    """Test glm model sets correct environment variables."""
    with patch.dict(
        "os.environ",
        {"ZHIPU_API_KEY": "test-key", "ANTHROPIC_API_KEY": "old-key", "CLAUDECODE": "1"},
        clear=True,
    ):
        with patch("sys.argv", ["channel", "glm", "-p", "test"]):
            with patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run:
                with patch("time.monotonic", side_effect=[0, 0.1]):
                    with patch.object(channel, "_record"):
                        with pytest.raises(SystemExit) as exc_info:
                            channel.main()
                        assert exc_info.value.code == 0
                        called_env = mock_run.call_args[1]["env"]
                        # Should have ZHIPU key as ANTHROPIC_API_KEY
                        assert called_env["ANTHROPIC_API_KEY"] == "test-key"
                        assert called_env["ANTHROPIC_BASE_URL"] == channel._ZHIPU_BASE_URL
                        # Should not have these vars
                        assert "CLAUDECODE" not in called_env
                        assert "ANTHROPIC_AUTH_TOKEN" not in called_env


# ---------------------------------------------------------------------------
# Test non-Zhipu model handling
# ---------------------------------------------------------------------------


def test_non_zhipu_exits_when_gate_fails():
    """Test non-Zhipu model exits when _gate check fails."""
    with patch("sys.argv", ["channel", "sonnet", "-p", "test"]):
        with patch.object(channel, "_gate", return_value=False):
            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc_info:
                    channel.main()
                assert exc_info.value.code == 2


def test_non_zhipu_removes_correct_env_vars():
    """Test non-Zhipu removes problematic environment variables."""
    with patch("sys.argv", ["channel", "sonnet", "-p", "test"]):
        with patch.object(channel, "_gate", return_value=True):
            with patch.dict(
                "os.environ", {"CLAUDECODE": "1", "ANTHROPIC_API_KEY": "key"}, clear=True
            ):
                with patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run:
                    with patch("time.monotonic", side_effect=[0, 0.1]):
                        with patch.object(channel, "_record"):
                            with pytest.raises(SystemExit) as exc_info:
                                channel.main()
                            assert exc_info.value.code == 0
                            called_env = mock_run.call_args[1]["env"]
                            assert "CLAUDECODE" not in called_env
                            assert "ANTHROPIC_API_KEY" not in called_env


# ---------------------------------------------------------------------------
# Test piping - stdin input
# ---------------------------------------------------------------------------


def test_main_passes_rest_args_through():
    """Test main passes all remaining arguments to claude."""
    with patch("sys.argv", ["channel", "opus", "--max-tokens", "4096", "-p"]):
        with patch.object(channel, "_gate", return_value=True):
            with patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run:
                with patch("time.monotonic", side_effect=[0, 0.1]):
                    with patch.object(channel, "_record"):
                        with pytest.raises(SystemExit) as exc_info:
                            channel.main()
                        assert exc_info.value.code == 0
                        called_args = mock_run.call_args[0][0]
                        # Should be claude --print --model opus --max-tokens 4096 -p
                        assert called_args[0] == channel.CLAUDE
                        assert "--print" in called_args
                        assert "--max-tokens" in called_args
                        assert "4096" in called_args
                        assert "-p" in called_args


# ---------------------------------------------------------------------------
# Test exit code propagation
# ---------------------------------------------------------------------------


def test_main_propagates_exit_code():
    """Test main propagates exit code from claude."""
    with patch("sys.argv", ["channel", "sonnet", "-p", "test"]):
        with patch.object(channel, "_gate", return_value=True):
            with patch("subprocess.run", return_value=MagicMock(returncode=42)):
                with patch("time.monotonic", side_effect=[0, 0.1]):
                    with patch.object(channel, "_record"):
                        with pytest.raises(SystemExit) as exc_info:
                            channel.main()
                        assert exc_info.value.code == 42


# ---------------------------------------------------------------------------
# Test recording
# ---------------------------------------------------------------------------


def test_main_records_result():
    """Test main records the outcome."""
    with patch("sys.argv", ["channel", "sonnet", "-p", "test"]):
        with patch.object(channel, "_gate", return_value=True):
            with patch("subprocess.run", return_value=MagicMock(returncode=0)):
                with patch("time.monotonic", side_effect=[100.0, 100.5]):
                    with patch.object(channel, "_record") as mock_record:
                        with pytest.raises(SystemExit) as exc_info:
                            channel.main()
                        assert exc_info.value.code == 0
                        # Should have recorded success with ~500ms duration
                        mock_record.assert_called_once()
                        assert mock_record.call_args[0][0] == "sonnet"
                        assert mock_record.call_args[0][1] is True
                        assert 40 <= mock_record.call_args[0][2] <= 600
