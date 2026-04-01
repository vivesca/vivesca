from __future__ import annotations
import pytest
from unittest.mock import patch
from metabolon.enzymes.histone import histone, HistoneResult, _format_search_results
from metabolon.morphology import EffectorResult, Vital


def test_format_search_results_empty():
    assert _format_search_results([]) == "No results"


def test_format_search_results_with_results():
    results = [
        {"name": "test1", "path": "/path/test1", "content": "short content"},
        {"file": "test2", "content": "a" * 200},
    ]
    formatted = _format_search_results(results)
    assert "- test1" in formatted
    assert "path: /path/test1" in formatted
    assert "short content" in formatted
    assert "- test2" in formatted
    assert "..." in formatted


def test_histone_search_success():
    with patch("metabolon.enzymes.histone.search") as mock_search:
        mock_search.return_value = [{"name": "test", "path": "/test", "content": "test content"}]
        result = histone("search", query="test query")
        assert isinstance(result, HistoneResult)
        assert "- test" in result.results
        mock_search.assert_called_once_with(
            "test query",
            category="",
            source_enzyme="",
            limit=10,
            mode="hybrid",
            chromatin="open",
        )


def test_histone_search_missing_query():
    result = histone("search")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "requires: query" in result.message


def test_histone_mark_success():
    with patch("metabolon.enzymes.histone.add") as mock_add:
        mock_add.return_value = {"file": "test_file.md"}
        result = histone("mark", content="test content", category="test", confidence=0.9)
        assert isinstance(result, EffectorResult)
        assert result.success
        assert "test_file.md" in result.message
        mock_add.assert_called_once_with("test content", category="test", confidence=0.9)


def test_histone_mark_default_category():
    with patch("metabolon.enzymes.histone.add") as mock_add:
        mock_add.return_value = {"file": "gotcha_file.md"}
        result = histone("mark", content="test content")
        assert isinstance(result, EffectorResult)
        mock_add.assert_called_once_with("test content", category="gotcha", confidence=0.8)


def test_histone_mark_missing_content():
    result = histone("mark")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "requires: content" in result.message


def test_histone_stats():
    with patch("metabolon.enzymes.histone.stats") as mock_stats:
        mock_stats.return_value = {"count": 10, "size_kb": 50, "path": "/test/path"}
        result = histone("stats")
        assert isinstance(result, HistoneResult)
        assert "Marks: 10 files" in result.results
        assert "Size: 50KB" in result.results
        assert "Path: /test/path" in result.results


def test_histone_status():
    with patch("metabolon.enzymes.histone.status") as mock_status:
        mock_status.return_value = "Chromatin is healthy"
        result = histone("status")
        assert isinstance(result, Vital)
        assert result.status == "ok"
        assert result.message == "Chromatin is healthy"


def test_histone_unknown_action():
    result = histone("invalid_action")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "Unknown action" in result.message
