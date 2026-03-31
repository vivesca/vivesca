from __future__ import annotations
"""Tests for metabolon.organelles.rheotaxis_engine — pure functions and orchestration."""


import json
import textwrap
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.rheotaxis_engine import (
    _BACKENDS,
    _DEPTH_FN,
    _PERPLEXITY_MODELS,
    RheotaxisResult,
    format_results,
    multi_query_search,
    parallel_search,
    search_perplexity,
    _perplexity_key,
    _get_key,
    _perplexity_query,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_result(
    backend: str = "test",
    query: str = "q",
    results: list[dict] | None = None,
    answer: str = "",
    error: str = "",
) -> RheotaxisResult:
    return RheotaxisResult(
        backend=backend,
        query=query,
        results=results or [],
        answer=answer,
        error=error,
    )


# ---------------------------------------------------------------------------
# 1. Config / routing dicts
# ---------------------------------------------------------------------------

class TestConfigDicts:
    def test_perplexity_models_mapping(self) -> None:
        assert _PERPLEXITY_MODELS == {
            "quick": "sonar",
            "thorough": "sonar-pro",
            "deep": "sonar-deep-research",
        }

    def test_depth_fn_covers_all_tiers(self) -> None:
        assert set(_DEPTH_FN.keys()) == {"quick", "thorough", "deep"}

    def test_backends_registry(self) -> None:
        assert set(_BACKENDS.keys()) == {"perplexity", "exa", "tavily", "serper"}


# ---------------------------------------------------------------------------
# 2. format_results — pure formatting
# ---------------------------------------------------------------------------

class TestFormatResults:
    def test_empty_input(self) -> None:
        assert format_results([]) == ""

    def test_error_result(self) -> None:
        result = format_results([_make_result(backend="exa", query="test q", error="timeout")])
        assert "## exa (test q)" in result
        assert "ERROR: timeout" in result

    def test_answer_only(self) -> None:
        result = format_results([_make_result(backend="tavily", query="what", answer="42")])
        assert "Answer: 42" in result

    def test_hits_with_snippet(self) -> None:
        hits = [
            {
                "title": "Example Page",
                "url": "https://example.com",
                "snippet": "A" * 200,  # longer than 150
            }
        ]
        result = format_results([_make_result(backend="serper", query="q", results=hits)])
        assert "- Example Page" in result
        assert "https://example.com" in result
        # Snippet truncated to 150
        lines = result.split("\n")
        snippet_lines = [l for l in lines if l.strip().startswith("A" * 10)]
        assert len(snippet_lines) == 1
        assert len(snippet_lines[0].strip()) == 150

    def test_no_results_marker(self) -> None:
        result = format_results([_make_result(backend="exa", query="q")])
        assert "(no results)" in result

    def test_multiple_results_separated(self) -> None:
        out = format_results([
            _make_result(backend="exa", query="q1", answer="a1"),
            _make_result(backend="serper", query="q2", error="fail"),
        ])
        assert "## exa (q1)" in out
        assert "## serper (q2)" in out


# ---------------------------------------------------------------------------
# 3. Key helpers
# ---------------------------------------------------------------------------

class TestKeyHelpers:
    def test_perplexity_key_present(self) -> None:
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "pk_test"}):
            assert _perplexity_key() == "pk_test"

    def test_perplexity_key_missing(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="PERPLEXITY_API_KEY not set"):
                _perplexity_key()

    def test_get_key_present(self) -> None:
        with patch.dict("os.environ", {"MY_KEY": "abc"}):
            assert _get_key("MY_KEY") == "abc"

    def test_get_key_missing(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="MY_KEY not set"):
                _get_key("MY_KEY")


# ---------------------------------------------------------------------------
# 4. search_perplexity — dispatches to depth fn
# ---------------------------------------------------------------------------

class TestSearchPerplexity:
    def test_returns_answer(self) -> None:
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "k"}), \
             patch("metabolon.organelles.rheotaxis_engine._perplexity_query", return_value="ans") as mock_pq:
            result = search_perplexity("hello", depth="quick")
            assert result.backend == "perplexity"
            assert result.answer == "ans"
            assert result.error == ""
            mock_pq.assert_called_once_with("sonar", "hello", timeout=30)

    def test_depth_routing(self) -> None:
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "k"}), \
             patch("metabolon.organelles.rheotaxis_engine._perplexity_query", return_value="x"):
            search_perplexity("q", depth="thorough")
            # Should call with sonar-pro model

    def test_error_handling(self) -> None:
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "k"}), \
             patch("metabolon.organelles.rheotaxis_engine._perplexity_query", side_effect=ValueError("nope")):
            result = search_perplexity("q")
            assert result.error == "nope"
            assert result.backend == "perplexity"


# ---------------------------------------------------------------------------
# 5. _perplexity_query — citation formatting
# ---------------------------------------------------------------------------

class TestPerplexityQuery:
    def _mock_response(self, content: str, citations: list[str] | None = None) -> MagicMock:
        payload = {
            "choices": [{"message": {"content": content}}],
        }
        if citations is not None:
            payload["citations"] = citations
        raw = json.dumps(payload).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = raw
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_basic_answer(self) -> None:
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "k"}), \
             patch("urllib.request.urlopen", return_value=self._mock_response("Paris")) as mock_urlopen, \
             patch("builtins.open", MagicMock()):
            result = _perplexity_query("sonar", "capital of france")
            assert "Paris" in result
            assert "Sources" not in result

    def test_citations_appended(self) -> None:
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "k"}), \
             patch("urllib.request.urlopen", return_value=self._mock_response("Paris", ["https://a.com", "https://b.com"])), \
             patch("builtins.open", MagicMock()):
            result = _perplexity_query("sonar", "capital of france")
            assert "Sources:" in result
            assert "- https://a.com" in result
            assert "- https://b.com" in result


# ---------------------------------------------------------------------------
# 6. parallel_search — orchestration with mocked backends
# ---------------------------------------------------------------------------

class TestParallelSearch:
    def test_default_backends(self) -> None:
        mock_results = {
            "perplexity": _make_result(backend="perplexity", query="q"),
            "exa": _make_result(backend="exa", query="q"),
            "tavily": _make_result(backend="tavily", query="q"),
            "serper": _make_result(backend="serper", query="q"),
        }

        def fake_backend(name: str):
            def fn(*args, **kwargs):
                return mock_results[name]
            return fn

        with patch.dict(
            "metabolon.organelles.rheotaxis_engine._BACKENDS",
            {k: fake_backend(k) for k in mock_results},
        ):
            results = parallel_search("q")
            assert len(results) == 4
            backends = {r.backend for r in results}
            assert backends == {"perplexity", "exa", "tavily", "serper"}

    def test_subset_backends(self) -> None:
        mock_exa = _make_result(backend="exa", query="q")

        with patch.dict(
            "metabolon.organelles.rheotaxis_engine._BACKENDS",
            {"exa": MagicMock(return_value=mock_exa)},
        ):
            results = parallel_search("q", backends=["exa"])
            assert len(results) == 1
            assert results[0].backend == "exa"

    def test_unknown_backend_skipped(self) -> None:
        results = parallel_search("q", backends=["nonexistent"])
        assert results == []


# ---------------------------------------------------------------------------
# 7. multi_query_search — multiple queries
# ---------------------------------------------------------------------------

class TestMultiQuerySearch:
    def test_groups_by_query(self) -> None:
        mock_exa = _make_result(backend="exa", query="q1")

        with patch.dict(
            "metabolon.organelles.rheotaxis_engine._BACKENDS",
            {"exa": MagicMock(return_value=mock_exa)},
        ):
            out = multi_query_search(["q1", "q2"], backends=["exa"])
            assert "q1" in out
            assert "q2" in out
            assert len(out["q1"]) == 1
            assert len(out["q2"]) == 1
