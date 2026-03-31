"""Tests for metabolon/enzymes/proprioception.py — internal-state sensing with gradients."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from metabolon.enzymes.proprioception import (
    HKT,
    _diff_fork,
    _find_latest_cache_version,
    _log_and_gradient,
    _restore_fork_registry,
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


# ── _log_and_gradient ────────────────────────────────────────────────────


class TestLogAndGradient:
    def test_first_reading_returns_none(self, _isolate_gradient_log):
        result = _log_and_gradient("genome", "hello world")
        assert result is None
        lines = _isolate_gradient_log.read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["target"] == "genome"
        assert entry["size"] == 11

    def test_below_threshold_returns_none(self, _isolate_gradient_log):
        for _ in range(5):
            _log_and_gradient("genome", "x" * 20)
        result = _log_and_gradient("genome", "x" * 40)
        assert result is None

    def test_detects_growing_gradient(self, _isolate_gradient_log):
        _log_and_gradient("genome", "x" * 10)
        result = _log_and_gradient("genome", "x" * 200)
        assert result is not None
        assert "growing" in result
        assert "genome" in result
        assert "+190" in result

    def test_detects_shrinking_gradient(self, _isolate_gradient_log):
        _log_and_gradient("anatomy", "x" * 200)
        result = _log_and_gradient("anatomy", "x" * 10)
        assert result is not None
        assert "shrinking" in result
        assert "-190" in result

    def test_different_targets_independent(self, _isolate_gradient_log):
        _log_and_gradient("genome", "x" * 200)
        result = _log_and_gradient("anatomy", "x" * 10)
        assert result is None

    def test_handles_corrupt_log(self, _isolate_gradient_log):
        _isolate_gradient_log.write_text("not-json\n")
        result = _log_and_gradient("genome", "test")
        assert result is None

    def test_creates_log_directory(self, tmp_path, monkeypatch):
        log_path = tmp_path / "subdir" / "proprioception.jsonl"
        monkeypatch.setattr(
            "metabolon.enzymes.proprioception._GRADIENT_LOG", str(log_path)
        )
        result = _log_and_gradient("genome", "test")
        assert result is None
        assert log_path.exists()


# ── proprioception dispatch ──────────────────────────────────────────────


class TestProprioceptionDispatch:
    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_dispatches_genome(self, _mock_grad):
        with patch.dict(
            "metabolon.enzymes.proprioception._DISPATCH",
            {"genome": lambda: "GENOME_TEXT"},
        ):
            result = proprioception("genome")
        assert result == "GENOME_TEXT"

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_dispatches_anatomy(self, _mock_grad):
        with patch.dict(
            "metabolon.enzymes.proprioception._DISPATCH",
            {"anatomy": lambda: "ANATOMY_TEXT"},
        ):
            result = proprioception("anatomy")
        assert result == "ANATOMY_TEXT"

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_dispatches_circadian(self, _mock_grad):
        with patch.dict(
            "metabolon.enzymes.proprioception._DISPATCH",
            {"circadian": lambda: "CIRCADIAN_TEXT"},
        ):
            result = proprioception("circadian")
        assert result == "CIRCADIAN_TEXT"

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_dispatches_vitals(self, _mock_grad):
        with patch.dict(
            "metabolon.enzymes.proprioception._DISPATCH",
            {"vitals": lambda: "VITALS"},
        ):
            result = proprioception("vitals")
        assert result == "VITALS"

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_dispatches_reflexes(self, _mock_grad):
        with patch.dict(
            "metabolon.enzymes.proprioception._DISPATCH",
            {"reflexes": lambda: "REFLEXES"},
        ):
            result = proprioception("reflexes")
        assert result == "REFLEXES"

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value="GRADIENT_INFO")
    def test_gradient_appended_to_reading(self, _mock_grad):
        with patch.dict(
            "metabolon.enzymes.proprioception._DISPATCH",
            {"genome": lambda: "READING"},
        ):
            result = proprioception("genome")
        assert result == "READING\n\n--- Gradient ---\nGRADIENT_INFO"

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_drill_dispatch(self, _mock_grad):
        with patch("metabolon.enzymes.proprioception._drill", return_value="Recorded drill") as m:
            result = proprioception(target="drill", goal="t", category="c", score=2)
        m.assert_called_once_with("t", "c", 2, "flashcard", "", "")
        assert "Recorded drill" in result


# ── _circadian ───────────────────────────────────────────────────────────


class TestCircadian:
    @patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="Event1\nEvent2")
    def test_circadian_has_phase(self, _mock):
        from metabolon.enzymes.proprioception import _circadian

        result = _circadian()
        assert "Phase:" in result
        assert "Event1" in result

    @patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="Evt")
    def test_circadian_dormancy_phase(self, _mock):
        from metabolon.enzymes.proprioception import _circadian

        fake_dt = datetime(2026, 3, 31, 3, 0, tzinfo=HKT)
        with patch("metabolon.enzymes.proprioception.datetime") as mock_dt:
            mock_dt.now.return_value = fake_dt
            result = _circadian()
        assert "dormancy" in result

    @patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="Evt")
    def test_circadian_deep_work_phase(self, _mock):
        from metabolon.enzymes.proprioception import _circadian

        fake_dt = datetime(2026, 3, 31, 10, 0, tzinfo=HKT)
        with patch("metabolon.enzymes.proprioception.datetime") as mock_dt:
            mock_dt.now.return_value = fake_dt
            result = _circadian()
        assert "deep-work" in result


# ── _glycogen ────────────────────────────────────────────────────────────


class TestGlycogen:
    @patch("metabolon.organelles.vasomotor_sensor.sense")
    def test_glycogen_normal(self, mock_sense):
        from metabolon.enzymes.proprioception import _glycogen

        mock_sense.return_value = {"status": "healthy", "weekly_pct": 45.0, "sonnet_pct": 30.0}
        result = _glycogen()
        assert "healthy" in result
        assert "45%" in result
        assert "30%" in result

    @patch("metabolon.organelles.vasomotor_sensor.sense")
    def test_glycogen_error(self, mock_sense):
        from metabolon.enzymes.proprioception import _glycogen

        mock_sense.return_value = {"error": "no data"}
        result = _glycogen()
        assert "unavailable" in result
        assert "no data" in result

    @patch("metabolon.organelles.vasomotor_sensor.sense")
    def test_glycogen_stale(self, mock_sense):
        from metabolon.enzymes.proprioception import _glycogen

        mock_sense.return_value = {
            "status": "low", "weekly_pct": 90.0, "sonnet_pct": 85.0,
            "stale": True, "stale_label": "2h ago",
        }
        result = _glycogen()
        assert "[2h ago]" in result


# ── _consolidation ───────────────────────────────────────────────────────


class TestConsolidation:
    def test_no_memory_files(self):
        with patch("metabolon.metabolism.substrates.memory.ConsolidationSubstrate") as mock_cls:
            mock_cls.return_value.sense.return_value = []
            from metabolon.enzymes.proprioception import _consolidation

            result = _consolidation()
        assert "No memory files found" in result

    def test_with_sensed_data(self):
        with patch("metabolon.metabolism.substrates.memory.ConsolidationSubstrate") as mock_cls:
            mock_cls.return_value.sense.return_value = [{"file": "a.md"}]
            mock_cls.return_value.report.return_value = "Memory report content"
            from metabolon.enzymes.proprioception import _consolidation

            result = _consolidation()
        assert "Memory report content" in result


# ── _operons ─────────────────────────────────────────────────────────────


class TestOperons:
    def test_operons_output(self):
        with (
            patch("metabolon.resources.operons.express_operon_map", return_value="OPMAP"),
            patch("metabolon.resources.receptome.express_operon_index", return_value="OPINDEX"),
        ):
            from metabolon.enzymes.proprioception import _operons

            result = _operons()
        assert "OPMAP" in result
        assert "OPINDEX" in result


# ── _sensorium ───────────────────────────────────────────────────────────


class TestSensorium:
    def test_sensorium_no_log(self):
        from metabolon.enzymes.proprioception import _sensorium

        with patch("pathlib.Path.exists", return_value=False):
            result = _sensorium()
        assert "no search log" in result

    def test_sensorium_reads_entries(self, tmp_path):
        from metabolon.enzymes.proprioception import _sensorium

        entries = [
            json.dumps({"ts": "2026-01-01T10:00", "query": "python testing"}),
            json.dumps({"ts": "2026-01-02T11:00", "query": "fastmcp tools"}),
        ]
        # Build the real path that _sensorium constructs: Path.home() / "germline" / "loci" / "signals" / "rheotaxis.jsonl"
        signals_dir = tmp_path / "germline" / "loci" / "signals"
        signals_dir.mkdir(parents=True)
        (signals_dir / "rheotaxis.jsonl").write_text("\n".join(entries))
        with patch.object(Path, "home", return_value=tmp_path):
            result = _sensorium()
        assert "python testing" in result
        assert "fastmcp tools" in result


# ── _histone_store ───────────────────────────────────────────────────────


class TestHistoneStore:
    def test_histone_store_empty(self, tmp_path):
        from metabolon.enzymes.proprioception import _histone_store

        marks_dir = tmp_path / "epigenome" / "marks"
        marks_dir.mkdir(parents=True)
        with patch.object(Path, "home", return_value=tmp_path):
            result = _histone_store()
        assert "0 mark files" in result

    def test_histone_store_with_files(self, tmp_path):
        from metabolon.enzymes.proprioception import _histone_store

        marks_dir = tmp_path / "epigenome" / "marks"
        marks_dir.mkdir(parents=True)
        (marks_dir / "a.md").write_text("content " * 100)
        (marks_dir / "b.md").write_text("more " * 50)
        with patch.object(Path, "home", return_value=tmp_path):
            result = _histone_store()
        assert "2 marks" in result


# ── _effectors ───────────────────────────────────────────────────────────


class TestEffectors:
    def test_effectors(self):
        with patch("metabolon.resources.proteome.express_effector_index", return_value="effector idx"):
            from metabolon.enzymes.proprioception import _effectors

            result = _effectors()
        assert "effector idx" in result


# ── _oscillators ─────────────────────────────────────────────────────────


class TestOscillators:
    def test_oscillators(self):
        with patch("metabolon.resources.oscillators.express_pacemaker_status", return_value="pacemaker ok"):
            from metabolon.enzymes.proprioception import _oscillators

            result = _oscillators()
        assert "pacemaker ok" in result


# ── _sense ───────────────────────────────────────────────────────────────


class TestSense:
    def test_no_goals_configured(self):
        with patch("metabolon.organelles.receptor_sense.restore_goals", return_value=[]):
            from metabolon.enzymes.proprioception import _sense

            result = _sense()
        assert "No goals configured" in result

    def test_with_goals(self):
        summary = {
            "goal": "Learn Python", "phase": "active",
            "days_to_next_phase": 5, "total_drills": 10,
            "weakest": [], "categories": {},
        }
        with (
            patch("metabolon.organelles.receptor_sense.restore_goals", return_value=[{"name": "Learn Python"}]),
            patch("metabolon.organelles.receptor_sense.ProprioceptiveStore"),
            patch("metabolon.organelles.receptor_sense.synthesize_signal_summary", return_value=summary),
            patch("metabolon.organelles.receptor_sense.SIGNALS_DIR", Path("/tmp")),
        ):
            from metabolon.enzymes.proprioception import _sense

            result = _sense()
        assert "Learn Python" in result
        assert "active" in result
        assert "10" in result

    def test_with_weakest_categories(self):
        summary = {
            "goal": "Math", "phase": "phase1", "days_to_next_phase": None,
            "total_drills": 3, "weakest": ["algebra", "calc"],
            "categories": {
                "algebra": {"drill_count": 0, "avg_score": 0.0},
                "calc": {"drill_count": 5, "avg_score": 1.2},
            },
        }
        with (
            patch("metabolon.organelles.receptor_sense.restore_goals", return_value=[{"name": "Math"}]),
            patch("metabolon.organelles.receptor_sense.ProprioceptiveStore"),
            patch("metabolon.organelles.receptor_sense.synthesize_signal_summary", return_value=summary),
            patch("metabolon.organelles.receptor_sense.SIGNALS_DIR", Path("/tmp")),
        ):
            from metabolon.enzymes.proprioception import _sense

            result = _sense()
        assert "never drilled" in result
        assert "1.2/3" in result


# ── _drill ───────────────────────────────────────────────────────────────


class TestDrill:
    def test_valid_score_records(self):
        mock_store = MagicMock()
        with (
            patch("metabolon.organelles.receptor_sense.ProprioceptiveStore", return_value=mock_store),
            patch("metabolon.organelles.receptor_sense.SIGNALS_DIR", Path("/tmp")),
        ):
            from metabolon.enzymes.proprioception import _drill

            result = _drill("goal1", "math", 2, "flashcard", "derivatives", "ok")
        assert "Recorded" in result
        assert "2/3" in result
        assert "goal1" in result
        mock_store.append.assert_called_once()

    def test_invalid_score_low(self):
        with (
            patch("metabolon.organelles.receptor_sense.ProprioceptiveStore"),
            patch("metabolon.organelles.receptor_sense.SIGNALS_DIR", Path("/tmp")),
        ):
            from metabolon.enzymes.proprioception import _drill

            result = _drill("g", "c", 0)
        assert "Failed" in result
        assert "must be 1-3" in result

    def test_invalid_score_high(self):
        with (
            patch("metabolon.organelles.receptor_sense.ProprioceptiveStore"),
            patch("metabolon.organelles.receptor_sense.SIGNALS_DIR", Path("/tmp")),
        ):
            from metabolon.enzymes.proprioception import _drill

            result = _drill("g", "c", 5)
        assert "Failed" in result


# ── _gradient_detect ─────────────────────────────────────────────────────


class TestGradientDetect:
    def test_gradient_report(self):
        mock_report = MagicMock()
        mock_report.polarity_vector = "expanding"
        mock_report.interpretation = "Strong outward signal"
        g = MagicMock()
        g.domain = "search"
        g.signal_strength = 0.75
        g.sensor_coverage = 3
        g.topology_bonus = True
        g.top_titles = ["Title A"]
        g.top_queries = ["query x"]
        mock_report.gradients = [g]

        with patch("metabolon.organelles.gradient_sense.build_gradient_report", return_value=mock_report):
            from metabolon.enzymes.proprioception import _gradient_detect

            result = _gradient_detect()
        assert "expanding" in result
        assert "search" in result
        assert "Title A" in result
        assert "query x" in result


# ── _restore_fork_registry ───────────────────────────────────────────────


class TestRestoreForkRegistry:
    def test_returns_defaults_when_no_file(self, tmp_path):
        result = _restore_fork_registry(tmp_path / "nonexistent.yaml")
        assert "superpowers" in result
        assert "compound-engineering" in result

    def test_loads_existing_yaml(self, tmp_path):
        registry_path = tmp_path / "skill-forks.yaml"
        registry_path.write_text(yaml.dump({"custom-suite": {"local": "/tmp/x", "cache_pattern": "/tmp/y"}}))
        result = _restore_fork_registry(registry_path)
        assert "custom-suite" in result

    def test_empty_yaml_returns_empty_dict(self, tmp_path):
        registry_path = tmp_path / "skill-forks.yaml"
        registry_path.write_text("")
        result = _restore_fork_registry(registry_path)
        assert result == {}


# ── _find_latest_cache_version ───────────────────────────────────────────


class TestFindLatestCacheVersion:
    def test_no_dir_returns_none(self, tmp_path):
        assert _find_latest_cache_version(tmp_path / "nonexistent") is None

    def test_empty_dir_returns_none(self, tmp_path):
        cache = tmp_path / "cache"
        cache.mkdir()
        assert _find_latest_cache_version(cache) is None

    def test_finds_latest_version(self, tmp_path):
        cache = tmp_path / "cache"
        cache.mkdir()
        for v in ("1.0.0", "2.0.0", "1.5.0"):
            d = cache / v / "skills"
            d.mkdir(parents=True)
            (d / "tool.py").write_text("# skill")
        result = _find_latest_cache_version(cache)
        assert result is not None
        assert result.name == "skills"
        assert result.parent.name == "2.0.0"

    def test_ignores_non_version_dirs(self, tmp_path):
        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / "latest").mkdir()
        d = cache / "1.0.0" / "skills"
        d.mkdir(parents=True)
        (d / "tool.py").write_text("# skill")
        result = _find_latest_cache_version(cache)
        assert result is not None
        assert result.parent.name == "1.0.0"

    def test_ignores_version_dir_without_skills(self, tmp_path):
        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / "3.0.0").mkdir()
        d = cache / "2.0.0" / "skills"
        d.mkdir(parents=True)
        (d / "tool.py").write_text("# skill")
        result = _find_latest_cache_version(cache)
        assert result is not None
        assert result.parent.name == "2.0.0"


# ── _diff_fork ───────────────────────────────────────────────────────────


class TestDiffFork:
    def test_identical_dirs_no_changes(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (local / "a.py").write_text("hello")
        (cache / "a.py").write_text("hello")
        result = _diff_fork(local, cache)
        assert result["total_changes"] == 0

    def test_modified_file_detected(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (local / "a.py").write_text("hello")
        (cache / "a.py").write_text("world")
        result = _diff_fork(local, cache)
        assert result["total_changes"] == 1
        assert "a.py" in result["modified"]

    def test_added_upstream_detected(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (cache / "new_upstream.py").write_text("new file")
        result = _diff_fork(local, cache)
        assert "new_upstream.py" in result["added_upstream"]

    def test_ignores_git_dirs(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (cache / ".git").mkdir()
        (cache / ".git" / "config").write_text("git stuff")
        (local / "a.py").write_text("hello")
        (cache / "a.py").write_text("hello")
        result = _diff_fork(local, cache)
        assert result["total_changes"] == 0


# ── _skills ──────────────────────────────────────────────────────────────


class TestSkills:
    def test_empty_registry_no_changes(self):
        with patch("metabolon.enzymes.proprioception._restore_fork_registry", return_value={}):
            result = _skills()
        assert "No upstream skill changes" in result

    def test_local_dir_missing_skipped(self, tmp_path):
        registry = {
            "suite": {"local": str(tmp_path / "nonexistent"), "cache_pattern": str(tmp_path / "cache")}
        }
        with patch("metabolon.enzymes.proprioception._restore_fork_registry", return_value=registry):
            result = _skills()
        assert "No upstream skill changes" in result

    def test_no_cache_version(self, tmp_path):
        local = tmp_path / "local" / "suite"
        local.mkdir(parents=True)
        (local / "skill.md").write_text("content")
        cache_base = tmp_path / "cache" / "suite"
        cache_base.mkdir(parents=True)
        registry = {"suite": {"local": str(local), "cache_pattern": str(cache_base)}}
        with patch("metabolon.enzymes.proprioception._restore_fork_registry", return_value=registry):
            result = _skills()
        assert "No upstream skill changes" in result


# ── _timing ──────────────────────────────────────────────────────────────


class TestTiming:
    def test_no_entries(self):
        with patch("metabolon.membrane.timing_buffer") as mock_buf:
            mock_buf.snapshot.return_value = []
            result = _timing()
        assert "No tool call timings" in result

    def test_with_entries(self):
        e1 = MagicMock(latency_ms=100, tool="tool_a", outcome="success")
        e2 = MagicMock(latency_ms=500, tool="tool_b", outcome="success")
        e3 = MagicMock(latency_ms=200, tool="tool_a", outcome="error")
        with patch("metabolon.membrane.timing_buffer") as mock_buf:
            mock_buf.snapshot.return_value = [e1, e2, e3]
            result = _timing()
        assert "avg:" in result
        assert "p50:" in result
        assert "p95:" in result
        assert "Slowest tools" in result
        assert "tool_b: 500ms" in result
        assert "2 success, 1 error" in result


# ── dispatch table completeness ──────────────────────────────────────────


class TestDispatchCompleteness:
    def test_all_targets_have_dispatch_entries(self):
        from metabolon.enzymes.proprioception import _DISPATCH

        expected = {
            "genome", "anatomy", "circadian", "vitals", "glycogen",
            "reflexes", "consolidation", "operons", "sensorium",
            "histone_store", "effectors", "oscillators", "sense",
            "gradient", "skills", "timing",
        }
        assert expected == set(_DISPATCH.keys())
