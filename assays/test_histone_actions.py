from __future__ import annotations

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


def test_action_case_insensitive():
    """Action should be case insensitive."""
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.stats") as mock:
        mock.return_value = {"count": 1, "size_kb": 1, "path": "/marks"}
        result = histone(action="STATS")
        assert "1" in result.results


def test_action_with_whitespace():
    """Action should be stripped of whitespace."""
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.stats") as mock:
        mock.return_value = {"count": 1, "size_kb": 1, "path": "/marks"}
        result = histone(action="  stats  ")
        assert "1" in result.results


def test_search_passes_all_params():
    """Search should pass all parameters to chromatin.search."""
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.search") as mock:
        mock.return_value = []
        histone(
            action="search",
            query="test",
            category="finding",
            source="enzyme",
            limit=5,
            mode="regex",
            chromatin="closed",
        )
        mock.assert_called_once_with(
            "test",
            category="finding",
            source_enzyme="enzyme",
            limit=5,
            mode="regex",
            chromatin="closed",
        )


def test_mark_passes_all_params():
    """Mark should pass all parameters to chromatin.add."""
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.add") as mock:
        mock.return_value = {"file": "test.md"}
        histone(action="mark", content="note", category="insight", confidence=0.95)
        mock.assert_called_once_with("note", category="insight", confidence=0.95)


def test_mark_default_category():
    """Mark should use 'gotcha' as default category."""
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.add") as mock:
        mock.return_value = {"file": "test.md"}
        histone(action="mark", content="note")
        mock.assert_called_once_with("note", category="gotcha", confidence=0.8)


def test_format_search_results_truncates_long_content():
    """Long content should be truncated to 160 chars with ellipsis."""
    from metabolon.enzymes.histone import histone

    long_content = "x" * 200
    with patch("metabolon.organelles.chromatin.search") as mock:
        mock.return_value = [{"name": "test", "path": "/a", "content": long_content}]
        result = histone(action="search", query="x")
        # Content should be truncated
        assert "..." in result.results
        assert len([line for line in result.results.split("\n") if "content:" in line and "x" in line][0]) < 200


def test_format_search_results_uses_file_as_name_fallback():
    """When name is missing, should use file field."""
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.search") as mock:
        mock.return_value = [{"file": "myfile.md", "path": "/a", "content": "test"}]
        result = histone(action="search", query="test")
        assert "myfile.md" in result.results


def test_format_search_results_handles_missing_fields():
    """Should handle results with missing fields gracefully."""
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.search") as mock:
        mock.return_value = [{}]
        result = histone(action="search", query="test")
        assert "unknown" in result.results


def test_search_result_ordering():
    """Multiple results should all be formatted."""
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.search") as mock:
        mock.return_value = [
            {"name": "first", "path": "/a", "content": "content1"},
            {"name": "second", "path": "/b", "content": "content2"},
        ]
        result = histone(action="search", query="test")
        assert "first" in result.results
        assert "second" in result.results
        assert "/a" in result.results
        assert "/b" in result.results


def test_mark_returns_saved_file_in_data():
    """Mark should include saved file info in data field."""
    from metabolon.enzymes.histone import histone

    with patch("metabolon.organelles.chromatin.add") as mock:
        mock.return_value = {"file": "saved.md", "path": "/marks/saved.md"}
        result = histone(action="mark", content="remember")
        assert result.success
        assert result.data == {"file": "saved.md", "path": "/marks/saved.md"}
