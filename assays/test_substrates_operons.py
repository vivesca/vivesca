"""Tests for metabolon.metabolism.substrates.operon_monitor."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from metabolon.metabolism.substrates.operon_monitor import (
    _CADENCE_KEYWORDS,
    _DEFAULT_STALENESS_DAYS,
    _infer_cadence,
    OperonSubstrate,
)
from metabolon.operons import Operon


# ── Fixtures ────────────────────────────────────────────────────

TWO_DAYS_AGO = datetime.now(UTC) - timedelta(days=2)
TWENTY_DAYS_AGO = datetime.now(UTC) - timedelta(days=20)

DAILY_OP = Operon(
    reaction="triage",
    product="Incoming routed",
    substrates=["daily period", "inbox accumulation"],
    enzymes=["triage-filter", "triage-dispatch"],
    expressed=True,
)
MONTHLY_OP = Operon(
    reaction="homeostasis",
    product="Financial audit",
    substrates=["monthly cycle", "explicit request"],
    enzymes=["homeostasis", "fiscus"],
    expressed=True,
)
UNEXPRESSED_OP = Operon(
    reaction="dormant",
    product="Sleeping",
    substrates=["daily period"],
    enzymes=["zzz"],
    expressed=False,
)
NO_KEYWORD_OP = Operon(
    reaction="mystery",
    product="Unknown cadence",
    substrates=["no hint here"],
    enzymes=["mystery-enzyme"],
    expressed=True,
)


def _make_collector(tools_with_ts: dict[str, datetime]) -> MagicMock:
    """Build a fake SensorySystem whose recall_since returns Stimulus-like objects."""
    collector = MagicMock()
    signals = []
    for tool, ts in tools_with_ts.items():
        s = MagicMock()
        s.tool = tool
        s.ts = ts
        signals.append(s)
    collector.recall_since.return_value = signals
    return collector


# ── Tests ───────────────────────────────────────────────────────


class TestInferCadence:
    def test_daily_keyword(self):
        assert _infer_cadence(DAILY_OP) == _CADENCE_KEYWORDS["daily"]

    def test_monthly_keyword(self):
        assert _infer_cadence(MONTHLY_OP) == _CADENCE_KEYWORDS["monthly"]

    def test_no_keyword_returns_default(self):
        assert _infer_cadence(NO_KEYWORD_OP) == _DEFAULT_STALENESS_DAYS


@patch("metabolon.metabolism.substrates.operon_monitor.OPERONS", [DAILY_OP, MONTHLY_OP])
class TestSense:
    def test_all_stale_when_no_signals(self):
        collector = _make_collector({})
        sub = OperonSubstrate(collector)
        sensed = sub.sense(days=30)
        assert len(sensed) == 2
        assert all(e["stale"] is True for e in sensed)
        assert all(e["days_since"] is None for e in sensed)
        assert all(e["last_fired"] is None for e in sensed)

    def test_recent_signal_marks_healthy(self):
        half_day_ago = datetime.now(UTC) - timedelta(hours=12)
        collector = _make_collector({"triage-filter": half_day_ago})
        sub = OperonSubstrate(collector)
        sensed = sub.sense(days=30)
        triage = next(e for e in sensed if e["reaction"] == "triage")
        assert triage["stale"] is False
        assert triage["fired_enzyme"] == "triage-filter"
        assert triage["days_since"] is not None
        assert triage["days_since"] < 1

    def test_old_signal_marks_stale(self):
        forty_days_ago = datetime.now(UTC) - timedelta(days=40)
        collector = _make_collector({"homeostasis": forty_days_ago})
        sub = OperonSubstrate(collector)
        sensed = sub.sense(days=60)
        homeo = next(e for e in sensed if e["reaction"] == "homeostasis")
        assert homeo["stale"] is True
        assert homeo["days_since"] > _CADENCE_KEYWORDS["monthly"]


@patch("metabolon.metabolism.substrates.operon_monitor.OPERONS", [DAILY_OP, UNEXPRESSED_OP])
class TestUnexpressedFiltered:
    def test_unexpressed_operons_excluded(self):
        collector = _make_collector({})
        sub = OperonSubstrate(collector)
        sensed = sub.sense(days=30)
        reactions = [e["reaction"] for e in sensed]
        assert "triage" in reactions
        assert "dormant" not in reactions


class TestCandidates:
    def test_filters_stale_only(self):
        sensed = [
            {"reaction": "a", "stale": True},
            {"reaction": "b", "stale": False},
            {"reaction": "c", "stale": True},
        ]
        sub = OperonSubstrate.__new__(OperonSubstrate)
        result = sub.candidates(sensed)
        assert len(result) == 2
        assert all(e["stale"] for e in result)


class TestAct:
    def test_stale_message(self):
        sub = OperonSubstrate.__new__(OperonSubstrate)
        msg = sub.act({"reaction": "triage", "days_since": 5.0, "cadence_days": 2})
        assert "stale" in msg
        assert "triage" in msg
        assert "5d" in msg
        assert "cadence: 2d" in msg

    def test_dormant_message(self):
        sub = OperonSubstrate.__new__(OperonSubstrate)
        msg = sub.act({"reaction": "triage", "days_since": None, "cadence_days": 2})
        assert "dormant" in msg
        assert "triage" in msg


class TestReport:
    def test_report_includes_healthy_stale_actions(self):
        sub = OperonSubstrate.__new__(OperonSubstrate)
        sensed = [
            {
                "reaction": "triage",
                "product": "routed",
                "stale": False,
                "days_since": 1.0,
                "fired_enzyme": "triage-filter",
                "cadence_days": 2,
            },
            {
                "reaction": "homeostasis",
                "product": "audit",
                "stale": True,
                "days_since": 40.0,
                "fired_enzyme": "fiscus",
                "cadence_days": 35,
            },
        ]
        acted = ["stale: homeostasis — 40d since last fire (cadence: 35d)"]
        report = sub.report(sensed, acted)
        assert "Healthy" in report
        assert "Stale" in report
        assert "Actions" in report
        assert "triage" in report
        assert "homeostasis" in report

    def test_report_never_fired_shows_never(self):
        sub = OperonSubstrate.__new__(OperonSubstrate)
        sensed = [
            {
                "reaction": "mystery",
                "product": "unknown",
                "stale": True,
                "days_since": None,
                "fired_enzyme": None,
                "cadence_days": 14,
            },
        ]
        report = sub.report(sensed, [])
        assert "never fired" in report
