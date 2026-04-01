from __future__ import annotations

"""Tests for metabolon.organelles.metabolism_loop — self-improvement state machine."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.metabolism.fitness import Emotion
from metabolon.metabolism.gates import GateResult
from metabolon.metabolism.repair import ImmuneResult
from metabolon.metabolism.signals import Stimulus
from metabolon.organelles.metabolism_loop import (
    HEALTHY_THRESHOLD,
    INFECTED_THRESHOLD,
    MAX_ITERATIONS,
    build_graph,
    detect_infections,
    measure_fitness,
    repair,
    report,
    route_after_detection,
    route_after_sweep,
    route_after_verify,
    run_metabolism,
    sweep_for_issues,
    verify_fix,
)


# ── helpers ──────────────────────────────────────────────────────


def _emotion(tool="a", valence=0.5, activations=10, success_rate=0.8, metabolic_cost=5.0):
    return Emotion(
        tool=tool, valence=valence, activations=activations,
        success_rate=success_rate, metabolic_cost=metabolic_cost,
    )


def _state(**kw):
    base = dict(
        health_score=0.5, infections=[], repairs_attempted=[],
        sweep_results=[], iteration=0, report="",
        _has_infections=False, _sweep_found_issues=False,
    )
    base.update(kw)
    return base


def _infection(tool="t", fingerprint="fp", count=5, last_error="err",
               last_seen="2025-01-01", healed_count=0):
    return dict(
        tool=tool, fingerprint=fingerprint, count=count,
        last_error=last_error, last_seen=last_seen, healed_count=healed_count,
    )


# ══════════════════════════════════════════════════════════════════
# measure_fitness
# ══════════════════════════════════════════════════════════════════


class TestMeasureFitness:
    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_no_log_returns_neutral(self, mock_log, mock_sense):
        mock_log.exists.return_value = False
        r = measure_fitness(_state())
        assert r["health_score"] == 0.5
        assert r["iteration"] == 1
        mock_sense.assert_not_called()

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_empty_log_returns_neutral(self, mock_log, mock_sense):
        mock_log.exists.return_value = True
        mock_log.read_text.return_value = ""
        r = measure_fitness(_state())
        assert r["health_score"] == 0.5

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_stimuli_with_valence_averages(self, mock_log, mock_sense):
        mock_log.exists.return_value = True
        s = Stimulus(tool="a", outcome="success")
        mock_log.read_text.return_value = s.model_dump_json() + "\n"
        mock_sense.return_value = {
            "a": _emotion("a", valence=0.9),
            "b": _emotion("b", valence=0.5),
        }
        r = measure_fitness(_state())
        assert r["health_score"] == pytest.approx(0.7)

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_valence_clamped_upper(self, mock_log, mock_sense):
        mock_log.exists.return_value = True
        s = Stimulus(tool="a", outcome="success")
        mock_log.read_text.return_value = s.model_dump_json() + "\n"
        mock_sense.return_value = {"a": _emotion("a", valence=99.0)}
        assert measure_fitness(_state())["health_score"] == 1.0

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_valence_clamped_lower(self, mock_log, mock_sense):
        mock_log.exists.return_value = True
        s = Stimulus(tool="a", outcome="success")
        mock_log.read_text.return_value = s.model_dump_json() + "\n"
        mock_sense.return_value = {"a": _emotion("a", valence=-10.0)}
        assert measure_fitness(_state())["health_score"] == 0.0

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_all_none_valence_uses_llm(self, mock_log, mock_trans, mock_sense):
        mock_log.exists.return_value = True
        s = Stimulus(tool="a", outcome="success")
        mock_log.read_text.return_value = s.model_dump_json() + "\n"
        mock_sense.return_value = {"a": _emotion("a", valence=None)}
        mock_trans.return_value = ("claude", "0.83\n")
        assert measure_fitness(_state())["health_score"] == 0.83

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_llm_bad_float_defaults_neutral(self, mock_log, mock_trans, mock_sense):
        mock_log.exists.return_value = True
        s = Stimulus(tool="a", outcome="success")
        mock_log.read_text.return_value = s.model_dump_json() + "\n"
        mock_sense.return_value = {"a": _emotion("a", valence=None)}
        mock_trans.return_value = ("claude", "banana\n")
        assert measure_fitness(_state())["health_score"] == 0.5

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_corrupt_lines_skipped(self, mock_log, mock_sense):
        mock_log.exists.return_value = True
        mock_log.read_text.return_value = "bad json\n\n  \n"
        assert measure_fitness(_state())["health_score"] == 0.5
        mock_sense.assert_not_called()

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_iteration_increments(self, mock_log, mock_sense):
        mock_log.exists.return_value = False
        assert measure_fitness(_state(iteration=4))["iteration"] == 5

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_single_stimulus_single_tool(self, mock_log, mock_sense):
        mock_log.exists.return_value = True
        s = Stimulus(tool="solo", outcome="success")
        mock_log.read_text.return_value = s.model_dump_json() + "\n"
        mock_sense.return_value = {"solo": _emotion("solo", valence=0.42)}
        assert measure_fitness(_state())["health_score"] == pytest.approx(0.42)


# ══════════════════════════════════════════════════════════════════
# detect_infections
# ══════════════════════════════════════════════════════════════════


class TestDetectInfections:
    @patch("metabolon.organelles.metabolism_loop.chronic_infections")
    def test_empty(self, mock_ci):
        mock_ci.return_value = []
        r = detect_infections(_state())
        assert r["infections"] == []
        assert r["_has_infections"] is False

    @patch("metabolon.organelles.metabolism_loop.chronic_infections")
    def test_one_infection(self, mock_ci):
        mock_ci.return_value = [_infection(tool="web_search")]
        r = detect_infections(_state())
        assert len(r["infections"]) == 1
        assert r["infections"][0]["tool"] == "web_search"
        assert r["_has_infections"] is True

    @patch("metabolon.organelles.metabolism_loop.chronic_infections")
    def test_multiple_infections(self, mock_ci):
        mock_ci.return_value = [_infection(tool="a"), _infection(tool="b")]
        r = detect_infections(_state())
        assert len(r["infections"]) == 2

    @patch("metabolon.organelles.metabolism_loop.chronic_infections")
    def test_fields_propagated(self, mock_ci):
        inf = _infection(count=9, healed_count=3, last_error="timeout exceeded")
        mock_ci.return_value = [inf]
        r = detect_infections(_state())
        assert r["infections"][0]["count"] == 9
        assert r["infections"][0]["healed_count"] == 3
        assert r["infections"][0]["last_error"] == "timeout exceeded"


# ══════════════════════════════════════════════════════════════════
# repair
# ══════════════════════════════════════════════════════════════════


class TestRepair:
    @patch("metabolon.organelles.metabolism_loop.immune_response", new_callable=AsyncMock)
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    def test_accepted_repair(self, mock_trans, mock_immune):
        mock_trans.return_value = ("claude", "Searches the web")
        mock_immune.return_value = ImmuneResult(
            candidate="fixed", accepted=True,
            gate_result=GateResult(True, "ok"), attempts=1,
        )
        r = repair(_state(infections=[_infection()]))
        assert len(r["repairs_attempted"]) == 1
        rec = r["repairs_attempted"][0]
        assert rec["accepted"] is True
        assert rec["attempts"] == 1
        assert rec["gate_passed"] is True
        assert rec["candidate"] == "fixed"

    @patch("metabolon.organelles.metabolism_loop.immune_response", new_callable=AsyncMock)
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    def test_rejected_repair(self, mock_trans, mock_immune):
        mock_trans.return_value = ("claude", "A tool")
        mock_immune.return_value = ImmuneResult(
            candidate=None, accepted=False,
            gate_result=GateResult(False, "too short"), attempts=3,
        )
        r = repair(_state(infections=[_infection()]))
        rec = r["repairs_attempted"][0]
        assert rec["accepted"] is False
        assert rec["attempts"] == 3

    @patch("metabolon.organelles.metabolism_loop.immune_response", new_callable=AsyncMock)
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    def test_exception_in_repair(self, mock_trans, mock_immune):
        mock_trans.return_value = ("claude", "A tool")
        mock_immune.side_effect = RuntimeError("loop closed")
        r = repair(_state(infections=[_infection()]))
        rec = r["repairs_attempted"][0]
        assert rec["accepted"] is False
        assert rec["attempts"] == 0
        assert "repair exception" in rec["gate_reason"]

    @patch("metabolon.organelles.metabolism_loop.immune_response", new_callable=AsyncMock)
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    def test_no_infections_skips(self, mock_trans, mock_immune):
        r = repair(_state(infections=[]))
        assert r["repairs_attempted"] == []
        mock_trans.assert_not_called()
        mock_immune.assert_not_called()

    @patch("metabolon.organelles.metabolism_loop.immune_response", new_callable=AsyncMock)
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    def test_multiple_infections_all_repaired(self, mock_trans, mock_immune):
        mock_trans.return_value = ("claude", "Desc")
        mock_immune.return_value = ImmuneResult(
            candidate="ok", accepted=True,
            gate_result=GateResult(True, "ok"), attempts=1,
        )
        r = repair(_state(infections=[
            _infection(tool="a", fingerprint="f1"),
            _infection(tool="b", fingerprint="f2"),
        ]))
        assert len(r["repairs_attempted"]) == 2
        assert mock_immune.call_count == 2
        assert mock_trans.call_count == 2

    @patch("metabolon.organelles.metabolism_loop.immune_response", new_callable=AsyncMock)
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    def test_transduce_called_for_tool_description(self, mock_trans, mock_immune):
        mock_trans.return_value = ("claude", "Fetches data from API")
        mock_immune.return_value = ImmuneResult(
            candidate="c", accepted=True,
            gate_result=GateResult(True, "ok"), attempts=1,
        )
        repair(_state(infections=[_infection(tool="fetch_data")]))
        mock_trans.assert_called_once()
        call_prompt = mock_trans.call_args[0][1]
        assert "fetch_data" in call_prompt


# ══════════════════════════════════════════════════════════════════
# verify_fix
# ══════════════════════════════════════════════════════════════════


class TestVerifyFix:
    def test_all_healed_boosts_score(self):
        state = _state(
            health_score=0.5,
            infections=[_infection(fingerprint="fp1")],
            repairs_attempted=[
                dict(tool="t", fingerprint="fp1", accepted=True, attempts=1,
                     candidate="c", gate_passed=True, gate_reason="ok"),
            ],
        )
        r = verify_fix(state)
        assert r["health_score"] > 0.5
        assert r["_has_infections"] is False
        assert r["infections"] == []

    def test_partial_heal_keeps_remaining(self):
        state = _state(
            health_score=0.4,
            infections=[_infection(fingerprint="fp1"),
                        _infection(fingerprint="fp2")],
            repairs_attempted=[
                dict(tool="t", fingerprint="fp1", accepted=True, attempts=1,
                     candidate="c", gate_passed=True, gate_reason="ok"),
                dict(tool="t", fingerprint="fp2", accepted=False, attempts=3,
                     candidate=None, gate_passed=False, gate_reason="fail"),
            ],
        )
        r = verify_fix(state)
        assert len(r["infections"]) == 1
        assert r["infections"][0]["fingerprint"] == "fp2"
        assert r["_has_infections"] is True

    def test_no_repairs_score_unchanged(self):
        state = _state(health_score=0.6, infections=[_infection()])
        r = verify_fix(state)
        assert r["health_score"] == 0.6

    def test_score_capped_at_1(self):
        state = _state(
            health_score=0.99,
            infections=[_infection(fingerprint="fp1")],
            repairs_attempted=[
                dict(tool="t", fingerprint="fp1", accepted=True, attempts=1,
                     candidate="c", gate_passed=True, gate_reason="ok"),
            ],
        )
        r = verify_fix(state)
        assert r["health_score"] <= 1.0

    def test_sweep_flag_reset(self):
        r = verify_fix(_state())
        assert r["_sweep_found_issues"] is False

    def test_no_accepted_heal_ratio_zero(self):
        state = _state(
            health_score=0.3,
            infections=[_infection(fingerprint="fp1")],
            repairs_attempted=[
                dict(tool="t", fingerprint="fp1", accepted=False, attempts=3,
                     candidate=None, gate_passed=False, gate_reason="fail"),
            ],
        )
        r = verify_fix(state)
        assert r["health_score"] == 0.3  # unchanged


# ══════════════════════════════════════════════════════════════════
# sweep_for_issues
# ══════════════════════════════════════════════════════════════════


class TestSweepForIssues:
    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.organelles.metabolism_loop.select")
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_with_candidates(self, mock_log, mock_trans, mock_select, mock_sense):
        mock_log.exists.return_value = True
        s = Stimulus(tool="a", outcome="success")
        mock_log.read_text.return_value = s.model_dump_json() + "\n"
        mock_sense.return_value = {"a": _emotion("a", valence=0.1)}
        mock_select.return_value = ["a"]
        mock_trans.return_value = ("claude", "Rate-limited. Reduce call frequency.")
        r = sweep_for_issues(_state())
        assert len(r["sweep_results"]) == 1
        assert r["sweep_results"][0]["tool"] == "a"
        assert r["_sweep_found_issues"] is True

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.organelles.metabolism_loop.select")
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_candidates_capped_at_5(self, mock_log, mock_trans, mock_select, mock_sense):
        mock_log.exists.return_value = True
        s = Stimulus(tool="x", outcome="success")
        mock_log.read_text.return_value = s.model_dump_json() + "\n"
        mock_sense.return_value = {"x": _emotion("x", valence=0.1)}
        mock_select.return_value = [f"tool{i}" for i in range(10)]
        mock_trans.return_value = ("claude", "analysis")
        r = sweep_for_issues(_state())
        assert len(r["sweep_results"]) == 5

    @patch("metabolon.organelles.metabolism_loop.infection_summary", return_value="")
    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.organelles.metabolism_loop.select")
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_no_stimuli_no_infections_empty(self, mock_log, mock_trans, mock_select, mock_sense, mock_summary):
        mock_log.exists.return_value = False
        r = sweep_for_issues(_state())
        assert r["sweep_results"] == []
        assert r["_sweep_found_issues"] is False

    @patch("metabolon.organelles.metabolism_loop.infection_summary")
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_no_stimuli_with_infections_uses_llm(self, mock_log, mock_trans, mock_summary):
        mock_log.exists.return_value = False
        mock_summary.return_value = "5 infections found"
        mock_trans.return_value = ("claude", "- issue 1\n- issue 2")
        r = sweep_for_issues(_state())
        assert len(r["sweep_results"]) == 1
        assert r["sweep_results"][0]["tool"] == "system"
        assert r["_sweep_found_issues"] is True

    @patch("metabolon.organelles.metabolism_loop.infection_summary")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_no_stimuli_empty_infection_summary(self, mock_log, mock_summary):
        mock_log.exists.return_value = False
        mock_summary.return_value = ""
        r = sweep_for_issues(_state())
        assert r["sweep_results"] == []
        assert r["_sweep_found_issues"] is False

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.organelles.metabolism_loop.select")
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_select_returns_empty(self, mock_log, mock_trans, mock_select, mock_sense):
        mock_log.exists.return_value = True
        s = Stimulus(tool="a", outcome="success")
        mock_log.read_text.return_value = s.model_dump_json() + "\n"
        mock_sense.return_value = {"a": _emotion("a", valence=0.8)}
        mock_select.return_value = []
        r = sweep_for_issues(_state())
        assert r["sweep_results"] == []
        assert r["_sweep_found_issues"] is False

    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.organelles.metabolism_loop.select")
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_sweep_result_fields(self, mock_log, mock_trans, mock_select, mock_sense):
        mock_log.exists.return_value = True
        s = Stimulus(tool="slow", outcome="success")
        mock_log.read_text.return_value = s.model_dump_json() + "\n"
        mock_sense.return_value = {"slow": _emotion("slow", valence=0.1, activations=5, success_rate=0.3)}
        mock_select.return_value = ["slow"]
        mock_trans.return_value = ("claude", "Consider caching results.")
        r = sweep_for_issues(_state())
        sr = r["sweep_results"][0]
        assert sr["tool"] == "slow"
        assert sr["activations"] == 5
        assert sr["success_rate"] == 0.3
        assert "caching" in sr["analysis"]


# ══════════════════════════════════════════════════════════════════
# report
# ══════════════════════════════════════════════════════════════════


class TestReport:
    def test_basic_report(self):
        r = report(_state(health_score=0.85, iteration=2))
        assert "0.85" in r["report"]
        assert "Cycles: 2" in r["report"]
        assert "# Metabolism Report" in r["report"]

    def test_report_with_infections(self):
        r = report(_state(
            health_score=0.3,
            infections=[_infection(tool="bad_tool", fingerprint="fp1", count=7,
                                    last_error="timeout after 30s")],
        ))
        assert "bad_tool" in r["report"]
        assert "Remaining Infections" in r["report"]

    def test_report_with_repairs(self):
        repairs = [
            dict(tool="a", fingerprint="f1", accepted=True, attempts=1,
                 candidate="c", gate_passed=True, gate_reason="ok"),
            dict(tool="b", fingerprint="f2", accepted=False, attempts=3,
                 candidate=None, gate_passed=False, gate_reason="fail"),
        ]
        r = report(_state(repairs_attempted=repairs))
        assert "HEALED" in r["report"]
        assert "UNRESOLVED" in r["report"]
        assert "1 accepted" in r["report"]
        assert "1 rejected" in r["report"]

    def test_report_with_sweep(self):
        sweep = [dict(tool="slow_tool", valence="0.2", success_rate=0.3,
                      activations=5, analysis="Consider caching")]
        r = report(_state(sweep_results=sweep))
        assert "slow_tool" in r["report"]
        assert "Sweep Findings" in r["report"]

    def test_healthy_verdict(self):
        r = report(_state())
        assert "System healthy" in r["report"]
        assert "Verdict" in r["report"]

    def test_report_includes_timestamp(self):
        r = report(_state())
        assert "UTC" in r["report"]

    def test_infection_error_truncated(self):
        long_err = "x" * 200
        r = report(_state(
            infections=[_infection(tool="t", last_error=long_err)],
        ))
        # Report truncates last_error to 80 chars in the infection line
        assert long_err[:80] in r["report"]


# ══════════════════════════════════════════════════════════════════
# routing functions
# ══════════════════════════════════════════════════════════════════


class TestRouting:
    def test_route_after_detection_infected(self):
        assert route_after_detection(_state(_has_infections=True)) == "repair"

    def test_route_after_detection_clean(self):
        assert route_after_detection(_state(_has_infections=False)) == "sweep_for_issues"

    def test_route_after_verify_still_infected_under_cap(self):
        assert route_after_verify(
            _state(_has_infections=True, iteration=1)
        ) == "measure_fitness"

    def test_route_after_verify_still_infected_at_cap(self):
        assert route_after_verify(
            _state(_has_infections=True, iteration=MAX_ITERATIONS)
        ) == "sweep_for_issues"

    def test_route_after_verify_healed(self):
        assert route_after_verify(
            _state(_has_infections=False, iteration=1)
        ) == "sweep_for_issues"

    def test_route_after_sweep_issues_under_cap(self):
        assert route_after_sweep(
            _state(_sweep_found_issues=True, iteration=1)
        ) == "measure_fitness"

    def test_route_after_sweep_issues_at_cap(self):
        assert route_after_sweep(
            _state(_sweep_found_issues=True, iteration=MAX_ITERATIONS)
        ) == "report"

    def test_route_after_sweep_no_issues(self):
        assert route_after_sweep(
            _state(_sweep_found_issues=False, iteration=1)
        ) == "report"


# ══════════════════════════════════════════════════════════════════
# build_graph
# ══════════════════════════════════════════════════════════════════


class TestBuildGraph:
    def test_returns_state_graph(self):
        from langgraph.graph import StateGraph
        g = build_graph()
        assert isinstance(g, StateGraph)

    def test_graph_compiles(self):
        g = build_graph()
        app = g.compile()
        assert app is not None


# ══════════════════════════════════════════════════════════════════
# run_metabolism (integration)
# ══════════════════════════════════════════════════════════════════


class TestRunMetabolism:
    @patch("metabolon.organelles.metabolism_loop._open_checkpointer")
    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.organelles.metabolism_loop.chronic_infections")
    @patch("metabolon.organelles.metabolism_loop.infection_summary")
    @patch("metabolon.organelles.metabolism_loop.select")
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_clean_cycle(
        self, mock_log, mock_trans, mock_select, mock_summary,
        mock_ci, mock_sense, mock_cp,
    ):
        from langgraph.checkpoint.memory import InMemorySaver
        mock_cp.return_value = InMemorySaver()
        mock_log.exists.return_value = False
        mock_ci.return_value = []
        mock_summary.return_value = ""

        r = run_metabolism(thread_id="test_clean", persistent=False)

        assert "report" in r
        assert r["health_score"] == 0.5
        assert r["iteration"] == 1
        assert "System healthy" in r["report"]

    @patch("metabolon.organelles.metabolism_loop.immune_response", new_callable=AsyncMock)
    @patch("metabolon.organelles.metabolism_loop._open_checkpointer")
    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.organelles.metabolism_loop.chronic_infections")
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    @patch("metabolon.organelles.metabolism_loop.select")
    @patch("metabolon.organelles.metabolism_loop.infection_summary")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_infected_then_repair(
        self, mock_log, mock_summary, mock_select, mock_trans,
        mock_ci, mock_sense, mock_cp, mock_immune,
    ):
        from langgraph.checkpoint.memory import InMemorySaver
        mock_cp.return_value = InMemorySaver()
        mock_log.exists.return_value = False
        mock_ci.return_value = [_infection(tool="bad_tool")]
        mock_trans.return_value = ("claude", "A tool that searches")
        mock_immune.return_value = ImmuneResult(
            candidate="fixed", accepted=True,
            gate_result=GateResult(True, "ok"), attempts=1,
        )
        mock_select.return_value = []
        mock_summary.return_value = ""

        r = run_metabolism(thread_id="test_repair", persistent=False)

        assert len(r["repairs_attempted"]) >= 1
        assert r["repairs_attempted"][0]["accepted"] is True
        assert "HEALED" in r["report"]

    @patch("metabolon.organelles.metabolism_loop.immune_response", new_callable=AsyncMock)
    @patch("metabolon.organelles.metabolism_loop._open_checkpointer")
    @patch("metabolon.organelles.metabolism_loop.sense_affect")
    @patch("metabolon.organelles.metabolism_loop.chronic_infections")
    @patch("metabolon.organelles.metabolism_loop.transduce_safe")
    @patch("metabolon.organelles.metabolism_loop.select")
    @patch("metabolon.organelles.metabolism_loop.infection_summary")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_infected_repair_rejected_stays_unresolved(
        self, mock_log, mock_summary, mock_select, mock_trans,
        mock_ci, mock_sense, mock_cp, mock_immune,
    ):
        from langgraph.checkpoint.memory import InMemorySaver
        mock_cp.return_value = InMemorySaver()
        mock_log.exists.return_value = False
        mock_ci.return_value = [_infection(tool="stubborn")]
        mock_trans.return_value = ("claude", "A tool")
        mock_immune.return_value = ImmuneResult(
            candidate=None, accepted=False,
            gate_result=GateResult(False, "gate rejected"), attempts=3,
        )
        mock_select.return_value = []
        mock_summary.return_value = ""

        r = run_metabolism(thread_id="test_reject", persistent=False)

        assert any(not rep["accepted"] for rep in r["repairs_attempted"])
        assert "UNRESOLVED" in r["report"]


# ══════════════════════════════════════════════════════════════════
# CLI main
# ══════════════════════════════════════════════════════════════════


class TestMain:
    @patch("metabolon.organelles.metabolism_loop.chronic_infections")
    @patch("metabolon.organelles.metabolism_loop.infection_summary")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_dry_run(self, mock_log, mock_summary, mock_ci, capsys):
        mock_log.exists.return_value = False
        mock_summary.return_value = ""
        mock_ci.return_value = []
        from metabolon.organelles.metabolism_loop import main
        with patch.object(sys, "argv", ["metabolism_loop", "--dry-run"]):
            main()
        out = capsys.readouterr().out
        assert "Signal log: 0 valid stimuli" in out
        assert "Chronic infections: 0" in out

    @patch("metabolon.organelles.metabolism_loop.chronic_infections")
    @patch("metabolon.organelles.metabolism_loop.infection_summary")
    @patch("metabolon.metabolism.signals.DEFAULT_LOG")
    def test_dry_run_with_infections(self, mock_log, mock_summary, mock_ci, capsys):
        mock_log.exists.return_value = False
        mock_summary.return_value = "Infections: 3 events, 2 unhealed"
        mock_ci.return_value = [_infection(), _infection(tool="t2")]
        from metabolon.organelles.metabolism_loop import main
        with patch.object(sys, "argv", ["metabolism_loop", "--dry-run"]):
            main()
        out = capsys.readouterr().out
        assert "Chronic infections: 2" in out
        assert "Infections: 3 events" in out


# ══════════════════════════════════════════════════════════════════
# constants
# ══════════════════════════════════════════════════════════════════


class TestConstants:
    def test_max_iterations(self):
        assert MAX_ITERATIONS == 3

    def test_thresholds(self):
        assert HEALTHY_THRESHOLD == 0.7
        assert INFECTED_THRESHOLD == 0.3
