"""Test: soma-watchdog observability — JSONL resource logging + Telegram crit alerts.

Golem task: Add two functions to soma-watchdog:

1. log_resources() — each 60s tick, append a JSON line to
   ~/epigenome/chromatin/telemetry/soma-resources.jsonl with:
   {ts, cpu_1m, mem_pct, disk_pct, disk_free_gb, golem_count}
   Read cpu_1m from /proc/loadavg field 1. mem from /proc/meminfo.
   disk from shutil.disk_usage(HOME). golem_count from pgrep -c -f golem.
   Create telemetry dir if missing. Add JSONL_PATH constant.

2. alert_on_crit(health_json: dict) — after soma-health --json each tick,
   if any check has status "crit", call subprocess.run(["deltos", message]).
   Dedup: read ~/tmp/soma-alert-last.txt mtime — skip if <15 min ago,
   write current time after sending. Add ALERT_STAMP constant.

Call both from the main loop after each tick.

Acceptance: pytest tests/test_soma_watchdog_observability.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

JSONL_PATH = Path.home() / "epigenome" / "chromatin" / "telemetry" / "soma-resources.jsonl"
ALERT_STAMP = Path.home() / "tmp" / "soma-alert-last.txt"


def _import_watchdog():
    """Load soma-watchdog by exec-ing its source.

    Returns a module-like object whose __dict__ IS the exec namespace,
    so patch.object(mod, 'CONSTANT', ...) affects the functions' globals.
    """
    src = open(Path.home() / "germline" / "effectors" / "soma-watchdog").read()
    ns: dict = {"__name__": "soma_watchdog_test"}
    exec(src, ns)

    class _Module:
        """Module proxy whose __dict__ is the exec namespace itself."""

        pass

    mod = _Module()
    mod.__dict__ = ns  # identity — patch.object modifies ns directly
    return mod


# --- JSONL logging tests ---


class TestLogResources:
    def test_function_exists(self):
        mod = _import_watchdog()
        assert hasattr(mod, "log_resources"), "log_resources function must exist"

    def test_writes_valid_jsonl(self, tmp_path):
        mod = _import_watchdog()
        test_jsonl = tmp_path / "soma-resources.jsonl"

        with (
            patch.object(mod, "JSONL_PATH", test_jsonl),
            patch("builtins.open", wraps=open),
            patch("shutil.disk_usage") as mock_disk,
            patch("subprocess.run") as mock_pgrep,
        ):
            mock_disk.return_value = MagicMock(
                used=16 * 1024**3, total=20 * 1024**3, free=4 * 1024**3
            )
            mock_pgrep.return_value = MagicMock(stdout="3\n", returncode=0)
            mod.log_resources()

        if test_jsonl.exists():
            line = test_jsonl.read_text().strip().splitlines()[-1]
            data = json.loads(line)
            for key in ("ts", "cpu_1m", "mem_pct", "disk_pct", "disk_free_gb", "golem_count"):
                assert key in data, f"Missing field: {key}"
            assert isinstance(data["ts"], str)
            assert isinstance(data["cpu_1m"], (int, float))
            assert isinstance(data["golem_count"], int)


# --- Telegram alert tests ---

SAMPLE_CRIT = {
    "checks": [
        {"name": "disk", "status": "crit", "value": "92%", "detail": "0.8GB free"},
        {"name": "memory", "status": "ok", "value": "60%", "detail": ""},
    ],
    "overall": "crit",
}

SAMPLE_OK = {
    "checks": [
        {"name": "disk", "status": "ok", "value": "70%", "detail": ""},
        {"name": "memory", "status": "ok", "value": "60%", "detail": ""},
    ],
    "overall": "ok",
}


class TestAlertOnCrit:
    def test_function_exists(self):
        mod = _import_watchdog()
        assert hasattr(mod, "alert_on_crit"), "alert_on_crit function must exist"

    def test_sends_alert_on_crit(self, tmp_path):
        mod = _import_watchdog()
        stamp = tmp_path / "soma-alert-last.txt"

        with (
            patch.object(mod, "ALERT_STAMP", stamp),
            patch("subprocess.run") as mock_run,
        ):
            mod.alert_on_crit(SAMPLE_CRIT)
            calls = [c for c in mock_run.call_args_list if "deltos" in str(c)]
            assert len(calls) >= 1, f"deltos not called. Calls: {mock_run.call_args_list}"

    def test_no_alert_on_ok(self, tmp_path):
        mod = _import_watchdog()
        stamp = tmp_path / "soma-alert-last.txt"

        with (
            patch.object(mod, "ALERT_STAMP", stamp),
            patch("subprocess.run") as mock_run,
        ):
            mod.alert_on_crit(SAMPLE_OK)
            calls = [c for c in mock_run.call_args_list if "deltos" in str(c)]
            assert len(calls) == 0, f"deltos called on OK: {mock_run.call_args_list}"

    def test_dedup_within_15_min(self, tmp_path):
        mod = _import_watchdog()
        stamp = tmp_path / "soma-alert-last.txt"
        stamp.write_text(str(time.time()))

        with (
            patch.object(mod, "ALERT_STAMP", stamp),
            patch("subprocess.run") as mock_run,
        ):
            mod.alert_on_crit(SAMPLE_CRIT)
            calls = [c for c in mock_run.call_args_list if "deltos" in str(c)]
            assert len(calls) == 0, "Should skip alert within 15-min dedup window"

    def test_alert_after_dedup_expires(self, tmp_path):
        mod = _import_watchdog()
        stamp = tmp_path / "soma-alert-last.txt"
        stamp.write_text(str(time.time() - 1200))

        with (
            patch.object(mod, "ALERT_STAMP", stamp),
            patch("subprocess.run") as mock_run,
        ):
            mod.alert_on_crit(SAMPLE_CRIT)
            calls = [c for c in mock_run.call_args_list if "deltos" in str(c)]
            assert len(calls) >= 1, "Should alert after dedup window expired"
