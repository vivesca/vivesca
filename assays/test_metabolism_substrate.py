from __future__ import annotations

"""Tests for metabolon.metabolism.substrate — Substrate protocol contract."""

from metabolon.metabolism.substrate import Substrate

# ---------------------------------------------------------------------------
# Helpers — concrete implementations
# ---------------------------------------------------------------------------


class MinimalSubstrate:
    """Smallest class satisfying the Substrate protocol."""

    name = "minimal"

    def sense(self, days: int = 30) -> list[dict]:
        return [{"id": 1, "days": days}]

    def candidates(self, sensed: list[dict]) -> list[dict]:
        return sensed

    def act(self, candidate: dict) -> str:
        return f"acted:{candidate.get('id', '?')}"

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        return f"n={len(sensed)} acted={len(acted)}"


class FilteredSubstrate:
    """Substrate whose candidates() filters by a threshold."""

    name = "filtered"

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold

    def sense(self, days: int = 30) -> list[dict]:
        return [
            {"name": "a", "score": 0.9},
            {"name": "b", "score": 0.1},
            {"name": "c", "score": 0.6},
        ]

    def candidates(self, sensed: list[dict]) -> list[dict]:
        return [s for s in sensed if s["score"] < self.threshold]

    def act(self, candidate: dict) -> str:
        return f"prune {candidate['name']} (score {candidate['score']})"

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        lines = [f"## {self.name} report", *acted]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Protocol isinstance checks
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_minimal_satisfies_protocol(self):
        assert isinstance(MinimalSubstrate(), Substrate)

    def test_filtered_satisfies_protocol(self):
        assert isinstance(FilteredSubstrate(), Substrate)

    def test_plain_object_not_substrate(self):
        assert not isinstance(object(), Substrate)

    def test_partial_impl_not_substrate(self):
        """Missing 'report' → not a Substrate."""

        class Partial:
            name = "partial"

            def sense(self, days=30): ...
            def candidates(self, sensed): ...
            def act(self, candidate): ...

            # no report

        assert not isinstance(Partial(), Substrate)

    def test_wrong_signature_still_substrate(self):
        """Protocol checks attribute existence, not signatures."""

        class Weird:
            name = "weird"

            def sense(self):
                return []  # missing 'days' param

            def candidates(self, sensed):
                return sensed

            def act(self, candidate):
                return "ok"

            def report(self, sensed, acted):
                return ""

        # runtime_checkable only checks presence of attrs, not signatures
        assert isinstance(Weird(), Substrate)

    def test_name_only_not_substrate(self):
        class NameOnly:
            name = "name_only"

        assert not isinstance(NameOnly(), Substrate)


# ---------------------------------------------------------------------------
# sense()
# ---------------------------------------------------------------------------


class TestSense:
    def test_default_days(self):
        s = MinimalSubstrate()
        result = s.sense()
        assert result == [{"id": 1, "days": 30}]

    def test_custom_days(self):
        s = MinimalSubstrate()
        result = s.sense(days=7)
        assert result == [{"id": 1, "days": 7}]

    def test_returns_list(self):
        s = MinimalSubstrate()
        assert isinstance(s.sense(), list)

    def test_empty_sense(self):
        class EmptySubstrate:
            name = "empty"

            def sense(self, days=30):
                return []

            def candidates(self, sensed):
                return sensed

            def act(self, candidate):
                return "nop"

            def report(self, sensed, acted):
                return "nothing"

        s = EmptySubstrate()
        assert s.sense() == []

    def test_sense_returns_dicts(self):
        s = FilteredSubstrate()
        for item in s.sense():
            assert isinstance(item, dict)


# ---------------------------------------------------------------------------
# candidates()
# ---------------------------------------------------------------------------


class TestCandidates:
    def test_minimal_returns_all(self):
        s = MinimalSubstrate()
        sensed = [{"id": 1}, {"id": 2}]
        assert s.candidates(sensed) == sensed

    def test_filtered_returns_subset(self):
        s = FilteredSubstrate(threshold=0.5)
        sensed = s.sense()
        cands = s.candidates(sensed)
        assert len(cands) == 1
        assert cands[0]["name"] == "b"

    def test_candidates_empty_input(self):
        s = FilteredSubstrate()
        assert s.candidates([]) == []

    def test_candidates_none_pass_filter(self):
        s = FilteredSubstrate(threshold=0.0)
        sensed = s.sense()
        assert s.candidates(sensed) == []

    def test_candidates_all_pass_filter(self):
        s = FilteredSubstrate(threshold=1.0)
        sensed = s.sense()
        assert len(s.candidates(sensed)) == 3


# ---------------------------------------------------------------------------
# act()
# ---------------------------------------------------------------------------


class TestAct:
    def test_returns_string(self):
        s = MinimalSubstrate()
        result = s.act({"id": 42})
        assert isinstance(result, str)

    def test_minimal_act_content(self):
        s = MinimalSubstrate()
        assert s.act({"id": 7}) == "acted:7"

    def test_filtered_act_content(self):
        s = FilteredSubstrate()
        result = s.act({"name": "x", "score": 0.1})
        assert "x" in result
        assert "0.1" in result

    def test_act_with_empty_dict(self):
        s = MinimalSubstrate()
        result = s.act({})
        assert "?" in result


# ---------------------------------------------------------------------------
# report()
# ---------------------------------------------------------------------------


class TestReport:
    def test_returns_string(self):
        s = MinimalSubstrate()
        result = s.report([], [])
        assert isinstance(result, str)

    def test_minimal_report_content(self):
        s = MinimalSubstrate()
        r = s.report([{"id": 1}], ["acted:1"])
        assert "n=1" in r
        assert "acted=1" in r

    def test_empty_inputs(self):
        s = MinimalSubstrate()
        r = s.report([], [])
        assert "n=0" in r
        assert "acted=0" in r

    def test_filtered_report_format(self):
        s = FilteredSubstrate()
        r = s.report([{"name": "a"}], ["prune a"])
        assert "## filtered report" in r
        assert "prune a" in r

    def test_report_with_many_acted(self):
        s = MinimalSubstrate()
        acted = [f"item{i}" for i in range(10)]
        r = s.report([], acted)
        assert "acted=10" in r


# ---------------------------------------------------------------------------
# Full cycle integration
# ---------------------------------------------------------------------------


class TestCycle:
    def test_full_minimal_cycle(self):
        s = MinimalSubstrate()
        sensed = s.sense(days=14)
        cands = s.candidates(sensed)
        acted = [s.act(c) for c in cands]
        report = s.report(sensed, acted)
        assert "n=1" in report
        assert "acted=1" in report
        assert acted == ["acted:1"]

    def test_full_filtered_cycle(self):
        s = FilteredSubstrate(threshold=0.5)
        sensed = s.sense()
        cands = s.candidates(sensed)
        acted = [s.act(c) for c in cands]
        report = s.report(sensed, acted)
        assert len(cands) == 1
        assert "b" in acted[0]
        assert "## filtered report" in report

    def test_empty_cycle(self):
        s = FilteredSubstrate(threshold=0.0)
        sensed = s.sense()
        cands = s.candidates(sensed)
        acted = [s.act(c) for c in cands]
        report = s.report(sensed, acted)
        assert len(acted) == 0
        assert isinstance(report, str)
