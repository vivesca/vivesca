"""Tests for metabolon/enzymes/proprioception.py"""

from __future__ import annotations

import json
import os
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

HKT = timezone(timedelta(hours=8))

# ---------------------------------------------------------------------------
# Unit tests: _log_and_gradient
# ---------------------------------------------------------------------------


class TestLogAndGradient:
    """Tests for the _log_and_gradient helper."""

    @patch("metabolon.enzymes.proprioception._GRADIENT_LOG", "/tmp/fake_log.jsonl")
    @patch("os.makedirs")
    def test_first_reading_returns_none(self, mock_makedirs):
        """First reading for a target has no history → no gradient."""
        from metabolon.enzymes.proprioception import _log_and_gradient

        # Simulate file with no prior entries for this target
        existing = json.dumps({"ts": "t0", "target": "other", "size": 100}) + "\n"
        with patch("builtins.open", mock_open(read_data=existing)):
            result = _log_and_gradient("genome", "some reading content here")
        assert result is None

    @patch("metabolon.enzymes.proprioception._GRADIENT_LOG", "/tmp/fake_log.jsonl")
    @patch("os.makedirs")
    def test_significant_growth_detected(self, mock_makedirs):
        """Size delta > 50 triggers a 'growing' gradient."""
        from metabolon.enzymes.proprioception import _log_and_gradient

        # 3 prior small readings + we'll add a much larger one
        history = ""
        for i in range(3):
            history += json.dumps({"ts": f"t{i}", "target": "genome", "size": 100}) + "\n"
        with patch("builtins.open", mock_open(read_data=history)):
            result = _log_and_gradient("genome", "x" * 200)
        assert result is not None
        assert "growing" in result
        assert "genome" in result

    @patch("metabolon.enzymes.proprioception._GRADIENT_LOG", "/tmp/fake_log.jsonl")
    @patch("os.makedirs")
    def test_significant_shrink_detected(self, mock_makedirs):
        """Size delta < -50 triggers a 'shrinking' gradient."""
        from metabolon.enzymes.proprioception import _log_and_gradient

        history = ""
        for i in range(3):
            history += json.dumps({"ts": f"t{i}", "target": "anatomy", "size": 200}) + "\n"
        with patch("builtins.open", mock_open(read_data=history)):
            result = _log_and_gradient("anatomy", "x" * 100)
        assert result is not None
        assert "shrinking" in result

    @patch("metabolon.enzymes.proprioception._GRADIENT_LOG", "/tmp/fake_log.jsonl")
    @patch("os.makedirs")
    def test_below_threshold_returns_none(self, mock_makedirs):
        """Size delta < 50 is noise → no gradient."""
        from metabolon.enzymes.proprioception import _log_and_gradient

        history = json.dumps({"ts": "t0", "target": "vitals", "size": 100}) + "\n"
        with patch("builtins.open", mock_open(read_data=history)):
            result = _log_and_gradient("vitals", "x" * 120)
        assert result is None

    @patch("metabolon.enzymes.proprioception._GRADIENT_LOG", "/tmp/fake_log.jsonl")
    @patch("os.makedirs")
    def test_missing_log_file_returns_none(self, mock_makedirs):
        """If log file doesn't exist, return None gracefully."""
        from metabolon.enzymes.proprioception import _log_and_gradient

        with patch("builtins.open", side_effect=FileNotFoundError):
            result = _log_and_gradient("genome", "some content")
        assert result is None


# ---------------------------------------------------------------------------
# Dispatch target tests (mocked external dependencies)
# ---------------------------------------------------------------------------


class TestGenome:
    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_genome_found(self, mock_grad):
        from metabolon.enzymes.proprioception import proprioception

        with patch("metabolon.enzymes.proprioception._genome", return_value="constitution text"):
            result = proprioception(target="genome")
        assert "constitution text" in result

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_genome_missing(self, mock_grad):
        from metabolon.enzymes.proprioception import proprioception

        with patch("metabolon.enzymes.proprioception._genome", return_value="No constitution found."):
            result = proprioception(target="genome")
        assert "No constitution found" in result


class TestAnatomy:
    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_anatomy(self, mock_grad):
        from metabolon.enzymes.proprioception import proprioception

        with patch("metabolon.enzymes.proprioception._anatomy", return_value="anatomy report"):
            result = proprioception(target="anatomy")
        assert "anatomy report" in result


class TestCircadian:
    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_circadian_phase_dormancy(self, mock_grad):
        from metabolon.enzymes.proprioception import proprioception

        fake_dt = datetime(2026, 3, 31, 5, 0, tzinfo=HKT)  # 5 AM → dormancy
        with (
            patch("metabolon.enzymes.proprioception._circadian") as mock_circ,
            patch("metabolon.enzymes.proprioception.proprioception", side_effect=AssertionError) if False else MagicMock(),
        ):
            # Test the _circadian function directly
            pass
        # Test circadian by mocking its internal imports
        with patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="event list"):
            from metabolon.enzymes.proprioception import _circadian

            fake_dt = datetime(2026, 3, 31, 5, 0, tzinfo=HKT)
            with patch("metabolon.enzymes.proprioception.datetime") as mock_dt:
                mock_dt.now.return_value = fake_dt
                result = _circadian()
            assert "dormancy" in result

    def test_circadian_phase_deep_work(self):
        with patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="events"):
            from metabolon.enzymes.proprioception import _circadian

            fake_dt = datetime(2026, 3, 31, 10, 0, tzinfo=HKT)  # 10 AM → deep-work
            with patch("metabolon.enzymes.proprioception.datetime") as mock_dt:
                mock_dt.now.return_value = fake_dt
                result = _circadian()
            assert "deep-work" in result


class TestVitals:
    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_vitals(self, mock_grad):
        from metabolon.enzymes.proprioception import proprioception

        with patch("metabolon.enzymes.proprioception._vitals", return_value="vitals report"):
            result = proprioception(target="vitals")
        assert "vitals report" in result


class TestGlycogen:
    def test_glycogen_normal(self):
        from metabolon.enzymes.proprioception import _glycogen

        mock_sense = {"status": "healthy", "weekly_pct": 45.0, "sonnet_pct": 30.0}
        with patch("metabolon.organelles.vasomotor_sensor.sense", return_value=mock_sense):
            result = _glycogen()
        assert "healthy" in result
        assert "45%" in result
        assert "30%" in result

    def test_glycogen_error(self):
        from metabolon.enzymes.proprioception import _glycogen

        with patch("metabolon.organelles.vasomotor_sensor.sense", return_value={"error": "api down"}):
            result = _glycogen()
        assert "unavailable" in result
        assert "api down" in result

    def test_glycogen_with_stale(self):
        from metabolon.enzymes.proprioception import _glycogen

        mock_sense = {
            "status": "moderate",
            "weekly_pct": 75.0,
            "sonnet_pct": 60.0,
            "stale": True,
            "stale_label": "2h ago",
        }
        with patch("metabolon.organelles.vasomotor_sensor.sense", return_value=mock_sense):
            result = _glycogen()
        assert "2h ago" in result


class TestReflexes:
    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_reflexes(self, mock_grad):
        from metabolon.enzymes.proprioception import proprioception

        with patch("metabolon.enzymes.proprioception._reflexes", return_value="reflex inventory"):
            result = proprioception(target="reflexes")
        assert "reflex inventory" in result


class TestConsolidation:
    def test_consolidation_empty(self):
        from metabolon.enzymes.proprioception import _consolidation

        with patch(
            "metabolon.metabolism.substrates.memory.ConsolidationSubstrate.sense",
            return_value=[],
        ):
            result = _consolidation()
        assert "No memory files found" in result

    def test_consolidation_with_data(self):
        from metabolon.enzymes.proprioception import _consolidation

        mock_sensed = [{"file": "a.md", "age_days": 45}]
        with (
            patch(
                "metabolon.metabolism.substrates.memory.ConsolidationSubstrate.sense",
                return_value=mock_sensed,
            ),
            patch(
                "metabolon.metabolism.substrates.memory.ConsolidationSubstrate.report",
                return_value="consolidation report text",
            ),
        ):
            result = _consolidation()
        assert "consolidation report text" in result


class TestOperons:
    def test_operons(self):
        from metabolon.enzymes.proprioception import _operons

        with (
            patch("metabolon.resources.operons.express_operon_map", return_value="operon map"),
            patch("metabolon.resources.receptome.express_operon_index", return_value="operon index"),
        ):
            result = _operons()
        assert "operon map" in result
        assert "operon index" in result


class TestSensorium:
    def test_sensorium_no_log(self):
        from metabolon.enzymes.proprioception import _sensorium

        with patch("pathlib.Path.exists", return_value=False):
            result = _sensorium()
        assert "no search log" in result

    def test_sensorium_with_entries(self):
        from metabolon.enzymes.proprioception import _sensorium

        entries = [
            json.dumps({"ts": "2026-01-01", "query": "test query"}),
            json.dumps({"ts": "2026-01-02", "query": "another query"}),
        ]
        content = "\n".join(entries)
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = content
        with patch("metabolon.enzymes.proprioception.Path") as mock_path_cls:
            mock_path_cls.home.return_value = Path.home()
            # Path() / ... should return our mock
            mock_path_cls.return_value.__truediv__.return_value.__truediv__.return_value = mock_path
            result = _sensorium()
        # This approach is tricky with Path chaining; test via a tmp file instead
        # Let's use a real temp file approach

    def test_sensorium_reads_log(self, tmp_path):
        from metabolon.enzymes.proprioception import _sensorium

        log_data = [
            json.dumps({"ts": "2026-01-01T10:00", "query": "python testing"}),
            json.dumps({"ts": "2026-01-02T11:00", "query": "fastmcp tools"}),
        ]
        log_file = tmp_path / "rheotaxis.jsonl"
        log_file.write_text("\n".join(log_data))

        with patch("metabolon.enzymes.proprioception.Path") as mock_path_cls:
            mock_path_cls.home.return_value = tmp_path
            # Path.home() / "germline" / "loci" / "signals" / "rheotaxis.jsonl"
            mock_path_cls.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = log_file
            result = _sensorium()
        assert "python testing" in result
        assert "fastmcp tools" in result


class TestHistoneStore:
    def test_histone_store_empty(self, tmp_path):
        from metabolon.enzymes.proprioception import _histone_store

        marks_dir = tmp_path / "marks"
        marks_dir.mkdir()
        with patch("metabolon.enzymes.proprioception.Path") as mock_path_cls:
            mock_path_cls.home.return_value = tmp_path.parent
            mock_path_cls.return_value.__truediv__.return_value.__truediv__.return_value = marks_dir
            result = _histone_store()
        assert "0 mark files" in result

    def test_histone_store_with_files(self, tmp_path):
        from metabolon.enzymes.proprioception import _histone_store

        marks_dir = tmp_path / "marks"
        marks_dir.mkdir()
        (marks_dir / "a.md").write_text("# Mark A\ncontent here")
        (marks_dir / "b.md").write_text("# Mark B\nmore content here")

        with patch("metabolon.enzymes.proprioception.Path") as mock_path_cls:
            mock_path_cls.home.return_value = tmp_path.parent
            mock_path_cls.return_value.__truediv__.return_value.__truediv__.return_value = marks_dir
            result = _histone_store()
        assert "2 marks" in result


class TestEffectors:
    def test_effectors(self):
        from metabolon.enzymes.proprioception import _effectors

        with patch(
            "metabolon.resources.proteome.express_effector_index",
            return_value="effector index",
        ):
            result = _effectors()
        assert "effector index" in result


class TestOscillators:
    def test_oscillators(self):
        from metabolon.enzymes.proprioception import _oscillators

        with patch(
            "metabolon.resources.oscillators.express_pacemaker_status",
            return_value="pacemaker status",
        ):
            result = _oscillators()
        assert "pacemaker status" in result


class TestSense:
    def test_sense_no_goals(self):
        from metabolon.enzymes.proprioception import _sense

        with patch("metabolon.organelles.receptor_sense.restore_goals", return_value=[]):
            result = _sense()
        assert "No goals configured" in result

    def test_sense_with_goals(self):
        from metabolon.enzymes.proprioception import _sense

        goals = [{"name": "Test Goal", "categories": ["python"]}]
        summary = {
            "goal": "Test Goal",
            "phase": "drill",
            "days_to_next_phase": 5,
            "total_drills": 10,
            "weakest": ["python"],
            "categories": {"python": {"drill_count": 3, "avg_score": 2.1}},
        }
        mock_store = MagicMock()
        with (
            patch("metabolon.organelles.receptor_sense.restore_goals", return_value=goals),
            patch("metabolon.organelles.receptor_sense.ProprioceptiveStore", return_value=mock_store),
            patch("metabolon.organelles.receptor_sense.synthesize_signal_summary", return_value=summary),
            patch("metabolon.organelles.receptor_sense.SIGNALS_DIR", Path("/tmp/signals")),
        ):
            result = _sense()
        assert "Test Goal" in result
        assert "drill" in result
        assert "10" in result
        assert "python" in result


class TestDrill:
    def test_drill_invalid_score(self):
        from metabolon.enzymes.proprioception import _drill

        result = _drill(goal="test", category="python", score=5)
        assert "Failed" in result
        assert "score must be 1-3" in result

    def test_drill_valid_score(self):
        from metabolon.enzymes.proprioception import _drill

        mock_store = MagicMock()
        with (
            patch("metabolon.organelles.receptor_sense.ProprioceptiveStore", return_value=mock_store),
            patch("metabolon.organelles.receptor_sense.SIGNALS_DIR", Path("/tmp/signals")),
        ):
            result = _drill(
                goal="mygoal",
                category="python",
                score=2,
                drill_type="flashcard",
                material="decorators",
                notes="need practice",
            )
        assert "Recorded" in result
        assert "python" in result
        assert "2/3" in result
        assert "mygoal" in result
        mock_store.append.assert_called_once()


class TestGradientDetect:
    def test_gradient_detect(self):
        from metabolon.enzymes.proprioception import _gradient_detect

        mock_vector = MagicMock()
        mock_vector.__str__ = lambda self: "testing"
        mock_report = MagicMock()
        mock_report.polarity_vector = "machine-learning"
        mock_report.interpretation = "Drift toward ML topics"
        mock_g = MagicMock()
        mock_g.domain = "ml"
        mock_g.signal_strength = 0.75
        mock_g.sensor_coverage = 2
        mock_g.topology_bonus = "adjacent"
        mock_g.top_titles = ["Neural Networks 101"]
        mock_g.top_queries = ["pytorch tutorial"]
        mock_report.gradients = [mock_g]

        with patch(
            "metabolon.organelles.gradient_sense.build_gradient_report",
            return_value=mock_report,
        ):
            result = _gradient_detect()
        assert "machine-learning" in result
        assert "ml" in result
        assert "0.75" in result
        assert "Neural Networks 101" in result
        assert "pytorch tutorial" in result


class TestSkills:
    def test_skills_no_changes(self, tmp_path):
        from metabolon.enzymes.proprioception import _skills

        # Create identical local and cache dirs
        local_dir = tmp_path / "local" / "suite"
        local_dir.mkdir(parents=True)
        (local_dir / "skill.md").write_text("content")

        cache_base = tmp_path / "cache" / "suite"
        cache_base.mkdir(parents=True)
        ver_dir = cache_base / "1.0.0" / "skills"
        ver_dir.mkdir(parents=True)
        (ver_dir / "skill.md").write_text("content")

        registry = {
            "suite": {
                "local": str(local_dir),
                "cache_pattern": str(cache_base),
            }
        }
        with patch(
            "metabolon.enzymes.proprioception._restore_fork_registry",
            return_value=registry,
        ):
            result = _skills()
        assert "No upstream skill changes" in result

    def test_skills_with_modifications(self, tmp_path):
        from metabolon.enzymes.proprioception import _skills

        local_dir = tmp_path / "local" / "suite"
        local_dir.mkdir(parents=True)
        (local_dir / "skill.md").write_text("old content")

        cache_base = tmp_path / "cache" / "suite"
        cache_base.mkdir(parents=True)
        ver_dir = cache_base / "1.0.0" / "skills"
        ver_dir.mkdir(parents=True)
        (ver_dir / "skill.md").write_text("new content")
        (ver_dir / "added.md").write_text("brand new file")

        registry = {
            "suite": {
                "local": str(local_dir),
                "cache_pattern": str(cache_base),
            }
        }
        with patch(
            "metabolon.enzymes.proprioception._restore_fork_registry",
            return_value=registry,
        ):
            result = _skills()
        assert "suite" in result
        assert "modified" in result
        assert "new upstream" in result

    def test_skills_missing_local_dir(self, tmp_path):
        from metabolon.enzymes.proprioception import _skills

        registry = {
            "suite": {
                "local": str(tmp_path / "nonexistent"),
                "cache_pattern": str(tmp_path / "cache"),
            }
        }
        with patch(
            "metabolon.enzymes.proprioception._restore_fork_registry",
            return_value=registry,
        ):
            result = _skills()
        assert "No upstream skill changes" in result


class TestTiming:
    def test_timing_empty(self):
        from metabolon.enzymes.proprioception import _timing

        with patch("metabolon.membrane.timing_buffer") as mock_tb:
            mock_tb.snapshot.return_value = []
            result = _timing()
        assert "No tool call timings" in result

    def test_timing_with_data(self):
        from metabolon.enzymes.proprioception import _timing

        entries = []
        for i in range(5):
            e = MagicMock()
            e.tool = "proprioception" if i < 3 else "other_tool"
            e.latency_ms = 100 + i * 50
            e.outcome = "success" if i < 4 else "error"
            entries.append(e)

        with patch("metabolon.membrane.timing_buffer") as mock_tb:
            mock_tb.snapshot.return_value = entries
            result = _timing()
        assert "Tool Timing Stats" in result
        assert "avg" in result
        assert "p50" in result
        assert "p95" in result
        assert "4 success" in result
        assert "1 error" in result


class TestTimingHelpers:
    """Test _find_latest_cache_version and _diff_fork directly."""

    def test_find_latest_no_dir(self, tmp_path):
        from metabolon.enzymes.proprioception import _find_latest_cache_version

        assert _find_latest_cache_version(tmp_path / "nonexistent") is None

    def test_find_latest_with_versions(self, tmp_path):
        from metabolon.enzymes.proprioception import _find_latest_cache_version

        base = tmp_path / "cache"
        base.mkdir()
        for ver in ["1.0.0", "2.0.0", "1.5.0"]:
            d = base / ver / "skills"
            d.mkdir(parents=True)
            (d / "f.txt").write_text("x")
        result = _find_latest_cache_version(base)
        assert result is not None
        assert "2.0.0" in str(result)

    def test_find_latest_no_skills_subdir(self, tmp_path):
        from metabolon.enzymes.proprioception import _find_latest_cache_version

        base = tmp_path / "cache"
        base.mkdir()
        (base / "1.0.0").mkdir()
        assert _find_latest_cache_version(base) is None

    def test_diff_fork_identical(self, tmp_path):
        from metabolon.enzymes.proprioception import _diff_fork

        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (local / "a.md").write_text("same")
        (cache / "a.md").write_text("same")
        result = _diff_fork(local, cache)
        assert result["total_changes"] == 0

    def test_diff_fork_modified_and_added(self, tmp_path):
        from metabolon.enzymes.proprioception import _diff_fork

        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (local / "a.md").write_text("old")
        (cache / "a.md").write_text("new")
        (cache / "b.md").write_text("added upstream")
        result = _diff_fork(local, cache)
        assert "a.md" in result["modified"]
        assert "b.md" in result["added_upstream"]
        assert result["total_changes"] == 2


class TestRestoreForkRegistry:
    def test_returns_default_when_no_file(self, tmp_path):
        from metabolon.enzymes.proprioception import _restore_fork_registry, _SKILLS_DEFAULT_REGISTRY

        result = _restore_fork_registry(tmp_path / "nonexistent.yaml")
        assert result == _SKILLS_DEFAULT_REGISTRY

    def test_loads_existing(self, tmp_path):
        from metabolon.enzymes.proprioception import _restore_fork_registry

        yaml_file = tmp_path / "registry.yaml"
        yaml_file.write_text("suite:\n  local: /tmp/x\n  cache_pattern: /tmp/y\n")
        result = _restore_fork_registry(yaml_file)
        assert "suite" in result


class TestProprioceptionIntegration:
    """Test the top-level proprioception() function dispatch + gradient."""

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_dispatch_calls_correct_handler(self, mock_grad):
        from metabolon.enzymes.proprioception import proprioception

        with patch("metabolon.enzymes.proprioception._genome", return_value="genome data") as m:
            result = proprioception(target="genome")
        m.assert_called_once()
        assert "genome data" in result

    @patch("metabolon.enzymes.proprioception._log_and_gradient")
    def test_gradient_appended(self, mock_grad):
        mock_grad.return_value = "genome: growing (+100 chars)"
        from metabolon.enzymes.proprioception import proprioception

        with patch("metabolon.enzymes.proprioception._genome", return_value="genome data"):
            result = proprioception(target="genome")
        assert "genome data" in result
        assert "--- Gradient ---" in result
        assert "growing" in result

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_drill_dispatch(self, mock_grad):
        from metabolon.enzymes.proprioception import proprioception

        with patch("metabolon.enzymes.proprioception._drill", return_value="Recorded drill") as m:
            result = proprioception(
                target="drill",
                goal="test",
                category="python",
                score=2,
            )
        m.assert_called_once_with("test", "python", 2, "flashcard", "", "")
        assert "Recorded drill" in result
