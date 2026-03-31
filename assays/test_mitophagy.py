from __future__ import annotations

"""Tests for mitophagy — model fitness tracking and auto-blacklist."""

import json
import time
from unittest.mock import patch

import pytest


class TestLoadBlacklist:
    def test_no_file(self, tmp_path):
        from metabolon.organelles.mitophagy import _load_blacklist
        import metabolon.organelles.mitophagy as mp
        with patch.object(mp, "_BLACKLIST_PATH", tmp_path / "nope.json"):
            assert _load_blacklist() == {}

    def test_valid_file(self, tmp_path):
        from metabolon.organelles.mitophagy import _load_blacklist
        import metabolon.organelles.mitophagy as mp
        f = tmp_path / "blacklist.json"
        f.write_text(json.dumps({"glm": ["probe"]}))
        with patch.object(mp, "_BLACKLIST_PATH", f):
            bl = _load_blacklist()
        assert bl == {"glm": ["probe"]}


class TestIsBlacklisted:
    def test_not_blacklisted(self, tmp_path):
        from metabolon.organelles.mitophagy import is_blacklisted
        import metabolon.organelles.mitophagy as mp
        with patch.object(mp, "_BLACKLIST_PATH", tmp_path / "nope.json"):
            assert is_blacklisted("glm", "probe") is False

    def test_blacklisted(self, tmp_path):
        from metabolon.organelles.mitophagy import is_blacklisted
        import metabolon.organelles.mitophagy as mp
        f = tmp_path / "blacklist.json"
        f.write_text(json.dumps({"glm": ["probe"]}))
        with patch.object(mp, "_BLACKLIST_PATH", f):
            assert is_blacklisted("glm", "probe") is True

    def test_different_task(self, tmp_path):
        from metabolon.organelles.mitophagy import is_blacklisted
        import metabolon.organelles.mitophagy as mp
        f = tmp_path / "blacklist.json"
        f.write_text(json.dumps({"glm": ["probe"]}))
        with patch.object(mp, "_BLACKLIST_PATH", f):
            assert is_blacklisted("glm", "coding") is False


class TestRecordOutcome:
    def test_appends_to_file(self, tmp_path):
        from metabolon.organelles.mitophagy import record_outcome
        import metabolon.organelles.mitophagy as mp
        outcomes = tmp_path / "outcomes.jsonl"
        with patch.object(mp, "_CACHE_DIR", tmp_path), \
             patch.object(mp, "_OUTCOMES_PATH", outcomes), \
             patch.object(mp, "_BLACKLIST_PATH", tmp_path / "bl.json"):
            record_outcome("glm", "probe", True, 500)
        assert outcomes.exists()
        entry = json.loads(outcomes.read_text().strip())
        assert entry["model"] == "glm"
        assert entry["success"] is True


class TestModelFitness:
    def test_empty_outcomes(self, tmp_path):
        from metabolon.organelles.mitophagy import model_fitness
        import metabolon.organelles.mitophagy as mp
        with patch.object(mp, "_OUTCOMES_PATH", tmp_path / "nope.jsonl"), \
             patch.object(mp, "_BLACKLIST_PATH", tmp_path / "bl.json"):
            assert model_fitness() == []

    def test_computes_rate(self, tmp_path):
        from metabolon.organelles.mitophagy import model_fitness
        import metabolon.organelles.mitophagy as mp
        f = tmp_path / "outcomes.jsonl"
        now = time.time()
        entries = [
            json.dumps({"ts": now, "model": "glm", "task_type": "probe", "success": True}),
            json.dumps({"ts": now, "model": "glm", "task_type": "probe", "success": False}),
        ]
        f.write_text("\n".join(entries) + "\n")
        with patch.object(mp, "_OUTCOMES_PATH", f), \
             patch.object(mp, "_BLACKLIST_PATH", tmp_path / "bl.json"):
            results = model_fitness(days=1)
        assert len(results) == 1
        assert results[0]["model"] == "glm"
        assert results[0]["attempts"] == 2
        assert results[0]["rate"] == 0.5


class TestRecommendModel:
    def test_fallback_when_no_data(self, tmp_path):
        from metabolon.organelles.mitophagy import recommend_model
        import metabolon.organelles.mitophagy as mp
        with patch.object(mp, "_OUTCOMES_PATH", tmp_path / "nope.jsonl"), \
             patch.object(mp, "_BLACKLIST_PATH", tmp_path / "bl.json"):
            assert recommend_model("probe") == "opus"

    def test_recommends_best(self, tmp_path):
        from metabolon.organelles.mitophagy import recommend_model
        import metabolon.organelles.mitophagy as mp
        f = tmp_path / "outcomes.jsonl"
        now = time.time()
        entries = [
            json.dumps({"ts": now, "model": "glm", "task_type": "probe", "success": True}),
            json.dumps({"ts": now, "model": "glm", "task_type": "probe", "success": True}),
            json.dumps({"ts": now, "model": "sonnet", "task_type": "probe", "success": False}),
        ]
        f.write_text("\n".join(entries) + "\n")
        with patch.object(mp, "_OUTCOMES_PATH", f), \
             patch.object(mp, "_BLACKLIST_PATH", tmp_path / "bl.json"):
            best = recommend_model("probe")
        assert best == "glm"
