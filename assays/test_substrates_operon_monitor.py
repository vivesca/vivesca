"""Tests for metabolon.metabolism.substrates.operon_monitor."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from metabolon.metabolism.signals import SensorySystem, Stimulus
from metabolon.metabolism.substrates.operon_monitor import (
    _DEFAULT_STALENESS_DAYS,
    OperonSubstrate,
    _infer_cadence,
)
from metabolon.operons import Operon

# ── helpers ────────────────────────────────────────────────────────


def _make_operon(
    reaction: str = "test_reaction",
    product: str = "test product",
    substrates: list[str] | None = None,
    enzymes: list[str] | None = None,
    expressed: bool = True,
) -> Operon:
    return Operon(
        reaction=reaction,
        product=product,
        substrates=substrates or [],
        enzymes=enzymes or [],
        expressed=expressed,
    )


def _make_stimulus(tool: str, hours_ago: float = 0) -> Stimulus:
    ts = datetime.now(UTC) - timedelta(hours=hours_ago)
    return Stimulus(tool=tool, ts=ts, outcome="success")


def _mock_collector(stimuli: list[Stimulus]) -> MagicMock:
    """Return a mock SensorySystem that yields the given stimuli."""
    collector = MagicMock(spec=SensorySystem)
    collector.recall_since.return_value = stimuli
    return collector


# ── _infer_cadence ─────────────────────────────────────────────────


class TestInferCadence:
    def test_daily_keyword(self):
        op = _make_operon(substrates=["daily period"])
        assert _infer_cadence(op) == 2

    def test_zeitgeber_keyword(self):
        op = _make_operon(substrates=["zeitgeber cycle"])
        assert _infer_cadence(op) == 2

    def test_weekly_keyword(self):
        op = _make_operon(substrates=["weekly digest"])
        assert _infer_cadence(op) == 10

    def test_infradian_keyword(self):
        op = _make_operon(substrates=["infradian rhythm"])
        assert _infer_cadence(op) == 35

    def test_monthly_keyword(self):
        op = _make_operon(substrates=["monthly review"])
        assert _infer_cadence(op) == 35

    def test_default_when_no_keyword(self):
        op = _make_operon(substrates=["something unrelated"])
        assert _infer_cadence(op) == _DEFAULT_STALENESS_DAYS

    def test_default_when_no_substrates(self):
        op = _make_operon(substrates=[])
        assert _infer_cadence(op) == _DEFAULT_STALENESS_DAYS


# ── sense ──────────────────────────────────────────────────────────


class TestSense:
    @patch("metabolon.metabolism.substrates.operon_monitor.OPERONS")
    def test_skips_unexpressed_operons(self, mock_operons):
        """Unexpressed operons should not appear in sensed output."""
        mock_operons.__iter__ = lambda self_: iter(
            [
                _make_operon(reaction="active", enzymes=["e1"], expressed=True),
                _make_operon(reaction="dormant", enzymes=["e2"], expressed=False),
            ]
        )
        collector = _mock_collector([])
        sub = OperonSubstrate(collector)
        sensed = sub.sense()
        reactions = [s["reaction"] for s in sensed]
        assert "active" in reactions
        assert "dormant" not in reactions

    @patch("metabolon.metabolism.substrates.operon_monitor.OPERONS")
    def test_tracks_most_recent_enzyme(self, mock_operons):
        """When multiple enzymes exist, the most recent firing is used."""
        now = datetime.now(UTC)
        old_ts = now - timedelta(days=5)
        recent_ts = now - timedelta(days=1)
        mock_operons.__iter__ = lambda self_: iter(
            [
                _make_operon(
                    reaction="multi",
                    enzymes=["e_old", "e_recent"],
                    substrates=["daily"],
                ),
            ]
        )
        stimuli = [
            Stimulus(tool="e_old", ts=old_ts, outcome="success"),
            Stimulus(tool="e_recent", ts=recent_ts, outcome="success"),
        ]
        collector = _mock_collector(stimuli)
        sub = OperonSubstrate(collector)
        sensed = sub.sense()
        assert len(sensed) == 1
        assert sensed[0]["fired_enzyme"] == "e_recent"
        assert sensed[0]["days_since"] == pytest.approx(1.0, abs=0.1)

    @patch("metabolon.metabolism.substrates.operon_monitor.OPERONS")
    def test_stale_when_no_signals(self, mock_operons):
        """An operon with no enzyme activity is stale."""
        mock_operons.__iter__ = lambda self_: iter(
            [
                _make_operon(reaction="quiet", enzymes=["e1"], substrates=["daily"]),
            ]
        )
        collector = _mock_collector([])
        sub = OperonSubstrate(collector)
        sensed = sub.sense()
        assert len(sensed) == 1
        assert sensed[0]["stale"] is True
        assert sensed[0]["days_since"] is None
        assert sensed[0]["last_fired"] is None

    @patch("metabolon.metabolism.substrates.operon_monitor.OPERONS")
    def test_healthy_when_within_cadence(self, mock_operons):
        """An operon fired within its cadence window is not stale."""
        mock_operons.__iter__ = lambda self_: iter(
            [
                _make_operon(reaction="fresh", enzymes=["e1"], substrates=["daily"]),
            ]
        )
        stimuli = [_make_stimulus("e1", hours_ago=12)]  # 0.5 days < 2-day cadence
        collector = _mock_collector(stimuli)
        sub = OperonSubstrate(collector)
        sensed = sub.sense()
        assert sensed[0]["stale"] is False


# ── candidates ─────────────────────────────────────────────────────


class TestCandidates:
    def test_filters_stale_only(self):
        sub = OperonSubstrate()
        sensed = [
            {"reaction": "ok", "stale": False},
            {"reaction": "bad", "stale": True},
        ]
        result = sub.candidates(sensed)
        assert len(result) == 1
        assert result[0]["reaction"] == "bad"

    def test_returns_empty_when_all_healthy(self):
        sub = OperonSubstrate()
        sensed = [
            {"reaction": "a", "stale": False},
            {"reaction": "b", "stale": False},
        ]
        assert sub.candidates(sensed) == []


# ── act ────────────────────────────────────────────────────────────


class TestAct:
    def test_stale_message_with_days(self):
        sub = OperonSubstrate()
        msg = sub.act(
            {
                "reaction": "review",
                "days_since": 20,
                "cadence_days": 10,
            }
        )
        assert "stale: review" in msg
        assert "20d since last fire" in msg
        assert "cadence: 10d" in msg

    def test_dormant_message_when_no_activity(self):
        sub = OperonSubstrate()
        msg = sub.act(
            {
                "reaction": "silent_op",
                "days_since": None,
                "cadence_days": 7,
            }
        )
        assert "dormant signal" in msg
        assert "silent_op" in msg


# ── report ─────────────────────────────────────────────────────────


class TestReport:
    def test_report_includes_healthy_and_stale(self):
        sub = OperonSubstrate()
        sensed = [
            {
                "reaction": "alive",
                "days_since": 1,
                "fired_enzyme": "e1",
                "cadence_days": 2,
                "stale": False,
            },
            {
                "reaction": "neglected",
                "days_since": 30,
                "cadence_days": 10,
                "product": "test product",
                "stale": True,
            },
        ]
        acted = ["stale: neglected — 30d since last fire (cadence: 10d)"]
        report = sub.report(sensed, acted)
        assert "-- Healthy --" in report
        assert "-- Stale --" in report
        assert "-- Actions --" in report
        assert "alive" in report
        assert "neglected" in report

    def test_report_shows_never_fired_for_no_days(self):
        sub = OperonSubstrate()
        sensed = [
            {
                "reaction": "never",
                "days_since": None,
                "cadence_days": 7,
                "product": "ghost output",
                "stale": True,
            },
        ]
        report = sub.report(sensed, [])
        assert "never fired" in report
        assert "ghost output" in report

    def test_report_header(self):
        sub = OperonSubstrate()
        report = sub.report([], [])
        assert "0 expressed operon(s) sensed" in report
