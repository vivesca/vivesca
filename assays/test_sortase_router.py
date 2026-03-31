from __future__ import annotations

"""Tests for sortase router."""

from metabolon.sortase.router import DEFAULT_TOOL, RouteDecision, route_description


def test_forced_backend_overrides():
    d = route_description("anything", forced_backend="codex")
    assert d.tool == "codex"
    assert "Forced" in d.reason


def test_rust_routes_to_codex():
    d = route_description("Fix the cargo build for the crate")
    assert d.tool == "codex"


def test_algorithm_routes_to_gemini():
    d = route_description("Implement a sorting algorithm")
    assert d.tool == "gemini"


def test_boilerplate_routes_to_opencode():
    d = route_description("Generate boilerplate template code")
    assert d.tool == "opencode"


def test_default_routes_to_goose():
    d = route_description("Update the config file")
    assert d.tool == DEFAULT_TOOL
    assert d.tool == "goose"


def test_case_insensitive():
    d = route_description("RUST cargo build")
    assert d.tool == "codex"


def test_route_decision_fields():
    d = route_description("refactor the module")
    assert isinstance(d, RouteDecision)
    assert d.pattern is not None  # matched a rule
