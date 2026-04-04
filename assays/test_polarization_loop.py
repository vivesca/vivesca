from __future__ import annotations

"""Tests for polarization_loop — state types and constants."""

from pathlib import Path

import pytest

pytest.importorskip("langgraph")


class TestPaths:
    def test_checkpoint_db_path(self):
        from metabolon.organelles.polarization_loop import CHECKPOINT_DB

        assert isinstance(CHECKPOINT_DB, Path)
        assert "checkpoints" in str(CHECKPOINT_DB)

    def test_reports_dir(self):
        from metabolon.organelles.polarization_loop import REPORTS_DIR

        assert isinstance(REPORTS_DIR, Path)


class TestPolarizationState:
    def test_state_has_annotations(self):
        from metabolon.organelles.polarization_loop import PolarizationState

        assert len(PolarizationState.__annotations__) > 0
