"""Tests for endocytosis_rss/sorting.py - fate-based cargo sorting."""

from __future__ import annotations

from metabolon.organelles.endocytosis_rss.sorting import (
    FATE_DEGRADE,
    FATE_STORE,
    FATE_TRANSCYTOSE,
    _cargo_score,
    sort_by_fate,
    select_for_log,
)


def test_fate_constants():
    """Test fate constants are defined correctly."""
    assert FATE_TRANSCYTOSE == "transcytose"
    assert FATE_STORE == "store"
    assert FATE_DEGRADE == "degrade"


def test_cargo_score_int():
    """Test _cargo_score extracts integer score."""
    assert _cargo_score({"score": 5}) == 5
    assert _cargo_score({"score": 10}) == 10


def test_cargo_score_string():
    """Test _cargo_score converts string score to int."""
    assert _cargo_score({"score": "7"}) == 7
    assert _cargo_score({"score": "0"}) == 0


def test_cargo_score_missing():
    """Test _cargo_score returns 0 for missing score."""
    assert _cargo_score({}) == 0
    assert _cargo_score({"other": "field"}) == 0


def test_cargo_score_invalid():
    """Test _cargo_score returns 0 for invalid score."""
    assert _cargo_score({"score": "invalid"}) == 0
    assert _cargo_score({"score": None}) == 0


def test_sort_by_fate_empty():
    """Test sort_by_fate returns empty compartments for empty input."""
    result = sort_by_fate([])
    assert result[FATE_TRANSCYTOSE] == []
    assert result[FATE_STORE] == []
    assert result[FATE_DEGRADE] == []


def test_sort_by_fate_transcytose():
    """Test sort_by_fate routes high scores to transcytose."""
    items = [{"title": "Important", "score": 8}]
    result = sort_by_fate(items, threshold_high=7)
    assert len(result[FATE_TRANSCYTOSE]) == 1
    assert result[FATE_STORE] == []
    assert result[FATE_DEGRADE] == []


def test_sort_by_fate_store():
    """Test sort_by_fate routes medium scores to store."""
    items = [{"title": "Moderate", "score": 5}]
    result = sort_by_fate(items, threshold_high=7, threshold_low=4)
    assert result[FATE_TRANSCYTOSE] == []
    assert len(result[FATE_STORE]) == 1
    assert result[FATE_DEGRADE] == []


def test_sort_by_fate_degrade():
    """Test sort_by_fate routes low scores to degrade."""
    items = [{"title": "Low", "score": 2}]
    result = sort_by_fate(items, threshold_low=4)
    assert result[FATE_TRANSCYTOSE] == []
    assert result[FATE_STORE] == []
    assert len(result[FATE_DEGRADE]) == 1


def test_sort_by_fate_default_thresholds():
    """Test sort_by_fate uses default thresholds (high=7, low=4)."""
    items = [
        {"score": 8},   # transcytose
        {"score": 6},   # store
        {"score": 2},   # degrade
        {"score": 7},   # transcytose (boundary)
        {"score": 4},   # store (boundary)
    ]
    result = sort_by_fate(items)
    assert len(result[FATE_TRANSCYTOSE]) == 2
    assert len(result[FATE_STORE]) == 2
    assert len(result[FATE_DEGRADE]) == 1


def test_sort_by_fate_custom_thresholds():
    """Test sort_by_fate respects custom thresholds."""
    items = [{"score": 5}]
    
    # Score 5 is transcytose with low threshold
    result = sort_by_fate(items, threshold_high=4, threshold_low=2)
    assert len(result[FATE_TRANSCYTOSE]) == 1
    
    # Score 5 is degrade with high thresholds
    result = sort_by_fate(items, threshold_high=10, threshold_low=8)
    assert len(result[FATE_DEGRADE]) == 1


def test_sort_by_fate_preserves_items():
    """Test sort_by_fate doesn't modify original items."""
    items = [{"title": "Test", "score": 5, "extra": "data"}]
    result = sort_by_fate(items)
    assert result[FATE_STORE][0]["extra"] == "data"


def test_select_for_log_excludes_degrade():
    """Test select_for_log only returns transcytose and store items."""
    items = [
        {"score": 8, "name": "high"},
        {"score": 5, "name": "mid"},
        {"score": 2, "name": "low"},
    ]
    result = select_for_log(items)
    
    assert len(result) == 2
    names = {item["name"] for item in result}
    assert "high" in names
    assert "mid" in names
    assert "low" not in names


def test_select_for_log_preserves_order():
    """Test select_for_log preserves original order (transcytose first)."""
    items = [
        {"score": 5, "order": 1},
        {"score": 8, "order": 2},
        {"score": 6, "order": 3},
    ]
    result = select_for_log(items)
    
    # Transcytose items (score >= 7) come first
    assert result[0]["order"] == 2
    assert result[1]["order"] == 1
    assert result[2]["order"] == 3


def test_select_for_log_empty():
    """Test select_for_log returns empty list for empty input."""
    assert select_for_log([]) == []


def test_select_for_log_all_degrade():
    """Test select_for_log returns empty when all items degrade."""
    items = [{"score": 1}, {"score": 2}, {"score": 3}]
    assert select_for_log(items, threshold_low=4) == []


def test_select_for_log_custom_thresholds():
    """Test select_for_log respects custom thresholds."""
    items = [{"score": 3}]
    
    # With low threshold, item is included
    result = select_for_log(items, threshold_low=2)
    assert len(result) == 1
    
    # With higher threshold, item is degraded
    result = select_for_log(items, threshold_low=5)
    assert len(result) == 0
