from __future__ import annotations

"""Tests for metabolon.organelles.tissue_routing.

All external calls to mitophagy are mocked so tests run without filesystem
or network dependencies.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------
import metabolon.organelles.tissue_routing as tr


# ===================================================================
# default_routes
# ===================================================================

class TestDefaultRoutes:
    def test_returns_dict(self):
        result = tr.default_routes()
        assert isinstance(result, dict)

    def test_returns_all_known_task_types(self):
        result = tr.default_routes()
        expected_tasks = {
            "probe", "repair_known", "repair_novel", "methylation",
            "hybridization", "research", "coding", "synthesis",
            "poiesis_dispatch", "quality_gate",
        }
        assert expected_tasks == set(result.keys())

    def test_returns_copy_not_reference(self):
        r1 = tr.default_routes()
        r2 = tr.default_routes()
        assert r1 == r2
        assert r1 is not r2
        r1["probe"] = "mutated"
        assert r2["probe"] != "mutated"


# ===================================================================
# observed_routes
# ===================================================================

class TestObservedRoutes:

    @patch("metabolon.organelles.tissue_routing._DEFAULTS", {
        "probe": "glm", "coding": "codex",
    })
    def test_fallback_to_defaults_when_no_mitophagy(self):
        """When mitophagy import fails, should return plain defaults."""
        # Patching _DEFAULTS directly; observed_routes copies it at call time.
        # The import will fail because we aren't patching the full mitophagy module.
        result = tr.observed_routes()
        assert result == {"probe": "glm", "coding": "codex"}

    def test_overrides_with_best_model(self):
        """Should pick the model with highest (rate, attempts) per task."""
        fitness_data = [
            {"task_type": "probe", "model": "glm", "rate": 0.8, "attempts": 10},
            {"task_type": "probe", "model": "sonnet", "rate": 0.9, "attempts": 5},
            {"task_type": "coding", "model": "codex", "rate": 0.7, "attempts": 3},
            {"task_type": "coding", "model": "sonnet", "rate": 0.95, "attempts": 8},
        ]
        mock_mod = MagicMock()
        mock_mod.is_blacklisted.return_value = False
        mock_mod.model_fitness.return_value = fitness_data

        with patch.dict(sys.modules, {"metabolon.organelles.mitophagy": mock_mod}):
            # Need to also patch the import inside observed_routes
            with patch("metabolon.organelles.tissue_routing._DEFAULTS", {
                "probe": "glm", "coding": "codex",
            }):
                result = tr.observed_routes()

        # probe: sonnet (0.9) beats glm (0.8)
        assert result["probe"] == "sonnet"
        # coding: sonnet (0.95) beats codex (0.7)
        assert result["coding"] == "sonnet"

    def test_skips_blacklisted_models(self):
        """Blacklisted models should not win even with higher rate."""
        fitness_data = [
            {"task_type": "probe", "model": "sonnet", "rate": 0.99, "attempts": 20},
            {"task_type": "probe", "model": "glm", "rate": 0.6, "attempts": 5},
        ]
        mock_mod = MagicMock()

        def _is_blacklisted(model, task):
            return model == "sonnet" and task == "probe"

        mock_mod.is_blacklisted = _is_blacklisted
        mock_mod.model_fitness.return_value = fitness_data

        with patch.dict(sys.modules, {"metabolon.organelles.mitophagy": mock_mod}):
            with patch("metabolon.organelles.tissue_routing._DEFAULTS", {
                "probe": "glm",
            }):
                result = tr.observed_routes()

        assert result["probe"] == "glm"

    def test_keeps_default_for_unknown_task(self):
        """Tasks not in _DEFAULTS should not appear in observed routes."""
        fitness_data = [
            {"task_type": "unknown_task", "model": "opus", "rate": 1.0, "attempts": 50},
        ]
        mock_mod = MagicMock()
        mock_mod.is_blacklisted.return_value = False
        mock_mod.model_fitness.return_value = fitness_data

        with patch.dict(sys.modules, {"metabolon.organelles.mitophagy": mock_mod}):
            with patch("metabolon.organelles.tissue_routing._DEFAULTS", {
                "probe": "glm",
            }):
                result = tr.observed_routes()

        assert "unknown_task" not in result

    def test_tiebreak_by_attempts(self):
        """When rates are equal, higher attempts wins."""
        fitness_data = [
            {"task_type": "probe", "model": "glm", "rate": 0.8, "attempts": 10},
            {"task_type": "probe", "model": "sonnet", "rate": 0.8, "attempts": 20},
        ]
        mock_mod = MagicMock()
        mock_mod.is_blacklisted.return_value = False
        mock_mod.model_fitness.return_value = fitness_data

        with patch.dict(sys.modules, {"metabolon.organelles.mitophagy": mock_mod}):
            with patch("metabolon.organelles.tissue_routing._DEFAULTS", {
                "probe": "glm",
            }):
                result = tr.observed_routes()

        assert result["probe"] == "sonnet"

    def test_empty_rows_from_fitness(self):
        """model_fitness returning empty list should give defaults."""
        mock_mod = MagicMock()
        mock_mod.is_blacklisted.return_value = False
        mock_mod.model_fitness.return_value = []

        with patch.dict(sys.modules, {"metabolon.organelles.mitophagy": mock_mod}):
            with patch("metabolon.organelles.tissue_routing._DEFAULTS", {
                "probe": "glm",
            }):
                result = tr.observed_routes()

        assert result == {"probe": "glm"}


# ===================================================================
# route
# ===================================================================

class TestRoute:

    def test_unknown_task_returns_sonnet_fallback(self):
        """Unknown task_type falls back to 'sonnet'."""
        with patch.object(tr, "observed_routes", return_value=tr.default_routes()):
            # mitophagy import will fail, so it returns observed or default
            result = tr.route("nonexistent_task")
        assert result == "sonnet"

    def test_returns_default_for_known_task(self):
        """Known task returns its default model when no override."""
        with patch.object(tr, "observed_routes", return_value=tr.default_routes()):
            result = tr.route("coding")
        assert result == "codex"

    def test_returns_observed_override(self):
        """observed_routes overrides take precedence."""
        observed = tr.default_routes()
        observed["coding"] = "sonnet"
        with patch.object(tr, "observed_routes", return_value=observed):
            result = tr.route("coding")
        assert result == "sonnet"

    def test_blacklisted_default_triggers_recommend(self):
        """When default model is blacklisted, recommend_model is consulted."""
        mock_mod = MagicMock()
        mock_mod.is_blacklisted.return_value = True
        mock_mod.recommend_model.return_value = "opus"

        with patch.dict(sys.modules, {"metabolon.organelles.mitophagy": mock_mod}):
            with patch.object(tr, "observed_routes", return_value=tr.default_routes()):
                result = tr.route("probe")

        assert result == "opus"

    def test_blacklisted_default_recommend_falls_back(self):
        """When recommend_model returns empty, fall back to default anyway."""
        mock_mod = MagicMock()
        mock_mod.is_blacklisted.return_value = True
        mock_mod.recommend_model.return_value = ""

        with patch.dict(sys.modules, {"metabolon.organelles.mitophagy": mock_mod}):
            with patch.object(tr, "observed_routes", return_value=tr.default_routes()):
                result = tr.route("probe")

        assert result == "glm"


# ===================================================================
# route_report
# ===================================================================

class TestRouteReport:

    def test_report_has_header(self):
        with patch.object(tr, "observed_routes", return_value=tr.default_routes()):
            with patch.object(tr, "default_routes", return_value=tr.default_routes()):
                report = tr.route_report()
        assert "Tissue routing" in report

    def test_report_lists_all_tasks(self):
        defaults = tr.default_routes()
        with patch.object(tr, "observed_routes", return_value=defaults):
            with patch.object(tr, "default_routes", return_value=defaults):
                report = tr.route_report()
        for task in defaults:
            assert task in report

    def test_report_with_fitness_data(self):
        """Should include success/attempts annotation when data exists."""
        defaults = {"probe": "glm"}
        fitness_data = [
            {"task_type": "probe", "model": "glm", "rate": 0.85,
             "attempts": 20, "successes": 17},
        ]
        mock_mod = MagicMock()
        mock_mod.model_fitness.return_value = fitness_data
        mock_mod._load_blacklist.return_value = {}

        with patch.dict(sys.modules, {"metabolon.organelles.mitophagy": mock_mod}):
            with patch.object(tr, "observed_routes", return_value=defaults):
                with patch.object(tr, "default_routes", return_value=defaults):
                    report = tr.route_report()

        assert "17/20" in report
        assert "85%" in report

    def test_report_shows_blacklisted_flag(self):
        """Blacklisted model+task pairs should be flagged."""
        defaults = {"probe": "glm"}
        mock_mod = MagicMock()
        mock_mod.model_fitness.return_value = []
        mock_mod._load_blacklist.return_value = {"glm": ["probe"]}

        with patch.dict(sys.modules, {"metabolon.organelles.mitophagy": mock_mod}):
            with patch.object(tr, "observed_routes", return_value=defaults):
                with patch.object(tr, "default_routes", return_value=defaults):
                    report = tr.route_report()

        assert "BLACKLISTED" in report

    def test_report_no_mitophagy_module(self):
        """Should still produce a report when mitophagy is unavailable."""
        defaults = {"probe": "glm", "coding": "codex"}
        with patch.object(tr, "observed_routes", return_value=defaults):
            with patch.object(tr, "default_routes", return_value=defaults):
                report = tr.route_report()
        assert "probe" in report
        assert "coding" in report
        assert "no mitophagy data" in report

    def test_report_observed_differs_from_default(self):
        """When observed differs from default, should note it."""
        defaults = {"probe": "glm"}
        observed = {"probe": "sonnet"}
        mock_mod = MagicMock()
        mock_mod.model_fitness.return_value = []
        mock_mod._load_blacklist.return_value = {}

        with patch.dict(sys.modules, {"metabolon.organelles.mitophagy": mock_mod}):
            with patch.object(tr, "observed_routes", return_value=observed):
                with patch.object(tr, "default_routes", return_value=defaults):
                    report = tr.route_report()

        assert "observed" in report
        assert "default was glm" in report


# ===================================================================
# Edge cases / robustness
# ===================================================================

class TestEdgeCases:

    def test_default_routes_known_values(self):
        """Spot-check a few known default mappings."""
        d = tr.default_routes()
        assert d["hybridization"] == "opus"
        assert d["coding"] == "codex"
        assert d["synthesis"] == "opus"

    def test_route_always_returns_string(self):
        """route() should always return a string, never None."""
        with patch.object(tr, "observed_routes", return_value=tr.default_routes()):
            for task in ["probe", "unknown_xyz", ""]:
                result = tr.route(task)
                assert isinstance(result, str)
                assert len(result) > 0

    def test_route_report_is_string(self):
        with patch.object(tr, "observed_routes", return_value=tr.default_routes()):
            with patch.object(tr, "default_routes", return_value=tr.default_routes()):
                report = tr.route_report()
        assert isinstance(report, str)
        assert len(report) > 0
