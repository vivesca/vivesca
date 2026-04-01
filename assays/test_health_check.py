"""Tests for effectors/health-check — subprocess-based, as per effector convention."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

EFFECTOR = Path(__file__).resolve().parent.parent / "effectors" / "health-check"

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(args: list[str] | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run health-check as a subprocess (the correct effector test pattern)."""
    cmd = [sys.executable, str(EFFECTOR)]
    if args:
        cmd.extend(args)
    merged_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    if env is not None:
        merged_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=15, env=merged_env)


# ---------------------------------------------------------------------------
# No data source available
# ---------------------------------------------------------------------------

class TestNoDataSource:
    def test_unknown_when_no_data(self, tmp_path, monkeypatch):
        """With no sopor, no oura cache, no API token → status unknown, exit 1."""
        monkeypatch.setenv("PATH", str(tmp_path))  # no sopor on PATH
        monkeypatch.delenv("OURA_PERSONAL_ACCESS_TOKEN", raising=False)
        # Point HOME to tmp so no ~/.cache/oura exists
        monkeypatch.setenv("HOME", str(tmp_path))
        result = _run()
        assert result.returncode == 1
        assert "UNKNOWN" in result.stdout or "unknown" in result.stdout.lower()

    def test_unknown_json_output(self, tmp_path, monkeypatch):
        """--json flag should produce valid JSON even with no data."""
        monkeypatch.setenv("PATH", str(tmp_path))
        monkeypatch.delenv("OURA_PERSONAL_ACCESS_TOKEN", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        result = _run(["--json"])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "unknown"


# ---------------------------------------------------------------------------
# Data from oura cache
# ---------------------------------------------------------------------------

class TestOuraCache:
    def test_green_status_from_cache(self, tmp_path, monkeypatch):
        """Good sleep/readiness → green."""
        cache_dir = tmp_path / ".cache" / "oura"
        cache_dir.mkdir(parents=True)
        row = {
            "date": "2026-04-01",
            "readiness_score": 88,
            "sleep_hours": 7.5,
            "sleep_score": 85,
            "hrv": 45,
        }
        (cache_dir / "latest.json").write_text(json.dumps([row]))
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("PATH", str(tmp_path))  # no sopor
        monkeypatch.delenv("OURA_PERSONAL_ACCESS_TOKEN", raising=False)
        result = _run()
        assert result.returncode == 0
        assert "GREEN" in result.stdout
        assert "readiness=88" in result.stdout
        assert "sleep=7.5h" in result.stdout

    def test_yellow_low_readiness(self, tmp_path, monkeypatch):
        """Readiness below 70 → yellow + advisory."""
        cache_dir = tmp_path / ".cache" / "oura"
        cache_dir.mkdir(parents=True)
        row = {
            "date": "2026-04-01",
            "readiness_score": 65,
            "sleep_hours": 7.0,
            "sleep_score": 70,
            "hrv": 40,
        }
        (cache_dir / "latest.json").write_text(json.dumps([row]))
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypath_env = str(tmp_path)
        monkeypatch.setenv("PATH", monkeypath_env)
        monkeypatch.delenv("OURA_PERSONAL_ACCESS_TOKEN", raising=False)
        result = _run()
        assert result.returncode == 0
        assert "YELLOW" in result.stdout
        assert "Light activity only today." in result.stdout

    def test_red_very_low_readiness(self, tmp_path, monkeypatch):
        """Readiness below 50 → red."""
        cache_dir = tmp_path / ".cache" / "oura"
        cache_dir.mkdir(parents=True)
        row = {
            "date": "2026-04-01",
            "readiness_score": 45,
            "sleep_hours": 7.0,
            "sleep_score": 60,
            "hrv": 35,
        }
        (cache_dir / "latest.json").write_text(json.dumps([row]))
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("PATH", str(tmp_path))
        monkeypatch.delenv("OURA_PERSONAL_ACCESS_TOKEN", raising=False)
        result = _run()
        assert result.returncode == 0
        assert "RED" in result.stdout

    def test_yellow_low_sleep_advisory(self, tmp_path, monkeypatch):
        """Sleep < 6h → yellow + sleep debt advisory."""
        cache_dir = tmp_path / ".cache" / "oura"
        cache_dir.mkdir(parents=True)
        row = {
            "date": "2026-04-01",
            "readiness_score": 75,
            "sleep_hours": 5.2,
            "sleep_score": 55,
            "hrv": 40,
        }
        (cache_dir / "latest.json").write_text(json.dumps([row]))
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("PATH", str(tmp_path))
        monkeypatch.delenv("OURA_PERSONAL_ACCESS_TOKEN", raising=False)
        result = _run()
        assert result.returncode == 0
        assert "YELLOW" in result.stdout
        assert "Sleep debt" in result.stdout

    def test_json_output_structure(self, tmp_path, monkeypatch):
        """--json returns valid JSON with expected keys."""
        cache_dir = tmp_path / ".cache" / "oura"
        cache_dir.mkdir(parents=True)
        row = {
            "date": "2026-04-01",
            "readiness_score": 80,
            "sleep_hours": 7.0,
            "sleep_score": 82,
            "hrv": 42,
        }
        (cache_dir / "latest.json").write_text(json.dumps([row]))
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("PATH", str(tmp_path))
        monkeypatch.delenv("OURA_PERSONAL_ACCESS_TOKEN", raising=False)
        result = _run(["--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "green"
        assert data["readiness"] == 80
        assert data["sleep_hours"] == 7.0
        assert data["advisories"] == []


# ---------------------------------------------------------------------------
# classify() unit tests (import-free via exec)
# ---------------------------------------------------------------------------

class TestClassifyUnit:
    """Test classify() directly by exec-loading the effector source."""

    @pytest.fixture(autouse=True)
    def _load(self):
        ns: dict = {"__name__": "health_check"}
        exec(open(EFFECTOR).read(), ns)
        self.classify = ns["classify"]

    def test_green(self):
        assert self.classify({"readiness": 85, "sleep_hours": 7.5, "hrv": 50}) == "green"

    def test_yellow_readiness(self):
        assert self.classify({"readiness": 65, "sleep_hours": 7.5, "hrv": 40}) == "yellow"

    def test_yellow_sleep(self):
        assert self.classify({"readiness": 80, "sleep_hours": 5.5, "hrv": 40}) == "yellow"

    def test_yellow_hrv(self):
        assert self.classify({"readiness": 80, "sleep_hours": 7.5, "hrv": 25}) == "yellow"

    def test_red_readiness(self):
        assert self.classify({"readiness": 45, "sleep_hours": 7.5, "hrv": 40}) == "red"

    def test_red_sleep(self):
        assert self.classify({"readiness": 50, "sleep_hours": 4.0, "hrv": 40}) == "red"

    def test_defaults_to_green(self):
        """No metrics provided defaults to green."""
        assert self.classify({}) == "green"
