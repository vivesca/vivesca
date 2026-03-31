"""Tests for ecphory enzyme."""

from __future__ import annotations

from unittest.mock import patch, MagicMock
import pytest


def test_unknown_action():
    from metabolon.enzymes.ecphory import ecphory

    result = ecphory(action="nonexistent")
    assert "Unknown action" in result.results


def test_engram_requires_query():
    from metabolon.enzymes.ecphory import ecphory

    result = ecphory(action="engram")
    assert "requires" in result.results.lower()


def test_engram_with_results():
    from metabolon.enzymes.ecphory import ecphory

    with patch("metabolon.organelles.engram.search") as mock:
        fragment = MagicMock()
        fragment.date = "2026-03-31"
        fragment.time_str = "10:00"
        fragment.role = "user"
        fragment.snippet = "hello world"
        mock.return_value = [fragment]
        result = ecphory(action="engram", query="hello")
        assert "1 match" in result.results
        assert "hello world" in result.results


def test_engram_no_results():
    from metabolon.enzymes.ecphory import ecphory

    with patch("metabolon.organelles.engram.search") as mock:
        mock.return_value = []
        result = ecphory(action="engram", query="nonexistent")
        assert "No matches" in result.results


def test_chromatin_requires_query():
    from metabolon.enzymes.ecphory import ecphory

    result = ecphory(action="chromatin")
    assert "requires" in result.results.lower()


def test_chromatin_with_results():
    from metabolon.enzymes.ecphory import ecphory

    with patch("metabolon.organelles.chromatin.search") as mock:
        mock.return_value = [{"name": "test-mem", "file": "marks/test.md", "content": "some memory"}]
        result = ecphory(action="chromatin", query="test")
        assert "1 memory" in result.results
        assert "test-mem" in result.results


def test_chromatin_no_results():
    from metabolon.enzymes.ecphory import ecphory

    with patch("metabolon.organelles.chromatin.search") as mock:
        mock.return_value = []
        result = ecphory(action="chromatin", query="nothing")
        assert "No memories" in result.results


def test_logs_requires_query():
    from metabolon.enzymes.ecphory import ecphory

    result = ecphory(action="logs")
    assert "requires" in result.results.lower()


def test_logs_no_matches():
    from metabolon.enzymes.ecphory import ecphory

    with patch("metabolon.locus.meal_plan") as mock_mp, \
         patch("metabolon.locus.symptom_log") as mock_sl, \
         patch("metabolon.locus.experiments") as mock_exp:
        mock_mp.exists.return_value = False
        mock_sl.exists.return_value = False
        mock_exp.is_dir.return_value = False
        result = ecphory(action="logs", query="zzz_no_match")
        assert "No matches" in result.results
