"""Tests for metabolon.metabolism.substrates.vasomotor."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from metabolon.metabolism.substrates.vasomotor import VasomotorSubstrate, _parse_ts

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(event: str, ts: datetime, **extra) -> str:
    """Build a single JSONL line."""
    obj = {"ts": ts.isoformat(), "event": event}
    obj.update(extra)
    return json.dumps(obj)


def _write_events(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def _default_substrate(tmp_path: Path) -> VasomotorSubstrate:
    return VasomotorSubstrate(
        events_path=tmp_path / "events.jsonl",
        state_path=tmp_path / "state.json",
        config_path=tmp_path / "vasomotor.conf",
        pulse_dir=tmp_path / "pulse",
    )


# ---------------------------------------------------------------------------
# _parse_ts
# ---------------------------------------------------------------------------


class TestParseTs:
    def test_microsecond_format(self):
        ts = _parse_ts("2025-06-15T10:30:00.123456")
        assert ts.year == 2025
        assert ts.month == 6
        assert ts.tzinfo is not None

    def test_second_format(self):
        ts = _parse_ts("2025-06-15T10:30:00")
        assert ts.minute == 30
        assert ts.tzinfo is not None

    def test_iso_with_timezone(self):
        ts = _parse_ts("2025-06-15T10:30:00+05:30")
        assert ts.hour == 10


# ---------------------------------------------------------------------------
# sense
# ---------------------------------------------------------------------------


class TestSense:
    def test_missing_events_file_returns_empty(self, tmp_path):
        sub = _default_substrate(tmp_path)
        assert sub.sense() == []

    def test_empty_file_returns_empty(self, tmp_path):
        sub = _default_substrate(tmp_path)
        _write_events(sub.events_path, [])
        assert sub.sense() == []

    def test_corrupted_lines_skipped(self, tmp_path):
        sub = _default_substrate(tmp_path)
        now = datetime.now(UTC)
        lines = [
            "not json",
            "",
            _make_event("systole_start", now),
        ]
        _write_events(sub.events_path, lines)
        result = sub.sense()
        assert len(result) == 1
        assert result[0]["systole_count"] == 1

    def test_old_events_filtered_by_days(self, tmp_path):
        sub = _default_substrate(tmp_path)
        now = datetime.now(UTC)
        old = now - timedelta(days=60)
        _write_events(
            sub.events_path,
            [
                _make_event("systole_start", old),
                _make_event("systole_start", now),
            ],
        )
        result = sub.sense(days=30)
        assert len(result) == 1
        assert result[0]["systole_count"] == 1

    def test_daily_summary_fields(self, tmp_path):
        sub = _default_substrate(tmp_path)
        now = datetime.now(UTC)
        lines = [
            _make_event("systole_start", now),
            _make_event("saturation_detected", now + timedelta(minutes=1)),
            _make_event("cost_measured", now + timedelta(minutes=2), cost=0.42),
            _make_event("systole_usage", now + timedelta(minutes=3), weekly_delta=2.5),
            _make_event("systole_yield", now + timedelta(minutes=4), secretion_count=7),
            _make_event("systole_end", now + timedelta(minutes=10), exit_code=0, elapsed_s=600),
            _make_event("circuit_breaker", now + timedelta(minutes=12)),
        ]
        _write_events(sub.events_path, lines)
        result = sub.sense()
        assert len(result) == 1
        d = result[0]
        assert d["systole_count"] == 1
        assert d["saturated_count"] == 1
        assert d["cost_samples"] == [0.42]
        assert d["systole_costs"] == [2.5]
        assert d["systole_yields"] == [7]
        assert d["rq"] == round(7 / 2.5, 2)
        assert d["successful_systoles"] == 1
        assert d["failed_systoles"] == 0
        assert d["avg_systole_duration"] == 600.0
        assert d["circuit_breakers"] == 1

    def test_apnea_window_computed(self, tmp_path):
        sub = _default_substrate(tmp_path)
        base = datetime.now(UTC) - timedelta(minutes=10)
        lines = [
            _make_event("systole_start", base),
            _make_event("systole_end", base + timedelta(hours=5, minutes=1)),
        ]
        _write_events(sub.events_path, lines)
        # Events 5h apart but both within the 30-day window and same date
        result = sub.sense()
        total_events = sum(d["event_count"] for d in result)
        assert total_events == 2
        # Find the day that has both events
        combined = [d for d in result if d["event_count"] == 2]
        if combined:
            assert combined[0]["apnea_window"] >= 5.0

    def test_budget_climb_rate(self, tmp_path):
        sub = _default_substrate(tmp_path)
        base = datetime.now(UTC) - timedelta(minutes=30)
        lines = [
            _make_event("budget_raw", base, weekly=10.0),
            _make_event("budget_raw", base + timedelta(minutes=12), weekly=20.0),
        ]
        _write_events(sub.events_path, lines)
        result = sub.sense()
        # Both events are on the same day and within 30 days
        assert len(result) == 1
        # (20 - 10) / 0.2 hours = 50
        assert result[0]["budget_climb_rate"] == pytest.approx(50.0)

    def test_failed_systole_counted(self, tmp_path):
        sub = _default_substrate(tmp_path)
        now = datetime.now(UTC)
        _write_events(
            sub.events_path,
            [
                _make_event("systole_end", now, exit_code=1),
            ],
        )
        result = sub.sense()
        assert result[0]["failed_systoles"] == 1
        assert result[0]["successful_systoles"] == 0

    def test_pacing_check_extracts_budget(self, tmp_path):
        sub = _default_substrate(tmp_path)
        now = datetime.now(UTC)
        _write_events(
            sub.events_path,
            [
                _make_event("pacing_check", now, daily_budget=15, estimated_burn=10),
            ],
        )
        result = sub.sense()
        assert result[0]["daily_budget"] == 15
        assert result[0]["estimated_burn"] == 10


# ---------------------------------------------------------------------------
# candidates
# ---------------------------------------------------------------------------


class TestCandidates:
    def test_empty_sensed_returns_empty(self, tmp_path):
        sub = _default_substrate(tmp_path)
        assert sub.candidates([]) == []

    def test_overburn_detected(self, tmp_path):
        sub = _default_substrate(tmp_path)
        days = [
            {
                "date": f"2025-06-{i:02d}",
                "systole_count": 5,
                "saturated_count": 0,
                "daily_budget": 10,
                "estimated_burn": 15,
                "apnea_window": 1.0,
                "systole_costs": [],
                "systole_yields": [],
                "failed_systoles": 0,
                "successful_systoles": 5,
                "circuit_breakers": 0,
            }
            for i in range(10, 13)
        ]
        result = sub.candidates(days)
        issues = [d["issue"] for d in result]
        assert "overburn" in issues
        overburn = next(d for d in result if d["issue"] == "overburn")
        assert overburn["count"] == 3
        assert overburn["severity"] == "high"

    def test_saturation_detected(self, tmp_path):
        sub = _default_substrate(tmp_path)
        days = [
            {
                "date": "2025-06-10",
                "systole_count": 10,
                "saturated_count": 5,
                "daily_budget": None,
                "estimated_burn": None,
                "apnea_window": 0.5,
                "systole_costs": [],
                "systole_yields": [],
                "failed_systoles": 0,
                "successful_systoles": 10,
                "circuit_breakers": 0,
            }
        ]
        result = sub.candidates(days)
        issues = [d["issue"] for d in result]
        assert "saturation" in issues

    def test_silence_detected(self, tmp_path):
        sub = _default_substrate(tmp_path)
        days = [
            {
                "date": "2025-06-10",
                "systole_count": 2,
                "saturated_count": 0,
                "daily_budget": 10,
                "estimated_burn": 5,
                "apnea_window": 5.5,
                "systole_costs": [],
                "systole_yields": [],
                "failed_systoles": 0,
                "successful_systoles": 2,
                "circuit_breakers": 0,
            }
        ]
        result = sub.candidates(days)
        issues = [d["issue"] for d in result]
        assert "silence" in issues

    def test_volatility_detected(self, tmp_path):
        sub = _default_substrate(tmp_path)
        days = [
            {
                "date": "2025-06-10",
                "systole_count": 1,
                "saturated_count": 0,
                "daily_budget": 100,
                "estimated_burn": 50,
                "apnea_window": 0.5,
                "systole_costs": [1.0],
                "systole_yields": [],
                "failed_systoles": 0,
                "successful_systoles": 1,
                "circuit_breakers": 0,
            },
            {
                "date": "2025-06-11",
                "systole_count": 1,
                "saturated_count": 0,
                "daily_budget": 100,
                "estimated_burn": 50,
                "apnea_window": 0.5,
                "systole_costs": [50.0],
                "systole_yields": [],
                "failed_systoles": 0,
                "successful_systoles": 1,
                "circuit_breakers": 0,
            },
            {
                "date": "2025-06-12",
                "systole_count": 1,
                "saturated_count": 0,
                "daily_budget": 100,
                "estimated_burn": 50,
                "apnea_window": 0.5,
                "systole_costs": [1.0],
                "systole_yields": [],
                "failed_systoles": 0,
                "successful_systoles": 1,
                "circuit_breakers": 0,
            },
        ]
        result = sub.candidates(days)
        issues = [d["issue"] for d in result]
        assert "volatility" in issues

    def test_failure_ratio_detected(self, tmp_path):
        sub = _default_substrate(tmp_path)
        days = [
            {
                "date": "2025-06-10",
                "systole_count": 5,
                "saturated_count": 0,
                "daily_budget": 10,
                "estimated_burn": 5,
                "apnea_window": 1.0,
                "systole_costs": [],
                "systole_yields": [],
                "failed_systoles": 4,
                "successful_systoles": 1,
                "circuit_breakers": 0,
            }
        ]
        result = sub.candidates(days)
        issues = [d["issue"] for d in result]
        assert "failure_ratio" in issues

    def test_circuit_breaker_detected(self, tmp_path):
        sub = _default_substrate(tmp_path)
        days = [
            {
                "date": "2025-06-10",
                "systole_count": 2,
                "saturated_count": 0,
                "daily_budget": 10,
                "estimated_burn": 5,
                "apnea_window": 0.5,
                "systole_costs": [],
                "systole_yields": [],
                "failed_systoles": 0,
                "successful_systoles": 2,
                "circuit_breakers": 3,
            }
        ]
        result = sub.candidates(days)
        issues = [d["issue"] for d in result]
        assert "circuit_breaker" in issues

    def test_reafference_confirmed(self, tmp_path):
        sub = _default_substrate(tmp_path)
        # Config has a prior issue that no longer appears in sensed data
        conf = {"_efference_copy": [{"issue": "overburn", "ts": "2025-06-01T00:00:00"}]}
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        sub.config_path.write_text(json.dumps(conf))
        days = [
            {
                "date": "2025-06-10",
                "systole_count": 2,
                "saturated_count": 0,
                "daily_budget": 10,
                "estimated_burn": 5,
                "apnea_window": 0.5,
                "systole_costs": [],
                "systole_yields": [],
                "failed_systoles": 0,
                "successful_systoles": 2,
                "circuit_breakers": 0,
            }
        ]
        result = sub.candidates(days)
        issues = [d["issue"] for d in result]
        assert "reafference_confirmed" in issues


# ---------------------------------------------------------------------------
# act
# ---------------------------------------------------------------------------


class TestAct:
    def test_overburn_high_reduces_basal_rate(self, tmp_path):
        sub = _default_substrate(tmp_path)
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        sub.config_path.write_text(json.dumps({"basal_rate": 0.5}))
        result = sub.act(
            {
                "issue": "overburn",
                "severity": "high",
                "count": 3,
            }
        )
        assert "APPLIED" in result
        conf = json.loads(sub.config_path.read_text())
        assert conf["basal_rate"] == 0.45

    def test_overburn_high_floor(self, tmp_path):
        sub = _default_substrate(tmp_path)
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        sub.config_path.write_text(json.dumps({"basal_rate": 0.11}))
        sub.act({"issue": "overburn", "severity": "high", "count": 3})
        conf = json.loads(sub.config_path.read_text())
        assert conf["basal_rate"] >= 0.10

    def test_saturation_high_increases_penalty(self, tmp_path):
        sub = _default_substrate(tmp_path)
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        sub.config_path.write_text(json.dumps({"saturation_penalty": 1.5}))
        result = sub.act(
            {
                "issue": "saturation",
                "severity": "high",
                "count": 3,
            }
        )
        assert "APPLIED" in result
        conf = json.loads(sub.config_path.read_text())
        assert conf["saturation_penalty"] == 2.0

    def test_saturation_high_capped(self, tmp_path):
        sub = _default_substrate(tmp_path)
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        sub.config_path.write_text(json.dumps({"saturation_penalty": 2.8}))
        sub.act({"issue": "saturation", "severity": "high", "count": 3})
        conf = json.loads(sub.config_path.read_text())
        assert conf["saturation_penalty"] <= 3.0

    def test_starvation_increases_basal_rate(self, tmp_path):
        sub = _default_substrate(tmp_path)
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        sub.config_path.write_text(json.dumps({"basal_rate": 0.4}))
        result = sub.act(
            {
                "issue": "starvation",
                "severity": "medium",
                "count": 3,
            }
        )
        assert "APPLIED" in result
        conf = json.loads(sub.config_path.read_text())
        assert conf["basal_rate"] > 0.4

    def test_starvation_capped(self, tmp_path):
        sub = _default_substrate(tmp_path)
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        sub.config_path.write_text(json.dumps({"basal_rate": 0.55}))
        sub.act({"issue": "starvation", "severity": "medium", "count": 3})
        conf = json.loads(sub.config_path.read_text())
        assert conf["basal_rate"] <= 0.6

    def test_volatility_is_report_only(self, tmp_path):
        sub = _default_substrate(tmp_path)
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        sub.config_path.write_text(json.dumps({}))
        result = sub.act({"issue": "volatility", "severity": "medium", "count": 1})
        assert "APPLIED" not in result
        assert "variance" in result

    def test_efference_copy_recorded(self, tmp_path):
        sub = _default_substrate(tmp_path)
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        sub.config_path.write_text(json.dumps({"basal_rate": 0.5}))
        sub.act({"issue": "overburn", "severity": "high", "count": 3})
        conf = json.loads(sub.config_path.read_text())
        history = conf["_efference_copy"]
        assert len(history) == 1
        assert history[0]["issue"] == "overburn"

    def test_efference_copy_truncated_to_10(self, tmp_path):
        sub = _default_substrate(tmp_path)
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        existing = [{"ts": "t", "issue": "overburn", "action": "a"}] * 9
        sub.config_path.write_text(json.dumps({"basal_rate": 0.5, "_efference_copy": existing}))
        sub.act({"issue": "overburn", "severity": "high", "count": 3})
        conf = json.loads(sub.config_path.read_text())
        assert len(conf["_efference_copy"]) == 10

    def test_overproduction_high_throttles(self, tmp_path):
        sub = _default_substrate(tmp_path)
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        sub.config_path.write_text(json.dumps({"basal_rate": 0.5}))
        result = sub.act(
            {
                "issue": "overproduction",
                "severity": "high",
                "count": 3,
            }
        )
        assert "APPLIED" in result
        conf = json.loads(sub.config_path.read_text())
        assert conf["basal_rate"] < 0.5

    def test_unknown_issue_returns_review(self, tmp_path):
        sub = _default_substrate(tmp_path)
        sub.config_path.parent.mkdir(parents=True, exist_ok=True)
        sub.config_path.write_text(json.dumps({}))
        result = sub.act({"issue": "made_up", "severity": "low", "count": 1})
        assert "review: made_up" in result


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


class TestReport:
    def test_empty_sensed(self, tmp_path):
        sub = _default_substrate(tmp_path)
        r = sub.report([], [])
        assert "0 day(s) sensed" in r
        assert "0 issue(s)" in r

    def test_report_with_data(self, tmp_path):
        sub = _default_substrate(tmp_path)
        days = [
            {
                "date": "2025-06-10",
                "systole_count": 5,
                "saturated_count": 1,
                "daily_budget": 10.0,
                "estimated_burn": 8,
                "apnea_window": 1.2,
                "systole_costs": [2.0],
                "systole_yields": [5],
                "rq": 2.5,
                "failed_systoles": 0,
                "successful_systoles": 5,
                "circuit_breakers": 0,
            },
        ]
        r = sub.report(days, ["[high] something"])
        assert "Total systoles: 5" in r
        assert "RQ" in r
        assert "something" in r

    def test_report_no_issues(self, tmp_path):
        sub = _default_substrate(tmp_path)
        days = [
            {
                "date": "2025-06-10",
                "systole_count": 3,
                "saturated_count": 0,
                "daily_budget": None,
                "estimated_burn": None,
                "apnea_window": 0.5,
                "systole_costs": [],
                "systole_yields": [],
                "failed_systoles": 0,
                "successful_systoles": 3,
                "circuit_breakers": 0,
            },
        ]
        r = sub.report(days, [])
        assert "No pacing issues detected" in r


# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------


class TestDefaults:
    def test_default_name(self):
        sub = VasomotorSubstrate()
        assert sub.name == "respiration"

    def test_default_paths_are_set(self):
        sub = VasomotorSubstrate()
        assert sub.events_path.name == "vivesca-events.jsonl"
        assert sub.state_path.name == "respiration-daily.json"
        assert sub.config_path.name == "vasomotor.conf"
        assert sub.pulse_dir.name == "pulse"
