from __future__ import annotations

"""Tests for pseudopod — browser cookie bridge + translocon dispatch."""

from unittest.mock import patch

import pytest

from metabolon.enzymes import pseudopod
from metabolon.morphology import EffectorResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _capture_dispatch_kwargs(mock_result: dict) -> dict:
    """Return a dict that captures kwargs passed to translocon.dispatch."""
    captured: dict = {}

    def _mock(**kwargs):
        captured.update(kwargs)
        return mock_result

    return captured, _mock


# ---------------------------------------------------------------------------
# porta_inject
# ---------------------------------------------------------------------------


class TestPortaInject:
    def test_success_response(self):
        mock_result = {"success": True, "message": "Injected 3 cookies", "count": 3}
        with patch("metabolon.organelles.porta.inject", return_value=mock_result):
            result = pseudopod.porta_inject("example.com")

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.message == "Injected 3 cookies"
        assert result.data["count"] == 3
        assert result.data["domain"] == "example.com"

    def test_failure_response(self):
        mock_result = {"success": False, "message": "No cookies found", "count": 0}
        with patch("metabolon.organelles.porta.inject", return_value=mock_result):
            result = pseudopod.porta_inject("example.com")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert result.message == "No cookies found"
        assert result.data["count"] == 0
        assert result.data["domain"] == "example.com"

    def test_domain_passthrough(self):
        """Domain string is forwarded verbatim to porta.inject."""
        captured: dict = {}
        mock_result = {"success": True, "message": "ok", "count": 1}

        def _mock(domain):
            captured["domain"] = domain
            return mock_result

        with patch("metabolon.organelles.porta.inject", side_effect=_mock):
            pseudopod.porta_inject("bigmodel.cn")

        assert captured["domain"] == "bigmodel.cn"

    def test_injected_domain_in_data(self):
        """The domain is echoed back in data regardless of inject result."""
        mock_result = {"success": True, "message": "ok", "count": 5}
        with patch("metabolon.organelles.porta.inject", return_value=mock_result):
            result = pseudopod.porta_inject("sub.example.org")

        assert result.data["domain"] == "sub.example.org"

    def test_zero_cookies_success(self):
        """inject can succeed with count=0 (e.g. empty cookie jar)."""
        mock_result = {"success": True, "message": "No cookies to inject", "count": 0}
        with patch("metabolon.organelles.porta.inject", return_value=mock_result):
            result = pseudopod.porta_inject("empty.com")

        assert result.success is True
        assert result.data["count"] == 0

    def test_exception_propagates(self):
        """Underlying inject() exceptions are not swallowed."""
        with patch(
            "metabolon.organelles.porta.inject",
            side_effect=RuntimeError("cookie store unavailable"),
        ):
            with pytest.raises(RuntimeError, match="cookie store unavailable"):
                pseudopod.porta_inject("boom.com")

    def test_tool_metadata(self):
        """Verify @tool decorator metadata lives in __fastmcp__."""
        meta = pseudopod.porta_inject.__fastmcp__
        assert meta.name == "porta_inject"
        assert meta.annotations.readOnlyHint is False
        assert meta.annotations.destructiveHint is False


# ---------------------------------------------------------------------------
# translocon_dispatch
# ---------------------------------------------------------------------------


class TestTransloconDispatch:
    def test_basic_dispatch(self):
        mock_result = {
            "success": True,
            "output": "Task completed successfully with result",
            "model": "glm-5.1",
            "tokens": 1200,
        }
        with patch("metabolon.organelles.translocon.dispatch", return_value=mock_result):
            result = pseudopod.translocon_dispatch(
                "Explore this codebase",
                mode="explore",
                skill="python",
            )

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.message == "Task completed successfully with result"
        assert result.data["success"] is True
        assert result.data["model"] == "glm-5.1"
        assert result.data["tokens"] == 1200

    def test_truncates_long_message(self):
        long_output = "x" * 300
        mock_result = {"success": True, "output": long_output}
        with patch("metabolon.organelles.translocon.dispatch", return_value=mock_result):
            result = pseudopod.translocon_dispatch("Test long output")

        assert len(result.message) == 200
        assert result.message == "x" * 200
        assert result.data["output"] == long_output

    def test_message_exactly_200_chars(self):
        """Output of exactly 200 chars should NOT be truncated."""
        exact_output = "y" * 200
        mock_result = {"success": True, "output": exact_output}
        with patch("metabolon.organelles.translocon.dispatch", return_value=mock_result):
            result = pseudopod.translocon_dispatch("boundary")

        assert result.message == exact_output
        assert len(result.message) == 200

    def test_message_201_chars_truncated(self):
        """Output of 201 chars is truncated to 200."""
        output = "z" * 201
        mock_result = {"success": True, "output": output}
        with patch("metabolon.organelles.translocon.dispatch", return_value=mock_result):
            result = pseudopod.translocon_dispatch("boundary+1")

        assert len(result.message) == 200

    def test_short_message_unchanged(self):
        short = "ok"
        mock_result = {"success": True, "output": short}
        with patch("metabolon.organelles.translocon.dispatch", return_value=mock_result):
            result = pseudopod.translocon_dispatch("short")

        assert result.message == "ok"

    def test_handles_json_output_flag(self):
        mock_result = {"success": True, "output": '{"key": "value"}'}
        captured, mock_fn = _capture_dispatch_kwargs(mock_result)

        with patch("metabolon.organelles.translocon.dispatch", side_effect=mock_fn):
            pseudopod.translocon_dispatch(
                "Test json",
                json_output=True,
                model="deepseek",
                backend="ark-code",
            )

        assert captured["json_output"] is True
        assert captured["model"] == "deepseek"
        assert captured["backend"] == "ark-code"
        assert captured["prompt"] == "Test json"

    def test_failure_response(self):
        mock_result = {"success": False, "output": "Error: API rate limit exceeded"}
        with patch("metabolon.organelles.translocon.dispatch", return_value=mock_result):
            result = pseudopod.translocon_dispatch("Test failure")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert result.message == "Error: API rate limit exceeded"

    def test_default_parameters(self):
        """Defaults: mode=explore, directory='.', json_output=False."""
        mock_result = {"success": True, "output": "done"}
        captured, mock_fn = _capture_dispatch_kwargs(mock_result)

        with patch("metabolon.organelles.translocon.dispatch", side_effect=mock_fn):
            pseudopod.translocon_dispatch("hello")

        assert captured["mode"] == "explore"
        assert captured["directory"] == "."
        assert captured["json_output"] is False
        assert captured["prompt"] == "hello"

    def test_empty_skill_becomes_none(self):
        """Empty string skill is converted to None before dispatch."""
        mock_result = {"success": True, "output": "done"}
        captured, mock_fn = _capture_dispatch_kwargs(mock_result)

        with patch("metabolon.organelles.translocon.dispatch", side_effect=mock_fn):
            pseudopod.translocon_dispatch("task", skill="")

        assert captured["skill"] is None

    def test_empty_model_becomes_none(self):
        mock_result = {"success": True, "output": "done"}
        captured, mock_fn = _capture_dispatch_kwargs(mock_result)

        with patch("metabolon.organelles.translocon.dispatch", side_effect=mock_fn):
            pseudopod.translocon_dispatch("task", model="")

        assert captured["model"] is None

    def test_empty_backend_becomes_none(self):
        mock_result = {"success": True, "output": "done"}
        captured, mock_fn = _capture_dispatch_kwargs(mock_result)

        with patch("metabolon.organelles.translocon.dispatch", side_effect=mock_fn):
            pseudopod.translocon_dispatch("task", backend="")

        assert captured["backend"] is None

    def test_nonempty_skill_preserved(self):
        mock_result = {"success": True, "output": "done"}
        captured, mock_fn = _capture_dispatch_kwargs(mock_result)

        with patch("metabolon.organelles.translocon.dispatch", side_effect=mock_fn):
            pseudopod.translocon_dispatch("task", skill="summarize")

        assert captured["skill"] == "summarize"

    def test_directory_passthrough(self):
        mock_result = {"success": True, "output": "done"}
        captured, mock_fn = _capture_dispatch_kwargs(mock_result)

        with patch("metabolon.organelles.translocon.dispatch", side_effect=mock_fn):
            pseudopod.translocon_dispatch("task", directory="/tmp/project")

        assert captured["directory"] == "/tmp/project"

    def test_data_contains_full_result(self):
        """The data field holds the entire dispatch result dict."""
        mock_result = {"success": True, "output": "result", "extra": 42}
        with patch("metabolon.organelles.translocon.dispatch", return_value=mock_result):
            result = pseudopod.translocon_dispatch("task")

        assert result.data == mock_result
        assert result.data["extra"] == 42

    def test_all_modes_pass_through(self):
        """Every mode string is forwarded verbatim."""
        for mode in ("explore", "build", "mcp", "safe", "skill"):
            mock_result = {"success": True, "output": "ok"}
            captured, mock_fn = _capture_dispatch_kwargs(mock_result)

            with patch("metabolon.organelles.translocon.dispatch", side_effect=mock_fn):
                pseudopod.translocon_dispatch("task", mode=mode)

            assert captured["mode"] == mode

    def test_empty_output_string(self):
        """Empty output string is handled without error."""
        mock_result = {"success": True, "output": ""}
        with patch("metabolon.organelles.translocon.dispatch", return_value=mock_result):
            result = pseudopod.translocon_dispatch("t")

        assert result.message == ""
        assert result.success is True

    def test_exception_propagates(self):
        """Underlying dispatch() exceptions are not swallowed."""
        with patch(
            "metabolon.organelles.translocon.dispatch",
            side_effect=ConnectionError("API unreachable"),
        ):
            with pytest.raises(ConnectionError, match="API unreachable"):
                pseudopod.translocon_dispatch("t")

    def test_tool_metadata(self):
        """Verify @tool decorator metadata lives in __fastmcp__."""
        meta = pseudopod.translocon_dispatch.__fastmcp__
        assert meta.name == "translocon_dispatch"
        assert meta.annotations.readOnlyHint is True
        assert meta.annotations.destructiveHint is False
