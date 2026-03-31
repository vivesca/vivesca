"""Tests for rheotaxis web search module."""

from unittest.mock import patch, MagicMock
from metabolon.enzymes.rheotaxis import rheotaxis_search
from metabolon.organelles.rheotaxis_engine import (
    RheotaxisResult,
    parallel_search,
    multi_query_search,
    format_results,
    _get_key,
    _perplexity_key,
)


def test_rheotaxis_search_single_query():
    """Test rheotaxis_search with a single query."""
    mock_results = [
        RheotaxisResult(
            backend="perplexity",
            query="test query",
            results=[],
            answer="Test answer from perplexity",
            error="",
        ),
        RheotaxisResult(
            backend="exa",
            query="test query",
            results=[{"title": "Test Result", "url": "https://example.com", "snippet": "Test snippet"}],
            answer="",
            error="",
        ),
    ]
    
    with patch("metabolon.organelles.rheotaxis_engine.parallel_search") as mock_parallel:
        mock_parallel.return_value = mock_results
        
        result = rheotaxis_search("test query", backends="perplexity,exa", depth="quick")
        
        mock_parallel.assert_called_once()
        assert "perplexity" in result
        assert "Test answer from perplexity" in result
        assert "Test Result" in result
        assert "https://example.com" in result


def test_rheotaxis_search_multi_query():
    """Test rheotaxis_search with multiple pipe-separated queries."""
    mock_all_results = {
        "first query": [
            RheotaxisResult(
                backend="perplexity",
                query="first query",
                results=[],
                answer="First answer",
                error="",
            ),
        ],
        "second query": [
            RheotaxisResult(
                backend="perplexity",
                query="second query",
                results=[],
                answer="Second answer",
                error="",
            ),
        ],
    }
    
    with patch("metabolon.organelles.rheotaxis_engine.multi_query_search") as mock_multi:
        mock_multi.return_value = mock_all_results
        
        result = rheotaxis_search("first query|second query", backends="perplexity")
        
        mock_multi.assert_called_once()
        assert "# first query" in result
        assert "# second query" in result
        assert "First answer" in result
        assert "Second answer" in result


def test_format_results_with_errors():
    """Test format_results handles error cases correctly."""
    results = [
        RheotaxisResult(
            backend="test",
            query="bad query",
            results=[],
            answer="",
            error="API key missing",
        ),
    ]
    
    formatted = format_results(results)
    assert "test" in formatted
    assert "ERROR: API key missing" in formatted


def test_format_results_no_results():
    """Test format_results when no results are found."""
    results = [
        RheotaxisResult(
            backend="empty",
            query="nothing",
            results=[],
            answer="",
            error="",
        ),
    ]
    
    formatted = format_results(results)
    assert "(no results)" in formatted


def test_parallel_search_unknown_backend_skipped():
    """Test that unknown backends are skipped in parallel_search."""
    with patch("metabolon.organelles.rheotaxis_engine._BACKENDS") as mock_backends:
        mock_backends.keys.return_value = ["perplexity"]
        results = parallel_search("test", backends=["perplexity", "nonexistent"])
        # Should just skip nonexistent without error
        assert len(results) == 0  # No actual search executed due to mock


def test_get_key_raises_when_missing():
    """Test _get_key raises ValueError when env var missing."""
    with patch("os.environ.get") as mock_getenv:
        mock_getenv.return_value = ""
        try:
            _get_key("TEST_KEY")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "TEST_KEY not set" in str(e)


def test_perplexity_key_raises_when_missing():
    """Test _perplexity_key raises ValueError when PERPLEXITY_API_KEY missing."""
    with patch("os.environ.get") as mock_getenv:
        mock_getenv.return_value = ""
        try:
            _perplexity_key()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "PERPLEXITY_API_KEY not set" in str(e)


def test_format_results_with_all_result_types():
    """Test format_results with answer, results, and no error."""
    result = RheotaxisResult(
        backend="tavily",
        query="test",
        results=[
            {"title": "Result 1", "url": "https://example.com/1", "snippet": "First result snippet"},
            {"title": "Result 2", "url": "https://example.com/2", "snippet": "Second result snippet"},
        ],
        answer="Synthesized answer from Tavily",
        error="",
    )
    
    formatted = format_results([result])
    
    assert "tavily" in formatted
    assert "Synthesized answer from Tavily" in formatted
    assert "Result 1" in formatted
    assert "Result 2" in formatted
    assert "https://example.com/1" in formatted
    assert "First result snippet" in formatted


def test_multi_query_search_structure():
    """Test multi_query_search returns correct dict structure."""
    with patch("metabolon.organelles.rheotaxis_engine._BACKENDS") as mock_backends:
        # Mock only with perplexity that returns error
        mock_search = MagicMock()
        mock_search.return_value = RheotaxisResult(
            backend="perplexity",
            query="test",
            results=[],
            error="mocked",
        )
        mock_backends.__getitem__.return_value = mock_search
        mock_backends.__contains__.side_effect = lambda x: x == "perplexity"
        
        queries = ["query1", "query2"]
        result = multi_query_search(queries, backends=["perplexity"])
        
        assert isinstance(result, dict)
        assert "query1" in result
        assert "query2" in result
        assert len(result) == 2
        assert all(isinstance(v, list) for v in result.values())
