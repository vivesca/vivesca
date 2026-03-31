"""Tests for histone enzyme."""
from unittest.mock import patch
import pytest


def test_unknown_action():
    from metabolon.enzymes.histone import histone

    result = histone(action="nonexistent")
    assert not result.success
    assert "Unknown action" in result.message


def test_search_requires_query():
    from metabolon.enzymes.histone import histone

    result = histone(action="search")
    assert not result.success
    assert "query" in result.message.lower()


def test_search_with_results():
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.search") as mock:
        mock.return_value = [{"name": "test", "path": "/a/b", "content": "hello world"}]
        result = histone(action="search", query="hello")
        assert "test" in result.results
        assert "/a/b" in result.results


def test_search_no_results():
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.search") as mock:
        mock.return_value = []
        result = histone(action="search", query="nothing")
        assert "No results" in result.results


def test_mark_requires_content():
    from metabolon.enzymes.histone import histone

    result = histone(action="mark")
    assert not result.success
    assert "content" in result.message.lower()


def test_mark_success():
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.add") as mock:
        mock.return_value = {"file": "test.md"}
        result = histone(action="mark", content="remember this")
        assert result.success
        assert "test.md" in result.message


def test_stats():
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.stats") as mock:
        mock.return_value = {"count": 42, "size_kb": 100, "path": "/marks"}
        result = histone(action="stats")
        assert "42" in result.results
        assert "100" in result.results


def test_status():
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.status") as mock:
        mock.return_value = "All systems operational"
        result = histone(action="status")
        assert result.status == "ok"
