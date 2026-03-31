"""Tests for rheotaxis and rheotaxis_engine.

All external API calls are mocked.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.rheotaxis import rheotaxis_search
from metabolon.organelles.rheotaxis_engine import (
    RheotaxisResult,
    format_results,
    multi_query_search,
    parallel_search,
    search_exa,
    search_perplexity,
    search_serper,
    search_tavily,
)


class MockResponse:
    """Mock urllib response."""

    def __init__(self, data):
        self.data = json.dumps(data).encode()

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_rheotaxis_result_dataclass():
    """Test RheotaxisResult dataclass initialization."""
    result = RheotaxisResult(
        backend="test",
        query="test query",
        results=[{"title": "Test", "url": "https://test.com", "snippet": "test"}],
        answer="test answer",
    )
    assert result.backend == "test"
    assert result.query == "test query"
    assert len(result.results) == 1
    assert result.answer == "test answer"
    assert result.error == ""


def test_format_results_with_error():
    """Test formatting results with error."""
    results = [RheotaxisResult(backend="test", query="q", results=[], error="failed")]
    formatted = format_results(results)
    assert "## test (q)" in formatted
    assert "ERROR: failed" in formatted


def test_format_results_no_results():
    """Test formatting when there are no results."""
    results = [RheotaxisResult(backend="test", query="q", results=[])]
    formatted = format_results(results)
    assert "(no results)" in formatted


def test_format_results_with_answer_and_results():
    """Test formatting with answer and results."""
    results = [
        RheotaxisResult(
            backend="test",
            query="q",
            results=[{"title": "Test Title", "url": "https://test.com", "snippet": "snippet text"}],
            answer="This is the answer",
        )
    ]
    formatted = format_results(results)
    assert "Answer: This is the answer" in formatted
    assert "Test Title" in formatted
    assert "https://test.com" in formatted
    assert "snippet text" in formatted


@patch("metabolon.organelles.rheotaxis_engine._perplexity_query")
def test_search_perplexity_success(mock_perp_query):
    """Test search_perplexity success."""
    mock_perp_query.return_value = "answer from perplexity"

    result = search_perplexity("test query", depth="quick")

    assert result.backend == "perplexity"
    assert result.query == "test query"
    assert result.answer == "answer from perplexity"
    assert not result.error
    mock_perp_query.assert_called_once()


@patch("metabolon.organelles.rheotaxis_engine._perplexity_query")
def test_search_perplexity_error(mock_perp_query):
    """Test search_perplexity error handling."""
    mock_perp_query.side_effect = ValueError("API key missing")

    result = search_perplexity("test query")

    assert result.backend == "perplexity"
    assert result.error == "API key missing"
    assert not result.answer


@patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
@patch.dict("os.environ", {"EXA_API_KEY": "test-key"})
def test_search_exa_success(mock_urlopen):
    """Test search_exa success."""
    mock_resp = MockResponse({
        "results": [
            {"title": "Exa Result", "url": "https://exa.com", "text": "exa snippet text"},
        ]
    })
    mock_urlopen.return_value = mock_resp

    result = search_exa("test query")

    assert result.backend == "exa"
    assert len(result.results) == 1
    assert result.results[0]["title"] == "Exa Result"
    assert not result.error


@patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
@patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"})
def test_search_tavily_success(mock_urlopen):
    """Test search_tavily success."""
    mock_resp = MockResponse({
        "answer": "tavily answer",
        "results": [
            {"title": "Tavily Result", "url": "https://tavily.com", "content": "tavily content"},
        ]
    })
    mock_urlopen.return_value = mock_resp

    result = search_tavily("test query")

    assert result.backend == "tavily"
    assert result.answer == "tavily answer"
    assert len(result.results) == 1
    assert not result.error


@patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
@patch.dict("os.environ", {"SERPER_API_KEY": "test-key"})
def test_search_serper_success(mock_urlopen):
    """Test search_serper success."""
    mock_resp = MockResponse({
        "organic": [
            {"title": "Serper Result", "link": "https://serper.com", "snippet": "serper snippet"},
        ],
        "knowledgeGraph": {"title": "KG Title", "description": "KG description"},
    })
    mock_urlopen.return_value = mock_resp

    result = search_serper("test query")

    assert result.backend == "serper"
    assert result.answer == "KG Title: KG description"
    assert len(result.results) == 1
    assert not result.error


@patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
@patch.dict("os.environ", {"EXA_API_KEY": "test-key"})
def test_search_exa_error(mock_urlopen):
    """Test search_exa error handling."""
    mock_urlopen.side_effect = Exception("Network error")

    result = search_exa("test query")

    assert result.backend == "exa"
    assert "Network error" in result.error


@patch("metabolon.organelles.rheotaxis_engine.search_perplexity")
def test_parallel_search_single_backend(mock_search_p):
    """Test parallel_search with single backend."""
    mock_result = RheotaxisResult(backend="perplexity", query="test", results=[], answer="ok")
    mock_search_p.return_value = mock_result

    results = parallel_search("test query", backends=["perplexity"], depth="quick", timeout=20)

    assert len(results) == 1
    assert results[0].backend == "perplexity"
    # Since it's called through ThreadPoolExecutor, just verify it was called
    # with the correct arguments (order matters: query, timeout, depth)
    assert mock_search_p.called
    call_args = mock_search_p.call_args
    assert call_args[0][0] == "test query"
    assert call_args[0][1] == 20
    assert call_args[0][2] == "quick"


@patch("metabolon.organelles.rheotaxis_engine.search_perplexity")
@patch("metabolon.organelles.rheotaxis_engine.search_exa")
def test_parallel_search_multiple_backends(mock_exa, mock_perp):
    """Test parallel_search with multiple backends."""
    mock_perp.return_value = RheotaxisResult(backend="perplexity", query="test", results=[], answer="p")
    mock_exa.return_value = RheotaxisResult(backend="exa", query="test", results=[], answer="e")

    results = parallel_search("test query", backends=["perplexity", "exa"])

    assert len(results) == 2
    backends = {r.backend for r in results}
    assert backends == {"perplexity", "exa"}


@patch("metabolon.organelles.rheotaxis_engine.search_perplexity")
@patch("metabolon.organelles.rheotaxis_engine.search_exa")
def test_multi_query_search(mock_exa, mock_perp):
    """Test multi_query_search with multiple queries."""
    mock_perp.return_value = RheotaxisResult(backend="perplexity", query="q1", results=[], answer="p")
    mock_exa.return_value = RheotaxisResult(backend="exa", query="q1", results=[], answer="e")

    results_dict = multi_query_search(["q1", "q2"], backends=["perplexity"])

    assert "q1" in results_dict
    assert "q2" in results_dict
    assert len(results_dict["q1"]) == 1
    assert results_dict["q1"][0].backend == "perplexity"


def test_parallel_search_skips_unknown_backend():
    """Test parallel_search skips unknown backends."""
    results = parallel_search("test query", backends=["nonexistent"])
    assert len(results) == 0


@patch("metabolon.enzymes.rheotaxis.rheotaxis_engine.parallel_search")
def test_rheotaxis_search_single_query(mock_parallel):
    """Test rheotaxis_search with single query."""
    mock_result = RheotaxisResult(backend="test", query="q", results=[], answer="answer")
    mock_parallel.return_value = [mock_result]

    with patch("metabolon.enzymes.rheotaxis.rheotaxis_engine.format_results") as mock_format:
        mock_format.return_value = "formatted text"
        result = rheotaxis_search("single query", backends="test", depth="quick")

    mock_parallel.assert_called_once()
    assert result == "formatted text"


@patch("metabolon.enzymes.rheotaxis.rheotaxis_engine.multi_query_search")
@patch("metabolon.enzymes.rheotaxis.rheotaxis_engine.format_results")
def test_rheotaxis_search_multi_query(mock_format, mock_multi):
    """Test rheotaxis_search with multiple pipe-separated queries."""
    mock_result1 = [RheotaxisResult(backend="test", query="q1", results=[], answer="a1")]
    mock_result2 = [RheotaxisResult(backend="test", query="q2", results=[], answer="a2")]
    mock_multi.return_value = {"q1": mock_result1, "q2": mock_result2}
    mock_format.side_effect = ["formatted1", "formatted2"]

    result = rheotaxis_search("q1|q2", backends="test")

    assert "# q1" in result
    assert "# q2" in result
    assert "formatted1" in result
    assert "formatted2" in result
    mock_multi.assert_called_once()
    assert mock_format.call_count == 2


def test_rheotaxis_search_parses_backends():
    """Test that rheotaxis_search correctly parses comma-separated backends."""
    with patch("metabolon.enzymes.rheotaxis.rheotaxis_engine.parallel_search") as mock_parallel:
        mock_parallel.return_value = []
        with patch("metabolon.enzymes.rheotaxis.rheotaxis_engine.format_results") as mock_format:
            mock_format.return_value = ""
            rheotaxis_search("query", backends="perplexity, exa, tavily")

    # Check that backends were parsed correctly
    call_args = mock_parallel.call_args
    backends_arg = call_args[0][1]
    assert backends_arg == ["perplexity", "exa", "tavily"]


def test_rheotaxis_search_parses_queries():
    """Test that rheotaxis_search correctly parses pipe-separated queries."""
    with patch("metabolon.enzymes.rheotaxis.rheotaxis_engine.multi_query_search") as mock_multi:
        mock_multi.return_value = {}
        rheotaxis_search("q1 | q2 | q3", backends="test")

    call_args = mock_multi.call_args
    queries_arg = call_args[0][0]
    assert queries_arg == ["q1", "q2", "q3"]


@patch("metabolon.organelles.rheotaxis_engine._perplexity_key")
@patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
def test__perplexity_query(mock_urlopen, mock_perp_key):
    """Test _perplexity_query with mocked response."""
    mock_perp_key.return_value = "test-key"
    mock_resp = MockResponse({
        "choices": [{"message": {"content": "perplexity answer"}}],
        "citations": ["https://source1.com", "https://source2.com"],
    })
    mock_urlopen.return_value = mock_resp

    from metabolon.organelles.rheotaxis_engine import _perplexity_query

    result = _perplexity_query("sonar", "test query", timeout=10)

    assert "perplexity answer" in result
    assert "Sources:" in result
    assert "https://source1.com" in result


@patch("metabolon.organelles.rheotaxis_engine._perplexity_key")
@patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
def test__perplexity_query_no_citations(mock_urlopen, mock_perp_key):
    """Test _perplexity_query when no citations are present."""
    mock_perp_key.return_value = "test-key"
    mock_resp = MockResponse({
        "choices": [{"message": {"content": "answer without citations"}}],
    })
    mock_urlopen.return_value = mock_resp

    from metabolon.organelles.rheotaxis_engine import _perplexity_query

    result = _perplexity_query("sonar", "test query")

    assert "answer without citations" in result
    assert "Sources:" not in result
