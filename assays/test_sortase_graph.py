from __future__ import annotations

"""Tests for metabolon.sortase.graph DOT visualization."""


import subprocess
import sys

import pytest


# ── import helper ──────────────────────────────────────────────

@pytest.fixture()
def graph_mod():
    from metabolon.sortase import graph as g
    return g


# ── sample data ────────────────────────────────────────────────

def _sample_tasks():
    """Three tasks: a is standalone, b depends on a, c depends on b."""
    return [
        {"name": "add-model", "description": "Add model class",
         "spec": "", "files": ["model.py"], "signal": "default",
         "prerequisite": None},
        {"name": "add-routes", "description": "Add routes",
         "spec": "", "files": ["routes.py"], "signal": "default",
         "prerequisite": "add-model"},
        {"name": "add-tests", "description": "Add tests",
         "spec": "", "files": ["tests/test_app.py"], "signal": "default",
         "prerequisite": "add-routes"},
    ]


def _sample_state():
    return {
        "tasks": _sample_tasks(),
        "tool_by_task": {
            "add-model": "goose",
            "add-routes": "codex",
            "add-tests": "gemini",
        },
        "route_decisions": [],
    }


# ── task dependency DOT ────────────────────────────────────────

class TestTaskDependencyDot:
    """to_dot() produces valid DOT for the task dependency graph."""

    def test_basic_structure(self, graph_mod):
        dot = graph_mod.to_dot(_sample_state())
        assert dot.startswith("digraph")
        assert "add-model" in dot
        assert "add-routes" in dot
        assert "add-tests" in dot

    def test_edges_reflect_prerequisites(self, graph_mod):
        dot = graph_mod.to_dot(_sample_state())
        # b -> a (add-routes depends on add-model)
        assert '"add-model" -> "add-routes"' in dot or \
               '"add-model" -> "add-routes"' in dot.replace("\n", "")
        # c -> b (add-tests depends on add-routes)
        assert '"add-routes" -> "add-tests"' in dot or \
               '"add-routes" -> "add-tests"' in dot.replace("\n", "")

    def test_includes_tool_labels(self, graph_mod):
        dot = graph_mod.to_dot(_sample_state())
        assert "goose" in dot
        assert "codex" in dot
        assert "gemini" in dot

    def test_no_duplicate_edges(self, graph_mod):
        dot = graph_mod.to_dot(_sample_state())
        # Each edge should appear exactly once
        edge = '"add-model" -> "add-routes"'
        assert dot.count(edge) == 1

    def test_independent_tasks_no_edges(self, graph_mod):
        """Tasks with no prerequisites should have no incoming edges."""
        tasks = [
            {"name": "task-a", "description": "A", "spec": "",
             "files": [], "signal": "default", "prerequisite": None},
            {"name": "task-b", "description": "B", "spec": "",
             "files": [], "signal": "default", "prerequisite": None},
        ]
        state = {"tasks": tasks, "tool_by_task": {}, "route_decisions": []}
        dot = graph_mod.to_dot(state)
        assert "->" not in dot

    def test_valid_dot_syntax(self, graph_mod):
        """Output should parse without error via graphviz dot if available."""
        dot = graph_mod.to_dot(_sample_state())
        # At minimum, balanced braces and proper keywords
        assert dot.count("{") == dot.count("}")
        assert "digraph" in dot

    def test_empty_tasks(self, graph_mod):
        state = {"tasks": [], "tool_by_task": {}, "route_decisions": []}
        dot = graph_mod.to_dot(state)
        assert "digraph" in dot
        # Should produce a valid but empty graph
        assert dot.count("{") == dot.count("}")

    def test_tasks_without_routing(self, graph_mod):
        """to_dot should work even when tool_by_task is empty."""
        state = {"tasks": _sample_tasks(), "tool_by_task": {},
                 "route_decisions": []}
        dot = graph_mod.to_dot(state)
        assert "add-model" in dot
        # Tool label should show "unrouted" or similar
        assert "unrouted" in dot.lower()

    def test_name_sanitization(self, graph_mod):
        """Node names with special chars should be quoted safely."""
        tasks = [
            {"name": "task:with:colons", "description": "D", "spec": "",
             "files": [], "signal": "default", "prerequisite": None},
        ]
        state = {"tasks": tasks, "tool_by_task": {}, "route_decisions": []}
        dot = graph_mod.to_dot(state)
        assert '"task:with:colons"' in dot


# ── pipeline DOT ───────────────────────────────────────────────

class TestPipelineDot:
    """pipeline_dot() renders the LangGraph node graph."""

    def test_contains_all_nodes(self, graph_mod):
        dot = graph_mod.pipeline_dot()
        for node in ("decompose", "route", "execute", "validate", "log_results"):
            assert node in dot, f"Missing node: {node}"

    def test_contains_end(self, graph_mod):
        dot = graph_mod.pipeline_dot()
        assert "END" in dot

    def test_edges_in_order(self, graph_mod):
        dot = graph_mod.pipeline_dot()
        assert "decompose" in dot
        assert "route" in dot
        # Edge sequence: decompose->route->execute->validate->log_results->END
        for a, b in [("decompose", "route"), ("route", "execute"),
                      ("execute", "validate"), ("validate", "log_results"),
                      ("log_results", "END")]:
            assert f'"{a}" -> "{b}"' in dot or f"{a} -> {b}" in dot, \
                f"Missing edge: {a} -> {b}"

    def test_valid_dot_structure(self, graph_mod):
        dot = graph_mod.pipeline_dot()
        assert dot.startswith("digraph")
        assert dot.count("{") == dot.count("}")
