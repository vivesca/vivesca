"""Test: soma-health CPU load check.

Golem task: Add check_cpu() to soma-health that reads /proc/loadavg,
returns Check with warn if 1-min avg > 6, crit if > 12.
Include in --json output and --daemon one-liner.

Acceptance: these tests pass with `pytest tests/test_soma_health_cpu.py`.
"""
from __future__ import annotations

import importlib
import importlib.machinery
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import mock_open, patch


_SOMA_HEALTH_PATH = str(Path.home() / "germline" / "effectors" / "soma-health")


def _import_soma_health():
    """Import soma-health as a module (file has no .py extension)."""
    loader = importlib.machinery.SourceFileLoader("soma_health", _SOMA_HEALTH_PATH)
    spec = importlib.util.spec_from_file_location(
        "soma_health", _SOMA_HEALTH_PATH, loader=loader
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCheckCpu:
    """check_cpu() must exist and return a Check based on /proc/loadavg."""

    def test_check_cpu_exists(self):
        mod = _import_soma_health()
        assert hasattr(mod, "check_cpu"), "check_cpu function must exist in soma-health"

    def test_cpu_ok(self):
        mod = _import_soma_health()
        loadavg_content = "2.50 2.00 1.50 3/200 12345\n"
        with patch("builtins.open", mock_open(read_data=loadavg_content)):
            result = mod.check_cpu()
        assert result.status == "ok"
        assert "2.5" in result.value or "2.50" in result.value

    def test_cpu_warn(self):
        mod = _import_soma_health()
        loadavg_content = "7.50 5.00 4.00 3/200 12345\n"
        with patch("builtins.open", mock_open(read_data=loadavg_content)):
            result = mod.check_cpu()
        assert result.status == "warn"

    def test_cpu_crit(self):
        mod = _import_soma_health()
        loadavg_content = "13.00 10.00 8.00 3/200 12345\n"
        with patch("builtins.open", mock_open(read_data=loadavg_content)):
            result = mod.check_cpu()
        assert result.status == "crit"

    def test_cpu_in_json_output(self):
        """--json output must include a 'cpu' check."""
        result = subprocess.run(
            [sys.executable, str(Path.home() / "germline" / "effectors" / "soma-health"), "--json"],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(result.stdout)
        check_names = [c["name"] for c in data["checks"]]
        assert "cpu" in check_names, f"cpu not in JSON checks: {check_names}"
