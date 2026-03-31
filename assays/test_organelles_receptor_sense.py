from __future__ import annotations

"""Tests for receptor_sense organelle."""


import datetime
import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from metabolon.organelles.receptor_sense import (
    GOALS_DIR,
    ProprioceptiveStore,
    current_phase,
    decode_flashcard_deck,
    restore_goals,
    synthesize_signal_summary,
)


def test_current_phase_before_first_deadline():
    """Test current_phase returns first phase when today is before its deadline."""
    phases = [
        {"name": "phase1", "until": "2030-01-01"},
        {"name": "phase2", "until": "2030-02-01"},
        {"name": "phase3"},
    ]
    today = datetime.date(2025, 1, 1)
    result = current_phase(phases, today)
    assert result == phases[0]


def test_current_phase_between_deadlines():
    """Test current_phase returns correct phase when between deadlines."""
    phases = [
        {"name": "phase1", "until": "2025-01-01"},
        {"name": "phase2", "until": "2030-02-01"},
        {"name": "phase3"},
    ]
    today = datetime.date(2025, 1, 15)
    result = current_phase(phases, today)
    assert result == phases[1]


def test_current_phase_after_all_deadlines():
    """Test current_phase returns last phase when all deadlines passed."""
    phases = [
        {"name": "phase1", "until": "2025-01-01"},
        {"name": "phase2", "until": "2025-02-01"},
        {"name": "phase3"},
    ]
    today = datetime.date(2030, 1, 1)
    result = current_phase(phases, today)
    assert result == phases[2]


def test_current_phase_no_until_in_middle_phase():
    """Test that a middle phase without until returns immediately."""
    phases = [
        {"name": "phase1", "until": "2025-01-01"},
        {"name": "phase2"},
        {"name": "phase3", "until": "2030-01-01"},
    ]
    today = datetime.date(2025, 1, 15)
    result = current_phase(phases, today)
    assert result == phases[1]


def test_restore_goals_directory_not_exists():
    """Test restore_goals returns empty list when directory doesn't exist."""
    fake_dir = Path("/does/not/exist")
    result = restore_goals(fake_dir)
    assert result == []


def test_restore_goals_empty_directory(tmp_path: Path):
    """Test restore_goals returns empty list when directory is empty."""
    result = restore_goals(tmp_path)
    assert result == []


def test_restore_goals_loads_multiple_files(tmp_path: Path):
    """Test restore_goals loads and parses multiple YAML files."""
    # Create two goal files
    goal1 = {"name": "Goal 1", "description": "First goal"}
    goal2 = {"name": "Goal 2", "description": "Second goal"}

    (tmp_path / "goal1.yaml").write_text(yaml.dump(goal1))
    (tmp_path / "goal2.yaml").write_text(yaml.dump(goal2))

    result = restore_goals(tmp_path)
    assert len(result) == 2
    # Sorted by filename
    assert result[0]["name"] == "Goal 1"
    assert result[1]["name"] == "Goal 2"
    # Check _file was added
    assert "_file" in result[0]
    assert str(tmp_path / "goal1.yaml") in result[0]["_file"]


def test_restore_goals_skips_empty_files(tmp_path: Path):
    """Test restore_goals skips empty YAML files."""
    (tmp_path / "empty.yaml").write_text("")
    result = restore_goals(tmp_path)
    assert result == []


class TestProprioceptiveStore:
    """Tests for ProprioceptiveStore class."""

    def test_append_creates_directory_and_writes_entry(self, tmp_path: Path):
        """Test append creates parent directory and writes JSONL entry."""
        store_path = tmp_path / "signals" / "signals.jsonl"
        store = ProprioceptiveStore(store_path)

        store.append(
            goal="test-goal",
            material="test-material",
            category="D1",
            score=3,
            drill_type="timed",
        )

        assert store_path.exists()
        lines = list(store_path.read_text().splitlines())
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["goal"] == "test-goal"
        assert entry["material"] == "test-material"
        assert entry["category"] == "D1"
        assert entry["score"] == 3
        assert entry["drill_type"] == "timed"
        assert "ts" in entry

    def test_recall_all_no_file(self, tmp_path: Path):
        """Test recall_all returns empty list when file doesn't exist."""
        store_path = tmp_path / "nonexistent.jsonl"
        store = ProprioceptiveStore(store_path)
        assert store.recall_all() == []

    def test_recall_all_with_entries(self, tmp_path: Path):
        """Test recall_all correctly parses JSONL entries."""
        store_path = tmp_path / "signals.jsonl"
        entries = [
            {
                "ts": "2025-01-01T00:00:00+00:00",
                "goal": "goal1",
                "category": "D1",
                "score": 3,
                "drill_type": "drill",
            },
            {
                "ts": "2025-01-02T00:00:00+00:00",
                "goal": "goal1",
                "category": "D2",
                "score": 4,
                "drill_type": "drill",
            },
        ]

        with open(store_path, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        store = ProprioceptiveStore(store_path)
        recalled = store.recall_all()
        assert len(recalled) == 2
        assert recalled[0]["goal"] == "goal1"
        assert recalled[1]["category"] == "D2"

    def test_recall_all_skips_bad_json(self, tmp_path: Path):
        """Test recall_all skips invalid JSON lines."""
        store_path = tmp_path / "signals.jsonl"
        with open(store_path, "w") as f:
            f.write('{"valid": true}\n')
            f.write("not valid json\n")
            f.write('{"another_valid": 42}\n')

        store = ProprioceptiveStore(store_path)
        recalled = store.recall_all()
        assert len(recalled) == 2

    def test_recall_since_filters_by_timestamp(self, tmp_path: Path):
        """Test recall_since returns only entries after given timestamp."""
        store_path = tmp_path / "signals.jsonl"
        entries = [
            {"ts": "2025-01-01T00:00:00+00:00", "goal": "g1"},
            {"ts": "2025-01-02T00:00:00+00:00", "goal": "g2"},
            {"ts": "2025-01-03T00:00:00+00:00", "goal": "g3"},
        ]
        with open(store_path, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

        store = ProprioceptiveStore(store_path)
        since = datetime.datetime(2025, 1, 2, 0, 0, 0, tzinfo=datetime.UTC)
        recalled = store.recall_since(since)
        assert len(recalled) == 2
        assert {e["goal"] for e in recalled} == {"g2", "g3"}


def test_decode_flashcard_deck_parses_correctly(tmp_path: Path):
    """Test decode_flashcard_deck correctly parses markdown flashcard deck."""
    markdown_content = """## D1 — First Category
### Card 1 — D1 — Multiple Choice
**Q:** What is the answer to question 1?
**A:** It's definitely answer A.

### Card 2 — D1 — Free Response
**Q:** Explain the concept.
**A:** The concept has three main principles...

## D2 — Second Category
### Card 3 — D2 — Term Definition
**Q:** Define X.
**A:** X is a Y that does Z.
"""
    deck_path = tmp_path / "deck.md"
    deck_path.write_text(markdown_content)

    cards = decode_flashcard_deck(deck_path)
    assert len(cards) == 3

    # Check first card
    assert cards[0]["category"] == "D1"
    assert cards[0]["card_type"] == "Multiple Choice"
    assert cards[0]["question"] == "What is the answer to question 1?"
    assert cards[0]["answer"] == "It's definitely answer A."

    # Check third card
    assert cards[2]["category"] == "D2"
    assert cards[2]["card_type"] == "Term Definition"
    assert cards[2]["question"] == "Define X."


def test_decode_flashcard_deck_skips_non_card_sections(tmp_path: Path):
    """Test decode_flashcard_deck skips sections that aren't cards."""
    markdown_content = """# This is a deck

Some introduction text here.

## D1 — Category
This is some intro text before any cards.

### Card 1 — D1 — Type
**Q:** Question?
**A:** Answer.
"""
    deck_path = tmp_path / "deck.md"
    deck_path.write_text(markdown_content)
    cards = decode_flashcard_deck(deck_path)
    assert len(cards) == 1
    assert cards[0]["question"] == "Question?"


def test_synthesize_signal_summary_no_signals():
    """Test synthesize_signal_summary handles goal with no signals."""
    today = datetime.date(2025, 1, 1)
    goal = {
        "name": "Test Goal",
        "phases": [{"name": "Active", "until": "2025-06-01"}],
        "materials": [
            {"name": "Material 1", "categories": ["D1", "D2"]},
            {"name": "Material 2", "categories": ["D3"]},
        ],
        "_file": "/test/test-goal.yaml",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "store.jsonl"
        store = ProprioceptiveStore(store_path)
        summary = synthesize_signal_summary(goal, store, today)

    assert summary["goal"] == "Test Goal"
    assert summary["phase"] == "Active"
    assert summary["days_to_next_phase"] == 151
    assert set(summary["categories"].keys()) == {"D1", "D2", "D3"}
    assert summary["categories"]["D1"]["avg_score"] == 0
    assert summary["categories"]["D1"]["drill_count"] == 0
    assert summary["weakest"] == ["D1", "D2", "D3"]
    assert summary["total_drills"] == 0


def test_synthesize_signal_summary_with_signals():
    """Test synthesize_signal_summary aggregates scores correctly."""
    today = datetime.date(2025, 1, 1)
    goal = {
        "name": "Test Goal",
        "phases": [{"name": "Active"}],
        "materials": [
            {"name": "Material 1", "categories": ["D1", "D2"]},
        ],
        "_file": "/test/test-goal.yaml",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "store.jsonl"
        store = ProprioceptiveStore(store_path)

        # Add some signals matching goal slugs (test-goal is stem from _file)
        store.append(goal="test-goal", material="mat1", category="D1", score=2, drill_type="drill")
        store.append(goal="test-goal", material="mat1", category="D1", score=4, drill_type="drill")
        store.append(goal="test-goal", material="mat2", category="D2", score=5, drill_type="drill")
        # Add a signal for another goal that should be ignored
        store.append(goal="other-goal", material="mat1", category="D1", score=1, drill_type="drill")

        summary = synthesize_signal_summary(goal, store, today)

    assert summary["total_drills"] == 3
    assert abs(summary["categories"]["D1"]["avg_score"] - 3.0) < 0.001
    assert summary["categories"]["D1"]["drill_count"] == 2
    assert summary["categories"]["D2"]["avg_score"] == 5.0
    assert summary["categories"]["D2"]["drill_count"] == 1
    # Weakest is D1 then D2
    assert summary["weakest"] == ["D1", "D2"]


def test_synthesize_signal_summary_deduplicates_by_timestamp():
    """Test synthesize_signal_summary deduplicates signals with same timestamp."""
    today = datetime.date(2025, 1, 1)
    goal = {
        "name": "Test Goal",
        "phases": [{"name": "Active"}],
        "materials": [{"name": "M1", "categories": ["D1"]}],
        "_file": "/test/test-goal.yaml",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "store.jsonl"
        store = ProprioceptiveStore(store_path)

        # Write duplicate entries manually with same timestamp
        entries = [
            {
                "ts": "2025-01-01T10:00:00+00:00",
                "goal": "test-goal",
                "category": "D1",
                "score": 2,
                "drill_type": "drill",
            },
            {
                "ts": "2025-01-01T10:00:00+00:00",
                "goal": "test-goal",
                "category": "D1",
                "score": 4,
                "drill_type": "drill",
            },
        ]
        with open(store_path, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

        summary = synthesize_signal_summary(goal, store, today)
        # Should only count one of them due to duplicate timestamp
        assert summary["total_drills"] == 1


def test_synthesize_signal_summary_terminal_phase_no_days():
    """Test synthesize_signal_summary returns None for days_to_next in terminal phase."""
    today = datetime.date(2025, 1, 1)
    goal = {
        "name": "Test Goal",
        "phases": [{"name": "Maintenance"}],
        "materials": [],
        "_file": "/test/test-goal.yaml",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "store.jsonl"
        store = ProprioceptiveStore(store_path)
        summary = synthesize_signal_summary(goal, store, today)

    assert summary["days_to_next_phase"] is None
