"""Tests for effectors/channel - Gated transport to symbiont via Max subscription."""

import os
import sys
from unittest.mock import patch, MagicMock

import pytest

# Add effectors directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'effectors')))

import channel


# ─────────────────────────────────────────────────────────────────────────────
# Constant tests
# ─────────────────────────────────────────────────────────────────────────────

def test_claude_path():
    """Test CLAUDE path is set."""
    assert channel.CLAUDE == "/Users/terry/.local/bin/claude"


def test_models_defined():
    """Test all expected models are defined."""
    assert "sonnet" in channel.MODELS
    assert "haiku" in channel.MODELS
    assert "opus" in channel.MODELS
    assert "glm" in channel.MODELS
    assert channel.MODELS["sonnet"] == "sonnet"
    assert channel.MODELS["glm"] == "glm-5.1"


def test_zhipu_models():
    """Test ZhiPu models are identified correctly."""
    assert "glm" in channel._ZHIPU_MODELS
    assert "sonnet" not in channel._ZHIPU_MODELS


def test_zhipu_base_url():
    """Test ZhiPu base URL is set."""
    assert channel._ZHIPU_BASE_URL == "https://open.bigmodel.cn/api/anthropic"


# ─────────────────────────────────────────────────────────────────────────────
# Gate function tests
# ─────────────────────────────────────────────────────────────────────────────

def test_gate_success():
    """Test _gate returns True when claude --version succeeds."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = channel._gate()
        assert result is True
        mock_run.assert_called_once()


def test_gate_failure():
    """Test _gate returns False when claude --version fails."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        result = channel._gate()
        assert result is False


def test_gate_exception():
    """Test _gate returns False on exception."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("boom")
        result = channel._gate()
        assert result is False


def test_gate_strips_claud_ecode_and_api_key():
    """Test _gate removes CLAUDECODE and ANTHROPIC_API_KEY from env."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        channel._gate()
        call_env = mock_run.call_args[1]["env"]
        assert "CLAUDECODE" not in call_env
        assert "ANTHROPIC_API_KEY" not in call_env


# ─────────────────────────────────────────────────────────────────────────────
# Tissue routing tests
# ─────────────────────────────────────────────────────────────────────────────

def test_tissue_default_success():
    """Test _tissue_default returns model from tissue routing."""
    mock_route = MagicMock(return_value="sonnet")
    with patch.dict(sys.modules, {"metabolon.organelles.tissue_routing": MagicMock(route=mock_route)}):
        result = channel._tissue_default()
        assert result == "sonnet"


def test_tissue_default_failure():
    """Test _tissue_default returns None on any failure."""
    with patch.dict(sys.modules, {}, clear=True):
        # Force import error
        with patch.dict(sys.modules, {"metabolon.organelles.tissue_routing": None}):
            result = channel._tissue_default()
            assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# Record function tests
# ─────────────────────────────────────────────────────────────────────────────

def test_record_success():
    """Test _record calls mitophagy record_outcome."""
    mock_record = MagicMock()
    with patch.dict(sys.modules, {"metabolon.organelles.mitophagy": MagicMock(record_outcome=mock_record)}):
        channel._record("sonnet", True, 500, "general")
        mock_record.assert_called_once_with(
            model="sonnet", task_type="general", success=True, duration_ms=500
        )


def test_record_silent_on_failure():
    """Test _record silently ignores errors."""
    with patch.dict(sys.modules, {}, clear=True):
        # Should not raise
        channel._record("sonnet", True, 500, "general")


# ─────────────────────────────────────────────────────────────────────────────
# Main function tests
# ─────────────────────────────────────────────────────────────────────────────

def test_main_help_exits():
    """Test main exits with help message."""
    with patch("sys.argv", ["channel", "--help"]):
        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                channel.main()
            assert exc_info.value.code == 0
            assert "gated transport" in mock_print.call_args[0][0].lower()


def test_main_no_args_shows_help():
    """Test main with no args shows help."""
    with patch("sys.argv", ["channel"]):
        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                channel.main()
            assert exc_info.value.code == 0


def test_main_zhipu_model_missing_key_exits():
    """Test main exits when ZHIPU_API_KEY not set for glm model."""
    with patch("sys.argv", ["channel", "glm", "-p", "test"]):
        with patch.dict(os.environ, {"ZHIPU_API_KEY": ""}, clear=False):
            with pytest.raises(SystemExit) as exc_info:
                channel.main()
            assert exc_info.value.code == 2


def test_main_zhipu_model_sets_env():
    """Test main sets correct env for ZhiPu models."""
    with patch("sys.argv", ["channel", "glm", "-p", "test"]):
        with patch.dict(os.environ, {"ZHIPU_API_KEY": "test-key"}, clear=False):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                
                channel.main()
                
                call_env = mock_run.call_args[1]["env"]
                assert call_env["ANTHROPIC_API_KEY"] == "test-key"
                assert call_env["ANTHROPIC_BASE_URL"] == channel._ZHIPU_BASE_URL


def test_main_anthropic_model_checks_gate():
    """Test main checks gate for Anthropic models."""
    with patch("sys.argv", ["channel", "sonnet", "-p", "test"]):
        with patch("channel._gate", return_value=False) as mock_gate:
            with pytest.raises(SystemExit) as exc_info:
                channel.main()
            mock_gate.assert_called_once()
            assert exc_info.value.code == 2


def test_main_anthropic_model_strips_api_key():
    """Test main strips ANTHROPIC_API_KEY for Anthropic models."""
    with patch("sys.argv", ["channel", "sonnet", "-p", "test"]):
        with patch("channel._gate", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                
                channel.main()
                
                call_env = mock_run.call_args[1]["env"]
                assert "ANTHROPIC_API_KEY" not in call_env
                assert "CLAUDECODE" not in call_env


def test_main_organism_flag():
    """Test main handles --organism flag."""
    with patch("sys.argv", ["channel", "sonnet", "--organism", "-p", "test"]):
        with patch("channel._gate", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                
                channel.main()
                
                call_args = mock_run.call_args[0][0]
                assert "--permission-mode" in call_args
                assert "bypassPermissions" in call_args


def test_main_uses_tissue_routing():
    """Test main uses tissue routing when no model specified."""
    with patch("sys.argv", ["channel", "-p", "test"]):
        with patch("channel._tissue_default", return_value="haiku"):
            with patch("channel._gate", return_value=True):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    
                    channel.main()
                    
                    call_args = mock_run.call_args[0][0]
                    assert "--model" in call_args
                    model_idx = call_args.index("--model")
                    assert call_args[model_idx + 1] == "haiku"


def test_main_records_outcome():
    """Test main records outcome after execution."""
    with patch("sys.argv", ["channel", "sonnet", "-p", "test"]):
        with patch("channel._gate", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                
                with patch("channel._record") as mock_record:
                    channel.main()
                    mock_record.assert_called_once()
                    assert mock_record.call_args[1]["model"] == "sonnet"
                    assert mock_record.call_args[1]["success"] is True


def test_main_exit_code_propagates():
    """Test main propagates subprocess exit code."""
    with patch("sys.argv", ["channel", "sonnet", "-p", "test"]):
        with patch("channel._gate", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=42)
                
                with pytest.raises(SystemExit) as exc_info:
                    channel.main()
                assert exc_info.value.code == 42
