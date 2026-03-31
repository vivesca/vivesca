from __future__ import annotations

"""Tests for pseudopod — browser cookie bridge + translocon dispatch."""

from unittest.mock import patch, Mock

import pytest

from metabolon.enzymes import pseudopod
from metabolon.morphology import EffectorResult


class TestPortaInject:
    def test_success_response(self):
        # Mock the inject function from porta (mock where it's defined, not where it's imported)
        mock_result = {"success": True, "message": "Injected 3 cookies", "count": 3}
        with patch("metabolon.organelles.porta.inject", return_value=mock_result):
            result = pseudopod.porta_inject("example.com")
            
        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.message == "Injected 3 cookies"
        assert result.data["count"] == 3
        assert result.data["domain"] == "example.com"

    def test_failure_response(self):
        # Mock failure
        mock_result = {"success": False, "message": "No cookies found", "count": 0}
        with patch("metabolon.organelles.porta.inject", return_value=mock_result):
            result = pseudopod.porta_inject("example.com")
            
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert result.message == "No cookies found"
        assert result.data["count"] == 0
        assert result.data["domain"] == "example.com"


class TestTransloconDispatch:
    def test_basic_dispatch(self):
        mock_result = {
            "success": True,
            "output": "Task completed successfully with result",
            "model": "glm-5.1",
            "tokens": 1200
        }
        with patch("metabolon.organelles.translocon.dispatch", return_value=mock_result):
            result = pseudopod.translocon_dispatch(
                "Explore this codebase", mode="explore", skill="python"
            )
            
        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.message == "Task completed successfully with result"
        assert result.data["success"] is True
        assert result.data["model"] == "glm-5.1"
        assert result.data["tokens"] == 1200

    def test_truncates_long_message(self):
        long_output = "x" * 300
        mock_result = {
            "success": True,
            "output": long_output,
        }
        with patch("metabolon.organelles.translocon.dispatch", return_value=mock_result):
            result = pseudopod.translocon_dispatch("Test long output")
            
        assert len(result.message) == 200
        assert result.message == "x" * 200
        assert result.data["output"] == long_output

    def test_handles_json_output_flag(self):
        mock_result = {
            "success": True,
            "output": '{"key": "value"}',
        }
        # Check that json_output is passed correctly to dispatch
        captured_kwargs = {}
        def mock_dispatch(**kwargs):
            captured_kwargs.update(kwargs)
            return mock_result
        
        with patch("metabolon.organelles.translocon.dispatch", side_effect=mock_dispatch):
            pseudopod.translocon_dispatch(
                "Test json", json_output=True, model="deepseek", backend="ark-code"
            )
            
        assert captured_kwargs["json_output"] is True
        assert captured_kwargs["model"] == "deepseek"
        assert captured_kwargs["backend"] == "ark-code"
        assert captured_kwargs["prompt"] == "Test json"

    def test_failure_response(self):
        mock_result = {
            "success": False,
            "output": "Error: API rate limit exceeded",
        }
        with patch("metabolon.organelles.translocon.dispatch", return_value=mock_result):
            result = pseudopod.translocon_dispatch("Test failure")
            
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert result.message == "Error: API rate limit exceeded"
