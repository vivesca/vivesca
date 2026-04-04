from __future__ import annotations

"""Tests for metabolism_loop — state types and constants."""

import pytest

pytest.importorskip("langgraph")


class TestConstants:
    def test_max_iterations(self):
        from metabolon.organelles.metabolism_loop import MAX_ITERATIONS

        assert MAX_ITERATIONS > 0
        assert MAX_ITERATIONS <= 10

    def test_thresholds(self):
        from metabolon.organelles.metabolism_loop import HEALTHY_THRESHOLD, INFECTED_THRESHOLD

        assert 0 < INFECTED_THRESHOLD < HEALTHY_THRESHOLD < 1


class TestMetabolismState:
    def test_state_type_has_required_keys(self):
        from metabolon.organelles.metabolism_loop import MetabolismState

        annotations = MetabolismState.__annotations__
        assert "iteration" in annotations or "health_score" in annotations
