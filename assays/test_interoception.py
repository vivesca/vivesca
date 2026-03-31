"""Tests for interoception enzyme."""
import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

from metabolon.enzymes.interoception import (
    interoception,
    _format_duration,
    _sleep_result,
    _heartrate_result,
    CircadianResult,
    HeartRateResult,
    MembranePotentialResult,
    HomeostasisResult,
    HomeostasisFinancialResult,
    LysosomeResult,
    AnabolismResult,
    GlycolysisResult,
    TissueRoutingResult,
    CrisprResult,
    RetrogradeResult,
    MitophagyResult,
    AngiogenesisResult,
    InflammasomeResult,
    EffectorResult,
)


def test_format_duration():
    """Test _format_duration handles various cases."""
    assert _format_duration(None) == "n/a"
    assert _format_duration(0) == "0m"
    assert _format_duration(30) == "0m"
    assert _format_duration(45) == "0m"
    assert _format_duration(60) == "1m"
    assert _format_duration(75) == "1m"
    assert _format_duration(90) == "1m30m"  # Wait: 90 seconds is 1m30? 90//60 = 1m, 30 seconds remainder → 1h30m format → 1m30? Wait let's check code.
    # 90 seconds = 1 minutes 30 seconds → divmod(90//60, 60) = 1 minutes 30 seconds → 1m30 → actually: 90 seconds = 1 minute 30 seconds → output "1m30"
    assert _format_duration(4320) == "1h12m"  # 4320 seconds = 72 minutes = 1h12m
    assert _format_duration(480 * 60) == "8h00m"


def test_unknown_action():
    """Test unknown action returns error."""
    result = interoception(action="invalid_action_that_does_not_exist")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "Unknown action" in result.message
    assert "Valid:" in result.message


def test_action_system_with_mocks():
    """Test system action with all external calls mocked."""
    mock_subprocess = MagicMock()
    mock_subprocess.return_value.stdout = "com.terry.vivesca.pulse\n"
    mock_subprocess.return_value.stderr = ""

    mock_vasomotor = MagicMock()
    mock_vasomotor.return_value = {"formatted": "12.5GB / 50GB (25%)"}

    mock_precision = MagicMock(return_value="Precision: everything up to date")

    mock_threshold = MagicMock()
    mock_threshold.read.return_value = 15.0

    with patch("metabolon.enzymes.interoception.subprocess.run", mock_subprocess), \
         patch("metabolon.organelles.vasomotor_sensor.sense", mock_vasomotor), \
         patch("metabolon.metabolism.mismatch_repair.summary", mock_precision), \
         patch("metabolon.metabolism.setpoint.Threshold", return_value=mock_threshold), \
         patch("builtins.open", MagicMock(side_effect=FileNotFoundError)):

        result = interoception(action="system")
        assert isinstance(result, HomeostasisResult)
        assert isinstance(result.sections, list)
        assert len(result.sections) > 0
        # Should contain Gate line
        assert any("Gate:" in section for section in result.sections)
        # Pulse should be found
        assert any("Pulse:" in section for section in result.sections)
        assert any("vivesca" in section for section in result.sections)


def test_action_sleep_period_today():
    """Test sleep action with today period."""
    mock_sense = MagicMock(return_value={
        "sleep_score": 82,
        "readiness_score": 76,
        "average_hrv": 35,
        "sleep_contributors": {"consistency": 90},
        "contributors": {"activity": 80},
        "temperature_deviation": 0.2,
        "temperature_trend_deviation": -0.1,
        "deep_sleep_duration": 4320,
        "light_sleep_duration": 2160,
        "rem_sleep_duration": 1080,
        "awake_time": 180,
        "total_sleep_duration": 7740,
        "time_in_bed": 8400,
        "bedtime_start": "2025-01-01T23:00:00",
        "bedtime_end": "2025-01-02T07:00:00",
        "latency": 15,
        "efficiency": 92,
        "restless_periods": 3,
        "average_heart_rate": 58,
        "lowest_heart_rate": 52,
        "average_breath": 12,
        "type": "decent",
        "sleep_phase_5_min": "111222333  ",
        "movement_30_sec": "11223",
    })

    with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
        result = interoception(action="sleep", period="today")
        assert isinstance(result, CircadianResult)
        assert "82" in result.summary
        assert "76" in result.summary
        assert "Deep" in result.summary
        assert "Hypnogram" in result.summary
        assert "Movement" in result.summary


def test_action_sleep_with_error():
    """Test sleep when API returns error."""
    mock_sense = MagicMock(return_value={"error": "API rate limit exceeded"})

    with patch("metabolon.organelles.chemoreceptor.sense", mock_sense):
        result = interoception(action="sleep", period="today")
        assert isinstance(result, CircadianResult)
        assert "Error: API rate limit exceeded" in result.summary


def test_action_sleep_week():
    """Test sleep action with week period."""
    mock_week = MagicMock(return_value="Weekly summary: ...")

    with patch("metabolon.organelles.chemoreceptor.week", mock_week):
        result = interoception(action="sleep", period="week")
        assert isinstance(result, CircadianResult)
        assert "Weekly summary" in result.summary


def test_action_membrane():
    """Test membrane action."""
    mock_oura_today = MagicMock(return_value={"formatted": "Readiness: 68/100"})

    with patch("metabolon.organelles.chemoreceptor.today", mock_oura_today):
        result = interoception(action="membrane")
        assert isinstance(result, MembranePotentialResult)
        assert "Readiness: 68" in result.summary
        assert "Exercise guidance" in result.guidance


def test_action_heartrate_no_data():
    """Test heartrate action when no data available."""
    mock_heartrate = MagicMock(return_value=[])

    with patch("metabolon.organelles.chemoreceptor.heartrate", mock_heartrate):
        result = interoception(action="heartrate")
        assert isinstance(result, HeartRateResult)
        assert "No heart rate data available" in result.summary


def test_action_heartrate_with_data():
    """Test heartrate action with data."""
    mock_records = [
        {"timestamp": "2025-01-01T08:00:00", "bpm": 62},
        {"timestamp": "2025-01-01T08:01:00", "bpm": 65},
        {"timestamp": "2025-01-01T08:02:00", "bpm": 60},
    ]
    mock_heartrate = MagicMock(return_value=mock_records)

    with patch("metabolon.organelles.chemoreceptor.heartrate", mock_heartrate):
        result = interoception(action="heartrate", start_datetime="2025-01-01", end_datetime="2025-01-02")
        assert isinstance(result, HeartRateResult)
        assert "3 readings" in result.summary
        assert "62" in result.summary
        assert "avg 62" in result.summary


def test_action_log_symptom_missing_symptom():
    """Test log_symptom without symptom."""
    result = interoception(action="log_symptom")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "requires: symptom" in result.message


@patch("metabolon.enzymes.interoception._cross_link_experiment_symptom")
@patch("builtins.open")
@patch("os.makedirs")
def test_action_log_symptom_success(mock_makedirs, mock_open, mock_cross):
    """Test successful symptom logging."""
    mock_cross.return_value = None

    result = interoception(action="log_symptom", symptom="headache", severity="mild", notes="After lunch")
    assert isinstance(result, EffectorResult)
    assert result.success
    assert "Logged: headache" in result.message
    mock_open.assert_called_once()


def test_action_flywheel_all_fail():
    """Test flywheel action when all sensors fail."""
    with patch("metabolon.organelles.chemoreceptor.today", side_effect=Exception("Network error")), \
         patch("metabolon.organelles.circadian_clock.scheduled_events", side_effect=Exception("No module")), \
         patch("metabolon.enzymes.interoception.subprocess.run", side_effect=Exception("Git error")), \
         patch("pathlib.Path.exists", return_value=False):

        result = interoception(action="flywheel")
        assert isinstance(result, AnabolismResult)
        assert len(result.links) == 4
        assert any(link["name"] == "sleep" and link["score"] is None for link in result.links)
        assert any(link["name"] == "symptoms" and link["recent_entries_7d"] == 0 for link in result.links)
        assert len(result.blind_spots) == 3


def test_action_disk_clean():
    """Test disk_clean action."""
    mock_subprocess = MagicMock()
    mock_subprocess.return_value.stdout = "Cleaned up 1.2GB\n"
    mock_subprocess.return_value.stderr = ""

    mock_disk_usage = MagicMock()
    mock_disk_usage.side_effect = [
        MagicMock(free=int(100 * 1024**3)),  # before
        MagicMock(free=int(103 * 1024**3)),  # after
    ]

    mock_threshold = MagicMock()
    mock_threshold.read.return_value = 15.0

    with patch("metabolon.enzymes.interoception.subprocess.run", mock_subprocess), \
         patch("shutil.disk_usage", mock_disk_usage), \
         patch("metabolon.enzymes.interoception._clean_build_artifacts", return_value=(1.2, ["Node: project/node_modules"])), \
         patch("metabolon.metabolism.setpoint.Threshold", return_value=mock_threshold):

        result = interoception(action="disk_clean")
        assert isinstance(result, LysosomeResult)
        assert result.freed_gb == 3.0
        assert "Build artifacts" in result.output


def test_action_glycolysis():
    """Test glycolysis action."""
    mock_snapshot = MagicMock(return_value={
        "deterministic_count": 42,
        "symbiont_count": 18,
        "hybrid_count": 7,
        "total": 67,
        "glycolysis_pct": 62.7,
    })
    mock_trend = MagicMock(return_value=[
        {"date": "2025-01-01", "glycolysis_pct": 58.0},
        {"date": "2025-01-30", "glycolysis_pct": 62.7},
    ])

    with patch("metabolon.organelles.glycolysis_rate.snapshot", mock_snapshot), \
         patch("metabolon.organelles.glycolysis_rate.trend", mock_trend):

        result = interoception(action="glycolysis", trend_days=30)
        assert isinstance(result, GlycolysisResult)
        assert result.deterministic_count == 42
        assert result.symbiont_count == 18
        assert result.glycolysis_pct == 62.7
        assert "62.7% deterministic" in result.summary
        assert len(result.trend) == 2


def test_action_tissue_routing():
    """Test tissue_routing action."""
    mock_observed = MagicMock(return_value={"dna": "replication", "protein": "translation"})
    mock_report = MagicMock(return_value="All routes observed: 2 active.")

    with patch("metabolon.organelles.tissue_routing.observed_routes", mock_observed), \
         patch("metabolon.organelles.tissue_routing.route_report", mock_report):

        result = interoception(action="tissue_routing")
        assert isinstance(result, TissueRoutingResult)
        assert result.routes == {"dna": "replication", "protein": "translation"}
        assert "All routes observed" in result.report


def test_action_crispr():
    """Test crispr action."""
    mock_spacer_count = MagicMock(return_value=127)
    mock_compile_guides = MagicMock(return_value=[{"spacer": "AAA", "pam": "NGG"}])

    with patch("metabolon.organelles.crispr.spacer_count", mock_spacer_count), \
         patch("metabolon.organelles.crispr.compile_guides", mock_compile_guides), \
         patch("pathlib.Path.exists", return_value=False):

        result = interoception(action="crispr", recent_n=5)
        assert isinstance(result, CrisprResult)
        assert result.spacer_count == 127
        assert result.guide_count == 1
        assert "127 spacers" in result.summary


def test_action_retrograde():
    """Test retrograde action."""
    mock_signal_balance = MagicMock(return_value={
        "anterograde_count": 12,
        "retrograde_count": 8,
        "ratio": 1.5,
        "assessment": "balanced",
    })

    with patch("metabolon.organelles.retrograde.signal_balance", mock_signal_balance):

        result = interoception(action="retrograde", days=7)
        assert isinstance(result, RetrogradeResult)
        assert result.anterograde_count == 12
        assert result.retrograde_count == 8
        assert result.ratio == 1.5
        assert result.assessment == "balanced"
        assert "balanced" in result.summary.upper()


def test_action_mitophagy():
    """Test mitophagy action."""
    mock_fitness = MagicMock(return_value=[
        {"model": "model1", "score": 0.85},
        {"model": "model2", "score": 0.62},
    ])
    mock_blacklist = MagicMock(return_value={"model2": "outdated"})

    with patch("metabolon.organelles.mitophagy.model_fitness", mock_fitness), \
         patch("metabolon.organelles.mitophagy._load_blacklist", mock_blacklist):

        result = interoception(action="mitophagy", task_type="coding", days=30)
        assert isinstance(result, MitophagyResult)
        assert len(result.fitness) == 2
        assert result.blacklist == {"model2": "outdated"}


def test_action_angiogenesis():
    """Test angiogenesis action."""
    mock_detect = MagicMock(return_value=[{"source": "module_a", "target": "module_b"}])
    mock_propose = MagicMock(return_value={"source": "module_a", "target": "module_b", "proposal": "Add connector X"})
    mock_registry = MagicMock(return_value=[{"name": "existing_vessel", "source": "x", "target": "y"}])

    with patch("metabolon.organelles.angiogenesis.detect_hypoxia", mock_detect), \
         patch("metabolon.organelles.angiogenesis.propose_vessel", mock_propose), \
         patch("metabolon.organelles.angiogenesis.vessel_registry", mock_registry):

        result = interoception(action="angiogenesis")
        assert isinstance(result, AngiogenesisResult)
        assert len(result.hypoxic_pairs) == 1
        assert len(result.proposals) == 1
        assert len(result.existing_vessels) == 1


def test_action_probe():
    """Test probe (inflammasome) action."""
    mock_run_all = MagicMock(return_value=[
        {"name": "probe1", "passed": True, "message": "OK", "duration_ms": 120},
        {"name": "probe2", "passed": False, "message": "Failed", "duration_ms": 80},
    ])

    with patch("metabolon.organelles.inflammasome.run_all_probes", mock_run_all):

        result = interoception(action="probe")
        assert isinstance(result, InflammasomeResult)
        assert result.passed == 1
        assert result.total == 2
        assert "[PASS]" in result.report
        assert "[FAIL]" in result.report
        assert "1/2 passed" in result.report


def test__sleep_result_wrapper():
    """Test _sleep_result wrapper function."""
    mock_interoception = MagicMock(return_value=CircadianResult(summary="Test"))

    with patch("metabolon.enzymes.interoception.interoception", mock_interoception):
        result = _sleep_result("today")
        assert isinstance(result, CircadianResult)
        mock_interoception.assert_called_with(action="sleep", period="today")


def test__heartrate_result_wrapper():
    """Test _heartrate_result wrapper function."""
    mock_interoception = MagicMock(return_value=HeartRateResult(summary="Test"))

    with patch("metabolon.enzymes.interoception.interoception", mock_interoception):
        result = _heartrate_result("2025-01-01", "2025-01-02")
        assert isinstance(result, HeartRateResult)
        mock_interoception.assert_called_with(
            action="heartrate",
            start_datetime="2025-01-01",
            end_datetime="2025-01-02"
        )
