"""Tests for inflammasome — deterministic self-test probes."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok_probe():
    return (True, "ok")


def _fail_probe():
    return (False, "something broke")


def _boom_probe():
    raise RuntimeError("boom")


# ---------------------------------------------------------------------------
# run_all_probes
# ---------------------------------------------------------------------------


class TestRunAllProbes:
    """Tests for run_all_probes — aggregation layer only (probes mocked)."""

    def test_returns_list_of_dicts_with_expected_keys(self):
        from metabolon.organelles.inflammasome import run_all_probes

        with patch("metabolon.organelles.inflammasome._PROBES", [
            ("test_probe", _ok_probe),
        ]):
            results = run_all_probes()

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["name"] == "test_probe"
        assert results[0]["passed"] is True
        assert results[0]["message"] == "ok"
        assert "duration_ms" in results[0]

    def test_catches_probe_exceptions(self):
        """A probe that raises must be captured, not propagated."""
        from metabolon.organelles.inflammasome import run_all_probes

        with patch("metabolon.organelles.inflammasome._PROBES", [
            ("crasher", _boom_probe),
        ]):
            results = run_all_probes()

        assert len(results) == 1
        assert results[0]["passed"] is False

    def test_failed_probe_message_preserved(self):
        from metabolon.organelles.inflammasome import run_all_probes

        with patch("metabolon.organelles.inflammasome._PROBES", [
            ("broken", _fail_probe),
        ]):
            results = run_all_probes()

        assert "something broke" in results[0]["message"]

    def test_multiple_probes_independent(self):
        """One failure must not prevent other probes from running."""
        from metabolon.organelles.inflammasome import run_all_probes

        with patch("metabolon.organelles.inflammasome._PROBES", [
            ("first", _fail_probe),
            ("second", _ok_probe),
            ("third", _boom_probe),
        ]):
            results = run_all_probes()

        assert len(results) == 3
        assert results[0]["passed"] is False
        assert results[1]["passed"] is True
        assert results[2]["passed"] is False

    def test_empty_probes_returns_empty_list(self):
        from metabolon.organelles.inflammasome import run_all_probes

        with patch("metabolon.organelles.inflammasome._PROBES", []):
            results = run_all_probes()

        assert results == []


# ---------------------------------------------------------------------------
# probe_report
# ---------------------------------------------------------------------------


class TestProbeReport:
    def test_report_format(self):
        from metabolon.organelles.inflammasome import probe_report

        with patch("metabolon.organelles.inflammasome._PROBES", [
            ("alpha", _ok_probe),
            ("beta", _fail_probe),
        ]):
            report = probe_report()

        assert "[PASS] alpha" in report
        assert "[FAIL] beta" in report
        assert "Summary: 1/2 passed" in report


# ---------------------------------------------------------------------------
# adaptive_response
# ---------------------------------------------------------------------------


class TestAdaptiveResponse:
    """Tests for adaptive_response — repair dispatch and priming logic."""

    def _make_results(self, **overrides):
        """Build a single result dict. Defaults to passed=True."""
        result = {
            "name": "test_probe",
            "passed": True,
            "message": "ok",
            "duration_ms": 5,
        }
        result.update(overrides)
        return [result]

    def test_passed_probe_gets_no_repair(self):
        from metabolon.organelles.inflammasome import adaptive_response

        results = self._make_results(passed=True)
        with patch("metabolon.organelles.inflammasome._load_priming", return_value={}):
            out = adaptive_response(results)

        assert out[0]["repair_attempted"] is None

    def test_failed_probe_priming_on_first_failure(self):
        """First failure should set repair_attempted='priming'."""
        from metabolon.organelles.inflammasome import adaptive_response

        results = self._make_results(passed=False, name="rss_state", message="state.json is stale: 52h")
        with patch("metabolon.organelles.inflammasome._load_priming", return_value={}):
            out = adaptive_response(results)

        assert out[0]["repair_attempted"] == "priming"

    def test_repair_dispatched_on_second_failure(self):
        """Second consecutive failure triggers the repair pattern."""
        from metabolon.organelles.inflammasome import adaptive_response

        results = self._make_results(passed=False, name="rss_state", message="state.json is stale: 52h")
        mock_repair = MagicMock(return_value=(True, "dispatched fetch"))

        with patch("metabolon.organelles.inflammasome._load_priming", return_value={"rss_state": 1}), \
             patch("metabolon.organelles.inflammasome._save_priming"), \
             patch("metabolon.organelles.inflammasome._REPAIR_PATTERNS", [
                 ("rss_state", lambda msg: "stale" in msg, mock_repair, "rss_fetch"),
             ]), \
             patch("metabolon.organelles.inflammasome._PROBES", []):
            out = adaptive_response(results)

        assert "rss_fetch" in out[0]["repair_attempted"]
        assert ":ok" in out[0]["repair_attempted"]
        mock_repair.assert_called_once()

    def test_repair_failure_recorded(self):
        """Failed repair attempt is recorded in repair_attempted field."""
        from metabolon.organelles.inflammasome import adaptive_response

        results = self._make_results(passed=False, name="rss_state", message="state.json is stale: 52h")
        mock_repair = MagicMock(return_value=(False, "binary not found"))

        with patch("metabolon.organelles.inflammasome._load_priming", return_value={"rss_state": 1}), \
             patch("metabolon.organelles.inflammasome._save_priming"), \
             patch("metabolon.organelles.inflammasome._REPAIR_PATTERNS", [
                 ("rss_state", lambda msg: "stale" in msg, mock_repair, "rss_fetch"),
             ]), \
             patch("metabolon.organelles.inflammasome._PROBES", []):
            out = adaptive_response(results)

        assert "rss_fetch:fail" in out[0]["repair_attempted"]

    def test_unknown_failure_gets_unknown_label(self):
        """Failure with no matching repair pattern gets 'unknown'."""
        from metabolon.organelles.inflammasome import adaptive_response

        results = self._make_results(passed=False, name="mystery_probe", message="weird error")
        with patch("metabolon.organelles.inflammasome._load_priming", return_value={"mystery_probe": 1}), \
             patch("metabolon.organelles.inflammasome._save_priming"), \
             patch("metabolon.organelles.inflammasome._REPAIR_PATTERNS", []), \
             patch("metabolon.organelles.inflammasome._CRITICAL_NO_REPAIR", {}):
            out = adaptive_response(results)

        assert out[0]["repair_attempted"] == "unknown"

    def test_critical_probe_logged_not_repaired(self):
        """Critical probes (structural config issues) get 'critical' label."""
        from metabolon.organelles.inflammasome import adaptive_response

        results = self._make_results(
            passed=False, name="endocytosis",
            message="sources.yaml not found: /path",
        )
        with patch("metabolon.organelles.inflammasome._load_priming", return_value={"endocytosis": 1}), \
             patch("metabolon.organelles.inflammasome._save_priming"), \
             patch("metabolon.organelles.inflammasome._REPAIR_PATTERNS", []), \
             patch("metabolon.organelles.inflammasome._CRITICAL_NO_REPAIR", {
                 "endocytosis": "dangling symlink or not found — config issue",
             }):
            out = adaptive_response(results)

        assert out[0]["repair_attempted"] == "critical"

    def test_mutation_in_place(self):
        """adaptive_response mutates the input list in place and returns it."""
        from metabolon.organelles.inflammasome import adaptive_response

        results = self._make_results(passed=True)
        with patch("metabolon.organelles.inflammasome._load_priming", return_value={}):
            out = adaptive_response(results)

        assert out is results


# ---------------------------------------------------------------------------
# is_primed — two-signal model
# ---------------------------------------------------------------------------


class TestIsPrimed:
    def test_first_failure_primes_but_not_active(self):
        from metabolon.organelles.inflammasome import is_primed

        priming = {}
        active = is_primed("probe_a", False, priming)

        assert active is False
        assert priming["probe_a"] == 1

    def test_second_failure_activates(self):
        from metabolon.organelles.inflammasome import is_primed

        priming = {"probe_a": 1}
        active = is_primed("probe_a", False, priming)

        assert active is True
        assert priming["probe_a"] == 2

    def test_pass_resets_counter(self):
        from metabolon.organelles.inflammasome import is_primed

        priming = {"probe_a": 3}
        active = is_primed("probe_a", True, priming)

        assert active is False
        assert "probe_a" not in priming


# ---------------------------------------------------------------------------
# check_pyroptosis — escalation threshold
# ---------------------------------------------------------------------------


class TestCheckPyroptosis:
    def test_below_threshold(self):
        from metabolon.organelles.inflammasome import check_pyroptosis

        assert check_pyroptosis("probe_a", {"probe_a": 2}) is False

    def test_at_threshold(self):
        from metabolon.organelles.inflammasome import check_pyroptosis, _PYROPTOSIS_THRESHOLD

        assert check_pyroptosis("probe_a", {"probe_a": _PYROPTOSIS_THRESHOLD}) is True

    def test_missing_probe_is_not_pyroptosis(self):
        from metabolon.organelles.inflammasome import check_pyroptosis

        assert check_pyroptosis("probe_a", {}) is False
