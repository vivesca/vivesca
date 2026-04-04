from __future__ import annotations

"""Comprehensive tests for metabolon.organelles.mitophagy — all branches and edge cases."""

import json
import time
from unittest.mock import patch

import pytest

import metabolon.organelles.mitophagy as mp

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def isolated(tmp_path):
    """Patch all module-level paths so tests are fully isolated."""
    outcomes = tmp_path / "outcomes.jsonl"
    blacklist = tmp_path / "blacklist.json"
    with (
        patch.object(mp, "_CACHE_DIR", tmp_path),
        patch.object(mp, "_OUTCOMES_PATH", outcomes),
        patch.object(mp, "_BLACKLIST_PATH", blacklist),
    ):
        yield tmp_path, outcomes, blacklist


def _write_outcomes(path, rows):
    """Helper: write a list of dicts as JSONL."""
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _write_blacklist(path, bl):
    path.write_text(json.dumps(bl))


# ===========================================================================
# _ensure_cache
# ===========================================================================


class TestEnsureCache:
    def test_creates_directory(self, tmp_path):
        cache = tmp_path / "nested" / "dir"
        with patch.object(mp, "_CACHE_DIR", cache):
            mp._ensure_cache()
        assert cache.is_dir()

    def test_idempotent(self, tmp_path):
        cache = tmp_path / "cache"
        with patch.object(mp, "_CACHE_DIR", cache):
            mp._ensure_cache()
            mp._ensure_cache()  # second call must not raise
        assert cache.is_dir()


# ===========================================================================
# _load_blacklist
# ===========================================================================


class TestLoadBlacklist:
    def test_missing_file_returns_empty(self, isolated):
        _, _, _bl_path = isolated
        assert mp._load_blacklist() == {}

    def test_valid_blacklist(self, isolated):
        _, _, bl_path = isolated
        _write_blacklist(bl_path, {"glm": ["probe", "coding"]})
        assert mp._load_blacklist() == {"glm": ["probe", "coding"]}

    def test_corrupt_json_returns_empty(self, isolated):
        _, _, bl_path = isolated
        bl_path.write_text("NOT JSON!!!")
        assert mp._load_blacklist() == {}

    def test_empty_file_returns_empty(self, isolated):
        _, _, bl_path = isolated
        bl_path.write_text("")
        assert mp._load_blacklist() == {}


# ===========================================================================
# _save_blacklist
# ===========================================================================


class TestSaveBlacklist:
    def test_writes_json(self, isolated):
        _, _, bl_path = isolated
        mp._save_blacklist({"sonnet": ["repair"]})
        data = json.loads(bl_path.read_text())
        assert data == {"sonnet": ["repair"]}

    def test_overwrites_existing(self, isolated):
        _, _, bl_path = isolated
        _write_blacklist(bl_path, {"old": ["x"]})
        mp._save_blacklist({"new": ["y"]})
        data = json.loads(bl_path.read_text())
        assert data == {"new": ["y"]}

    def test_creates_parent_dirs(self, tmp_path):
        bl_path = tmp_path / "deep" / "sub" / "blacklist.json"
        with (
            patch.object(mp, "_CACHE_DIR", bl_path.parent),
            patch.object(mp, "_BLACKLIST_PATH", bl_path),
        ):
            mp._save_blacklist({})
        assert bl_path.exists()


# ===========================================================================
# _load_outcomes
# ===========================================================================


class TestLoadOutcomes:
    def test_missing_file(self, isolated):
        _, _outcomes, _ = isolated
        assert mp._load_outcomes() == []

    def test_reads_all_rows(self, isolated):
        _, outcomes, _ = isolated
        now = time.time()
        rows = [
            {"ts": now - 10, "model": "a", "task_type": "probe", "success": True},
            {"ts": now, "model": "b", "task_type": "coding", "success": False},
        ]
        _write_outcomes(outcomes, rows)
        result = mp._load_outcomes()
        assert len(result) == 2

    def test_filters_by_since_ts(self, isolated):
        _, outcomes, _ = isolated
        old = 1000.0
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": old, "model": "a", "task_type": "probe", "success": True},
                {"ts": now, "model": "b", "task_type": "probe", "success": True},
            ],
        )
        result = mp._load_outcomes(since_ts=now - 1)
        assert len(result) == 1
        assert result[0]["model"] == "b"

    def test_skips_corrupt_lines(self, isolated):
        _, outcomes, _ = isolated
        now = time.time()
        with outcomes.open("w") as f:
            f.write(
                json.dumps({"ts": now, "model": "a", "task_type": "probe", "success": True}) + "\n"
            )
            f.write("BROKEN LINE\n")
            f.write(
                json.dumps({"ts": now, "model": "b", "task_type": "probe", "success": False})
                + "\n"
            )
        result = mp._load_outcomes()
        assert len(result) == 2

    def test_skips_blank_lines(self, isolated):
        _, outcomes, _ = isolated
        now = time.time()
        with outcomes.open("w") as f:
            f.write("\n")
            f.write(
                json.dumps({"ts": now, "model": "a", "task_type": "probe", "success": True}) + "\n"
            )
            f.write("   \n")
        result = mp._load_outcomes()
        assert len(result) == 1

    def test_empty_file(self, isolated):
        _, outcomes, _ = isolated
        outcomes.write_text("")
        assert mp._load_outcomes() == []


# ===========================================================================
# record_outcome
# ===========================================================================


class TestRecordOutcome:
    def test_writes_row_with_all_fields(self, isolated):
        _, outcomes, _bl_path = isolated
        before = time.time()
        mp.record_outcome("glm", "probe", True, 1234)
        entry = json.loads(outcomes.read_text().strip())
        assert entry["model"] == "glm"
        assert entry["task_type"] == "probe"
        assert entry["success"] is True
        assert entry["duration_ms"] == 1234
        assert entry["ts"] >= before

    def test_appends_multiple(self, isolated):
        _, outcomes, _ = isolated
        mp.record_outcome("glm", "probe", True, 100)
        mp.record_outcome("sonnet", "coding", False, 200)
        lines = outcomes.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_auto_blacklist_triggers(self, isolated):
        """After 5+ failures with <50% success, model should be blacklisted."""
        _, outcomes, _bl_path = isolated
        now = time.time()
        # Write 5 failures + 1 success = 16.7% success rate → auto-blacklist
        rows = [
            {"ts": now, "model": "badmodel", "task_type": "repair", "success": False}
            for _ in range(5)
        ]
        rows.append({"ts": now, "model": "badmodel", "task_type": "repair", "success": True})
        _write_outcomes(outcomes, rows)

        mp.record_outcome("badmodel", "repair", False, 50)
        # The extra record_outcome call itself appends before checking, so
        # now there are 7 outcomes: 5 fail + 1 success + 1 fail = 6 fail / 7 = 14%
        assert mp.is_blacklisted("badmodel", "repair")

    def test_auto_blacklist_does_not_trigger_above_threshold(self, isolated):
        """60% success rate should NOT trigger auto-blacklist."""
        _, outcomes, _bl_path = isolated
        now = time.time()
        # 3 success + 2 fail = 60%
        rows = [
            {"ts": now, "model": "okmodel", "task_type": "probe", "success": True}
            for _ in range(3)
        ]
        rows += [
            {"ts": now, "model": "okmodel", "task_type": "probe", "success": False}
            for _ in range(2)
        ]
        _write_outcomes(outcomes, rows)

        mp.record_outcome("okmodel", "probe", True, 10)
        assert not mp.is_blacklisted("okmodel", "probe")

    def test_auto_blacklist_needs_min_attempts(self, isolated):
        """Fewer than 5 attempts should not trigger auto-blacklist even at 0%."""
        _, outcomes, _bl_path = isolated
        now = time.time()
        rows = [
            {"ts": now, "model": "newmodel", "task_type": "coding", "success": False}
            for _ in range(3)
        ]
        _write_outcomes(outcomes, rows)

        mp.record_outcome("newmodel", "coding", False, 10)
        # Only 4 attempts total — below _BLACKLIST_MIN_ATTEMPTS=5
        assert not mp.is_blacklisted("newmodel", "coding")

    def test_no_duplicate_blacklist_entry(self, isolated):
        """If already blacklisted, blacklist() should not duplicate the entry."""
        _, _outcomes, bl_path = isolated
        _write_blacklist(bl_path, {"glm": ["probe"]})
        mp.blacklist("glm", "probe")
        bl = json.loads(bl_path.read_text())
        assert bl["glm"].count("probe") == 1


# ===========================================================================
# blacklist
# ===========================================================================


class TestBlacklist:
    def test_adds_entry(self, isolated):
        _, _, bl_path = isolated
        mp.blacklist("sonnet", "coding")
        bl = json.loads(bl_path.read_text())
        assert "coding" in bl.get("sonnet", [])

    def test_adds_multiple_task_types(self, isolated):
        _, _, bl_path = isolated
        mp.blacklist("sonnet", "coding")
        mp.blacklist("sonnet", "repair")
        bl = json.loads(bl_path.read_text())
        assert set(bl["sonnet"]) == {"coding", "repair"}

    def test_no_duplicate(self, isolated):
        _, _, bl_path = isolated
        mp.blacklist("glm", "probe")
        mp.blacklist("glm", "probe")
        bl = json.loads(bl_path.read_text())
        assert bl["glm"] == ["probe"]

    def test_graceful_when_infection_missing(self, isolated):
        """blacklist() must not raise even if infection module is unavailable."""
        _, _, _bl_path = isolated
        import sys

        sys.modules.pop("metabolon.metabolism.infection", None)
        mp.blacklist("glm", "probe")  # should not raise
        assert mp.is_blacklisted("glm", "probe")

    def test_infection_called_when_available(self, isolated):
        _, _, _bl_path = isolated
        import types

        fake_infection = types.ModuleType("metabolon.metabolism.infection")
        call_log = []
        fake_infection.record_infection = lambda **kw: call_log.append(kw)

        with patch.dict("sys.modules", {"metabolon.metabolism.infection": fake_infection}):
            mp.blacklist("sonnet", "repair")

        assert len(call_log) == 1
        assert "sonnet" in call_log[0]["tool"]
        assert call_log[0]["healed"] is False


# ===========================================================================
# is_blacklisted
# ===========================================================================


class TestIsBlacklisted:
    def test_not_blacklisted_empty(self, isolated):
        assert mp.is_blacklisted("glm", "probe") is False

    def test_blacklisted(self, isolated):
        _, _, bl_path = isolated
        _write_blacklist(bl_path, {"glm": ["probe"]})
        assert mp.is_blacklisted("glm", "probe") is True

    def test_wrong_task_type(self, isolated):
        _, _, bl_path = isolated
        _write_blacklist(bl_path, {"glm": ["probe"]})
        assert mp.is_blacklisted("glm", "coding") is False

    def test_wrong_model(self, isolated):
        _, _, bl_path = isolated
        _write_blacklist(bl_path, {"glm": ["probe"]})
        assert mp.is_blacklisted("sonnet", "probe") is False

    def test_empty_model_entry(self, isolated):
        _, _, bl_path = isolated
        _write_blacklist(bl_path, {"glm": []})
        assert mp.is_blacklisted("glm", "probe") is False


# ===========================================================================
# model_fitness
# ===========================================================================


class TestModelFitness:
    def test_empty(self, isolated):
        assert mp.model_fitness() == []

    def test_basic_rate(self, isolated):
        _, outcomes, _ = isolated
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
                {"ts": now, "model": "glm", "task_type": "probe", "success": False},
            ],
        )
        results = mp.model_fitness(days=1)
        assert len(results) == 1
        r = results[0]
        assert r["model"] == "glm"
        assert r["task_type"] == "probe"
        assert r["attempts"] == 3
        assert r["successes"] == 2
        assert r["rate"] == round(2 / 3, 3)

    def test_filter_by_model(self, isolated):
        _, outcomes, _ = isolated
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
                {"ts": now, "model": "sonnet", "task_type": "probe", "success": True},
            ],
        )
        results = mp.model_fitness(model="glm", days=1)
        assert len(results) == 1
        assert results[0]["model"] == "glm"

    def test_filter_by_task_type(self, isolated):
        _, outcomes, _ = isolated
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
                {"ts": now, "model": "glm", "task_type": "coding", "success": False},
            ],
        )
        results = mp.model_fitness(task_type="coding", days=1)
        assert len(results) == 1
        assert results[0]["task_type"] == "coding"

    def test_blacklisted_flag(self, isolated):
        _, outcomes, bl_path = isolated
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": now, "model": "glm", "task_type": "probe", "success": False},
            ],
        )
        _write_blacklist(bl_path, {"glm": ["probe"]})
        results = mp.model_fitness(days=1)
        assert results[0]["blacklisted"] is True

    def test_not_blacklisted_flag(self, isolated):
        _, outcomes, _bl_path = isolated
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
            ],
        )
        results = mp.model_fitness(days=1)
        assert results[0]["blacklisted"] is False

    def test_ignores_old_data(self, isolated):
        _, outcomes, _ = isolated
        _write_outcomes(
            outcomes,
            [
                {"ts": 1000.0, "model": "glm", "task_type": "probe", "success": True},
            ],
        )
        results = mp.model_fitness(days=7)
        assert results == []

    def test_multiple_models_sorted(self, isolated):
        _, outcomes, _ = isolated
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": now, "model": "sonnet", "task_type": "probe", "success": True},
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
            ],
        )
        results = mp.model_fitness(days=1)
        models = [r["model"] for r in results]
        assert models == ["glm", "sonnet"]  # sorted by (model, task_type)


# ===========================================================================
# recommend_model
# ===========================================================================


class TestRecommendModel:
    def test_fallback_no_data(self, isolated):
        assert mp.recommend_model("probe") == "opus"

    def test_picks_best_rate(self, isolated):
        _, outcomes, _ = isolated
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
                {"ts": now, "model": "sonnet", "task_type": "probe", "success": False},
            ],
        )
        assert mp.recommend_model("probe") == "glm"

    def test_skips_blacklisted(self, isolated):
        _, outcomes, bl_path = isolated
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
                {"ts": now, "model": "sonnet", "task_type": "probe", "success": False},
            ],
        )
        _write_blacklist(bl_path, {"glm": ["probe"]})
        assert mp.recommend_model("probe") == "sonnet"

    def test_all_blacklisted_falls_back(self, isolated):
        _, outcomes, bl_path = isolated
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
                {"ts": now, "model": "sonnet", "task_type": "probe", "success": True},
            ],
        )
        _write_blacklist(bl_path, {"glm": ["probe"], "sonnet": ["probe"]})
        assert mp.recommend_model("probe") == "opus"

    def test_tiebreak_by_attempt_count(self, isolated):
        """When rates are equal, model with more attempts wins."""
        _, outcomes, _ = isolated
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
                {"ts": now, "model": "glm", "task_type": "probe", "success": True},
                {"ts": now, "model": "sonnet", "task_type": "probe", "success": True},
            ],
        )
        # Both 100%, but glm has 3 attempts vs sonnet's 1
        assert mp.recommend_model("probe") == "glm"

    def test_no_outcome_for_different_task(self, isolated):
        _, outcomes, _ = isolated
        now = time.time()
        _write_outcomes(
            outcomes,
            [
                {"ts": now, "model": "glm", "task_type": "coding", "success": True},
            ],
        )
        assert mp.recommend_model("probe") == "opus"
