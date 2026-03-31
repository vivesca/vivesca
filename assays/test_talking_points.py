"""Tests for talking points generator."""
from pathlib import Path
from unittest.mock import patch
import pytest

def test_talking_point_to_markdown():
    from metabolon.organelles.talking_points import TalkingPoint
    tp = TalkingPoint(
        thesis="AI governance reduces model risk",
        evidence="HKMA circular requires...",
        positioning="Frame as compliance enabler",
        source_asset="policy-001.md",
    )
    md = tp.to_markdown()
    assert "AI governance" in md
    assert "HKMA" in md

def test_talking_point_card_to_markdown():
    from metabolon.organelles.talking_points import TalkingPointCard, TalkingPoint
    card = TalkingPointCard(
        client="HSBC",
        meeting_context="AI governance kickoff",
        points=[
            TalkingPoint(thesis="Point 1", evidence="ev1", positioning="pos1", source_asset="a.md"),
        ],
        generated_at="2026-03-31 10:00",
    )
    md = card.to_markdown()
    assert "HSBC" in md
    assert "Point 1" in md

def test_score_relevance_client_match():
    from metabolon.organelles.talking_points import _score_relevance
    asset = {"content_preview": "HSBC AI governance framework", "title": "Policy", "domain": "banking"}
    score = _score_relevance(asset, "HSBC", "AI governance review")
    assert score > 0.3

def test_score_relevance_no_match():
    from metabolon.organelles.talking_points import _score_relevance
    asset = {"content_preview": "cooking recipe for pasta", "title": "Pasta", "domain": "food"}
    score = _score_relevance(asset, "HSBC", "AI governance review")
    assert score < 0.2

def test_scan_consulting_assets_missing_dir():
    from metabolon.organelles.talking_points import _scan_consulting_assets
    with patch("metabolon.organelles.talking_points.CONSULTING_DIR", Path("/nonexistent")):
        result = _scan_consulting_assets()
        assert result == []

def test_generate_talking_points_returns_card():
    from metabolon.organelles.talking_points import generate_talking_points
    # This will run against real consulting dir if it exists, or return empty
    card = generate_talking_points(client="Test", context="General meeting")
    assert card.client == "Test"
    assert isinstance(card.points, list)
    assert isinstance(card.to_markdown(), str)
