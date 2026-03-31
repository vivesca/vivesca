from __future__ import annotations
"""Tests for tissue_routing — symbiont strain matching."""

from unittest.mock import patch


class TestDefaultRoutes:
    def test_returns_dict(self):
        from metabolon.organelles.tissue_routing import default_routes
        routes = default_routes()
        assert isinstance(routes, dict)
        assert len(routes) > 0

    def test_all_values_are_strings(self):
        from metabolon.organelles.tissue_routing import default_routes
        for task, model in default_routes().items():
            assert isinstance(task, str)
            assert isinstance(model, str)

    def test_known_task_types(self):
        from metabolon.organelles.tissue_routing import default_routes
        routes = default_routes()
        assert "probe" in routes
        assert "coding" in routes
        assert "synthesis" in routes

    def test_returns_copy(self):
        from metabolon.organelles.tissue_routing import default_routes
        a = default_routes()
        b = default_routes()
        a["probe"] = "changed"
        assert b["probe"] != "changed"


class TestObservedRoutes:
    def test_falls_back_to_defaults(self):
        from metabolon.organelles.tissue_routing import observed_routes
        # When mitophagy is unavailable, should return defaults
        with patch("metabolon.organelles.tissue_routing.default_routes") as mock:
            mock.return_value = {"probe": "glm"}
            routes = observed_routes()
        assert "probe" in routes


class TestRoute:
    def test_known_task_returns_model(self):
        from metabolon.organelles.tissue_routing import route
        result = route("probe")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_task_returns_sonnet(self):
        from metabolon.organelles.tissue_routing import route
        result = route("nonexistent_task_xyz")
        assert result == "sonnet"


class TestRouteReport:
    def test_returns_string(self):
        from metabolon.organelles.tissue_routing import route_report
        report = route_report()
        assert isinstance(report, str)
        assert "routing" in report.lower()
        assert "probe" in report
