"""Tests for metabolon/organelles/endocytosis_rss/sorting.py"""
from __future__ import annotations

from typing import Any

import pytest

from metabolon.organelles.endocytosis_rss import sorting as rss_sorting


class TestFateConstants:
    """Tests for fate string constants."""

    def test_transcytose_value(self) -> None:
        assert rss_sorting.FATE_TRANSCYTOSE == "transcytose"

    def test_store_value(self) -> None:
        assert rss_sorting.FATE_STORE == "store"

    def test_degrade_value(self) -> None:
        assert rss_sorting.FATE_DEGRADE == "degrade"

    def test_constants_are_distinct(self) -> None:
        assert rss_sorting.FATE_TRANSCYTOSE != rss_sorting.FATE_STORE
        assert rss_sorting.FATE_STORE != rss_sorting.FATE_DEGRADE
        assert rss_sorting.FATE_TRANSCYTOSE != rss_sorting.FATE_DEGRADE


class TestCargoScore:
    """Tests for _cargo_score helper."""

    def test_extracts_int_score(self) -> None:
        item = {"score": 7}
        assert rss_sorting._cargo_score(item) == 7

    def test_converts_string_score(self) -> None:
        item = {"score": "8"}
        assert rss_sorting._cargo_score(item) == 8

    def test_defaults_to_zero(self) -> None:
        item: dict[str, Any] = {}
        assert rss_sorting._cargo_score(item) == 0

    def test_handles_invalid_string(self) -> None:
        item = {"score": "not a number"}
        assert rss_sorting._cargo_score(item) == 0

    def test_handles_none(self) -> None:
        item = {"score": None}
        assert rss_sorting._cargo_score(item) == 0

    def test_handles_float(self) -> None:
        item = {"score": 7.5}
        assert rss_sorting._cargo_score(item) == 7


class TestSortByFate:
    """Tests for sort_by_fate function."""

    def test_empty_list_returns_empty_compartments(self) -> None:
        result = rss_sorting.sort_by_fate([])
        assert result[rss_sorting.FATE_TRANSCYTOSE] == []
        assert result[rss_sorting.FATE_STORE] == []
        assert result[rss_sorting.FATE_DEGRADE] == []

    def test_high_score_transcytose(self) -> None:
        items = [{"title": "High", "score": 9}]
        result = rss_sorting.sort_by_fate(items)
        assert len(result[rss_sorting.FATE_TRANSCYTOSE]) == 1
        assert len(result[rss_sorting.FATE_STORE]) == 0
        assert len(result[rss_sorting.FATE_DEGRADE]) == 0

    def test_moderate_score_store(self) -> None:
        items = [{"title": "Moderate", "score": 5}]
        result = rss_sorting.sort_by_fate(items)
        assert len(result[rss_sorting.FATE_TRANSCYTOSE]) == 0
        assert len(result[rss_sorting.FATE_STORE]) == 1
        assert len(result[rss_sorting.FATE_DEGRADE]) == 0

    def test_low_score_degrade(self) -> None:
        items = [{"title": "Low", "score": 2}]
        result = rss_sorting.sort_by_fate(items)
        assert len(result[rss_sorting.FATE_TRANSCYTOSE]) == 0
        assert len(result[rss_sorting.FATE_STORE]) == 0
        assert len(result[rss_sorting.FATE_DEGRADE]) == 1

    def test_default_thresholds(self) -> None:
        """Default: threshold_high=7, threshold_low=4."""
        items = [
            {"score": 7},   # transcytose (>= 7)
            {"score": 6},   # store (>= 4, < 7)
            {"score": 4},   # store (>= 4)
            {"score": 3},   # degrade (< 4)
        ]
        result = rss_sorting.sort_by_fate(items)
        assert len(result[rss_sorting.FATE_TRANSCYTOSE]) == 1
        assert len(result[rss_sorting.FATE_STORE]) == 2
        assert len(result[rss_sorting.FATE_DEGRADE]) == 1

    def test_custom_thresholds(self) -> None:
        items = [{"score": 5}]
        # High threshold of 5 -> transcytose
        result = rss_sorting.sort_by_fate(items, threshold_high=5, threshold_low=2)
        assert len(result[rss_sorting.FATE_TRANSCYTOSE]) == 1

    def test_preserves_item_data(self) -> None:
        items = [{"title": "Test Article", "score": 8, "link": "https://example.com"}]
        result = rss_sorting.sort_by_fate(items)
        transcytose = result[rss_sorting.FATE_TRANSCYTOSE]
        assert transcytose[0]["title"] == "Test Article"
        assert transcytose[0]["link"] == "https://example.com"

    def test_boundary_condition_high(self) -> None:
        """Score exactly at threshold_high should transcytose."""
        items = [{"score": 7}]
        result = rss_sorting.sort_by_fate(items)
        assert len(result[rss_sorting.FATE_TRANSCYTOSE]) == 1

    def test_boundary_condition_low(self) -> None:
        """Score exactly at threshold_low should store."""
        items = [{"score": 4}]
        result = rss_sorting.sort_by_fate(items)
        assert len(result[rss_sorting.FATE_STORE]) == 1

    def test_below_threshold_low(self) -> None:
        """Score just below threshold_low should degrade."""
        items = [{"score": 3}]
        result = rss_sorting.sort_by_fate(items)
        assert len(result[rss_sorting.FATE_DEGRADE]) == 1


class TestSelectForLog:
    """Tests for select_for_log function."""

    def test_empty_returns_empty(self) -> None:
        result = rss_sorting.select_for_log([])
        assert result == []

    def test_excludes_degraded(self) -> None:
        items = [
            {"score": 8},   # transcytose
            {"score": 5},   # store
            {"score": 2},   # degrade (excluded)
        ]
        result = rss_sorting.select_for_log(items)
        assert len(result) == 2
        assert all(item["score"] >= 4 for item in result)

    def test_preserves_order(self) -> None:
        items = [
            {"title": "First", "score": 5},   # store
            {"title": "Second", "score": 8},  # transcytose
            {"title": "Third", "score": 4},   # store
        ]
        result = rss_sorting.select_for_log(items)
        # transcytose items first, then store items
        assert result[0]["title"] == "Second"  # transcytose
        assert result[1]["title"] == "First"   # store
        assert result[2]["title"] == "Third"   # store

    def test_all_degraded_returns_empty(self) -> None:
        items = [{"score": 1}, {"score": 2}, {"score": 3}]
        result = rss_sorting.select_for_log(items)
        assert result == []

    def test_all_transcytose(self) -> None:
        items = [{"score": 7}, {"score": 8}, {"score": 9}]
        result = rss_sorting.select_for_log(items)
        assert len(result) == 3

    def test_all_store(self) -> None:
        items = [{"score": 4}, {"score": 5}, {"score": 6}]
        result = rss_sorting.select_for_log(items)
        assert len(result) == 3

    def test_custom_thresholds(self) -> None:
        items = [{"score": 3}]  # Normally degrade, but with threshold_low=2 -> store
        result = rss_sorting.select_for_log(items, threshold_low=2)
        assert len(result) == 1


class TestIntegration:
    """Integration tests for sorting module."""

    def test_full_workflow(self) -> None:
        """Test the complete sorting workflow with realistic data."""
        items = [
            {
                "title": "Major Banking AI Breakthrough",
                "score": 9,
                "link": "https://example.com/1",
                "source": "TechNews",
            },
            {
                "title": "Standard FinTech Update",
                "score": 5,
                "link": "https://example.com/2",
                "source": "FinNews",
            },
            {
                "title": "Minor Crypto Price Movement",
                "score": 2,
                "link": "https://example.com/3",
                "source": "CryptoFeed",
            },
            {
                "title": "Important Regulatory Change",
                "score": 8,
                "link": "https://example.com/4",
                "source": "RegNews",
            },
        ]

        # Sort by fate
        compartments = rss_sorting.sort_by_fate(items)
        assert len(compartments[rss_sorting.FATE_TRANSCYTOSE]) == 2
        assert len(compartments[rss_sorting.FATE_STORE]) == 1
        assert len(compartments[rss_sorting.FATE_DEGRADE]) == 1

        # Select for log
        log_items = rss_sorting.select_for_log(items)
        assert len(log_items) == 3

        # Verify degraded item excluded
        titles = [item["title"] for item in log_items]
        assert "Minor Crypto Price Movement" not in titles

    def test_string_scores_in_workflow(self) -> None:
        """Test that string scores work throughout the pipeline."""
        items = [
            {"title": "String Score 8", "score": "8"},
            {"title": "String Score 5", "score": "5"},
            {"title": "String Score 2", "score": "2"},
        ]

        compartments = rss_sorting.sort_by_fate(items)
        assert len(compartments[rss_sorting.FATE_TRANSCYTOSE]) == 1
        assert len(compartments[rss_sorting.FATE_STORE]) == 1
        assert len(compartments[rss_sorting.FATE_DEGRADE]) == 1
