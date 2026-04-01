from __future__ import annotations

"""Tests for metabolon.enzymes.rheotaxis — the MCP tool wrapper.

All engine calls are mocked; no network access.
"""

from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.rheotaxis import rheotaxis_search
from metabolon.organelles.rheotaxis_engine import RheotaxisResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(backend: str = "test", query: str = "q", **kw) -> RheotaxisResult:
    """Shorthand to build a RheotaxisResult with sensible defaults."""
    return RheotaxisResult(backend=backend, query=query, results=[], **kw)


# Patches that every test needs — mock the engine module used by the enzyme.
_ENGINE = "metabolon.enzymes.rheotaxis.rheotaxis_engine"


# ---------------------------------------------------------------------------
# Single-query path  (calls parallel_search + format_results)
# ---------------------------------------------------------------------------

@patch(f"{_ENGINE}.format_results", return_value="FMT")
@patch(f"{_ENGINE}.parallel_search", return_value=[_result()])
class TestSingleQuery:
    """When query has no pipe character, the single-query path is taken."""

    def test_calls_parallel_search(self, mock_par, mock_fmt):
        rheotaxis_search("hello")
        mock_par.assert_called_once_with(
            "hello",
            backends=["perplexity", "exa", "tavily", "serper"],
            depth="quick",
            timeout=20,
        )

    def test_calls_format_results(self, mock_par, mock_fmt):
        rheotaxis_search("hello")
        mock_fmt.assert_called_once_with(mock_par.return_value)

    def test_returns_formatted_string(self, mock_par, mock_fmt):
        assert rheotaxis_search("hello") == "FMT"

    def test_custom_backends(self, mock_par, mock_fmt):
        rheotaxis_search("q", backends="exa, tavily")
        assert mock_par.call_args.kwargs["backends"] == ["exa", "tavily"]

    def test_custom_depth(self, mock_par, mock_fmt):
        rheotaxis_search("q", depth="deep")
        assert mock_par.call_args.kwargs["depth"] == "deep"

    def test_custom_timeout(self, mock_par, mock_fmt):
        rheotaxis_search("q", timeout=60)
        assert mock_par.call_args.kwargs["timeout"] == 60

    def test_does_not_call_multi_query(self, mock_par, mock_fmt):
        with patch(f"{_ENGINE}.multi_query_search") as mock_multi:
            rheotaxis_search("single")
            mock_multi.assert_not_called()


# ---------------------------------------------------------------------------
# Multi-query path  (pipe-separated → multi_query_search)
# ---------------------------------------------------------------------------

@patch(f"{_ENGINE}.format_results", return_value="FMT")
@patch(f"{_ENGINE}.multi_query_search")
class TestMultiQuery:
    """When query contains '|', the multi-query path is taken."""

    def _setup_multi(self, mock_multi):
        mock_multi.return_value = {
            "q1": [_result(query="q1")],
            "q2": [_result(query="q2")],
        }

    def test_calls_multi_query_search(self, mock_multi, mock_fmt):
        self._setup_multi(mock_multi)
        rheotaxis_search("q1|q2")
        mock_multi.assert_called_once_with(
            ["q1", "q2"],
            backends=["perplexity", "exa", "tavily", "serper"],
            depth="quick",
            timeout=20,
        )

    def test_formats_each_query_group(self, mock_multi, mock_fmt):
        self._setup_multi(mock_multi)
        rheotaxis_search("q1|q2")
        assert mock_fmt.call_count == 2

    def test_output_has_section_headers(self, mock_multi, mock_fmt):
        self._setup_multi(mock_multi)
        out = rheotaxis_search("q1|q2")
        assert "# q1" in out
        assert "# q2" in out

    def test_output_joins_sections(self, mock_multi, mock_fmt):
        self._setup_multi(mock_multi)
        out = rheotaxis_search("q1|q2")
        assert "FMT" in out
        # Two sections separated by newline
        parts = out.split("\n")
        header_idxs = [i for i, p in enumerate(parts) if p.startswith("# ")]
        assert len(header_idxs) == 2

    def test_strips_whitespace_from_queries(self, mock_multi, mock_fmt):
        self._setup_multi(mock_multi)
        rheotaxis_search("  q1  |  q2  ")
        queries_arg = mock_multi.call_args[0][0]
        assert queries_arg == ["q1", "q2"]

    def test_does_not_call_parallel_search(self, mock_multi, mock_fmt):
        self._setup_multi(mock_multi)
        with patch(f"{_ENGINE}.parallel_search") as mock_par:
            rheotaxis_search("q1|q2")
            mock_par.assert_not_called()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Boundary conditions and unusual inputs."""

    @patch(f"{_ENGINE}.format_results", return_value="EMPTY")
    @patch(f"{_ENGINE}.parallel_search", return_value=[])
    def test_empty_results_list(self, mock_par, mock_fmt):
        out = rheotaxis_search("nothing found")
        assert out == "EMPTY"

    @patch(f"{_ENGINE}.format_results", side_effect=["A", "B", "C"])
    @patch(f"{_ENGINE}.multi_query_search")
    def test_three_pipe_queries(self, mock_multi, mock_fmt):
        mock_multi.return_value = {
            "a": [_result(query="a")],
            "b": [_result(query="b")],
            "c": [_result(query="c")],
        }
        out = rheotaxis_search("a|b|c")
        assert "# a" in out
        assert "# b" in out
        assert "# c" in out
        assert mock_fmt.call_count == 3

    @patch(f"{_ENGINE}.format_results", return_value="OK")
    @patch(f"{_ENGINE}.parallel_search", return_value=[_result()])
    def test_default_backends_include_all_four(self, mock_par, mock_fmt):
        rheotaxis_search("q")
        backends = mock_par.call_args.kwargs["backends"]
        assert set(backends) == {"perplexity", "exa", "tavily", "serper"}

    @patch(f"{_ENGINE}.format_results", return_value="OK")
    @patch(f"{_ENGINE}.parallel_search", return_value=[_result()])
    def test_depth_values_passed_through(self, mock_par, mock_fmt):
        for depth in ("quick", "thorough", "deep"):
            mock_par.reset_mock()
            rheotaxis_search("q", depth=depth)
            assert mock_par.call_args.kwargs["depth"] == depth

    @patch(f"{_ENGINE}.format_results", return_value="OK")
    @patch(f"{_ENGINE}.multi_query_search", return_value={})
    def test_single_pipe_produces_two_queries(self, mock_multi, mock_fmt):
        rheotaxis_search("left|right")
        queries = mock_multi.call_args[0][0]
        assert queries == ["left", "right"]

    @patch(f"{_ENGINE}.format_results", return_value="X")
    @patch(f"{_ENGINE}.parallel_search", return_value=[_result()])
    def test_backends_trailing_comma(self, mock_par, mock_fmt):
        rheotaxis_search("q", backends="exa,")
        backends = mock_par.call_args.kwargs["backends"]
        # strip produces ["exa", ""]
        assert backends == ["exa", ""]
