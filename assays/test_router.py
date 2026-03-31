from __future__ import annotations
"""Tests for metabolon.sortase.router."""

from metabolon.sortase.router import (
    DEFAULT_TOOL,
    RouteDecision,
    route_description,
    ROUTING_RULES,
)


def test_forced_backend_overrides():
    d = route_description("anything", forced_backend="codex")
    assert d.tool == "codex"
    assert "Forced" in d.reason


def test_rust_routes_to_codex():
    d = route_description("Fix the cargo build for this crate")
    assert d.tool == "codex"


def test_algorithm_routes_to_gemini():
    d = route_description("Implement a new sorting algorithm")
    assert d.tool == "gemini"


def test_boilerplate_routes_to_opencode():
    d = route_description("Generate boilerplate for the new module")
    assert d.tool == "opencode"


def test_default_routes_to_goose():
    d = route_description("Fix a typo in the README")
    assert d.tool == DEFAULT_TOOL
    assert d.tool == "goose"


def test_case_insensitive_matching():
    d = route_description("RUST cargo build issue")
    assert d.tool == "codex"


def test_multifile_routes_to_codex():
    d = route_description("Refactor across multiple files")
    assert d.tool == "codex"


def test_route_decision_has_correct_fields():
    d = route_description("refactor the codebase")
    assert isinstance(d, RouteDecision)
    assert d.tool is not None
    assert d.reason is not None
    assert d.pattern is not None


def test_default_route_has_no_pattern():
    d = route_description("Just a regular change with no matching keywords")
    assert d.tool == DEFAULT_TOOL
    assert d.pattern is None


def test_all_routing_rules_are_valid():
    # Ensure all rules have expected tuple structure
    for pattern, tool, reason in ROUTING_RULES:
        assert isinstance(pattern, str)
        assert isinstance(tool, str)
        assert isinstance(reason, str)
        assert len(tool) > 0
