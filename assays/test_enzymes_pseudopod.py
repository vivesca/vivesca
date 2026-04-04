from __future__ import annotations

from unittest.mock import patch

from metabolon.enzymes.pseudopod import porta_inject, translocon_dispatch
from metabolon.morphology import EffectorResult


class TestPortaInject:
    """Tests for porta_inject function."""

    @patch("metabolon.organelles.porta.inject")
    def test_porta_inject_success(self, mock_inject):
        """Test successful cookie injection."""
        mock_inject.return_value = {
            "success": True,
            "message": "Injected 5 cookies",
            "count": 5,
        }

        result = porta_inject("example.com")

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.message == "Injected 5 cookies"
        assert result.data == {"count": 5, "domain": "example.com"}
        mock_inject.assert_called_once_with("example.com")

    @patch("metabolon.organelles.porta.inject")
    def test_porta_inject_failure(self, mock_inject):
        """Test failed cookie injection."""
        mock_inject.return_value = {
            "success": False,
            "message": "No cookies found",
            "count": 0,
        }

        result = porta_inject("nonexistent.com")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert result.message == "No cookies found"
        assert result.data == {"count": 0, "domain": "nonexistent.com"}
        mock_inject.assert_called_once_with("nonexistent.com")


class TestTransloconDispatch:
    """Tests for translocon_dispatch function."""

    @patch("metabolon.organelles.translocon.dispatch")
    def test_translocon_dispatch_default_params(self, mock_dispatch):
        """Test translocon_dispatch with default parameters."""
        mock_dispatch.return_value = {
            "success": True,
            "output": "Task completed successfully",
        }

        result = translocon_dispatch("Test prompt")

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.message == "Task completed successfully"
        assert result.data == mock_dispatch.return_value

        mock_dispatch.assert_called_once_with(
            prompt="Test prompt",
            mode="explore",
            skill=None,
            model=None,
            backend=None,
            directory=".",
            json_output=False,
        )

    @patch("metabolon.organelles.translocon.dispatch")
    def test_translocon_dispatch_custom_params(self, mock_dispatch):
        """Test translocon_dispatch with custom parameters."""
        mock_dispatch.return_value = {
            "success": True,
            "output": "Custom task completed",
        }

        result = translocon_dispatch(
            "Custom prompt",
            mode="implement",
            skill="python",
            model="gpt-4",
            backend="openai",
            directory="/tmp/test",
            json_output=True,
        )

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.message == "Custom task completed"
        assert result.data == mock_dispatch.return_value

        mock_dispatch.assert_called_once_with(
            prompt="Custom prompt",
            mode="implement",
            skill="python",
            model="gpt-4",
            backend="openai",
            directory="/tmp/test",
            json_output=True,
        )

    @patch("metabolon.organelles.translocon.dispatch")
    def test_translocon_dispatch_truncates_long_output(self, mock_dispatch):
        """Test that long output is truncated to 200 chars in message."""
        long_output = "x" * 300
        mock_dispatch.return_value = {
            "success": True,
            "output": long_output,
        }

        result = translocon_dispatch("Long prompt")

        assert len(result.message) == 200
        assert result.message == long_output[:200]
        assert result.data["output"] == long_output  # Full output preserved in data

    @patch("metabolon.organelles.translocon.dispatch")
    def test_translocon_dispatch_failure(self, mock_dispatch):
        """Test failed translocon dispatch."""
        mock_dispatch.return_value = {
            "success": False,
            "output": "Error: task failed",
        }

        result = translocon_dispatch("Failing prompt")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert result.message == "Error: task failed"
        assert result.data == mock_dispatch.return_value
