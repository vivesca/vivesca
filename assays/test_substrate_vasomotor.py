"""Tests for VasomotorSubstrate — respiration pacing metabolism."""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.metabolism.substrates.vasomotor import (
    _parse_ts,
    VasomotorSubstrate,
)


class TestParseTs:
    def test_with_microseconds(self):
        ts = _parse_ts("2025-03-15T10:30:45.123456")
        assert ts.year == 2025
        assert ts.month == 3
        assert ts.day == 15
        assert ts.hour == 10
        assert ts.minute == 30
        assert ts.second == 45
        assert ts.tzinfo is not None

    def test_without_microseconds(self):
        ts = _parse_ts("2025-03-15T10:30:45")
        assert ts.year == 2025
        assert ts.hour == 10
        assert ts.tzinfo is not None

    def test_with_timezone(self):
        ts = _parse_ts("2025-03-15T10:30:45+08:00")
        assert ts.year == 2025
        assert ts.hour == 10


class TestVasomotorSubstrateInit:
    def test_default_paths(self):
        sub = VasomotorSubstrate()
        assert sub.events_path.name == "vivesca-events.jsonl"
        assert sub.state_path.name == "respiration-daily.json"
        assert sub.config_path.name == "vasomotor.conf"
        assert sub.pulse_dir.name == "pulse"

    def test_custom_paths(self, tmp_path: Path):
        events = tmp_path / "events.jsonl"
        state = tmp_path / "state.json"
        config = tmp_path / "config.conf"
        pulse = tmp_path / "pulse"
        pulse.mkdir()

        sub = VasomotorSubstrate(
            events_path=events,
            state_path=state,
            config_path=config,
            pulse_dir=pulse,
        )
        assert sub.events_path == events
        assert sub.state_path == state
        assert sub.config_path == config
        assert sub.pulse_dir == pulse


class TestSense:
    def test_missing_events_file_returns_empty(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "nonexistent.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        assert sub.sense(days=30) == []

    def test_empty_events_file_returns_empty(self, tmp_path: Path):
        events = tmp_path / "events.jsonl"
        events.write_text("")
        sub = VasomotorSubstrate(
            events_path=events,
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        assert sub.sense(days=30) == []

    def test_parses_systole_events(self, tmp_path: Path):
        events = tmp_path / "events.jsonl"
        now = datetime.now(UTC)
        ts = now.strftime("%Y-%m-%dT%H:%M:%S.%f")

        events.write_text(
            json.dumps({"ts": ts, "event": "systole_start"}) + "\n"
            + json.dumps({"ts": ts, "event": "systole_end", "exit_code": 0, "elapsed_s": 120.5}) + "\n"
        )

        sub = VasomotorSubstrate(
            events_path=events,
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        result = sub.sense(days=30)

        assert len(result) == 1
        assert result[0]["systole_count"] == 1
        assert result[0]["successful_systoles"] == 1
        assert result[0]["avg_systole_duration"] == 120.5

    def test_parses_saturation_events(self, tmp_path: Path):
        events = tmp_path / "events.jsonl"
        now = datetime.now(UTC)
        ts = now.strftime("%Y-%m-%dT%H:%M:%S")

        events.write_text(
            json.dumps({"ts": ts, "event": "systole_start"}) + "\n"
            + json.dumps({"ts": ts, "event": "saturation_detected"}) + "\n"
            + json.dumps({"ts": ts, "event": "saturation_detected"}) + "\n"
        )

        sub = VasomotorSubstrate(
            events_path=events,
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        result = sub.sense(days=30)

        assert len(result) == 1
        assert result[0]["saturated_count"] == 2

    def test_parses_pacing_check_events(self, tmp_path: Path):
        events = tmp_path / "events.jsonl"
        now = datetime.now(UTC)
        ts = now.strftime("%Y-%m-%dT%H:%M:%S")

        events.write_text(
            json.dumps({
                "ts": ts,
                "event": "pacing_check",
                "daily_budget": 10.5,
                "estimated_burn": 8.2,
            }) + "\n"
        )

        sub = VasomotorSubstrate(
            events_path=events,
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        result = sub.sense(days=30)

        assert len(result) == 1
        assert result[0]["daily_budget"] == 10.5
        assert result[0]["estimated_burn"] == 8.2

    def test_parses_cost_and_yield_events(self, tmp_path: Path):
        events = tmp_path / "events.jsonl"
        now = datetime.now(UTC)
        ts = now.strftime("%Y-%m-%dT%H:%M:%S")

        events.write_text(
            json.dumps({"ts": ts, "event": "cost_measured", "cost": 0.5}) + "\n"
            + json.dumps({"ts": ts, "event": "systole_usage", "weekly_delta": 1.2}) + "\n"
            + json.dumps({"ts": ts, "event": "systole_yield", "secretion_count": 3}) + "\n"
        )

        sub = VasomotorSubstrate(
            events_path=events,
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        result = sub.sense(days=30)

        assert result[0]["cost_samples"] == [0.5]
        assert result[0]["systole_costs"] == [1.2]
        assert result[0]["systole_yields"] == [3]
        assert result[0]["rq"] == 2.5  # 3 / 1.2

    def test_parses_circuit_breaker_events(self, tmp_path: Path):
        events = tmp_path / "events.jsonl"
        now = datetime.now(UTC)
        ts = now.strftime("%Y-%m-%dT%H:%M:%S")

        events.write_text(
            json.dumps({"ts": ts, "event": "circuit_breaker"}) + "\n"
            + json.dumps({"ts": ts, "event": "circuit_breaker"}) + "\n"
        )

        sub = VasomotorSubstrate(
            events_path=events,
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        result = sub.sense(days=30)

        assert result[0]["circuit_breakers"] == 2

    def test_ignores_old_events(self, tmp_path: Path):
        events = tmp_path / "events.jsonl"
        old_ts = (datetime.now(UTC) - timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%S")

        events.write_text(
            json.dumps({"ts": old_ts, "event": "systole_start"}) + "\n"
        )

        sub = VasomotorSubstrate(
            events_path=events,
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        assert sub.sense(days=30) == []

    def test_handles_malformed_json(self, tmp_path: Path):
        events = tmp_path / "events.jsonl"
        now = datetime.now(UTC)
        ts = now.strftime("%Y-%m-%dT%H:%M:%S")

        events.write_text(
            "not valid json\n"
            + json.dumps({"ts": ts, "event": "systole_start"}) + "\n"
            + "{ broken\n"
        )

        sub = VasomotorSubstrate(
            events_path=events,
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        result = sub.sense(days=30)

        assert len(result) == 1
        assert result[0]["systole_count"] == 1


class TestCandidates:
    def test_empty_sensed_returns_empty(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        assert sub.candidates([]) == []

    def test_detects_overburn(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        sensed = [
            {"date": "2025-03-01", "daily_budget": 10, "estimated_burn": 12,
             "systole_count": 5, "saturated_count": 0, "apnea_window": 1.0},
            {"date": "2025-03-02", "daily_budget": 10, "estimated_burn": 15,
             "systole_count": 5, "saturated_count": 0, "apnea_window": 1.0},
        ]
        result = sub.candidates(sensed)
        overburn = [c for c in result if c["issue"] == "overburn"]
        assert len(overburn) == 1
        assert overburn[0]["severity"] == "medium"

    def test_detects_high_severity_overburn(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        sensed = [
            {"date": f"2025-03-0{i}", "daily_budget": 10, "estimated_burn": 15,
             "systole_count": 5, "saturated_count": 0, "apnea_window": 1.0}
            for i in range(1, 5)
        ]
        result = sub.candidates(sensed)
        overburn = [c for c in result if c["issue"] == "overburn"]
        assert len(overburn) == 1
        assert overburn[0]["severity"] == "high"

    def test_detects_saturation(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        sensed = [
            {"date": "2025-03-01", "systole_count": 10, "saturated_count": 5,
             "daily_budget": None, "estimated_burn": None, "apnea_window": 1.0},
        ]
        result = sub.candidates(sensed)
        sat = [c for c in result if c["issue"] == "saturation"]
        assert len(sat) == 1
        assert sat[0]["severity"] == "medium"

    def test_detects_starvation(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        sensed = [
            {"date": "2025-03-01", "daily_budget": 10, "estimated_burn": 3,
             "systole_count": 5, "saturated_count": 0, "apnea_window": 1.0},
            {"date": "2025-03-02", "daily_budget": 10, "estimated_burn": 4,
             "systole_count": 5, "saturated_count": 0, "apnea_window": 1.0},
        ]
        result = sub.candidates(sensed)
        starved = [c for c in result if c["issue"] == "starvation"]
        assert len(starved) == 1

    def test_detects_silence(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        sensed = [
            {"date": "2025-03-01", "systole_count": 5, "saturated_count": 0,
             "apnea_window": 5.5, "daily_budget": None, "estimated_burn": None},
        ]
        result = sub.candidates(sensed)
        silence = [c for c in result if c["issue"] == "silence"]
        assert len(silence) == 1

    def test_detects_failure_ratio(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        sensed = [
            {"date": f"2025-03-0{i}", "failed_systoles": 2, "successful_systoles": 1,
             "systole_count": 3, "saturated_count": 0, "apnea_window": 1.0,
             "daily_budget": None, "estimated_burn": None}
            for i in range(1, 8)
        ]
        result = sub.candidates(sensed)
        failure = [c for c in result if c["issue"] == "failure_ratio"]
        assert len(failure) == 1
        assert failure[0]["severity"] == "high"

    def test_detects_circuit_breaker(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        sensed = [
            {"date": "2025-03-01", "systole_count": 5, "saturated_count": 0,
             "apnea_window": 1.0, "circuit_breakers": 2,
             "daily_budget": None, "estimated_burn": None},
        ]
        result = sub.candidates(sensed)
        breaker = [c for c in result if c["issue"] == "circuit_breaker"]
        assert len(breaker) == 1
        assert breaker[0]["severity"] == "high"

    def test_detects_fast_burn(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        sensed = [
            {"date": "2025-03-01", "systole_count": 5, "saturated_count": 0,
             "apnea_window": 1.0, "budget_climb_rate": 6.5,
             "daily_budget": None, "estimated_burn": None},
        ]
        result = sub.candidates(sensed)
        fast = [c for c in result if c["issue"] == "fast_burn"]
        assert len(fast) == 1

    def test_detects_volatility(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        # Need stdev > mean: stdev([0.1, 0.2, 10.0]) ≈ 5.68 > mean ≈ 3.43
        sensed = [
            {"date": "2025-03-01", "systole_costs": [0.1, 0.2, 10.0],
             "systole_count": 3, "saturated_count": 0, "apnea_window": 1.0,
             "daily_budget": None, "estimated_burn": None},
        ]
        result = sub.candidates(sensed)
        vol = [c for c in result if c["issue"] == "volatility"]
        assert len(vol) == 1

    def test_detects_overproduction(self, tmp_path: Path):
        import time
        pulse_dir = tmp_path / "pulse"
        pulse_dir.mkdir()

        # Create files with timestamps on different "days"
        # Files are grouped by mtime date, need >= 2 days with >20 files each
        now = time.time()
        day_seconds = 86400

        # Create 25 files for "today"
        for i in range(25):
            p = pulse_dir / f"day1_file{i}.md"
            p.touch()

        # Manually set older mtimes for "yesterday" files
        for i in range(25):
            p = pulse_dir / f"day2_file{i}.md"
            p.touch()
            # Set mtime to 1 day ago
            os.utime(p, (now - day_seconds, now - day_seconds))

        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=pulse_dir,
        )
        sensed = [
            {"date": "2025-03-01", "systole_count": 5, "saturated_count": 0,
             "apnea_window": 1.0, "daily_budget": None, "estimated_burn": None},
            {"date": "2025-03-02", "systole_count": 5, "saturated_count": 0,
             "apnea_window": 1.0, "daily_budget": None, "estimated_burn": None},
        ]
        result = sub.candidates(sensed)
        overprod = [c for c in result if c["issue"] == "overproduction"]
        assert len(overprod) == 1


class TestAct:
    def test_applies_overburn_fix(self, tmp_path: Path):
        config = tmp_path / "vasomotor.conf"
        config.write_text('{"basal_rate": 0.5}')

        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=config,
            pulse_dir=tmp_path / "pulse",
        )
        candidate = {"issue": "overburn", "severity": "high", "count": 3}
        result = sub.act(candidate)

        assert "APPLIED" in result
        assert "basal_rate" in result
        conf = json.loads(config.read_text())
        assert conf["basal_rate"] == 0.45  # 0.5 * 0.9

    def test_applies_saturation_fix(self, tmp_path: Path):
        config = tmp_path / "vasomotor.conf"
        config.write_text('{"saturation_penalty": 1.5}')

        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=config,
            pulse_dir=tmp_path / "pulse",
        )
        candidate = {"issue": "saturation", "severity": "high", "count": 3}
        result = sub.act(candidate)

        assert "APPLIED" in result
        conf = json.loads(config.read_text())
        assert conf["saturation_penalty"] == 2.0  # 1.5 + 0.5

    def test_applies_starvation_fix(self, tmp_path: Path):
        config = tmp_path / "vasomotor.conf"
        config.write_text('{"basal_rate": 0.4}')

        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=config,
            pulse_dir=tmp_path / "pulse",
        )
        candidate = {"issue": "starvation", "severity": "medium", "count": 3}
        result = sub.act(candidate)

        assert "APPLIED" in result
        conf = json.loads(config.read_text())
        assert conf["basal_rate"] == 0.44  # 0.4 * 1.1

    def test_applies_overproduction_fix(self, tmp_path: Path):
        config = tmp_path / "vasomotor.conf"
        config.write_text('{"basal_rate": 0.5}')

        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=config,
            pulse_dir=tmp_path / "pulse",
        )
        candidate = {"issue": "overproduction", "severity": "high", "count": 3}
        result = sub.act(candidate)

        assert "APPLIED" in result
        conf = json.loads(config.read_text())
        # basal_rate 0.5 * 0.85 = 0.425, rounded to 0.42
        assert conf["basal_rate"] == 0.42

    def test_medium_overburn_proposes_only(self, tmp_path: Path):
        config = tmp_path / "vasomotor.conf"
        config.write_text('{}')

        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=config,
            pulse_dir=tmp_path / "pulse",
        )
        candidate = {"issue": "overburn", "severity": "medium", "count": 1}
        result = sub.act(candidate)

        assert "APPLIED" not in result
        assert "reduce" in result.lower()

    def test_proposes_for_unknown_issue(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        candidate = {"issue": "unknown_issue", "severity": "low", "count": 1}
        result = sub.act(candidate)

        assert "review" in result.lower()

    def test_records_efference_copy(self, tmp_path: Path):
        config = tmp_path / "vasomotor.conf"
        config.write_text('{"basal_rate": 0.5}')

        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=config,
            pulse_dir=tmp_path / "pulse",
        )
        candidate = {"issue": "overburn", "severity": "high", "count": 3}
        sub.act(candidate)

        conf = json.loads(config.read_text())
        assert "_efference_copy" in conf
        assert len(conf["_efference_copy"]) == 1
        assert conf["_efference_copy"][0]["issue"] == "overburn"

    def test_handles_missing_config(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "nonexistent.conf",
            pulse_dir=tmp_path / "pulse",
        )
        candidate = {"issue": "overburn", "severity": "high", "count": 3}
        result = sub.act(candidate)

        # Should still apply with default values
        assert "APPLIED" in result


class TestReport:
    def test_empty_report(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        report = sub.report([], [])
        assert "0 day(s) sensed" in report

    def test_report_with_data(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        sensed = [
            {"date": "2025-03-01", "systole_count": 10, "saturated_count": 2,
             "daily_budget": 10.0, "estimated_burn": 8.0, "rq": 1.5, "apnea_window": 1.5},
        ]
        report = sub.report(sensed, [])
        assert "1 day(s) sensed" in report
        assert "Total systoles: 10" in report
        assert "2025-03-01" in report

    def test_report_with_actions(self, tmp_path: Path):
        sub = VasomotorSubstrate(
            events_path=tmp_path / "events.jsonl",
            config_path=tmp_path / "config.conf",
            pulse_dir=tmp_path / "pulse",
        )
        sensed = [{"date": "2025-03-01", "systole_count": 5, "saturated_count": 0,
                   "daily_budget": None, "estimated_burn": None, "rq": None, "apnea_window": 1.0}]
        acted = ["[high] APPLIED: basal_rate 0.5 -> 0.45"]
        report = sub.report(sensed, acted)
        assert "Issues" in report
        assert "basal_rate" in report
