"""Tests for receptor_sense organelle."""

import datetime
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
import yaml

from metabolon.organelles.receptor_sense import (
    current_phase,
    restore_goals,
    ProprioceptiveStore,
    decode_flashcard_deck,
    synthesize_signal_summary,
    _goal_slugs,
)


class TestCurrentPhase:
    """Tests for current_phase function."""

    def test_terminal_phase_no_until(self):
        """Last phase with no until is always returned."""
        phases = [
            {"name": "phase1", "until": "2025-01-01"},
            {"name": "terminal"},
        ]
        today = datetime.date(2024, 1, 1)
        result = current_phase(phases, today)
        assert result["name"] == "phase1"

        today = datetime.date(2026, 1, 1)
        result = current_phase(phases, today)
        assert result["name"] == "terminal"

    def test_all_phases_passed_returns_last(self):
        """All dates passed returns last phase even if it has until."""
        phases = [
            {"name": "phase1", "until": "2024-01-01"},
            {"name": "phase2", "until": "2025-01-01"},
        ]
        today = datetime.date(2026, 1, 1)
        result = current_phase(phases, today)
        assert result["name"] == "phase2"

    def test_before_first_phase_returns_first(self):
        """Before first phase's until returns first phase."""
        phases = [
            {"name": "phase1", "until": "2030-01-01"},
            {"name": "phase2"},
        ]
        today = datetime.date(2026, 1, 1)
        result = current_phase(phases, today)
        assert result["name"] == "phase1"


class TestRestoreGoals:
    """Tests for restore_goals function."""

    def test_directory_not_exists_returns_empty(self):
        """Non-existent directory returns empty list."""
        with patch.object(Path, "exists", return_value=False):
            result = restore_goals(Path("/nonexistent"))
        assert result == []

    def test_loads_yaml_files(self):
        """Loads and parses YAML files correctly."""
        mock_goal = {"name": "Test Goal", "description": "test"}
        yaml_content = yaml.dump(mock_goal)

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "glob", return_value=[Path("test.yaml")]):
                with patch("builtins.open", mock_open(read_data=yaml_content)):
                    result = restore_goals(Path("/goals"))
        assert len(result) == 1
        assert result[0]["name"] == "Test Goal"
        assert "_file" in result[0]

    def test_empty_yaml_skipped(self):
        """Empty YAML is skipped."""
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "glob", return_value=[Path("empty.yaml")]):
                with patch("builtins.open", mock_open(read_data="")):
                    result = restore_goals(Path("/goals"))
        assert result == []


class TestProprioceptiveStore:
    """Tests for ProprioceptiveStore class."""

    def test_init_sets_path(self):
        """Initialization stores path correctly."""
        path = Path("/tmp/test.jsonl")
        store = ProprioceptiveStore(path)
        assert store.path == path

    def test_recall_no_file_returns_empty(self):
        """No existing file returns empty list."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)
        temp_path.unlink()
        store = ProprioceptiveStore(temp_path)
        assert store.recall_all() == []
        if temp_path.exists():
            temp_path.unlink()

    def test_append_creates_parent_dir(self):
        """Append creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "signals" / "store.jsonl"
            store = ProprioceptiveStore(store_path)
            assert not store_path.parent.exists()

            store.append(
                goal="test-goal",
                material="test",
                category="D1",
                score=80,
                drill_type="flashcard",
            )

            assert store_path.parent.exists()
            assert store_path.exists()
            content = store_path.read_text()
            assert len(content.strip().splitlines()) == 1
            entry = json.loads(content.strip())
            assert entry["goal"] == "test-goal"
            assert entry["category"] == "D1"
            assert entry["score"] == 80

    def test_recall_all_parses_entries(self):
        """Recall all correctly parses JSONL entries."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            entry1 = {"ts": "2026-01-01T10:00:00Z", "goal": "goal1", "score": 70}
            entry2 = {"ts": "2026-01-02T10:00:00Z", "goal": "goal2", "score": 80}
            f.write(json.dumps(entry1) + "\n")
            f.write(json.dumps(entry2) + "\n")
            f.write("\n")  # empty line
            temp_path = Path(f.name)

        try:
            store = ProprioceptiveStore(temp_path)
            entries = store.recall_all()
            assert len(entries) == 2
            assert entries[0]["goal"] == "goal1"
            assert entries[1]["score"] == 80
        finally:
            temp_path.unlink()

    def test_recall_all_skips_bad_json(self):
        """Invalid JSON lines are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"valid": true}\n')
            f.write('not valid json\n')
            f.write('{"another_valid": 42}\n')
            temp_path = Path(f.name)

        try:
            store = ProprioceptiveStore(temp_path)
            entries = store.recall_all()
            assert len(entries) == 2
        finally:
            temp_path.unlink()

    def test_recall_since_filters_by_timestamp(self):
        """recall_since only returns entries after given timestamp."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"ts": "2026-01-01T10:00:00"}) + "\n")
            f.write(json.dumps({"ts": "2026-01-03T10:00:00"}) + "\n")
            temp_path = Path(f.name)

        try:
            store = ProprioceptiveStore(temp_path)
            since = datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC)
            entries = store.recall_since(since)
            assert len(entries) == 1
            assert entries[0]["ts"] == "2026-01-03T10:00:00"
        finally:
            temp_path.unlink()


class TestDecodeFlashcardDeck:
    """Tests for decode_flashcard_deck function."""

    def test_empty_file_returns_empty(self):
        """Empty file returns empty list."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)
        try:
            cards = decode_flashcard_deck(temp_path)
            assert cards == []
        finally:
            temp_path.unlink()

    def test_parses_cards_correctly(self):
        """Parses cards with expected format."""
        content = """## D1 — First Category
### Card 1 — D1 — Multiple Choice
**Q:** What is the answer to question 1?
**A:** It's definitely option B.

### Card 2 — D2 — Short Answer
**Q:** Explain the concept.
**A:** This is the explanation that spans
multiple lines correctly.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        try:
            cards = decode_flashcard_deck(temp_path)
            assert len(cards) == 2

            # First card
            assert cards[0]["category"] == "D1"
            assert cards[0]["card_type"] == "Multiple Choice"
            assert cards[0]["question"] == "What is the answer to question 1?"
            assert cards[0]["answer"] == "It's definitely option B."

            # Second card
            assert cards[1]["category"] == "D2"
            assert cards[1]["card_type"] == "Short Answer"
            assert cards[1]["question"] == "Explain the concept."
            assert cards[1]["answer"] == "This is the explanation that spans\nmultiple lines correctly"
        finally:
            temp_path.unlink()

    def test_skips_non_card_sections(self):
        """Non-card content is skipped."""
        content = """# This is a deck
Introduction here.

## D1
Some text that doesn't have a card.

### Card 1 — D1 — Type
**Q:** Question?
**A:** Answer.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        try:
            cards = decode_flashcard_deck(temp_path)
            assert len(cards) == 1
            assert cards[0]["question"] == "Question?"
        finally:
            temp_path.unlink()


class TestGoalSlugs:
    """Tests for _goal_slugs helper."""

    def test_generates_slugs(self):
        """Generates all expected slug forms."""
        goal = {
            "name": "Test Goal",
            "_file": "/path/to/test-goal.yaml",
        }
        slugs = _goal_slugs(goal)
        assert slugs == {"Test Goal", "test-goal", "test-goal"}

    def test_handles_missing_name(self):
        """Handles missing name gracefully."""
        goal = {
            "_file": "/path/to/test-goal.yaml",
        }
        slugs = _goal_slugs(goal)
        assert slugs == {"test-goal"}

    def test_handles_missing_file(self):
        """Handles missing file gracefully."""
        goal = {
            "name": "Test Goal",
        }
        slugs = _goal_slugs(goal)
        assert slugs == {"Test Goal", "test-goal"}


class TestSynthesizeSignalSummary:
    """Tests for synthesize_signal_summary function."""

    def test_empty_store_returns_zero_scores(self):
        """With no signals, all categories have 0 average score."""
        goal = {
            "name": "Test Goal",
            "phases": [{"name": "Active", "until": "2030-01-01"}],
            "materials": [
                {"categories": ["D1", "D2"]},
            ],
        }
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)
        temp_path.unlink()

        store = ProprioceptiveStore(temp_path)
        today = datetime.date(2026, 1, 1)
        summary = synthesize_signal_summary(goal, store, today)

        assert summary["goal"] == "Test Goal"
        assert summary["phase"] == "Active"
        assert summary["days_to_next_phase"] == 1460  # 2030-01-01 - 2026-01-01
        assert list(summary["categories"].keys()) == ["D1", "D2"]
        assert summary["categories"]["D1"]["avg_score"] == 0
        assert summary["categories"]["D1"]["drill_count"] == 0
        assert summary["weakest"] == ["D1", "D2"]
        assert summary["total_drills"] == 0

        if temp_path.exists():
            temp_path.unlink()

    def test_aggregates_scores_by_category(self):
        """Aggregates multiple scores correctly by category."""
        goal = {
            "name": "test-goal",
            "phases": [{"name": "Active"}],
            "materials": [
                {"categories": ["D1", "D2"]},
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            entries = [
                {"ts": "2026-01-01T10:00:00", "goal": "test-goal", "category": "D1", "score": 70, "drill_type": "flashcard"},
                {"ts": "2026-01-02T10:00:00", "goal": "test-goal", "category": "D1", "score": 90, "drill_type": "flashcard"},
                {"ts": "2026-01-03T10:00:00", "goal": "test-goal", "category": "D2", "score": 80, "drill_type": "flashcard"},
            ]
            for e in entries:
                f.write(json.dumps(e) + "\n")
            temp_path = Path(f.name)

        store = ProprioceptiveStore(temp_path)
        today = datetime.date(2026, 1, 1)
        summary = synthesize_signal_summary(goal, store, today)

        assert summary["categories"]["D1"]["avg_score"] == 80.0
        assert summary["categories"]["D1"]["drill_count"] == 2
        assert summary["categories"]["D2"]["avg_score"] == 80.0
        assert summary["categories"]["D2"]["drill_count"] == 1
        assert summary["total_drills"] == 3

        # D1 and D2 same avg, sorted alphabetically
        assert summary["weakest"][0] in ["D1", "D2"]

        temp_path.unlink()

    def test_finds_weakest_categories(self):
        """Correctly identifies 3 weakest categories."""
        goal = {
            "name": "test",
            "phases": [{"name": "Active"}],
            "materials": [
                {"categories": ["D1", "D2", "D3", "D4"]},
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            scores = [
                ("D1", 50),
                ("D2", 60),
                ("D3", 70),
                ("D4", 80),
            ]
            for i, (cat, score) in enumerate(scores):
                entry = {
                    "ts": f"2026-01-0{i+1}T10:00:00",
                    "goal": "test",
                    "category": cat,
                    "score": score,
                    "drill_type": "flashcard",
                }
                f.write(json.dumps(entry) + "\n")
            temp_path = Path(f.name)

        store = ProprioceptiveStore(temp_path)
        summary = synthesize_signal_summary(goal, store, datetime.date(2026, 1, 1))
        assert summary["weakest"] == ["D1", "D2", "D3"]

        temp_path.unlink()

    def test_deduplicates_by_timestamp(self):
        """Duplicate timestamps are deduplicated."""
        goal = {
            "name": "test",
            "phases": [{"name": "Active"}],
            "materials": [{"categories": ["D1"]}],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Two entries with same timestamp
            entry = {"ts": "2026-01-01T10:00:00", "goal": "test", "category": "D1", "score": 50, "drill_type": "flashcard"}
            f.write(json.dumps(entry) + "\n")
            f.write(json.dumps(entry) + "\n")
            temp_path = Path(f.name)

        store = ProprioceptiveStore(temp_path)
        summary = synthesize_signal_summary(goal, store, datetime.date(2026, 1, 1))
        assert summary["total_drills"] == 1
        assert summary["categories"]["D1"]["drill_count"] == 1

        temp_path.unlink()
