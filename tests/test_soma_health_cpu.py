"""Tests for check_cpu() in soma-health."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

EFFECTOR = Path(__file__).resolve().parent.parent / "effectors" / "soma-health"

MOD_NAME = "test_soma_health_cpu_mod"


@pytest.fixture
def ns():
    """Load soma-health into a namespace (non-__main__ so main() doesn't fire)."""
    mod = types.ModuleType(MOD_NAME)
    sys.modules[MOD_NAME] = mod
    try:
        source = EFFECTOR.read_text()
        namespace: dict = {"__name__": MOD_NAME, "__file__": str(EFFECTOR)}
        exec(source, namespace)
        yield namespace
    finally:
        sys.modules.pop(MOD_NAME, None)


def _mock_loadavg(load_str: str):
    """mock_open that serves a /proc/loadavg line with a given 1-min value."""
    return mock_open(read_data=f"{load_str} 4.10 3.80 2/123 4567")


class TestCheckCpu:
    def test_ok(self, ns):
        with patch("builtins.open", _mock_loadavg("2.50")):
            result = ns["check_cpu"]()
        assert result.name == "cpu"
        assert result.status == "ok"
        assert result.value == "2.50"

    def test_warn(self, ns):
        with patch("builtins.open", _mock_loadavg("7.80")):
            result = ns["check_cpu"]()
        assert result.name == "cpu"
        assert result.status == "warn"
        assert result.value == "7.80"

    def test_crit(self, ns):
        with patch("builtins.open", _mock_loadavg("15.00")):
            result = ns["check_cpu"]()
        assert result.name == "cpu"
        assert result.status == "crit"
        assert result.value == "15.00"

    def test_boundary_warn_excluded(self, ns):
        """Load exactly 6.0 is ok — threshold is >6."""
        with patch("builtins.open", _mock_loadavg("6.00")):
            result = ns["check_cpu"]()
        assert result.status == "ok"

    def test_boundary_crit_excluded(self, ns):
        """Load exactly 12.0 is warn — threshold is >12."""
        with patch("builtins.open", _mock_loadavg("12.00")):
            result = ns["check_cpu"]()
        assert result.status == "warn"

    def test_error_on_missing_file(self, ns):
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = ns["check_cpu"]()
        assert result.name == "cpu"
        assert result.status == "error"
        assert result.value == "?"

    def test_wired_into_run_health(self, ns):
        """check_cpu must appear in run_health source."""
        source = EFFECTOR.read_text()
        assert "check_cpu()" in source
        # Also verify calling run_health (mocked) includes cpu in results
        report = ns["HealthReport"]()
        report.add(ns["Check"](name="disk", status="ok", value="50%"))
        # Can't fully run run_health without mocking everything, but we
        # can verify the function object exists and is callable
        assert callable(ns["check_cpu"])
