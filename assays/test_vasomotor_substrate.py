"""Tests for VasomotorSubstrate — pacing system metabolism.

Tests the full sense -> candidates -> act -> report cycle using
fixture JSONL events. No real filesystem state required.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from metabolon.metabolism.substrate import Substrate
from metabolon.metabolism.substrates.vasomotor import VasomotorSubstrate


@pytest.fixture(autouse=True)
def _isolated_respiration(tmp_path, monkeypatch):
    """Ensure VasomotorSubstrate never reads real filesystem state."""
    _orig_init = VasomotorSubstrate.__init__

    def _patched_init(self, events_path=None, state_path=None, config_path=None, pulse_dir=None):
        _orig_init(
            self,
            events_path=events_path,
            state_path=state_path or (tmp_path / "state.json"),
            config_path=config_path or (tmp_path / "conf.json"),
            pulse_dir=pulse_dir or (tmp_path / "pulse"),
        )

    monkeypatch.setattr(VasomotorSubstrate, "__init__", _patched_init)


# ── Helpers ──────────────────────────────────────────────────────────


# Fixed base time: noon UTC today. Using noon (not now()) guarantees that
# events with the same days_ago but different hours_ago (up to ±11h) always
# land on the same calendar day, regardless of when the test suite runs.
_BASE_TIME = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)


def _ts(days_ago: int = 0, hours_ago: int = 0) -> str:
    """Generate an ISO timestamp relative to a fixed noon-UTC base time."""
    dt = _BASE_TIME - timedelta(days=days_ago, hours=hours_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")


def _event(event_type: str, days_ago: int = 0, hours_ago: int = 0, **kwargs) -> dict:
    """Build an event dict."""
    e = {"ts": _ts(days_ago, hours_ago), "event": event_type}
    e.update(kwargs)
    return e


def _write_events(path, events: list[dict]):
    """Write events as JSONL to a file."""
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")


# ── Protocol conformance ────────────────────────────────────────────


class TestProtocol:
    def test_is_substrate(self, tmp_path):
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        assert isinstance(substrate, Substrate)

    def test_has_name(self):
        assert VasomotorSubstrate.name == "respiration"


# ── Sense ────────────────────────────────────────────────────────────


class TestSense:
    def test_missing_events_file(self, tmp_path):
        """Missing event log returns empty."""
        substrate = VasomotorSubstrate(events_path=tmp_path / "nonexistent.jsonl")
        assert substrate.sense() == []

    def test_empty_events_file(self, tmp_path):
        """Empty event log returns empty."""
        events_path = tmp_path / "events.jsonl"
        events_path.write_text("")
        substrate = VasomotorSubstrate(events_path=events_path)
        assert substrate.sense() == []

    def test_parses_systole_starts(self, tmp_path):
        """Systole starts are counted per day."""
        events_path = tmp_path / "events.jsonl"
        events = [
            _event("systole_start", days_ago=1, hours_ago=0),
            _event("systole_start", days_ago=1, hours_ago=1),
            _event("systole_start", days_ago=1, hours_ago=2),
        ]
        _write_events(events_path, events)

        substrate = VasomotorSubstrate(events_path=events_path)
        sensed = substrate.sense(days=7)

        assert len(sensed) == 1
        assert sensed[0]["systole_count"] == 3

    def test_parses_saturation(self, tmp_path):
        """Saturation events are counted per day."""
        events_path = tmp_path / "events.jsonl"
        events = [
            _event("systole_start", days_ago=1),
            _event("saturation_detected", days_ago=1, wave=1, consecutive=1),
            _event("systole_start", days_ago=1, hours_ago=1),
            _event("saturation_detected", days_ago=1, hours_ago=1, wave=2, consecutive=2),
        ]
        _write_events(events_path, events)

        substrate = VasomotorSubstrate(events_path=events_path)
        sensed = substrate.sense(days=7)

        assert sensed[0]["saturated_count"] == 2

    def test_parses_pacing_check(self, tmp_path):
        """Daily budget and burn extracted from pacing_check events."""
        events_path = tmp_path / "events.jsonl"
        events = [
            _event(
                "pacing_check",
                days_ago=1,
                weekly=30.0,
                remaining_budget=55.0,
                daily_budget=4.8,
                systoles_today=6,
                estimated_burn=6,
            ),
        ]
        _write_events(events_path, events)

        substrate = VasomotorSubstrate(events_path=events_path)
        sensed = substrate.sense(days=7)

        assert sensed[0]["daily_budget"] == 4.8
        assert sensed[0]["estimated_burn"] == 6

    def test_parses_cost_measured(self, tmp_path):
        """Cost samples extracted from cost_measured events."""
        events_path = tmp_path / "events.jsonl"
        events = [
            _event(
                "cost_measured",
                days_ago=1,
                cost=0.571,
                method="historical_all",
                samples=21,
            ),
            _event(
                "cost_measured",
                days_ago=1,
                hours_ago=1,
                cost=1.0,
                method="historical",
                samples=12,
            ),
        ]
        _write_events(events_path, events)

        substrate = VasomotorSubstrate(events_path=events_path)
        sensed = substrate.sense(days=7)

        assert len(sensed[0]["cost_samples"]) == 2
        assert 0.571 in sensed[0]["cost_samples"]

    def test_parses_systole_usage(self, tmp_path):
        """Systole cost deltas extracted from systole_usage events."""
        events_path = tmp_path / "events.jsonl"
        events = [
            _event("systole_usage", days_ago=1, wave=1, weekly_delta=1.0),
            _event("systole_usage", days_ago=1, hours_ago=1, wave=2, weekly_delta=2.0),
        ]
        _write_events(events_path, events)

        substrate = VasomotorSubstrate(events_path=events_path)
        sensed = substrate.sense(days=7)

        assert sensed[0]["systole_costs"] == [1.0, 2.0]

    def test_respects_days_window(self, tmp_path):
        """Events outside the window are excluded."""
        events_path = tmp_path / "events.jsonl"
        events = [
            _event("systole_start", days_ago=1),  # inside 7-day window
            _event("systole_start", days_ago=10),  # outside
        ]
        _write_events(events_path, events)

        substrate = VasomotorSubstrate(events_path=events_path)
        sensed = substrate.sense(days=7)

        assert len(sensed) == 1  # only the recent day

    def test_computes_max_gap(self, tmp_path):
        """Max gap between events is computed per day."""
        events_path = tmp_path / "events.jsonl"
        # Events 5 hours apart
        events = [
            _event("systole_start", days_ago=1, hours_ago=0),
            _event("systole_end", days_ago=1, hours_ago=5),
        ]
        _write_events(events_path, events)

        substrate = VasomotorSubstrate(events_path=events_path)
        sensed = substrate.sense(days=7)

        assert sensed[0]["apnea_window"] >= 4.9

    def test_handles_malformed_lines(self, tmp_path):
        """Malformed JSONL lines are skipped gracefully."""
        events_path = tmp_path / "events.jsonl"
        events_path.write_text(
            '{"ts": "2026-03-20T10:00:00.000000", "event": "systole_start"}\n'
            "not valid json\n"
            '{"ts": "2026-03-20T11:00:00.000000", "event": "systole_start"}\n'
        )

        substrate = VasomotorSubstrate(events_path=events_path)
        sensed = substrate.sense(days=30)

        assert len(sensed) == 1
        assert sensed[0]["systole_count"] == 2  # both valid lines parsed

    def test_multiple_days_sorted(self, tmp_path):
        """Sensed output is sorted by date."""
        events_path = tmp_path / "events.jsonl"
        events = [
            _event("systole_start", days_ago=3),
            _event("systole_start", days_ago=1),
            _event("systole_start", days_ago=2),
        ]
        _write_events(events_path, events)

        substrate = VasomotorSubstrate(events_path=events_path)
        sensed = substrate.sense(days=7)

        dates = [d["date"] for d in sensed]
        assert dates == sorted(dates)


# ── Candidates ───────────────────────────────────────────────────────


class TestCandidates:
    def test_empty_sensed(self, tmp_path):
        """No sensed data produces no candidates."""
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        assert substrate.candidates([]) == []

    def test_overburn_detection(self, tmp_path):
        """Days where burn > budget trigger overburn issue."""
        sensed = [
            {
                "date": "2026-03-20",
                "systole_count": 10,
                "saturated_count": 0,
                "daily_budget": 4.0,
                "estimated_burn": 8.0,
                "cost_samples": [],
                "systole_costs": [],
                "apnea_window": 1.0,
                "event_count": 20,
            },
        ]
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        issues = substrate.candidates(sensed)

        overburn = [i for i in issues if i["issue"] == "overburn"]
        assert len(overburn) == 1
        assert overburn[0]["count"] == 1

    def test_saturation_detection(self, tmp_path):
        """>30% systoles saturated triggers saturation issue."""
        sensed = [
            {
                "date": "2026-03-20",
                "systole_count": 10,
                "saturated_count": 5,
                "daily_budget": 10.0,
                "estimated_burn": 10.0,
                "cost_samples": [],
                "systole_costs": [],
                "apnea_window": 1.0,
                "event_count": 20,
            },
        ]
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        issues = substrate.candidates(sensed)

        saturation = [i for i in issues if i["issue"] == "saturation"]
        assert len(saturation) == 1
        assert "5/10" in saturation[0]["evidence"][0]

    def test_no_saturation_at_30_percent(self, tmp_path):
        """Exactly 30% saturated does NOT trigger (threshold is >30%)."""
        sensed = [
            {
                "date": "2026-03-20",
                "systole_count": 10,
                "saturated_count": 3,
                "daily_budget": 10.0,
                "estimated_burn": 10.0,
                "cost_samples": [],
                "systole_costs": [],
                "apnea_window": 1.0,
                "event_count": 20,
            },
        ]
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        issues = substrate.candidates(sensed)

        saturation = [i for i in issues if i["issue"] == "saturation"]
        assert len(saturation) == 0

    def test_starvation_detection(self, tmp_path):
        """<50% budget used triggers starvation issue."""
        sensed = [
            {
                "date": "2026-03-20",
                "systole_count": 2,
                "saturated_count": 0,
                "daily_budget": 10.0,
                "estimated_burn": 3.0,
                "cost_samples": [],
                "systole_costs": [],
                "apnea_window": 1.0,
                "event_count": 5,
            },
        ]
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        issues = substrate.candidates(sensed)

        starvation = [i for i in issues if i["issue"] == "starvation"]
        assert len(starvation) == 1

    def test_volatility_detection(self, tmp_path):
        """Cost stddev > mean triggers volatility issue."""
        sensed = [
            {
                "date": "2026-03-20",
                "systole_count": 5,
                "saturated_count": 0,
                "daily_budget": None,
                "estimated_burn": None,
                "cost_samples": [],
                "systole_costs": [0.1, 0.1, 0.1, 5.0, 5.0],
                "apnea_window": 1.0,
                "event_count": 10,
            },
        ]
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        issues = substrate.candidates(sensed)

        volatility = [i for i in issues if i["issue"] == "volatility"]
        assert len(volatility) == 1
        assert "stddev" in volatility[0]["evidence"][0]

    def test_no_volatility_with_stable_costs(self, tmp_path):
        """Stable costs do not trigger volatility."""
        sensed = [
            {
                "date": "2026-03-20",
                "systole_count": 5,
                "saturated_count": 0,
                "daily_budget": None,
                "estimated_burn": None,
                "cost_samples": [],
                "systole_costs": [1.0, 1.0, 1.0, 1.0, 1.0],
                "apnea_window": 1.0,
                "event_count": 10,
            },
        ]
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        issues = substrate.candidates(sensed)

        volatility = [i for i in issues if i["issue"] == "volatility"]
        assert len(volatility) == 0

    def test_silence_detection(self, tmp_path):
        """>4h gap triggers silence issue."""
        sensed = [
            {
                "date": "2026-03-20",
                "systole_count": 2,
                "saturated_count": 0,
                "daily_budget": None,
                "estimated_burn": None,
                "cost_samples": [],
                "systole_costs": [],
                "apnea_window": 6.5,
                "event_count": 3,
            },
        ]
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        issues = substrate.candidates(sensed)

        silence = [i for i in issues if i["issue"] == "silence"]
        assert len(silence) == 1
        assert "6.5h" in silence[0]["evidence"][0]

    def test_no_silence_under_4h(self, tmp_path):
        """Gaps under 4h do not trigger silence."""
        sensed = [
            {
                "date": "2026-03-20",
                "systole_count": 2,
                "saturated_count": 0,
                "daily_budget": None,
                "estimated_burn": None,
                "cost_samples": [],
                "systole_costs": [],
                "apnea_window": 3.5,
                "event_count": 3,
            },
        ]
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        issues = substrate.candidates(sensed)

        silence = [i for i in issues if i["issue"] == "silence"]
        assert len(silence) == 0

    def test_severity_escalation(self, tmp_path):
        """3+ days of overburn escalates severity to high."""
        sensed = [
            {
                "date": f"2026-03-{20 + i}",
                "systole_count": 10,
                "saturated_count": 0,
                "daily_budget": 4.0,
                "estimated_burn": 8.0,
                "cost_samples": [],
                "systole_costs": [],
                "apnea_window": 1.0,
                "event_count": 20,
            }
            for i in range(4)
        ]
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        issues = substrate.candidates(sensed)

        overburn = [i for i in issues if i["issue"] == "overburn"]
        assert overburn[0]["severity"] == "high"

    def test_healthy_system_no_issues(self, tmp_path):
        """Healthy pacing produces no candidates."""
        sensed = [
            {
                "date": "2026-03-20",
                "systole_count": 5,
                "saturated_count": 0,
                "daily_budget": 10.0,
                "estimated_burn": 7.0,
                "cost_samples": [1.0],
                "systole_costs": [1.0, 1.0, 1.0],
                "apnea_window": 2.0,
                "event_count": 15,
            },
        ]
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        issues = substrate.candidates(sensed)

        assert len(issues) == 0


# ── Act ──────────────────────────────────────────────────────────────


class TestAct:
    def test_overburn_proposal(self, tmp_path):
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        result = substrate.act(
            {"issue": "overburn", "severity": "high", "count": 3, "evidence": []}
        )
        assert "basal_rate" in result
        assert "APPLIED" in result

    def test_saturation_proposal(self, tmp_path):
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        result = substrate.act(
            {"issue": "saturation", "severity": "medium", "count": 2, "evidence": []}
        )
        assert "saturation penalty" in result

    def test_starvation_proposal(self, tmp_path):
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        result = substrate.act(
            {"issue": "starvation", "severity": "low", "count": 1, "evidence": []}
        )
        assert "increase dynamic_share" in result

    def test_volatility_proposal(self, tmp_path):
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        result = substrate.act(
            {"issue": "volatility", "severity": "medium", "count": 1, "evidence": []}
        )
        assert "variance" in result

    def test_silence_proposal(self, tmp_path):
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        result = substrate.act(
            {"issue": "silence", "severity": "high", "count": 5, "evidence": []}
        )
        assert "launchctl" in result


# ── Report ───────────────────────────────────────────────────────────


class TestReport:
    def test_report_empty(self, tmp_path):
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        report = substrate.report([], [])
        assert "Respiration substrate: 0 day(s) sensed" in report
        assert "0 issue(s) found" in report

    def test_report_with_data(self, tmp_path):
        sensed = [
            {
                "date": "2026-03-20",
                "systole_count": 5,
                "saturated_count": 1,
                "daily_budget": 4.8,
                "estimated_burn": 6,
                "cost_samples": [1.0],
                "systole_costs": [1.0],
                "apnea_window": 2.0,
                "event_count": 10,
            },
        ]
        acted = ["[high] reduce dynamic_share by 10% (3 day(s) over budget)"]

        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        report = substrate.report(sensed, acted)

        assert "Respiration substrate: 1 day(s) sensed" in report
        assert "Total systoles: 5" in report
        assert "Issues" in report
        assert "reduce dynamic_share" in report
        assert "1 issue(s) found" in report

    def test_report_healthy_shows_no_issues(self, tmp_path):
        sensed = [
            {
                "date": "2026-03-20",
                "systole_count": 5,
                "saturated_count": 0,
                "daily_budget": 10.0,
                "estimated_burn": 7.0,
                "cost_samples": [],
                "systole_costs": [],
                "apnea_window": 1.0,
                "event_count": 10,
            },
        ]
        substrate = VasomotorSubstrate(events_path=tmp_path / "e.jsonl")
        report = substrate.report(sensed, [])

        assert "No pacing issues detected" in report
        assert "0 issue(s) found" in report


# ── Full cycle ───────────────────────────────────────────────────────


class TestFullCycle:
    def test_end_to_end_with_overburn(self, tmp_path):
        """Full cycle from JSONL events through to report with overburn detection."""
        events_path = tmp_path / "events.jsonl"
        # Use the module-level noon-UTC base to avoid day-boundary issues
        base_ts = _BASE_TIME - timedelta(days=1)
        base_date = base_ts.strftime("%Y-%m-%d")
        events = []
        # 8 systole_starts on the same calendar day
        for h in range(8):
            ts = f"{base_date}T{10 + h:02d}:00:00.000000"
            events.append({"ts": ts, "event": "systole_start"})
        # pacing_check showing burn > budget on same day
        events.append(
            {
                "ts": f"{base_date}T18:00:00.000000",
                "event": "pacing_check",
                "daily_budget": 3.0,
                "estimated_burn": 8.0,
                "systoles_today": 8,
            }
        )
        _write_events(events_path, events)

        substrate = VasomotorSubstrate(events_path=events_path)
        sensed = substrate.sense(days=7)
        cands = substrate.candidates(sensed)
        acted = [substrate.act(c) for c in cands]
        report = substrate.report(sensed, acted)

        assert "Respiration substrate" in report
        assert any("reduce dynamic_share" in a for a in acted)

    def test_end_to_end_healthy(self, tmp_path):
        """Full cycle with a healthy system produces no issues."""
        events_path = tmp_path / "events.jsonl"
        events = [
            _event("systole_start", days_ago=1, hours_ago=0),
            _event("systole_end", days_ago=1, hours_ago=0, exit_code=0, elapsed_s=300),
            _event("systole_start", days_ago=1, hours_ago=1),
            _event("systole_end", days_ago=1, hours_ago=1, exit_code=0, elapsed_s=400),
            _event(
                "pacing_check",
                days_ago=1,
                daily_budget=10.0,
                estimated_burn=5.0,
                systoles_today=2,
            ),
            _event("systole_usage", days_ago=1, wave=1, weekly_delta=1.0),
            _event("systole_usage", days_ago=1, hours_ago=1, wave=2, weekly_delta=1.0),
        ]
        _write_events(events_path, events)

        substrate = VasomotorSubstrate(events_path=events_path)
        sensed = substrate.sense(days=7)
        cands = substrate.candidates(sensed)
        acted = [substrate.act(c) for c in cands]
        report = substrate.report(sensed, acted)

        assert "No pacing issues detected" in report
        assert "0 issue(s) found" in report
