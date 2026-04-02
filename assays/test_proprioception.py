from __future__ import annotations

"""Tests for metabolon/enzymes/proprioception.py — integration paths and
edge cases complementary to test_enzymes_proprioception.py."""


import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.proprioception import (
    HKT,
    _log_and_gradient,
    _sensorium,
    _histone_store,
    _skills,
    _timing,
    proprioception,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _isolate_gradient_log(tmp_path, monkeypatch):
    """Redirect gradient log to tmp so tests never touch the real file."""
    log = tmp_path / "proprioception.jsonl"
    monkeypatch.setattr(
        "metabolon.enzymes.proprioception._GRADIENT_LOG", str(log)
    )
    return log


# ── _genome integration ──────────────────────────────────────────────────


class TestGenome:
    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_genome_missing_constitution(self, _mock_grad):
        with patch("metabolon.resources.constitution.CANONICAL") as mock_path:
            mock_path.exists.return_value = False
            from metabolon.enzymes.proprioception import _genome

            result = _genome()
        assert "No constitution" in result

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_genome_reads_constitution_file(self, _mock_grad):
        with patch("metabolon.resources.constitution.CANONICAL") as mock_path:
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = "# Constitution\nBe excellent."
            from metabolon.enzymes.proprioception import _genome

            result = _genome()
        assert "Be excellent." in result


# ── _circadian phase boundary coverage ───────────────────────────────────


class TestCircadianPhases:
    """Cover all phase branches with specific hour values."""

    @patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="Evt")
    def test_pre_dawn_dormancy(self, _mock):
        from metabolon.enzymes.proprioception import _circadian

        fake_dt = __import__("datetime").datetime(2026, 4, 2, 2, 0, tzinfo=HKT)
        with patch("metabolon.enzymes.proprioception.datetime") as mock_dt:
            mock_dt.now.return_value = fake_dt
            result = _circadian()
        assert "dormancy" in result.lower()

    @patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="Evt")
    def test_morning_activation(self, _mock):
        from metabolon.enzymes.proprioception import _circadian

        fake_dt = __import__("datetime").datetime(2026, 4, 2, 8, 0, tzinfo=HKT)
        with patch("metabolon.enzymes.proprioception.datetime") as mock_dt:
            mock_dt.now.return_value = fake_dt
            result = _circadian()
        assert "photoreception" in result.lower()

    @patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="Evt")
    def test_midday_transition(self, _mock):
        from metabolon.enzymes.proprioception import _circadian

        fake_dt = __import__("datetime").datetime(2026, 4, 2, 13, 0, tzinfo=HKT)
        with patch("metabolon.enzymes.proprioception.datetime") as mock_dt:
            mock_dt.now.return_value = fake_dt
            result = _circadian()
        assert "transition" in result.lower()

    @patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="Evt")
    def test_evening_wind_down(self, _mock):
        from metabolon.enzymes.proprioception import _circadian

        fake_dt = __import__("datetime").datetime(2026, 4, 2, 18, 0, tzinfo=HKT)
        with patch("metabolon.enzymes.proprioception.datetime") as mock_dt:
            mock_dt.now.return_value = fake_dt
            result = _circadian()
        assert "wind-down" in result.lower()

    @patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="Evt")
    def test_night_dormancy_prep(self, _mock):
        from metabolon.enzymes.proprioception import _circadian

        fake_dt = __import__("datetime").datetime(2026, 4, 2, 21, 0, tzinfo=HKT)
        with patch("metabolon.enzymes.proprioception.datetime") as mock_dt:
            mock_dt.now.return_value = fake_dt
            result = _circadian()
        assert "dormancy" in result.lower()


# ── _sensorium edge cases ────────────────────────────────────────────────


class TestSensoriumEdgeCases:
    def test_sensorium_skips_malformed_json(self, tmp_path):
        log_path = tmp_path / "germline" / "loci" / "signals" / "rheotaxis.jsonl"
        log_path.parent.mkdir(parents=True)
        log_path.write_text("not-json\n" + json.dumps({"ts": "T1", "query": "valid query"}) + "\n")
        with patch.object(Path, "home", return_value=tmp_path):
            result = _sensorium()
        assert "valid query" in result
        assert "not-json" not in result

    def test_sensorium_limits_to_last_10(self, tmp_path):
        log_path = tmp_path / "germline" / "loci" / "signals" / "rheotaxis.jsonl"
        log_path.parent.mkdir(parents=True)
        lines = [json.dumps({"ts": f"T{i}", "query": f"q{i}"}) for i in range(15)]
        log_path.write_text("\n".join(lines))
        with patch.object(Path, "home", return_value=tmp_path):
            result = _sensorium()
        # Should contain the last 10 entries (q5..q14) but not earlier ones
        assert "q5" in result
        assert "q14" in result
        assert "q0" not in result
        assert "q4" not in result

    def test_sensorium_empty_log_file(self, tmp_path):
        log_path = tmp_path / "germline" / "loci" / "signals" / "rheotaxis.jsonl"
        log_path.parent.mkdir(parents=True)
        log_path.write_text("")
        with patch.object(Path, "home", return_value=tmp_path):
            result = _sensorium()
        assert "no search log" in result


# ── _histone_store size formatting ──────────────────────────────────────


class TestHistoneStoreFormatting:
    def test_histone_store_shows_kb_size(self, tmp_path):
        marks_dir = tmp_path / "epigenome" / "marks"
        marks_dir.mkdir(parents=True)
        # Write files totalling >1KB to verify KB formatting
        (marks_dir / "big.md").write_text("x" * 2048)
        (marks_dir / "small.md").write_text("y" * 100)
        with patch.object(Path, "home", return_value=tmp_path):
            result = _histone_store()
        assert "2 marks" in result
        assert "KB" in result
        assert "epigenome" in result


# ── _skills with actual diff output ──────────────────────────────────────


class TestSkillsOutput:
    def test_skills_reports_modified_and_added(self, tmp_path):
        local = tmp_path / "local" / "suite"
        cache_version = tmp_path / "cache" / "suite" / "1.0.0" / "skills"
        local.mkdir(parents=True)
        cache_version.mkdir(parents=True)
        # Modified file
        (local / "a.md").write_text("old content")
        (cache_version / "a.md").write_text("new content")
        # Upstream-only file
        (cache_version / "b.md").write_text("upstream addition")

        registry = {"suite": {"local": str(local), "cache_pattern": str(tmp_path / "cache" / "suite")}}
        with patch("metabolon.enzymes.proprioception._restore_fork_registry", return_value=registry):
            result = _skills()
        assert "suite" in result
        assert "2 change(s)" in result
        assert "modified: a.md" in result
        assert "new upstream: b.md" in result


# ── _timing with single entry ────────────────────────────────────────────


class TestTimingSingleEntry:
    def test_single_entry_stats(self):
        entry = MagicMock(latency_ms=300, tool="solo_tool", outcome="success")
        with patch("metabolon.membrane.timing_buffer") as mock_buf:
            mock_buf.snapshot.return_value = [entry]
            result = _timing()
        assert "1 calls" in result
        assert "avg:" in result
        assert "solo_tool" in result
        assert "1 success, 0 error" in result
