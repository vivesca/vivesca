"""Tests for the Substrate protocol."""

from metabolon.metabolism.substrate import Substrate


class ConcreteSubstrate:
    name = "test"

    def sense(self, days=30):
        return [{"item": "a"}]

    def candidates(self, sensed):
        return [s for s in sensed if s.get("item") == "a"]

    def act(self, candidate):
        return f"acted on {candidate['item']}"

    def report(self, sensed, acted):
        return f"{len(sensed)} sensed, {len(acted)} acted"


def test_substrate_concrete_is_substrate():
    """Verify that a concrete implementation satisfies the protocol."""
    s = ConcreteSubstrate()
    assert isinstance(s, Substrate)


def test_substrate_sense_returns_list():
    """Verify sense() returns a list of dicts."""
    s = ConcreteSubstrate()
    result = s.sense()
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], dict)


def test_candidates_filters_sensed():
    """Verify candidates() filters the sensed list."""
    s = ConcreteSubstrate()
    sensed = [{"item": "a"}, {"item": "b"}]
    cands = s.candidates(sensed)
    assert isinstance(cands, list)
    assert len(cands) == 1
    assert cands[0]["item"] == "a"


def test_substrate_act_returns_string():
    """Verify act() returns a human-readable string."""
    s = ConcreteSubstrate()
    result = s.act({"item": "x"})
    assert isinstance(result, str)
    assert "x" in result


def test_substrate_report_format():
    """Verify report() returns a formatted string."""
    s = ConcreteSubstrate()
    report = s.report([{"x": 1}], ["did thing"])
    assert isinstance(report, str)
    assert "1 sensed" in report
    assert "1 acted" in report


def test_non_substrate_does_not_match():
    """Verify incomplete implementations don't count as Substrate."""

    class NotASubstrate:
        pass

    assert not isinstance(NotASubstrate(), Substrate)


def test_all_substrate_implementations_follow_protocol():
    """Verify all existing substrate implementations follow the protocol."""
    from metabolon.metabolism.substrates.constitution import ExecutiveSubstrate
    from metabolon.metabolism.substrates.spending import SpendingSubstrate
    from metabolon.metabolism.substrates.tools import PhenotypeSubstrate

    assert isinstance(ExecutiveSubstrate(), Substrate)
    assert isinstance(PhenotypeSubstrate(), Substrate)
    assert isinstance(SpendingSubstrate(), Substrate)
