"""Tests for OperonSubstrate — the operon heartbeat monitor.

Full sense -> candidates -> act -> report cycle using fixture signals.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from metabolon.metabolism.signals import Outcome, SensorySystem, Stimulus
from metabolon.metabolism.substrate import Substrate
from metabolon.metabolism.substrates.operons import OperonSubstrate, _infer_cadence
from metabolon.operons import Operon

# ── Helpers ──────────────────────────────────────────────────────


def _make_signal(
    tool: str,
    outcome: Outcome = Outcome.success,
    days_ago: float = 0,
) -> Stimulus:
    s = Stimulus(
        tool=tool,
        outcome=outcome,
        substrate_consumed=10,
        product_released=50,
        response_latency=200,
    )
    if days_ago:
        s.ts = datetime.now(UTC) - timedelta(days=days_ago)
    return s


# ── Protocol ─────────────────────────────────────────────────────


class TestProtocol:
    def test_is_substrate(self):
        assert isinstance(OperonSubstrate(), Substrate)


# ── Cadence Inference ────────────────────────────────────────────


class TestCadenceInference:
    def test_daily_substrate(self):
        e = Operon(
            reaction="triage",
            product="Incoming routed",
            substrates=["daily period", "inbox accumulation"],
        )
        assert _infer_cadence(e) == 2

    def test_monthly_substrate(self):
        e = Operon(
            reaction="homeostasis",
            product="Status audited",
            substrates=["monthly cycle", "explicit request"],
        )
        assert _infer_cadence(e) == 35

    def test_zeitgeber_substrate(self):
        e = Operon(
            reaction="monitor",
            product="Health signals synthesised",
            substrates=["zeitgeber routine", "symptom reported"],
        )
        assert _infer_cadence(e) == 2

    def test_default_cadence(self):
        e = Operon(
            reaction="evaluate",
            product="Opportunity assessed",
            substrates=["job posting received", "opportunity surfaces"],
        )
        assert _infer_cadence(e) == 14


# ── Sense ────────────────────────────────────────────────────────


class TestSense:
    def test_sense_empty_signals(self, tmp_path):
        """No signals → all expressed operons stale."""
        collector = SensorySystem(tmp_path / "signals.jsonl")
        substrate = OperonSubstrate(collector=collector)
        sensed = substrate.sense(days=30)

        assert len(sensed) > 0
        # All should be stale with no signals
        for entry in sensed:
            assert entry["stale"] is True
            assert entry["last_fired"] is None
            assert entry["days_since"] is None

    def test_sense_with_recent_signal(self, tmp_path):
        """Recent enzyme signal → operon is healthy."""
        collector = SensorySystem(tmp_path / "signals.jsonl")
        # circadian_sleep is an enzyme of the "monitor" operon
        collector.append(_make_signal("circadian_sleep", days_ago=0.5))

        substrate = OperonSubstrate(collector=collector)
        sensed = substrate.sense(days=30)

        monitor = next(e for e in sensed if e["reaction"] == "monitor")
        assert monitor["stale"] is False
        assert monitor["fired_enzyme"] == "circadian_sleep"
        assert monitor["days_since"] is not None
        assert monitor["days_since"] < 1

    def test_sense_with_old_signal(self, tmp_path):
        """Old enzyme signal beyond cadence → operon is stale."""
        collector = SensorySystem(tmp_path / "signals.jsonl")
        # triage has daily cadence (2 days threshold)
        # "period" is a triage enzyme — fire it 5 days ago
        collector.append(_make_signal("period", days_ago=5))

        substrate = OperonSubstrate(collector=collector)
        sensed = substrate.sense(days=30)

        triage = next(e for e in sensed if e["reaction"] == "triage")
        assert triage["stale"] is True
        assert triage["days_since"] > 2

    def test_sense_excludes_dormant(self, tmp_path):
        """Dormant operons are not sensed."""
        collector = SensorySystem(tmp_path / "signals.jsonl")
        substrate = OperonSubstrate(collector=collector)
        sensed = substrate.sense(days=30)

        reactions = {e["reaction"] for e in sensed}
        # "decide", "plan", "gift" are dormant
        assert "decide" not in reactions
        assert "plan" not in reactions
        assert "gift" not in reactions

    def test_sense_picks_most_recent_enzyme(self, tmp_path):
        """When multiple enzymes fired, picks the most recent."""
        collector = SensorySystem(tmp_path / "signals.jsonl")
        # monitor has enzymes: circadian_sleep, membrane_potential, sopor
        collector.append(_make_signal("circadian_sleep", days_ago=3))
        collector.append(_make_signal("membrane_potential", days_ago=0.5))

        substrate = OperonSubstrate(collector=collector)
        sensed = substrate.sense(days=30)

        monitor = next(e for e in sensed if e["reaction"] == "monitor")
        assert monitor["fired_enzyme"] == "membrane_potential"


# ── Candidates ───────────────────────────────────────────────────


class TestCandidates:
    def test_candidates_are_stale(self, tmp_path):
        """Only stale operons are candidates."""
        collector = SensorySystem(tmp_path / "signals.jsonl")
        # Make monitor healthy
        collector.append(_make_signal("circadian_sleep", days_ago=0.5))

        substrate = OperonSubstrate(collector=collector)
        sensed = substrate.sense(days=30)
        cands = substrate.candidates(sensed)

        cand_reactions = {c["reaction"] for c in cands}
        assert "monitor" not in cand_reactions
        # But other unfired operons should be candidates
        assert len(cands) > 0


# ── Act ──────────────────────────────────────────────────────────


class TestAct:
    def test_act_stale(self):
        substrate = OperonSubstrate()
        result = substrate.act({"reaction": "triage", "days_since": 5.0, "cadence_days": 2})
        assert "stale" in result
        assert "triage" in result
        assert "5d" in result

    def test_act_never_fired(self):
        substrate = OperonSubstrate()
        result = substrate.act({"reaction": "scan", "days_since": None, "cadence_days": 35})
        assert "dormant signal" in result
        assert "scan" in result


# ── Report ───────────────────────────────────────────────────────


class TestReport:
    def test_report_empty(self):
        substrate = OperonSubstrate()
        report = substrate.report([], [])
        assert "Operon substrate: 0 expressed operon(s) sensed" in report

    def test_report_with_healthy_and_stale(self, tmp_path):
        collector = SensorySystem(tmp_path / "signals.jsonl")
        collector.append(_make_signal("circadian_sleep", days_ago=0.5))

        substrate = OperonSubstrate(collector=collector)
        sensed = substrate.sense(days=30)
        cands = substrate.candidates(sensed)
        acted = [substrate.act(c) for c in cands]
        report = substrate.report(sensed, acted)

        assert "Operon substrate" in report
        assert "Healthy" in report
        assert "Stale" in report
        assert "monitor" in report

    def test_full_cycle(self, tmp_path):
        """Full sense -> candidates -> act -> report."""
        collector = SensorySystem(tmp_path / "signals.jsonl")
        collector.append(_make_signal("circadian_sleep", days_ago=0.5))
        collector.append(_make_signal("period", days_ago=0.5))

        substrate = OperonSubstrate(collector=collector)
        sensed = substrate.sense(days=30)
        cands = substrate.candidates(sensed)
        acted = [substrate.act(c) for c in cands]
        report = substrate.report(sensed, acted)

        assert "Operon substrate" in report
        assert len(sensed) > 0
        assert len(cands) >= 0


# ── Registry ─────────────────────────────────────────────────────


class TestRegistry:
    def test_operons_in_catalog(self):
        from metabolon.metabolism.substrates import get_receptor_catalog

        reg = get_receptor_catalog()
        assert "operons" in reg
        assert reg["operons"] is OperonSubstrate
