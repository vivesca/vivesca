"""Tests for circulation organelle — state types, pure helpers, constants."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Annotated, get_type_hints

import pytest

lg = pytest.importorskip("langgraph")

from metabolon.organelles.circulation import (
    CHECKPOINT_DB,
    EVALUATOR_MODEL,
    MANIFEST_PATH,
    NORTH_STAR_PATH,
    PLANNER_MODEL,
    REPORT_DIR,
    WORKER_MODEL,
    CirculationState,
    _open_checkpointer,
    build_graph,
    checkpoint_node,
    preflight,
    should_continue,
)


# ── 1. CirculationState TypedDict keys ──────────────────────


class TestCirculationStateKeys:
    """Verify the state TypedDict has all required keys."""

    EXPECTED_KEYS = {
        "north_stars",
        "praxis_items",
        "budget_status",
        "mode",
        "systole_num",
        "selected_goals",
        "dispatched_work",
        "evaluation",
        "compound_ideas",
        "total_produced",
        "total_for_review",
        "errors",
        "should_stop",
        "stop_reason",
        "report",
    }

    def test_has_all_required_keys(self):
        hints = get_type_hints(CirculationState, include_extras=True)
        assert set(hints.keys()) == self.EXPECTED_KEYS

    def test_budget_status_accepts_strings(self):
        """A state dict with valid budget_status strings should be constructable."""
        for status in ("green", "yellow", "red"):
            state: CirculationState = {
                "north_stars": "",
                "praxis_items": "",
                "budget_status": status,
                "mode": "overnight",
                "systole_num": 0,
                "selected_goals": [],
                "dispatched_work": [],
                "evaluation": "",
                "compound_ideas": [],
                "total_produced": 0,
                "total_for_review": 0,
                "errors": [],
                "should_stop": False,
                "stop_reason": "",
                "report": "",
            }
            assert state["budget_status"] == status

    def test_mode_accepts_valid_values(self):
        for mode in ("overnight", "interactive"):
            state: CirculationState = {
                "north_stars": "",
                "praxis_items": "",
                "budget_status": "green",
                "mode": mode,
                "systole_num": 0,
                "selected_goals": [],
                "dispatched_work": [],
                "evaluation": "",
                "compound_ideas": [],
                "total_produced": 0,
                "total_for_review": 0,
                "errors": [],
                "should_stop": False,
                "stop_reason": "",
                "report": "",
            }
            assert state["mode"] == mode


# ── 2. Constants and configuration ──────────────────────────


class TestConstants:
    def test_checkpoint_db_under_vivesca(self):
        assert ".local/share/vivesca" in str(CHECKPOINT_DB)
        assert CHECKPOINT_DB.name == "checkpoints.db"

    def test_north_star_path_is_markdown(self):
        assert NORTH_STAR_PATH.suffix == ".md"
        assert "North Star" in NORTH_STAR_PATH.name

    def test_model_names_are_known(self):
        assert PLANNER_MODEL == "glm"
        assert WORKER_MODEL == "sonnet"
        assert EVALUATOR_MODEL == "claude"

    def test_manifest_path_under_tmp(self):
        assert "tmp" in str(MANIFEST_PATH)
        assert MANIFEST_PATH.name == "circulation-manifest.md"

    def test_report_dir_exists(self):
        assert "Poiesis Reports" in str(REPORT_DIR)


# ── 3. should_continue routing logic ────────────────────────


class TestShouldContinue:
    """Pure routing function — no side effects."""

    def _make_state(self, **overrides) -> dict:
        base: dict = {
            "should_stop": False,
            "budget_status": "green",
        }
        base.update(overrides)
        return base

    def test_continues_when_should_stop_false(self):
        assert should_continue(self._make_state(should_stop=False)) == "preflight"

    def test_reports_when_should_stop_true(self):
        assert should_continue(self._make_state(should_stop=True)) == "report"

    def test_defaults_to_continue_when_key_missing(self):
        # should_stop absent → get returns False → continue
        assert should_continue({}) == "preflight"


# ── 4. checkpoint_node stop decisions ────────────────────────


class TestCheckpointNode:
    """Test stop/reason logic without real filesystem writes."""

    @pytest.fixture(autouse=True)
    def _tmp_manifest(self, tmp_path: Path, monkeypatch):
        manifest = tmp_path / "circulation-manifest.md"
        monkeypatch.setattr(
            "metabolon.organelles.circulation.MANIFEST_PATH", manifest
        )
        yield manifest

    def _make_state(self, **overrides) -> dict:
        base: dict = {
            "systole_num": 3,
            "budget_status": "green",
            "dispatched_work": [
                {"success": True, "star": "growth", "goal": "write report"},
                {"success": False, "star": "ops", "goal": "fix CI"},
            ],
            "compound_ideas": ["compound idea 1", "compound idea 2"],
            "selected_goals": [{"star": "growth", "goal": "next thing"}],
            "total_produced": 5,
            "total_for_review": 1,
        }
        base.update(overrides)
        return base

    def test_green_budget_continues(self):
        result = checkpoint_node(self._make_state(budget_status="green"))
        assert result["should_stop"] is False
        assert "stop_reason" not in result

    def test_red_budget_stops(self):
        result = checkpoint_node(self._make_state(budget_status="red"))
        assert result["should_stop"] is True
        assert "red" in result["stop_reason"].lower()

    def test_yellow_budget_stops(self):
        result = checkpoint_node(self._make_state(budget_status="yellow"))
        assert result["should_stop"] is True
        assert "yellow" in result["stop_reason"].lower()

    def test_no_goals_stops(self):
        result = checkpoint_node(self._make_state(selected_goals=[]))
        assert result["should_stop"] is True
        assert "no goals" in result["stop_reason"].lower()

    def test_manifest_written(self, _tmp_manifest):
        checkpoint_node(self._make_state())
        text = _tmp_manifest.read_text()
        assert "Systole 3" in text
        assert "ok" in text
        assert "FAILED" in text
        assert "compound idea 1" in text


# ── 5. preflight budget parsing ──────────────────────────────


class TestPreflight:
    @pytest.fixture(autouse=True)
    def _mock_paths(self, tmp_path: Path, monkeypatch):
        north_star = tmp_path / "North Star.md"
        north_star.write_text("## North Star\nGrow the organism.")
        monkeypatch.setattr(
            "metabolon.organelles.circulation.NORTH_STAR_PATH", north_star
        )

        praxis_file = tmp_path / "praxis.md"
        praxis_file.write_text("- task 1\n- task 2\n")
        monkeypatch.setattr("metabolon.organelles.circulation.praxis", praxis_file)

        # preflight constructs allo_state as Path.home() / ".claude" / ...
        # so we mock Path.home to return tmp_path, then build the expected path
        allo = tmp_path / ".claude" / "allostasis-state.json"
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        yield (tmp_path, allo)

    def _make_state(self, **overrides) -> dict:
        base: dict = {"systole_num": 0, "mode": "overnight"}
        base.update(overrides)
        return base

    def test_budget_green_by_default(self, _mock_paths):
        _, allo = _mock_paths
        # No allostasis file → default green
        result = preflight(self._make_state())
        assert result["budget_status"] == "green"

    def test_budget_red_on_catabolic(self, _mock_paths):
        _, allo = _mock_paths
        allo.parent.mkdir(parents=True, exist_ok=True)
        allo.write_text(json.dumps({"tier": "catabolic"}))
        result = preflight(self._make_state())
        assert result["budget_status"] == "red"

    def test_budget_yellow_on_homeostatic(self, _mock_paths):
        _, allo = _mock_paths
        allo.parent.mkdir(parents=True, exist_ok=True)
        allo.write_text(json.dumps({"tier": "homeostatic"}))
        result = preflight(self._make_state())
        assert result["budget_status"] == "yellow"

    def test_systole_increments(self, _mock_paths):
        r1 = preflight(self._make_state(systole_num=0))
        r2 = preflight(self._make_state(systole_num=3))
        assert r1["systole_num"] == 1
        assert r2["systole_num"] == 4

    def test_north_stars_truncated_at_3000(self, _mock_paths):
        tmp, _ = _mock_paths
        ns = tmp / "North Star.md"
        ns.write_text("x" * 5000)
        result = preflight(self._make_state())
        assert len(result["north_stars"]) == 3000


# ── 6. _open_checkpointer ───────────────────────────────────


class TestCheckpointerFactory:
    def test_in_memory_when_not_persistent(self):
        cp = _open_checkpointer(persistent=False)
        assert cp is not None
        # InMemorySaver has a .put method
        assert hasattr(cp, "put")


# ── 7. build_graph structure ────────────────────────────────


class TestGraphStructure:
    def test_graph_builds_without_error(self):
        graph = build_graph()
        assert graph is not None

    def test_graph_has_all_nodes(self):
        graph = build_graph()
        # StateGraph.nodes is populated after add_node calls
        expected_nodes = {
            "preflight",
            "select_goals",
            "dispatch",
            "evaluate",
            "compound",
            "checkpoint",
            "report",
        }
        assert expected_nodes.issubset(set(graph.nodes))
