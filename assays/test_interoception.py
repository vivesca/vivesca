"""Tests for metabolon/enzymes/interoception.py — internal state sensing."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from datetime import date

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fn():
    """Return the raw function behind the @tool decorator."""
    from metabolon.enzymes import interoception as mod
    return mod.interoception


def _result_classes():
    from metabolon.enzymes.interoception import (
        CircadianResult,
        HeartRateResult,
        MembranePotentialResult,
        HomeostasisResult,
        HomeostasisFinancialResult,
        LysosomeResult,
        AnabolismResult,
        AngiogenesisResult,
        MitophagyResult,
        GlycolysisResult,
        TissueRoutingResult,
        CrisprResult,
        RetrogradeResult,
        InflammasomeResult,
    )
    return {
        "CircadianResult": CircadianResult,
        "HeartRateResult": HeartRateResult,
        "MembranePotentialResult": MembranePotentialResult,
        "HomeostasisResult": HomeostasisResult,
        "HomeostasisFinancialResult": HomeostasisFinancialResult,
        "LysosomeResult": LysosomeResult,
        "AnabolismResult": AnabolismResult,
        "AngiogenesisResult": AngiogenesisResult,
        "MitophagyResult": MitophagyResult,
        "GlycolysisResult": GlycolysisResult,
        "TissueRoutingResult": TissueRoutingResult,
        "CrisprResult": CrisprResult,
        "RetrogradeResult": RetrogradeResult,
        "InflammasomeResult": InflammasomeResult,
    }


# ---------------------------------------------------------------------------
# Format duration tests
# ---------------------------------------------------------------------------

class TestFormatDuration:
    """Tests for _format_duration helper."""

    def test_none_returns_na(self):
        from metabolon.enzymes.interoception import _format_duration
        assert _format_duration(None) == "n/a"

    def test_zero_minutes(self):
        from metabolon.enzymes.interoception import _format_duration
        assert _format_duration(0) == "0m"

    def test_only_minutes(self):
        from metabolon.enzymes.interoception import _format_duration
        assert _format_duration(45 * 60) == "45m"

    def test_hours_and_minutes(self):
        from metabolon.enzymes.interoception import _format_duration
        assert _format_duration((7 * 60 + 5) * 60) == "7h05m"

    def test_hours_and_minutes_padded(self):
        from metabolon.enzymes.interoception import _format_duration
        assert _format_duration((2 * 60 + 9) * 60) == "2h09m"


# ---------------------------------------------------------------------------
# Unknown action tests
# ---------------------------------------------------------------------------

class TestUnknownAction:
    """Tests for unknown actions."""

    def test_unknown_action_returns_error(self):
        result = _fn()(action="invalid_action")
        assert result.success is False
        assert "Unknown action" in result.message
        assert "invalid_action" in result.message

    def test_action_case_insensitive(self):
        """Action is lowercased and stripped."""
        with patch("metabolon.enzymes.interoception.subprocess.run"):
            with patch("metabolon.enzymes.interoception.shutil.disk_usage"):
                result = _fn()(action="  SYSTEM  ")
        from metabolon.enzymes.interoception import HomeostasisResult
        assert isinstance(result, HomeostasisResult)
        assert hasattr(result, "sections")


# ---------------------------------------------------------------------------
# System action tests
# ---------------------------------------------------------------------------

class TestSystemAction:
    """Tests for system action."""

    def test_system_returns_homeostasis_result(self):
        mock_proc = MagicMock()
        mock_proc.stdout = ""
        with (
            patch("metabolon.enzymes.interoception.subprocess.run", return_value=mock_proc),
            patch("metabolon.enzymes.interoception.shutil.disk_usage") as mock_disk,
            patch("builtins.open"),
            patch("metabolon.enzymes.interoception.contextlib.suppress"),
        ):
            mock_usage = MagicMock()
            mock_usage.free = 100 * (1024**3)
            mock_usage.total = 500 * (1024**3)
            mock_disk.return_value = mock_usage
            result = _fn()(action="system")

        from metabolon.enzymes.interoception import HomeostasisResult
        assert isinstance(result, HomeostasisResult)
        assert isinstance(result.sections, list)
        assert len(result.sections) > 0


# ---------------------------------------------------------------------------
# Sleep action tests
# ---------------------------------------------------------------------------

class TestSleepAction:
    """Tests for sleep action."""

    def test_sleep_returns_circadian_result(self):
        mock_sense = MagicMock(return_value={
            "sleep_score": 85,
            "readiness_score": 75,
            "average_hrv": 45,
        })
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            with patch("metabolon.enzymes.interoception._health_log_path", return_value="/tmp/fake"):
                result = _fn()(action="sleep")

        from metabolon.enzymes.interoception import CircadianResult
        assert isinstance(result, CircadianResult)
        assert isinstance(result.summary, str)
        assert "85" in result.summary
        assert "75" in result.summary

    def test_sleep_handles_error_data(self):
        mock_sense = MagicMock(return_value={"error": "API unavailable"})
        with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
            result = _fn()(action="sleep")

        from metabolon.enzymes.interoception import CircadianResult
        assert isinstance(result, CircadianResult)
        assert "Error: API unavailable" in result.summary

    def test_sleep_week_delegates_to_week(self):
        mock_week = MagicMock(return_value="Weekly summary")
        with patch("metabolon.organelles.chemoreceptor.week", mock_week):
            result = _fn()(action="sleep", period="week")

        from metabolon.enzymes.interoception import CircadianResult
        assert isinstance(result, CircadianResult)
        assert result.summary == "Weekly summary"
        mock_week.assert_called_once()


# ---------------------------------------------------------------------------
# Membrane/readiness action tests
# ---------------------------------------------------------------------------

class TestMembraneAction:
    """Tests for membrane/readiness action."""

    def test_membrane_returns_membrane_result(self):
        mock_oura_today = MagicMock(return_value={"formatted": "Readiness: 82"})
        with patch("metabolon.organelles.chemoreceptor.today", mock_oura_today):
            result = _fn()(action="membrane")

        from metabolon.enzymes.interoception import MembranePotentialResult
        assert isinstance(result, MembranePotentialResult)
        assert "82" in result.summary
        assert "Exercise guidance" in result.guidance

    def test_readiness_is_same_as_membrane(self):
        mock_oura_today = MagicMock(return_value={"formatted": "Readiness: 68"})
        with patch("metabolon.organelles.chemoreceptor.today", mock_oura_today):
            result = _fn()(action="readiness")

        from metabolon.enzymes.interoception import MembranePotentialResult
        assert isinstance(result, MembranePotentialResult)


# ---------------------------------------------------------------------------
# Heartrate action tests
# ---------------------------------------------------------------------------

class TestHeartRateAction:
    """Tests for heartrate action."""

    def test_no_data_returns_no_data_message(self):
        mock_heartrate = MagicMock(return_value=[])
        with patch("metabolon.organelles.chemoreceptor.heartrate", mock_heartrate):
            result = _fn()(action="heartrate")

        from metabolon.enzymes.interoception import HeartRateResult
        assert isinstance(result, HeartRateResult)
        assert "No heart rate data available" in result.summary

    def test_with_data_aggregates_correctly(self):
        mock_heartrate = MagicMock(return_value=[
            {"timestamp": "2024-01-01T10:00", "bpm": 60},
            {"timestamp": "2024-01-01T10:00", "bpm": 62},
            {"timestamp": "2024-01-01T10:30", "bpm": 65},
        ])
        with patch("metabolon.organelles.chemoreceptor.heartrate", mock_heartrate):
            result = _fn()(action="heartrate")

        from metabolon.enzymes.interoception import HeartRateResult
        assert isinstance(result, HeartRateResult)
        assert "3 readings" in result.summary
        assert "avg 62" in result.summary


# ---------------------------------------------------------------------------
# log_symptom tests
# ---------------------------------------------------------------------------

class TestLogSymptom:
    """Tests for log_symptom action."""

    def test_missing_symptom_returns_error(self):
        result = _fn()(action="log_symptom")
        assert result.success is False
        assert "requires: symptom" in result.message

    def test_log_symptom_success(self):
        with (
            patch("metabolon.enzymes.interoception._health_log_path", return_value="/tmp/test_health_log.md"),
            patch("metabolon.enzymes.interoception._cross_link_experiment_symptom", return_value=None),
            patch("builtins.open", MagicMock()) as mock_open,
        ):
            result = _fn()(action="log_symptom", symptom="headache", severity="moderate", notes="after lunch")

        assert result.success is True
        assert "Logged: headache (moderate)" in result.message
        mock_open.assert_called_once()


# ---------------------------------------------------------------------------
# flywheel action tests
# ---------------------------------------------------------------------------

class TestFlywheelAction:
    """Tests for flywheel action."""

    def test_flywheel_returns_anabolism_result(self):
        with (
            patch("metabolon.locus"),
            patch("metabolon.enzymes.interoception.subprocess.run") as mock_run,
            patch("builtins.open", MagicMock()),
            patch("metabolon.enzymes.interoception.os.path.exists", return_value=False),
            patch("metabolon.organelles.chemoreceptor.today", side_effect=Exception("unavailable")),
            patch("metabolon.organelles.circadian_clock.scheduled_events", side_effect=Exception("unavailable")),
        ):
            mock_proc1 = MagicMock()
            mock_proc1.stdout = ""
            mock_proc2 = MagicMock()
            mock_proc2.stdout = ""
            mock_run.side_effect = [mock_proc1, mock_proc2]
            result = _fn()(action="flywheel")

        from metabolon.enzymes.interoception import AnabolismResult
        assert isinstance(result, AnabolismResult)
        assert len(result.links) == 5
        assert len(result.blind_spots) > 0


# ---------------------------------------------------------------------------
# disk_clean action tests
# ---------------------------------------------------------------------------

class TestDiskCleanAction:
    """Tests for disk_clean action."""

    def test_disk_clean_returns_lysosome_result(self):
        with (
            patch("metabolon.enzymes.interoception.subprocess.run") as mock_run,
            patch("metabolon.enzymes.interoception._clean_build_artifacts", return_value=(0.5, ["cleaned something"])),
            patch("metabolon.enzymes.interoception.shutil.disk_usage") as mock_disk,
            patch("metabolon.metabolism.setpoint.Threshold"),
        ):
            mock_proc = MagicMock()
            mock_proc.stdout = "cleaned\n"
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc
            mock_usage1 = MagicMock()
            mock_usage1.free = 10 * (1024**3)
            mock_usage2 = MagicMock()
            mock_usage2.free = 12 * (1024**3)
            mock_disk.side_effect = [mock_usage1, mock_usage2]
            result = _fn()(action="disk_clean")

        from metabolon.enzymes.interoception import LysosomeResult
        assert isinstance(result, LysosomeResult)
        assert result.before_gb == 10.0
        assert result.after_gb == 12.0
        assert result.freed_gb == 2.0
        assert "cleaned something" in result.output


# ---------------------------------------------------------------------------
# _clean_build_artifacts tests
# ---------------------------------------------------------------------------

class TestCleanBuildArtifacts:
    """Tests for _clean_build_artifacts helper."""

    def test_cargo_sweep_not_installed(self):
        from metabolon.enzymes.interoception import _clean_build_artifacts
        with (
            patch("metabolon.enzymes.interoception.CODE_DIR", "/tmp/fake"),
            patch("os.path.isdir", return_value=True),
            patch("subprocess.run", side_effect=FileNotFoundError),
            patch("os.scandir", return_value=[]),
            patch("shutil.disk_usage") as mock_disk,
        ):
            mock_usage1 = MagicMock()
            mock_usage1.free = 100 * (1024**3)
            mock_usage2 = MagicMock()
            mock_usage2.free = 100 * (1024**3)
            mock_disk.side_effect = [mock_usage1, mock_usage2]
            freed_gb, logs = _clean_build_artifacts()

        assert freed_gb == 0.0
        assert any("cargo-sweep not installed" in line for line in logs)


# ---------------------------------------------------------------------------
# glycolysis action tests
# ---------------------------------------------------------------------------

class TestGlycolysisAction:
    """Tests for glycolysis action."""

    def test_glycolysis_returns_glycolysis_result(self):
        mock_snapshot = MagicMock(return_value={
            "glycolysis_pct": 65.5,
            "deterministic_count": 120,
            "symbiont_count": 30,
            "hybrid_count": 10,
            "total": 160,
        })
        mock_trend = MagicMock(return_value=[])
        with (
            patch("metabolon.organelles.glycolysis_rate.snapshot", mock_snapshot),
            patch("metabolon.organelles.glycolysis_rate.trend", mock_trend),
        ):
            result = _fn()(action="glycolysis")

        from metabolon.enzymes.interoception import GlycolysisResult
        assert isinstance(result, GlycolysisResult)
        assert result.glycolysis_pct == 65.5
        assert result.deterministic_count == 120
        assert result.symbiont_count == 30
        assert "65.5% deterministic" in result.summary


# ---------------------------------------------------------------------------
# tissue_routing action tests
# ---------------------------------------------------------------------------

class TestTissueRoutingAction:
    """Tests for tissue_routing action."""

    def test_tissue_routing_returns_result(self):
        mock_routes = MagicMock(return_value={"a": "path-a", "b": "path-b"})
        mock_report = MagicMock(return_value="Routing report here")
        with (
            patch("metabolon.organelles.tissue_routing.observed_routes", mock_routes),
            patch("metabolon.organelles.tissue_routing.route_report", mock_report),
        ):
            result = _fn()(action="tissue_routing")

        from metabolon.enzymes.interoception import TissueRoutingResult
        assert isinstance(result, TissueRoutingResult)
        assert result.routes == {"a": "path-a", "b": "path-b"}
        assert result.report == "Routing report here"


# ---------------------------------------------------------------------------
# crispr action tests
# ---------------------------------------------------------------------------

class TestCrisprAction:
    """Tests for crispr action."""

    def test_crispr_returns_result(self):
        mock_spacer_count = MagicMock(return_value=127)
        mock_compile_guides = MagicMock(return_value=[{"guide": "seq1"}, {"guide": "seq2"}])
        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("metabolon.organelles.crispr.spacer_count", mock_spacer_count),
            patch("metabolon.organelles.crispr.compile_guides", mock_compile_guides),
        ):
            result = _fn()(action="crispr")

        from metabolon.enzymes.interoception import CrisprResult
        assert isinstance(result, CrisprResult)
        assert result.spacer_count == 127
        assert result.guide_count == 2
        assert "127 acquired" in result.summary
        assert "No spacers acquired yet" in result.summary


# ---------------------------------------------------------------------------
# retrograde action tests
# ---------------------------------------------------------------------------

class TestRetrogradeAction:
    """Tests for retrograde action."""

    def test_retrograde_returns_result(self):
        mock_balance = MagicMock(return_value={
            "anterograde_count": 10,
            "retrograde_count": 5,
            "ratio": 2.0,
            "assessment": "balanced",
        })
        with (
            patch("metabolon.organelles.retrograde.signal_balance", mock_balance),
        ):
            result = _fn()(action="retrograde", days=7)

        from metabolon.enzymes.interoception import RetrogradeResult
        assert isinstance(result, RetrogradeResult)
        assert result.anterograde_count == 10
        assert result.retrograde_count == 5
        assert result.ratio == 2.0
        assert "2.0:1" in result.summary


# ---------------------------------------------------------------------------
# mitophagy action tests
# ---------------------------------------------------------------------------

class TestMitophagyAction:
    """Tests for mitophagy action."""

    def test_mitophagy_returns_result(self):
        mock_fitness = MagicMock(return_value=[{"model": "model1", "score": 0.8}])
        mock_blacklist = MagicMock(return_value={"model1": "accuracy issues"})
        with (
            patch("metabolon.organelles.mitophagy.model_fitness", mock_fitness),
            patch("metabolon.organelles.mitophagy._load_blacklist", mock_blacklist),
        ):
            result = _fn()(action="mitophagy")

        from metabolon.enzymes.interoception import MitophagyResult
        assert isinstance(result, MitophagyResult)
        assert len(result.fitness) == 1
        assert "model1" in result.blacklist


# ---------------------------------------------------------------------------
# angiogenesis action tests
# ---------------------------------------------------------------------------

class TestAngiogenesisAction:
    """Tests for angiogenesis action."""

    def test_angiogenesis_returns_result(self):
        mock_detect = MagicMock(return_value=[{"source": "a", "target": "b"}])
        mock_propose = MagicMock(return_value={"source": "a", "target": "b", "proposal": "build corridor"})
        mock_registry = MagicMock(return_value=[{"name": "existing-vessel-1"}])
        with (
            patch("metabolon.organelles.angiogenesis.detect_hypoxia", mock_detect),
            patch("metabolon.organelles.angiogenesis.propose_vessel", mock_propose),
            patch("metabolon.organelles.angiogenesis.vessel_registry", mock_registry),
        ):
            result = _fn()(action="angiogenesis")

        from metabolon.enzymes.interoception import AngiogenesisResult
        assert isinstance(result, AngiogenesisResult)
        assert len(result.hypoxic_pairs) == 1
        assert len(result.proposals) == 1
        assert len(result.existing_vessels) == 1


# ---------------------------------------------------------------------------
# probe action tests
# ---------------------------------------------------------------------------

class TestProbeAction:
    """Tests for probe (inflammasome) action."""

    def test_probe_returns_result(self):
        mock_run_all = MagicMock(return_value=[
            {"name": "probe1", "passed": True, "message": "ok", "duration_ms": 10},
            {"name": "probe2", "passed": False, "message": "fail", "duration_ms": 20},
        ])
        with (
            patch("metabolon.organelles.inflammasome.run_all_probes", mock_run_all),
        ):
            result = _fn()(action="probe")

        from metabolon.enzymes.interoception import InflammasomeResult
        assert isinstance(result, InflammasomeResult)
        assert result.passed == 1
        assert result.total == 2
        assert "1/2 passed" in result.report


# ---------------------------------------------------------------------------
# financial action tests
# ---------------------------------------------------------------------------

class TestFinancialAction:
    """Tests for financial action."""

    def test_financial_returns_result(self):
        with (
            patch("metabolon.locus"),
            patch("builtins.open", MagicMock()),
            patch("metabolon.cytosol.synthesize", return_value="Summary with no urgent items"),
        ):
            result = _fn()(action="financial")

        from metabolon.enzymes.interoception import HomeostasisFinancialResult
        assert isinstance(result, HomeostasisFinancialResult)
        assert "Summary" in result.summary
        assert isinstance(result.flagged_count, int)


# ---------------------------------------------------------------------------
# Result classes all subclass Secretion
# ---------------------------------------------------------------------------

class TestResultTypes:
    """Verify all result types inherit from Secretion."""

    def test_all_result_types_are_secretion_subclasses(self):
        from metabolon.morphology import Secretion
        classes = _result_classes()
        for name, cls in classes.items():
            assert issubclass(cls, Secretion), f"{name} is not a subclass of Secretion"


# ---------------------------------------------------------------------------
# Wrappers tests
# ---------------------------------------------------------------------------

class TestWrappers:
    """Tests for the wrapper functions _sleep_result and _heartrate_result."""

    def test_sleep_result_wrapper(self):
        from metabolon.enzymes.interoception import _sleep_result, CircadianResult
        with patch("metabolon.enzymes.interoception.interoception", return_value=CircadianResult(summary="test")):
            result = _sleep_result("week")
        assert isinstance(result, CircadianResult)
        assert result.summary == "test"

    def test_heartrate_result_wrapper(self):
        from metabolon.enzymes.interoception import _heartrate_result, HeartRateResult
        with patch("metabolon.enzymes.interoception.interoception", return_value=HeartRateResult(summary="hr test")):
            result = _heartrate_result("2024-01-01", "2024-01-02")
        assert isinstance(result, HeartRateResult)
        assert result.summary == "hr test"
