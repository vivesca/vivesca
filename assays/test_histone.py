from __future__ import annotations

"""Tests for metabolon.enzymes.histone."""
import pytest
from unittest.mock import patch, MagicMock

from metabolon.enzymes.histone import histone, HistoneResult, _format_search_results
from metabolon.morphology import EffectorResult, Vital


class TestFormatSearchResults:
    def test_empty_results(self):
        assert _format_search_results([]) == "No results"

    def test_with_results(self):
        results = [
            {
                "name": "test_file.py",
                "path": "/path/test_file.py",
                "content": "This is some test content that should appear in the output"
            }
        ]
        formatted = _format_search_results(results)
        assert "- test_file.py" in formatted
        assert "path: /path/test_file.py" in formatted
        assert "content: This is some test content that should appear in the output" in formatted

    def test_truncates_long_content(self):
        long_content = "x" * 200
        results = [{"name": "long", "path": "/long.txt", "content": long_content}]
        formatted = _format_search_results(results)
        assert "..." in formatted
        assert len(formatted) < 200 + 50  # Should be truncated


class TestHistoneTool:
    def test_unknown_action(self):
        result = histone(action="invalid")
        assert isinstance(result, EffectorResult)
        assert not result.success
        assert "Unknown action" in result.message

    def test_search_missing_query(self):
        result = histone(action="search")
        assert isinstance(result, EffectorResult)
        assert not result.success
        assert "requires: query" in result.message

    def test_mark_missing_content(self):
        result = histone(action="mark")
        assert isinstance(result, EffectorResult)
        assert not result.success
        assert "requires: content" in result.message

    @patch("metabolon.organelles.chromatin.search")
    def test_search_success(self, mock_search):
        mock_search.return_value = [
            {"name": "test", "path": "/test.py", "content": "test content"}
        ]
        result = histone(action="search", query="test", limit=5)
        assert isinstance(result, HistoneResult)
        assert "test" in result.results
        mock_search.assert_called_once()

    @patch("metabolon.organelles.chromatin.add")
    def test_mark_success(self, mock_add):
        mock_add.return_value = {"file": "/tmp/test.md"}
        result = histone(action="mark", content="test content", category="notes")
        assert isinstance(result, EffectorResult)
        assert result.success
        assert "Memory added" in result.message
        mock_add.assert_called_once()

    @patch("metabolon.organelles.chromatin.stats")
    def test_stats_success(self, mock_stats):
        mock_stats.return_value = {
            "count": 100,
            "size_kb": 250,
            "path": "/path/to/db"
        }
        result = histone(action="stats")
        assert isinstance(result, HistoneResult)
        assert "Marks: 100" in result.results
        assert "Size: 250KB" in result.results
        assert "Path: /path/to/db" in result.results

    @patch("metabolon.organelles.chromatin.status")
    def test_status_success(self, mock_status):
        mock_status.return_value = "OK"
        result = histone(action="status")
        assert isinstance(result, Vital)
        assert result.status == "ok"
        assert result.message == "OK"

    @patch("metabolon.organelles.chromatin.search")
    def test_search_passes_correct_parameters(self, mock_search):
        mock_search.return_value = []
        histone(
            action="search",
            query="test query",
            category="docs",
            source="golem",
            limit=20,
            mode="fulltext",
            chromatin="closed"
        )
        mock_search.assert_called_with(
            "test query",
            category="docs",
            source_enzyme="golem",
            limit=20,
            mode="fulltext",
            chromatin="closed"
        )

    @patch("metabolon.organelles.chromatin.add")
    def test_mark_uses_default_category(self, mock_add):
        mock_add.return_value = {"file": "test"}
        histone(action="mark", content="test content", confidence=0.9)
        mock_add.assert_called_with("test content", category="gotcha", confidence=0.9)
