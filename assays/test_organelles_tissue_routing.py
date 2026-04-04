from __future__ import annotations

"""Tests for metabolon.organelles.tissue_routing.

All external calls to metabolon.organelles.mitophagy are mocked so the tests
run without a real database or mitophagy data file.
"""

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_FITNESS = [
    {"task_type": "probe", "model": "glm", "rate": 0.9, "attempts": 20, "successes": 18},
    {"task_type": "probe", "model": "sonnet", "rate": 0.8, "attempts": 10, "successes": 8},
    {"task_type": "repair_novel", "model": "opus", "rate": 0.95, "attempts": 30, "successes": 28},
    {"task_type": "coding", "model": "codex", "rate": 0.85, "attempts": 40, "successes": 34},
]

SAMPLE_BLACKLIST = {"glm": ["hybridization"], "opus": ["probe"]}


def _mitophagy_mocks(fitness=None, blacklist=None, blacklisted=False, recommend="sonnet"):
    """Return a dict of patch targets for mitophagy functions."""
    return {
        "metabolon.organelles.mitophagy.model_fitness": MagicMock(return_value=fitness or []),
        "metabolon.organelles.mitophagy._load_blacklist": MagicMock(return_value=blacklist or {}),
        "metabolon.organelles.mitophagy.is_blacklisted": MagicMock(return_value=blacklisted),
        "metabolon.organelles.mitophagy.recommend_model": MagicMock(return_value=recommend),
    }


# ===================================================================
# default_routes
# ===================================================================


class TestDefaultRoutes:
    def test_returns_dict(self):
        from metabolon.organelles.tissue_routing import default_routes

        result = default_routes()
        assert isinstance(result, dict)

    def test_contains_all_known_tasks(self):
        from metabolon.organelles.tissue_routing import default_routes

        r = default_routes()
        expected = [
            "probe",
            "repair_known",
            "repair_novel",
            "methylation",
            "hybridization",
            "research",
            "coding",
            "synthesis",
            "poiesis_dispatch",
            "quality_gate",
        ]
        for task in expected:
            assert task in r, f"missing task: {task}"

    def test_values_are_strings(self):
        from metabolon.organelles.tissue_routing import default_routes

        r = default_routes()
        for k, v in r.items():
            assert isinstance(v, str), f"{k}: {v!r} is not str"

    def test_returns_copy(self):
        from metabolon.organelles.tissue_routing import _DEFAULTS, default_routes

        r = default_routes()
        assert r is not _DEFAULTS
        assert r == _DEFAULTS

    def test_modifying_return_does_not_affect_defaults(self):
        from metabolon.organelles.tissue_routing import _DEFAULTS, default_routes

        r = default_routes()
        r["probe"] = "CHANGED"
        assert _DEFAULTS["probe"] != "CHANGED"


# ===================================================================
# observed_routes
# ===================================================================


class TestObservedRoutes:
    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=[])
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=False)
    def test_falls_back_to_defaults_when_empty(self, mock_bl, mock_mf):
        from metabolon.organelles.tissue_routing import _DEFAULTS, observed_routes

        result = observed_routes()
        assert result == dict(_DEFAULTS)

    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=SAMPLE_FITNESS)
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=False)
    def test_selects_best_model_per_task(self, mock_bl, mock_mf):
        from metabolon.organelles.tissue_routing import observed_routes

        result = observed_routes()
        # probe: glm 0.9 > sonnet 0.8 → glm
        assert result["probe"] == "glm"
        # repair_novel: opus 0.95 → opus (overrides default sonnet)
        assert result["repair_novel"] == "opus"

    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=SAMPLE_FITNESS)
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=False)
    def test_ignores_tasks_not_in_defaults(self, mock_bl, mock_mf):
        from metabolon.organelles.tissue_routing import observed_routes

        result = observed_routes()
        # fitness has 'coding' which IS in defaults, so it should be present
        assert "coding" in result
        # Should not have any extra keys beyond default tasks
        from metabolon.organelles.tissue_routing import _DEFAULTS

        for key in result:
            assert key in _DEFAULTS

    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=SAMPLE_FITNESS)
    @patch(
        "metabolon.organelles.mitophagy.is_blacklisted",
        side_effect=lambda m, t: m == "opus" and t == "repair_novel",
    )
    def test_excludes_blacklisted_models(self, mock_bl, mock_mf):
        from metabolon.organelles.tissue_routing import observed_routes

        result = observed_routes()
        # opus is blacklisted for repair_novel; no other candidates → stays default (sonnet)
        assert result["repair_novel"] == "sonnet"

    @patch("metabolon.organelles.mitophagy.model_fitness", side_effect=Exception("db down"))
    def test_handles_exception_gracefully(self, mock_mf):
        from metabolon.organelles.tissue_routing import _DEFAULTS, observed_routes

        result = observed_routes()
        assert result == dict(_DEFAULTS)

    @patch(
        "metabolon.organelles.mitophagy.model_fitness",
        return_value=[
            {"task_type": "probe", "model": "sonnet", "rate": 0.7, "attempts": 5, "successes": 3},
        ],
    )
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=False)
    def test_tiebreak_by_attempts(self, mock_bl, mock_mf):
        """When rates are equal, pick the model with more attempts."""
        from metabolon.organelles.tissue_routing import observed_routes

        # Only one candidate for 'probe', rate 0.7 < default glm. But since it's
        # the only eligible, it should still be selected over default.
        # Actually, observed_routes only selects from fitness data, not default.
        result = observed_routes()
        assert result["probe"] == "sonnet"

    @patch(
        "metabolon.organelles.mitophagy.model_fitness",
        return_value=[
            {"task_type": "probe", "model": "glm", "rate": 0.9, "attempts": 10, "successes": 9},
            {
                "task_type": "probe",
                "model": "sonnet",
                "rate": 0.9,
                "attempts": 20,
                "successes": 18,
            },
        ],
    )
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=False)
    def test_tiebreak_prefers_more_attempts(self, mock_bl, mock_mf):
        """Same rate → model with more attempts wins."""
        from metabolon.organelles.tissue_routing import observed_routes

        result = observed_routes()
        assert result["probe"] == "sonnet"  # 20 attempts > 10

    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=[])
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=False)
    def test_passes_days_7(self, mock_bl, mock_mf):
        from metabolon.organelles.tissue_routing import observed_routes

        observed_routes()
        mock_mf.assert_called_with(days=7)


# ===================================================================
# route
# ===================================================================


class TestRoute:
    @patch(
        "metabolon.organelles.tissue_routing.observed_routes",
        return_value={
            "probe": "glm",
            "repair_novel": "opus",
        },
    )
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=False)
    def test_returns_observed_when_not_blacklisted(self, mock_bl, mock_or):
        from metabolon.organelles.tissue_routing import route

        assert route("probe") == "glm"

    @patch("metabolon.organelles.tissue_routing.observed_routes", return_value={"probe": "glm"})
    @patch("metabolon.organelles.mitophagy.recommend_model", return_value="sonnet")
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=True)
    def test_blacklisted_default_falls_to_recommend(self, mock_bl, mock_rec, mock_or):
        from metabolon.organelles.tissue_routing import route

        result = route("probe")
        # default for probe is glm, blacklisted → recommend_model("probe") → "sonnet"
        assert result == "sonnet"

    @patch("metabolon.organelles.tissue_routing.observed_routes", return_value={})
    @patch("metabolon.organelles.mitophagy.recommend_model", return_value="")
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=True)
    def test_blacklisted_and_no_recommend_returns_default(self, mock_bl, mock_rec, mock_or):
        from metabolon.organelles.tissue_routing import route

        # default is glm, blacklisted, recommend returns "" → falls back to default_model (glm)
        result = route("probe")
        assert result == "glm"

    @patch("metabolon.organelles.tissue_routing.observed_routes", return_value={"probe": "glm"})
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=False)
    def test_unknown_task_returns_sonnet_default(self, mock_bl, mock_or):
        from metabolon.organelles.tissue_routing import route

        result = route("totally_unknown_task")
        assert result == "sonnet"

    @patch(
        "metabolon.organelles.tissue_routing.observed_routes",
        return_value={
            "synthesis": "opus",
        },
    )
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=False)
    def test_known_task_returns_observed(self, mock_bl, mock_or):
        from metabolon.organelles.tissue_routing import route

        assert route("synthesis") == "opus"

    @patch("metabolon.organelles.tissue_routing.observed_routes", side_effect=Exception("fail"))
    @patch("metabolon.organelles.mitophagy.is_blacklisted", side_effect=Exception("fail"))
    def test_exception_in_observed_routes_propagates(self, mock_bl, mock_or):
        """When observed_routes raises, the exception propagates (outside mitophagy try/except)."""
        from metabolon.organelles.tissue_routing import route

        with pytest.raises(Exception, match="fail"):
            route("probe")

    @patch("metabolon.organelles.tissue_routing.observed_routes", return_value={"probe": "glm"})
    @patch(
        "metabolon.organelles.mitophagy.is_blacklisted", side_effect=Exception("mitophagy down")
    )
    def test_mitophagy_exception_skips_blacklist_check(self, mock_bl, mock_or):
        """When mitophagy import fails, blacklist check is skipped; observed route is returned."""
        from metabolon.organelles.tissue_routing import route

        assert route("probe") == "glm"

    @patch(
        "metabolon.organelles.tissue_routing.observed_routes",
        return_value={
            "coding": "codex",
        },
    )
    @patch("metabolon.organelles.mitophagy.is_blacklisted", return_value=False)
    def test_coding_routes_to_codex(self, mock_bl, mock_or):
        from metabolon.organelles.tissue_routing import route

        assert route("coding") == "codex"


# ===================================================================
# route_report
# ===================================================================


class TestRouteReport:
    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=[])
    @patch("metabolon.organelles.mitophagy._load_blacklist", return_value={})
    @patch("metabolon.organelles.tissue_routing.observed_routes")
    def test_report_includes_all_task_types(self, mock_or, mock_bl_load, mock_mf):
        from metabolon.organelles.tissue_routing import default_routes, route_report

        mock_or.return_value = default_routes()
        report = route_report()
        for task in default_routes():
            assert task in report, f"missing task: {task}"

    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=[])
    @patch("metabolon.organelles.mitophagy._load_blacklist", return_value={})
    @patch("metabolon.organelles.tissue_routing.observed_routes")
    def test_report_is_string(self, mock_or, mock_bl_load, mock_mf):
        from metabolon.organelles.tissue_routing import default_routes, route_report

        mock_or.return_value = default_routes()
        report = route_report()
        assert isinstance(report, str)

    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=SAMPLE_FITNESS)
    @patch("metabolon.organelles.mitophagy._load_blacklist", return_value={})
    @patch("metabolon.organelles.tissue_routing.observed_routes")
    def test_report_shows_fitness_data(self, mock_or, mock_bl_load, mock_mf):
        from metabolon.organelles.tissue_routing import default_routes, route_report

        mock_or.return_value = default_routes()
        report = route_report()
        assert "18/20 ok" in report
        assert "90%" in report

    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=[])
    @patch("metabolon.organelles.mitophagy._load_blacklist", return_value=SAMPLE_BLACKLIST)
    @patch("metabolon.organelles.tissue_routing.observed_routes")
    def test_report_shows_blacklisted_pairs(self, mock_or, mock_bl_load, mock_mf):
        from metabolon.organelles.tissue_routing import default_routes, route_report

        mock_or.return_value = default_routes()
        report = route_report()
        assert "Blacklisted pairs" in report
        assert "glm x hybridization" in report

    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=[])
    @patch("metabolon.organelles.mitophagy._load_blacklist", return_value=SAMPLE_BLACKLIST)
    @patch("metabolon.organelles.tissue_routing.observed_routes")
    def test_report_marks_blacklisted_active_model(self, mock_or, mock_bl_load, mock_mf):
        from metabolon.organelles.tissue_routing import default_routes, route_report

        routes = default_routes()
        routes["hybridization"] = "glm"  # force active model that is blacklisted
        mock_or.return_value = routes
        report = route_report()
        assert "BLACKLISTED" in report

    @patch("metabolon.organelles.mitophagy.model_fitness", side_effect=Exception("no db"))
    @patch("metabolon.organelles.tissue_routing.observed_routes")
    def test_report_handles_exceptions(self, mock_or, mock_mf):
        from metabolon.organelles.tissue_routing import default_routes, route_report

        mock_or.return_value = default_routes()
        report = route_report()
        assert isinstance(report, str)
        assert "Tissue routing" in report

    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=[])
    @patch("metabolon.organelles.mitophagy._load_blacklist", return_value={})
    @patch("metabolon.organelles.tissue_routing.observed_routes")
    def test_report_no_blacklist_section_when_empty(self, mock_or, mock_bl_load, mock_mf):
        from metabolon.organelles.tissue_routing import default_routes, route_report

        mock_or.return_value = default_routes()
        report = route_report()
        assert "Blacklisted pairs" not in report

    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=[])
    @patch("metabolon.organelles.mitophagy._load_blacklist", return_value={})
    @patch("metabolon.organelles.tissue_routing.observed_routes")
    def test_report_arrow_format(self, mock_or, mock_bl_load, mock_mf):
        from metabolon.organelles.tissue_routing import default_routes, route_report

        mock_or.return_value = default_routes()
        report = route_report()
        assert "->" in report

    @patch("metabolon.organelles.mitophagy.model_fitness", return_value=[])
    @patch("metabolon.organelles.mitophagy._load_blacklist", return_value={})
    @patch("metabolon.organelles.tissue_routing.observed_routes")
    def test_report_shows_no_data_annotation(self, mock_or, mock_bl_load, mock_mf):
        from metabolon.organelles.tissue_routing import default_routes, route_report

        mock_or.return_value = default_routes()
        report = route_report()
        assert "no mitophagy data" in report
