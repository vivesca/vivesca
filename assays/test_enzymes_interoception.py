from __future__ import annotations

"""Deeper tests for metabolon/enzymes/interoception.py — edge cases and branches
not covered by test_interoception.py or test_interoception_actions.py."""

import datetime
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fn():
    """Return the raw interoception function (behind @tool decorator)."""
    from metabolon.enzymes import interoception as mod
    return mod.interoception


def _module():
    from metabolon.enzymes import interoception as mod
    return mod


# ---------------------------------------------------------------------------
# _format_duration edge cases
# ---------------------------------------------------------------------------

class TestFormatDurationEdges:
    """Additional _format_duration edge cases."""

    def test_float_seconds_input(self):
        from metabolon.enzymes.interoception import _format_duration
        # 90 * 60 = 5400 seconds = 1h30m
        assert _format_duration(5400.7) == "1h30m"

    def test_large_hours(self):
        from metabolon.enzymes.interoception import _format_duration
        # 48h
        assert _format_duration(48 * 3600) == "48h00m"

    def test_one_hour_exactly(self):
        from metabolon.enzymes.interoception import _format_duration
        assert _format_duration(3600) == "1h00m"


# ---------------------------------------------------------------------------
# _cross_link_experiment_symptom
# ---------------------------------------------------------------------------

class TestCrossLinkExperimentSymptom:
    """Tests for _cross_link_experiment_symptom helper."""

    def test_no_experiments_dir_returns_none(self):
        from metabolon.enzymes.interoception import _cross_link_experiment_symptom
        with patch("metabolon.locus.experiments") as mock_exp:
            mock_exp.exists.return_value = False
            result = _cross_link_experiment_symptom("headache", "mild", "test")
        assert result is None

    def test_matching_keyword_appends_to_experiment(self):
        from metabolon.enzymes.interoception import _cross_link_experiment_symptom
        mock_file = MagicMock()
        mock_file.name = "assay-caffeine.md"
        mock_file.read_text.return_value = (
            "---\nstatus: active\nwatch_keywords: [caffeine, coffee]\n---\nSome content\n"
        )
        mock_tmp = MagicMock()
        with patch("metabolon.locus.experiments") as mock_exp:
            mock_exp.exists.return_value = True
            mock_exp.glob.return_value = [mock_file]
            mock_file.with_suffix.return_value = mock_tmp
            result = _cross_link_experiment_symptom("headache", "severe", "had coffee")
        assert result is not None
        assert "assay-caffeine.md" in result
        mock_tmp.write_text.assert_called_once()
        mock_tmp.replace.assert_called_once_with(mock_file)

    def test_inactive_experiment_skipped(self):
        from metabolon.enzymes.interoception import _cross_link_experiment_symptom
        mock_file = MagicMock()
        mock_file.name = "assay-sleep.md"
        mock_file.read_text.return_value = (
            "---\nstatus: completed\nwatch_keywords: [insomnia]\n---\nDone\n"
        )
        with patch("metabolon.locus.experiments") as mock_exp:
            mock_exp.exists.return_value = True
            mock_exp.glob.return_value = [mock_file]
            result = _cross_link_experiment_symptom("insomnia", "mild", "test")
        assert result is None

    def test_no_matching_keyword_returns_none(self):
        from metabolon.enzymes.interoception import _cross_link_experiment_symptom
        mock_file = MagicMock()
        mock_file.name = "assay-caffeine.md"
        mock_file.read_text.return_value = (
            "---\nstatus: active\nwatch_keywords: [caffeine]\n---\nSome content\n"
        )
        with patch("metabolon.locus.experiments") as mock_exp:
            mock_exp.exists.return_value = True
            mock_exp.glob.return_value = [mock_file]
            result = _cross_link_experiment_symptom("headache", "mild", "no match here")
        assert result is None

    def test_no_watch_keywords_field_skipped(self):
        from metabolon.enzymes.interoception import _cross_link_experiment_symptom
        mock_file = MagicMock()
        mock_file.name = "assay-sleep.md"
        mock_file.read_text.return_value = "---\nstatus: active\n---\nNo keywords\n"
        with patch("metabolon.locus.experiments") as mock_exp:
            mock_exp.exists.return_value = True
            mock_exp.glob.return_value = [mock_file]
            result = _cross_link_experiment_symptom("insomnia", "mild", "test")
        assert result is None


# ---------------------------------------------------------------------------
# _clean_build_artifacts edge cases
# ---------------------------------------------------------------------------

class TestCleanBuildArtifactsEdges:
    """Additional tests for _clean_build_artifacts."""

    def test_code_dir_not_exists(self):
        from metabolon.enzymes.interoception import _clean_build_artifacts
        with (
            patch("metabolon.enzymes.interoception.CODE_DIR", "/tmp/nonexistent_dir_xyz"),
            patch("os.path.isdir", return_value=False),
            patch("shutil.disk_usage") as mock_disk,
        ):
            mock_usage = MagicMock()
            mock_usage.free = 100 * (1024**3)
            mock_disk.side_effect = [mock_usage, mock_usage]
            freed, logs = _clean_build_artifacts()
        assert freed == 0.0
        assert logs == []

    def test_stale_node_modules_cleaned(self):
        from metabolon.enzymes.interoception import _clean_build_artifacts
        import time

        mock_entry = MagicMock()
        mock_entry.is_dir.return_value = True
        mock_entry.name = "myproject"
        mock_entry.path = "/tmp/fakecode/myproject"

        with (
            patch("metabolon.enzymes.interoception.CODE_DIR", "/tmp/fakecode"),
            patch("os.path.isdir") as mock_isdir,
            patch("os.scandir", return_value=[mock_entry]),
            patch("shutil.rmtree") as mock_rmtree,
            patch("os.path.getmtime", return_value=time.time() - 10 * 86400),  # stale
            patch("shutil.disk_usage") as mock_disk,
            patch("subprocess.run", side_effect=FileNotFoundError),
        ):
            def isdir_side_effect(path):
                if path == "/tmp/fakecode":
                    return True
                if path == "/tmp/fakecode/myproject/node_modules":
                    return True
                return False
            mock_isdir.side_effect = isdir_side_effect
            mock_usage = MagicMock()
            mock_usage.free = 100 * (1024**3)
            mock_disk.side_effect = [mock_usage, mock_usage]
            freed, logs = _clean_build_artifacts()
        assert any("myproject" in line and "stale" in line for line in logs)

    def test_fresh_node_modules_not_cleaned(self):
        from metabolon.enzymes.interoception import _clean_build_artifacts
        import time

        mock_entry = MagicMock()
        mock_entry.is_dir.return_value = True
        mock_entry.name = "freshproject"
        mock_entry.path = "/tmp/fakecode/freshproject"

        with (
            patch("metabolon.enzymes.interoception.CODE_DIR", "/tmp/fakecode"),
            patch("os.path.isdir") as mock_isdir,
            patch("os.scandir", return_value=[mock_entry]),
            patch("shutil.rmtree") as mock_rmtree,
            patch("os.path.getmtime", return_value=time.time() - 1 * 86400),  # fresh
            patch("shutil.disk_usage") as mock_disk,
            patch("subprocess.run", side_effect=FileNotFoundError),
        ):
            def isdir_side_effect(path):
                if path == "/tmp/fakecode":
                    return True
                if path == "/tmp/fakecode/freshproject/node_modules":
                    return True
                return False
            mock_isdir.side_effect = isdir_side_effect
            mock_usage = MagicMock()
            mock_usage.free = 100 * (1024**3)
            mock_disk.side_effect = [mock_usage, mock_usage]
            freed, logs = _clean_build_artifacts()
        assert not any("freshproject" in line for line in logs)


# ---------------------------------------------------------------------------
# Sleep action — low-score alerts
# ---------------------------------------------------------------------------

class TestSleepAlerts:
    """Test sleep action generates alerts for low scores."""

    def _base_data(self, **overrides):
        data = {
            "sleep_score": 85,
            "readiness_score": 75,
            "average_hrv": 45,
        }
        data.update(overrides)
        return data

    def test_low_sleep_score_triggers_alert(self):
        mock_sense = MagicMock(return_value=self._base_data(sleep_score=55))
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "SLEEP LOW (55)" in result.summary
        assert "below 70 threshold" in result.summary

    def test_low_readiness_triggers_alert(self):
        mock_sense = MagicMock(return_value=self._base_data(readiness_score=60))
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "READINESS LOW (60)" in result.summary

    def test_low_hrv_triggers_alert(self):
        mock_sense = MagicMock(return_value=self._base_data(average_hrv=15))
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "HRV LOW (15)" in result.summary

    def test_all_good_no_alerts_section(self):
        mock_sense = MagicMock(return_value=self._base_data())
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "--- Alerts ---" not in result.summary


# ---------------------------------------------------------------------------
# Sleep action — optional sections
# ---------------------------------------------------------------------------

class TestSleepOptionalSections:
    """Test sleep action renders optional sections when data is present."""

    def _full_data(self):
        return {
            "sleep_score": 80,
            "readiness_score": 75,
            "average_hrv": 40,
            "sleep_phase_5_min": "1122334",
            "movement_30_sec": "1122334",
            "activity": {
                "score": 90,
                "steps": 8000,
                "active_calories": 400,
                "total_calories": 2200,
                "high_activity_time": 1800,
                "medium_activity_time": 2400,
                "low_activity_time": 3600,
                "sedentary_time": 36000,
                "equivalent_walking_distance": 6000,
            },
            "stress": {
                "day_summary": "normal",
                "stress_high": 1200,
                "recovery_high": 3600,
            },
            "spo2": {
                "average": 97,
                "breathing_disturbance_index": 2.1,
            },
            "resilience": {
                "level": "good",
                "contributors": {"sleep": 0.8},
            },
            "sleep_time": {
                "recommendation": "22:30",
                "status": "on_time",
                "optimal_bedtime": {"start": "22:15", "end": "22:45"},
            },
            "vascular_age": 30,
            "vo2_max": 42.5,
            "workouts": [
                {
                    "activity": "running",
                    "intensity": "moderate",
                    "start": "2024-01-15T07:00:00",
                    "calories": 350.0,
                    "source": "oura",
                }
            ],
        }

    def test_hypnogram_rendered(self):
        mock_sense = MagicMock(return_value=self._full_data())
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "--- Hypnogram" in result.summary
        assert "█=deep" in result.summary

    def test_movement_rendered(self):
        mock_sense = MagicMock(return_value=self._full_data())
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "--- Movement" in result.summary
        assert "·=still" in result.summary

    def test_activity_rendered(self):
        mock_sense = MagicMock(return_value=self._full_data())
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "--- Activity" in result.summary
        assert "8000" in result.summary

    def test_stress_rendered(self):
        mock_sense = MagicMock(return_value=self._full_data())
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "--- Stress ---" in result.summary
        assert "normal" in result.summary

    def test_spo2_rendered(self):
        mock_sense = MagicMock(return_value=self._full_data())
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "--- SpO2 ---" in result.summary
        assert "97%" in result.summary

    def test_resilience_rendered(self):
        mock_sense = MagicMock(return_value=self._full_data())
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "--- Resilience ---" in result.summary
        assert "good" in result.summary

    def test_bedtime_recommendation_rendered(self):
        mock_sense = MagicMock(return_value=self._full_data())
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "--- Bedtime recommendation ---" in result.summary
        assert "22:30" in result.summary

    def test_cardiovascular_rendered(self):
        mock_sense = MagicMock(return_value=self._full_data())
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "--- Cardiovascular ---" in result.summary
        assert "Vascular age: 30" in result.summary
        assert "VO2 max: 42.5" in result.summary

    def test_workouts_rendered(self):
        mock_sense = MagicMock(return_value=self._full_data())
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "--- Workouts ---" in result.summary
        assert "running" in result.summary
        assert "350 kcal" in result.summary

    def test_optional_sections_absent_when_no_data(self):
        mock_sense = MagicMock(return_value={
            "sleep_score": 80,
            "readiness_score": 75,
            "average_hrv": 40,
        })
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")
        assert "--- Hypnogram" not in result.summary
        assert "--- Movement" not in result.summary
        assert "--- Activity" not in result.summary
        assert "--- Stress ---" not in result.summary
        assert "--- SpO2 ---" not in result.summary
        assert "--- Resilience ---" not in result.summary
        assert "--- Cardiovascular ---" not in result.summary
        assert "--- Workouts ---" not in result.summary


# ---------------------------------------------------------------------------
# Sleep action — experiment parsing
# ---------------------------------------------------------------------------

class TestSleepExperiments:
    """Test sleep action includes active experiment summaries."""

    def test_active_experiment_included(self):
        experiment_content = (
            "---\n"
            "name: Caffeine Fast\n"
            "status: active\n"
            "start_date: 2024-01-01\n"
            "end_date: 2024-01-14\n"
            "hypothesis: No caffeine improves sleep\n"
            "---\n"
            "Baseline: Readiness: avg 72.3\n"
        )
        mock_sense = MagicMock(return_value={
            "sleep_score": 80,
            "readiness_score": 75,
            "average_hrv": 40,
        })
        mock_file = MagicMock()
        mock_file.stem = "assay-caffeine"
        mock_file.read_text.return_value = experiment_content

        with (
            patch("metabolon.organelles.chemoreceptor.sense", mock_sense),
            patch("metabolon.locus") as mock_locus,
        ):
            mock_locus.experiments.glob.return_value = [mock_file]
            result = _fn()(action="sleep")

        assert "--- Active Experiments ---" in result.summary
        assert "Caffeine Fast" in result.summary

    def test_no_experiments_no_section(self):
        mock_sense = MagicMock(return_value={
            "sleep_score": 80,
            "readiness_score": 75,
            "average_hrv": 40,
        })
        with (
            patch("metabolon.organelles.chemoreceptor.sense", mock_sense),
            patch("metabolon.locus") as mock_locus,
        ):
            mock_locus.experiments.glob.return_value = []
            result = _fn()(action="sleep")
        assert "--- Active Experiments ---" not in result.summary


# ---------------------------------------------------------------------------
# System action — gate logic
# ---------------------------------------------------------------------------

class TestSystemGateLogic:
    """Test system action gate decisions (PASS/WARN/BLOCK)."""

    def _make_proc(self, stdout=""):
        proc = MagicMock()
        proc.stdout = stdout
        return proc

    def _mock_disk(self, free_gb=100, total_gb=500):
        usage = MagicMock()
        usage.free = free_gb * (1024**3)
        usage.total = total_gb * (1024**3)
        return usage

    def test_gate_pass_when_all_ok(self):
        # Pulse stdout must contain "vivesca" to avoid "NOT FOUND" → BLOCK
        proc = self._make_proc("12345  0  com.vivesca.daemon\n")
        with (
            patch("metabolon.enzymes.interoception.subprocess.run", return_value=proc),
            patch("metabolon.enzymes.interoception.shutil.disk_usage", return_value=self._mock_disk()),
            patch("builtins.open", side_effect=FileNotFoundError),
            patch("metabolon.metabolism.infection.infection_summary", return_value=""),
            patch("metabolon.metabolism.mismatch_repair.summary", return_value=""),
        ):
            result = _fn()(action="system")
        assert result.sections[0].startswith("Gate: PASS")

    def test_gate_block_when_pulse_not_found(self):
        proc = self._make_proc("some output vivesca_service NOT FOUND\n")
        with (
            patch("metabolon.enzymes.interoception.subprocess.run", return_value=proc),
            patch("metabolon.enzymes.interoception.shutil.disk_usage", return_value=self._mock_disk()),
            patch("builtins.open", side_effect=FileNotFoundError),
            patch("metabolon.enzymes.interoception.contextlib.suppress"),
        ):
            result = _fn()(action="system")
        assert "Gate: BLOCK" in result.sections[0]
        assert "pulse not running" in result.sections[0]

    def test_gate_block_when_disk_low(self):
        with (
            patch("metabolon.enzymes.interoception.subprocess.run", return_value=self._make_proc()),
            patch("metabolon.enzymes.interoception.shutil.disk_usage", return_value=self._mock_disk(free_gb=8)),
            patch("builtins.open", side_effect=FileNotFoundError),
            patch("metabolon.enzymes.interoception.contextlib.suppress"),
        ):
            result = _fn()(action="system")
        assert "Gate: BLOCK" in result.sections[0]
        assert "disk pressure" in result.sections[0]

    def test_gate_warn_when_degraded(self):
        health_data = {"failures": ["tool_x"], "checked": "2024-01-01"}

        def open_side_effect(path, *args, **kwargs):
            if "health.json" in str(path):
                return mock_open(read_data=json.dumps(health_data))()
            raise FileNotFoundError

        with (
            patch("metabolon.enzymes.interoception.subprocess.run", return_value=self._make_proc()),
            patch("metabolon.enzymes.interoception.shutil.disk_usage", return_value=self._mock_disk()),
            patch("builtins.open", side_effect=open_side_effect),
            patch("metabolon.enzymes.interoception.contextlib.suppress"),
        ):
            result = _fn()(action="system")
        assert "Gate: WARN" in result.sections[0]
        assert "tool updates degraded" in result.sections[0]


# ---------------------------------------------------------------------------
# Financial action — edge cases
# ---------------------------------------------------------------------------

class TestFinancialEdgeCases:
    """Financial action edge cases."""

    def test_financial_counts_overdue_flagged(self):
        with (
            patch("metabolon.locus"),
            patch("builtins.open", MagicMock()),
            patch("metabolon.cytosol.synthesize", return_value="OVERDUE: tax filing\nURGENT: insurance renewal"),
        ):
            result = _fn()(action="financial")
        assert result.flagged_count >= 2

    def test_financial_synthesis_failure_handled(self):
        with (
            patch("metabolon.locus"),
            patch("builtins.open", MagicMock()),
            patch("metabolon.cytosol.synthesize", side_effect=Exception("API down")),
        ):
            result = _fn()(action="financial")
        assert "LLM synthesis failed" in result.summary


# ---------------------------------------------------------------------------
# Log symptom — cross-link integration
# ---------------------------------------------------------------------------

class TestLogSymptomCrossLink:
    """Test log_symptom integrates with cross-link."""

    def test_log_symptom_with_cross_link(self):
        with (
            patch("metabolon.enzymes.interoception._health_log_path", return_value="/tmp/test_xlog.md"),
            patch("metabolon.enzymes.interoception._cross_link_experiment_symptom", return_value="Cross-linked to experiment: assay-caffeine.md"),
            patch("builtins.open", MagicMock()),
        ):
            result = _fn()(action="log_symptom", symptom="jitters", severity="mild", notes="coffee")
        assert result.success is True
        assert "Cross-linked to experiment" in result.message

    def test_log_symptom_writes_notes_field(self):
        written = {}
        mock_file = MagicMock()

        def mock_open_fn(path, *args, **kwargs):
            if "test_xlog2" in str(path):
                mock_file.write.side_effect = lambda s: written.update(content=s)
                return mock_file
            return MagicMock()

        with (
            patch("metabolon.enzymes.interoception._health_log_path", return_value="/tmp/test_xlog2.md"),
            patch("metabolon.enzymes.interoception._cross_link_experiment_symptom", return_value=None),
            patch("os.makedirs"),
            patch("builtins.open", side_effect=mock_open_fn),
        ):
            result = _fn()(action="log_symptom", symptom="headache", severity="moderate", notes="after lunch")
        assert result.success is True


# ---------------------------------------------------------------------------
# Glycolysis — trend data
# ---------------------------------------------------------------------------

class TestGlycolysisTrend:
    """Test glycolysis action with trend data."""

    def test_trend_with_two_data_points(self):
        mock_snapshot = MagicMock(return_value={
            "glycolysis_pct": 70.0,
            "deterministic_count": 140,
            "symbiont_count": 20,
            "hybrid_count": 5,
            "total": 165,
        })
        mock_trend = MagicMock(return_value=[
            {"date": "2024-01-01", "glycolysis_pct": 60.0},
            {"date": "2024-01-15", "glycolysis_pct": 70.0},
        ])
        with (
            patch("metabolon.organelles.glycolysis_rate.snapshot", mock_snapshot),
            patch("metabolon.organelles.glycolysis_rate.trend", mock_trend),
        ):
            result = _fn()(action="glycolysis", trend_days=30)
        assert "Trend (30d): +10.0%" in result.summary

    def test_trend_negative_delta(self):
        mock_snapshot = MagicMock(return_value={
            "glycolysis_pct": 55.0,
            "deterministic_count": 100,
            "symbiont_count": 40,
            "hybrid_count": 10,
            "total": 150,
        })
        mock_trend = MagicMock(return_value=[
            {"date": "2024-01-01", "glycolysis_pct": 60.0},
            {"date": "2024-01-15", "glycolysis_pct": 55.0},
        ])
        with (
            patch("metabolon.organelles.glycolysis_rate.snapshot", mock_snapshot),
            patch("metabolon.organelles.glycolysis_rate.trend", mock_trend),
        ):
            result = _fn()(action="glycolysis")
        assert "Trend (30d): -5.0%" in result.summary


# ---------------------------------------------------------------------------
# CRISPR — with spacers file
# ---------------------------------------------------------------------------

class TestCrisprWithSpacers:
    """Test crispr action when spacers file exists."""

    def test_crispr_reads_recent_spacers(self):
        spacers_content = (
            '{"ts": "2024-01-15T10:00:00", "tool": "gpt4", "pattern": "erratic behavior in module X"}\n'
            '{"ts": "2024-01-14T09:00:00", "tool": "claude", "pattern": "hallucinated import os.path"}\n'
        )
        mock_spacer_count = MagicMock(return_value=2)
        mock_compile_guides = MagicMock(return_value=[{"guide": "g1"}])

        with (
            patch("metabolon.organelles.crispr.spacer_count", mock_spacer_count),
            patch("metabolon.organelles.crispr.compile_guides", mock_compile_guides),
            patch("pathlib.Path.home", return_value=Path("/home/testuser")),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=spacers_content),
        ):
            result = _fn()(action="crispr", recent_n=5)

        assert result.spacer_count == 2
        assert len(result.recent) == 2
        assert result.recent[0]["tool"] == "claude"  # reversed
        assert "gpt4" in result.recent[1]["tool"]


# ---------------------------------------------------------------------------
# Retrograde — zero retrograde
# ---------------------------------------------------------------------------

class TestRetrogradeZeroRetrograde:
    """Test retrograde action with zero retrograde count."""

    def test_zero_retrograde_count(self):
        mock_balance = MagicMock(return_value={
            "anterograde_count": 5,
            "retrograde_count": 0,
            "ratio": 0.0,
            "assessment": "unidirectional",
        })
        with patch("metabolon.organelles.retrograde.signal_balance", mock_balance):
            result = _fn()(action="retrograde", days=14)

        assert result.retrograde_count == 0
        assert "5:0" in result.summary
        assert "14d" in result.summary


# ---------------------------------------------------------------------------
# Probe — all pass / all fail
# ---------------------------------------------------------------------------

class TestProbeAllPassAllFail:
    """Test probe action with all passing or all failing probes."""

    def test_all_probes_pass(self):
        mock_run = MagicMock(return_value=[
            {"name": "p1", "passed": True, "message": "ok", "duration_ms": 5},
            {"name": "p2", "passed": True, "message": "ok", "duration_ms": 3},
        ])
        with patch("metabolon.organelles.inflammasome.run_all_probes", mock_run):
            result = _fn()(action="probe")
        assert result.passed == 2
        assert result.total == 2
        assert "2/2 passed" in result.report

    def test_all_probes_fail(self):
        mock_run = MagicMock(return_value=[
            {"name": "p1", "passed": False, "message": "err", "duration_ms": 10},
        ])
        with patch("metabolon.organelles.inflammasome.run_all_probes", mock_run):
            result = _fn()(action="probe")
        assert result.passed == 0
        assert result.total == 1
        assert "0/1 passed" in result.report


# ---------------------------------------------------------------------------
# Heartrate — edge cases
# ---------------------------------------------------------------------------

class TestHeartRateEdges:
    """Heartrate action edge cases."""

    def test_records_with_none_bpm_skipped(self):
        mock_heartrate = MagicMock(return_value=[
            {"timestamp": "2024-01-01T10:00", "bpm": 60},
            {"timestamp": "2024-01-01T10:00", "bpm": None},
            {"timestamp": "2024-01-01T10:30", "bpm": 70},
        ])
        with patch("metabolon.organelles.chemoreceptor.heartrate", mock_heartrate):
            result = _fn()(action="heartrate")
        assert "2 readings" in result.summary
        assert "avg 65" in result.summary

    def test_empty_timestamp_skipped(self):
        mock_heartrate = MagicMock(return_value=[
            {"timestamp": "", "bpm": 60},
            {"timestamp": "2024-01-01T10:00", "bpm": 70},
        ])
        with patch("metabolon.organelles.chemoreceptor.heartrate", mock_heartrate):
            result = _fn()(action="heartrate")
        assert "1 buckets" in result.summary


# ---------------------------------------------------------------------------
# Disk clean — mo clean timeout
# ---------------------------------------------------------------------------

class TestDiskCleanTimeout:
    """Test disk_clean action handles mo clean timeout."""

    def test_mo_clean_timeout_handled(self):
        import subprocess
        with (
            patch("metabolon.enzymes.interoception.subprocess.run", side_effect=subprocess.TimeoutExpired("mo", 300)),
            patch("metabolon.enzymes.interoception._clean_build_artifacts", return_value=(0.0, [])),
            patch("metabolon.enzymes.interoception.shutil.disk_usage") as mock_disk,
            patch("metabolon.metabolism.setpoint.Threshold"),
        ):
            mock_usage = MagicMock()
            mock_usage.free = 50 * (1024**3)
            mock_disk.side_effect = [mock_usage, mock_usage]
            result = _fn()(action="disk_clean")

        assert isinstance(result.after_gb, float)
        assert "timed out" in result.output


# ---------------------------------------------------------------------------
# _ACTIONS constant validation
# ---------------------------------------------------------------------------

class TestActionsConstant:
    """Test _ACTIONS constant includes all expected actions."""

    def test_actions_string_contains_core_actions(self):
        from metabolon.enzymes.interoception import _ACTIONS
        expected = ["system", "financial", "sleep", "readiness", "heartrate",
                     "log_symptom", "flywheel", "disk_clean", "glycolysis",
                     "tissue_routing", "crispr", "retrograde", "mitophagy",
                     "angiogenesis", "membrane", "probe"]
        for action in expected:
            assert action in _ACTIONS, f"'{action}' missing from _ACTIONS"


# ---------------------------------------------------------------------------
# Wrapper functions edge cases
# ---------------------------------------------------------------------------

class TestWrapperEdges:
    """Additional wrapper function tests."""

    def test_sleep_result_default_period(self):
        from metabolon.enzymes.interoception import _sleep_result, CircadianResult
        with patch("metabolon.enzymes.interoception.interoception", return_value=CircadianResult(summary="default")) as mock_fn:
            result = _sleep_result()
        mock_fn.assert_called_once_with(action="sleep", period="today")

    def test_heartrate_result_default_params(self):
        from metabolon.enzymes.interoception import _heartrate_result, HeartRateResult
        with patch("metabolon.enzymes.interoception.interoception", return_value=HeartRateResult(summary="hr")) as mock_fn:
            result = _heartrate_result()
        mock_fn.assert_called_once_with(action="heartrate", start_datetime="", end_datetime="")
