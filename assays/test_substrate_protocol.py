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


def test_substrate_protocol_concrete_is_substrate():
    s = ConcreteSubstrate()
    assert isinstance(s, Substrate)


def test_substrate_protocol_sense_returns_list():
    s = ConcreteSubstrate()
    result = s.sense()
    assert isinstance(result, list)
    assert len(result) == 1


def test_candidates_filters():
    s = ConcreteSubstrate()
    sensed = [{"item": "a"}, {"item": "b"}]
    cands = s.candidates(sensed)
    assert len(cands) == 1


def test_substrate_protocol_act_returns_string():
    s = ConcreteSubstrate()
    result = s.act({"item": "x"})
    assert isinstance(result, str)


def test_substrate_protocol_report_format():
    s = ConcreteSubstrate()
    report = s.report([{"x": 1}], ["did thing"])
    assert "1 sensed" in report
    assert "1 acted" in report


def test_non_substrate():
    class NotASubstrate:
        pass

    assert not isinstance(NotASubstrate(), Substrate)
