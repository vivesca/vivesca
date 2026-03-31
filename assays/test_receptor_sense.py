from __future__ import annotations

"""Tests for receptor_sense — proprioceptive readiness organelle."""

import datetime
import json
import tempfile
from pathlib import Path

import pytest
import yaml


class TestCurrentPhase:
    def test_returns_current_phase(self):
        from metabolon.organelles.receptor_sense import current_phase
        phases = [
            {"name": "prep", "until": "2026-04-01"},
            {"name": "exam", "until": "2026-04-15"},
            {"name": "done"},
        ]
        result = current_phase(phases, today=datetime.date(2026, 3, 25))
        assert result["name"] == "prep"

    def test_returns_next_phase_after_date(self):
        from metabolon.organelles.receptor_sense import current_phase
        phases = [
            {"name": "prep", "until": "2026-04-01"},
            {"name": "exam", "until": "2026-04-15"},
            {"name": "done"},
        ]
        result = current_phase(phases, today=datetime.date(2026, 4, 5))
        assert result["name"] == "exam"

    def test_returns_terminal_phase(self):
        from metabolon.organelles.receptor_sense import current_phase
        phases = [
            {"name": "prep", "until": "2026-04-01"},
            {"name": "done"},
        ]
        result = current_phase(phases, today=datetime.date(2026, 5, 1))
        assert result["name"] == "done"

    def test_single_terminal_phase(self):
        from metabolon.organelles.receptor_sense import current_phase
        phases = [{"name": "ongoing"}]
        result = current_phase(phases, today=datetime.date(2026, 1, 1))
        assert result["name"] == "ongoing"


class TestRestoreGoals:
    def test_empty_dir(self, tmp_path):
        from metabolon.organelles.receptor_sense import restore_goals
        assert restore_goals(tmp_path) == []

    def test_nonexistent_dir(self, tmp_path):
        from metabolon.organelles.receptor_sense import restore_goals
        assert restore_goals(tmp_path / "nope") == []

    def test_loads_yaml_files(self, tmp_path):
        from metabolon.organelles.receptor_sense import restore_goals
        goal = {"name": "GARP", "categories": ["risk", "ai"]}
        (tmp_path / "garp.yaml").write_text(yaml.dump(goal))
        goals = restore_goals(tmp_path)
        assert len(goals) == 1
        assert goals[0]["name"] == "GARP"
        assert "_file" in goals[0]

    def test_skips_empty_yaml(self, tmp_path):
        from metabolon.organelles.receptor_sense import restore_goals
        (tmp_path / "empty.yaml").write_text("")
        goals = restore_goals(tmp_path)
        assert goals == []


class TestProprioceptiveStore:
    def test_append_and_recall(self, tmp_path):
        from metabolon.organelles.receptor_sense import ProprioceptiveStore
        store = ProprioceptiveStore(tmp_path / "signals.jsonl")
        store.append(goal="GARP", material="M3", category="fairness", score=8, drill_type="flashcard")
        entries = store.recall_all()
        assert len(entries) == 1
        assert entries[0]["goal"] == "GARP"
        assert entries[0]["score"] == 8

    def test_recall_empty(self, tmp_path):
        from metabolon.organelles.receptor_sense import ProprioceptiveStore
        store = ProprioceptiveStore(tmp_path / "signals.jsonl")
        assert store.recall_all() == []

    def test_multiple_appends(self, tmp_path):
        from metabolon.organelles.receptor_sense import ProprioceptiveStore
        store = ProprioceptiveStore(tmp_path / "signals.jsonl")
        store.append(goal="A", material="M1", category="c1", score=5, drill_type="drill")
        store.append(goal="B", material="M2", category="c2", score=9, drill_type="mock")
        entries = store.recall_all()
        assert len(entries) == 2

    def test_recall_since_filters(self, tmp_path):
        from metabolon.organelles.receptor_sense import ProprioceptiveStore
        store = ProprioceptiveStore(tmp_path / "signals.jsonl")
        # Write an old entry by directly writing to file
        old_entry = {"ts": "2025-01-01T00:00:00", "goal": "old"}
        with open(tmp_path / "signals.jsonl", "w") as f:
            f.write(json.dumps(old_entry) + "\n")
        # Append a new one
        store.append(goal="new", material="M1", category="c", score=10, drill_type="drill")
        cutoff = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
        recent = store.recall_since(cutoff)
        assert len(recent) == 1
        assert recent[0]["goal"] == "new"
