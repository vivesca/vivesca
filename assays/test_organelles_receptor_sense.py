"""Tests for receptor_sense organelle.

All external filesystem operations are mocked.
"""

import datetime
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from metabolon.organelles.receptor_sense import (
    GOALS_DIR,
    ProprioceptiveStore,
    current_phase,
    decode_flashcard_deck,
    restore_goals,
    synthesize_signal_summary,
    _goal_slugs,
)


def test_current_phase_returns_first_matching():
    """Test current_phase selects correct phase based on date."""
    phases = [
        {"name": "early", "until": "2025-01-01"},
        {"name": "mid", "until": "2025-06-01"},
        {"name": "late"},
    ]
    
    result = current_phase(phases, today=datetime.date(2024, 12, 31))
    assert result["name"] == "early"
    
    result = current_phase(phases, today=datetime.date(2025, 1, 1))
    assert result["name"] == "mid"
    
    result = current_phase(phases, today=datetime.date(2025, 6, 1))
    assert result["name"] == "late"
    
    result = current_phase(phases, today=datetime.date(2025, 12, 31))
    assert result["name"] == "late"


def test_restore_goals_returns_empty_when_directory_missing():
    """Test restore_goals returns empty list when directory doesn't exist."""
    fake_dir = Path("/nonexistent/path/that/never/exists")
    result = restore_goals(goals_dir=fake_dir)
    assert result == []


def test_restore_goals_loads_yaml_files(tmp_path):
    """Test restore_goals loads and parses all YAML files from directory."""
    # Create test goal files
    goal1 = tmp_path / "goal1.yaml"
    goal1.write_text("name: Test Goal 1\nphases: []\n")
    
    goal2 = tmp_path / "goal2.yaml"
    goal2.write_text("name: Test Goal 2\nphases: [{name: phase1}]\n")
    
    # Empty file should be skipped
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    
    result = restore_goals(goals_dir=tmp_path)
    
    assert len(result) == 2
    assert any(g["name"] == "Test Goal 1" for g in result)
    assert any(g["name"] == "Test Goal 2" for g in result)
    assert all("_file" in g for g in result)


class TestProprioceptiveStore:
    """Tests for ProprioceptiveStore append-only JSONL store."""

    def test_store_creates_parent_dirs(self):
        """Test store creates parent directories when appending."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "signals.jsonl"
            store = ProprioceptiveStore(path)
            assert not path.exists()
            
            store.append(
                goal="test-goal",
                material="test",
                category="D1",
                score=3,
                drill_type="flashcard",
            )
            
            assert path.exists()

    def test_append_and_recall_all(self):
        """Test appending entries and recalling all."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "signals.jsonl"
            store = ProprioceptiveStore(path)
            
            store.append(
                goal="goal1",
                material="mat1",
                category="D1",
                score=4,
                drill_type="flashcard",
            )
            store.append(
                goal="goal2",
                material="mat2",
                category="D2",
                score=2,
                drill_type="multiple-choice",
                extra_field="value",
            )
            
            entries = store.recall_all()
            assert len(entries) == 2
            assert entries[0]["goal"] == "goal1"
            assert entries[0]["score"] == 4
            assert entries[1]["goal"] == "goal2"
            assert entries[1]["extra_field"] == "value"
            assert "ts" in entries[0]

    def test_recall_all_returns_empty_when_file_missing(self):
        """Test recall_all returns empty when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent.jsonl"
            store = ProprioceptiveStore(path)
            assert store.recall_all() == []

    def test_recall_all_skips_bad_json(self):
        """Test recall_all skips invalid JSON lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "signals.jsonl"
            path.write_text('{"valid": true}\nnot valid json\n{"another": 42}\n')
            
            store = ProprioceptiveStore(path)
            entries = store.recall_all()
            
            assert len(entries) == 2
            assert entries[0]["valid"] is True
            assert entries[1]["another"] == 42

    def test_recall_since_filters_by_timestamp(self):
        """Test recall_since filters entries by timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "signals.jsonl"
            store = ProprioceptiveStore(path)
            
            # We'll manually create entries with known timestamps
            # to avoid sleeping in tests
            path.write_text(json.dumps({
                "ts": "2025-01-01T00:00:00+00:00",
                "goal": "old",
                "score": 1
            }) + "\n")
            path.write_text(json.dumps({
                "ts": "2025-02-01T00:00:00+00:00",
                "goal": "new",
                "score": 2
            }) + "\n")
            
            since = datetime.datetime(2025, 1, 15, tzinfo=datetime.UTC)
            entries = store.recall_since(since)
            
            assert len(entries) == 1
            assert entries[0]["goal"] == "new"


def test_decode_flashcard_deck_parses_correctly(tmp_path):
    """Test decode_flashcard_deck parses markdown deck into structured cards."""
    markdown_content = """## D1 — First Category

### Card 1 — D1 — Basic Recall
**Q:** What is the capital of France?
**A:** Paris

### Card 2 — D1 — Application
**Q:** Explain why water boils at higher altitude.
**A:** Lower atmospheric pressure reduces boiling point.

## D2 — Second Category

### Card 3 — D2 — Terminology
**Q:** Define photosynthesis.
**A:** Process by which plants convert light to energy.
"""
    deck_path = tmp_path / "deck.md"
    deck_path.write_text(markdown_content)
    
    cards = decode_flashcard_deck(deck_path)
    
    assert len(cards) == 3
    
    # Check first card
    assert cards[0]["category"] == "D1"
    assert cards[0]["card_type"] == "Basic Recall"
    assert "capital of France" in cards[0]["question"]
    assert cards[0]["answer"] == "Paris"
    
    # Check second card
    assert cards[1]["category"] == "D1"
    assert cards[1]["card_type"] == "Application"
    
    # Check third card
    assert cards[2]["category"] == "D2"
    assert cards[2]["card_type"] == "Terminology"


def test_decode_flashcard_deck_skips_non_card_content(tmp_path):
    """Test decode_flashcard_deck skips content that doesn't match card pattern."""
    markdown_content = """# My Deck

Some introductory text here that doesn't match.

## D1

Just a section with no cards.
"""
    deck_path = tmp_path / "deck.md"
    deck_path.write_text(markdown_content)
    
    cards = decode_flashcard_deck(deck_path)
    assert len(cards) == 0


def test_goal_slugs_generates_correct_slugs():
    """Test _goal_slugs generates all plausible slugs for matching."""
    goal = {
        "name": "Test Goal",
        "_file": "/path/to/test-goal.yaml",
    }
    
    slugs = _goal_slugs(goal)
    
    assert slugs == {"Test Goal", "test-goal", "test-goal"}


def test_goal_slugs_handles_missing_fields():
    """Test _goal_slugs handles goals with missing name/_file fields."""
    goal = {}
    slugs = _goal_slugs(goal)
    assert slugs == set()
    
    goal = {"name": "OnlyName"}
    slugs = _goal_slugs(goal)
    assert slugs == {"OnlyName", "onlyname"}


def test_synthesize_signal_summary_aggregates_scores():
    """Test synthesize_signal_summary aggregates scores by category."""
    # Create a test goal
    goal = {
        "name": "Test Goal",
        "phases": [
            {"name": "Active", "until": "2026-12-31"},
        ],
        "materials": [
            {"categories": ["D1", "D2"]},
            {"categories": ["D3"]},
        ],
        "_file": "/path/test-goal.yaml",
    }
    
    # Create mock store with some signals
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test-signals.jsonl"
        store = ProprioceptiveStore(path)
        
        # Add some signals matching this goal
        store.append(goal="test-goal", material="a", category="D1", score=4, drill_type="drill")
        store.append(goal="test-goal", material="b", category="D1", score=2, drill_type="drill")
        store.append(goal="test-goal", material="c", category="D2", score=5, drill_type="drill")
        # D3 has no drills → avg 0
        
        summary = synthesize_signal_summary(goal, store, today=datetime.date(2026, 1, 1))
    
    assert summary["goal"] == "Test Goal"
    assert summary["phase"] == "Active"
    assert summary["days_to_next_phase"] == 364  # 2026 is leap year
    assert summary["total_drills"] == 3
    
    # Check category aggregates
    categories = summary["categories"]
    assert "D1" in categories
    assert "D2" in categories
    assert "D3" in categories
    
    assert categories["D1"]["avg_score"] == 3.0  # (4+2)/2
    assert categories["D1"]["drill_count"] == 2
    assert categories["D2"]["avg_score"] == 5.0
    assert categories["D2"]["drill_count"] == 1
    assert categories["D3"]["avg_score"] == 0.0
    assert categories["D3"]["drill_count"] == 0
    assert categories["D3"]["last_drilled"] == "never"
    
    # Weakest should be D3 (0), D1 (3), D2 (5)
    assert summary["weakest"] == ["D3", "D1", "D2"]


def test_synthesize_signal_summary_handles_no_signals():
    """Test synthesize_signal_summary works when no signals exist."""
    goal = {
        "name": "Empty Goal",
        "phases": [{"name": "Start"}],
        "materials": [{"categories": ["D1"]}],
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "empty.jsonl"
        store = ProprioceptiveStore(path)
        
        summary = synthesize_signal_summary(goal, store, today=datetime.date.today())
    
    assert summary["total_drills"] == 0
    assert summary["categories"]["D1"]["avg_score"] == 0
    assert summary["weakest"] == ["D1"]


def test_synthesize_signal_summary_finds_weakest():
    """Test synthesize_signal_summary correctly identifies weakest categories."""
    goal = {
        "name": "Scoring Test",
        "phases": [{"name": "P1"}],
        "materials": [{"categories": ["A", "B", "C", "D"]}],
        "_file": "scoring-test",
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "signals.jsonl"
        store = ProprioceptiveStore(path)
        
        store.append(goal="scoring-test", category="A", score=5, drill_type="x", material="m")
        store.append(goal="scoring-test", category="B", score=2, drill_type="x", material="m")
        store.append(goal="scoring-test", category="C", score=4, drill_type="x", material="m")
        store.append(goal="scoring-test", category="D", score=3, drill_type="x", material="m")
        
        summary = synthesize_signal_summary(goal, store, today=datetime.date.today())
        
        # Weakest order: B (2), D (3), C (4) → top 3 weakest
        assert summary["weakest"] == ["B", "D", "C"]
