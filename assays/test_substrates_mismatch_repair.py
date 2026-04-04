from __future__ import annotations

"""Tests for metabolon.metabolism.substrates.mismatch_repair."""

import subprocess
from unittest.mock import patch

from metabolon.metabolism.substrates.mismatch_repair import (
    AnamScanSubstrate,
    _run,
)

# ---------------------------------------------------------------------------
# _run helper
# ---------------------------------------------------------------------------


class TestRun:
    """Tests for the _run wrapper around subprocess.run."""

    @patch("metabolon.metabolism.substrates.mismatch_repair.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo"], returncode=0, stdout="ok\n", stderr=""
        )
        result = _run(["echo", "hello"])
        assert result.returncode == 0
        assert result.stdout == "ok\n"

    @patch("metabolon.metabolism.substrates.mismatch_repair.subprocess.run")
    def test_timeout_returns_error(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["x"], timeout=300)
        result = _run(["slow-cmd"], timeout=5)
        assert result.returncode == 1
        assert "timeout" in result.stderr

    @patch("metabolon.metabolism.substrates.mismatch_repair.subprocess.run")
    def test_file_not_found_returns_error(self, mock_run):
        mock_run.side_effect = FileNotFoundError("no such binary")
        result = _run(["nonexistent"])
        assert result.returncode == 1
        assert "not found" in result.stderr


# ---------------------------------------------------------------------------
# AnamScanSubstrate.sense
# ---------------------------------------------------------------------------


class TestSense:
    def setup_method(self):
        self.sub = AnamScanSubstrate()

    @patch("metabolon.metabolism.substrates.mismatch_repair._run")
    def test_parses_sessions_line(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Sessions: 12\nCorrections: 3 across 2 sessions\n",
            stderr="",
        )
        signals = self.sub.sense(days=7)
        kinds = {s["kind"] for s in signals}
        assert "sessions" in kinds
        assert "corrections" in kinds
        sessions_sig = next(s for s in signals if s["kind"] == "sessions")
        assert sessions_sig["count"] == 12
        corrections_sig = next(s for s in signals if s["kind"] == "corrections")
        assert corrections_sig["total"] == 3
        assert corrections_sig["sessions"] == 2

    @patch("metabolon.metabolism.substrates.mismatch_repair._run")
    def test_returns_error_on_failure(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="something broke"
        )
        signals = self.sub.sense()
        assert len(signals) == 1
        assert signals[0]["kind"] == "error"
        assert "something broke" in signals[0]["message"]

    @patch("metabolon.metabolism.substrates.mismatch_repair._run")
    def test_no_data_when_empty_output(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        signals = self.sub.sense()
        assert len(signals) == 1
        assert signals[0]["kind"] == "no_data"

    @patch("metabolon.metabolism.substrates.mismatch_repair._run")
    def test_session_prompts_parsed(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Sessions: 5\nSession prompts: 42\n",
            stderr="",
        )
        signals = self.sub.sense()
        prompt_sig = next(s for s in signals if s["kind"] == "session_prompts")
        assert prompt_sig["count"] == 42


# ---------------------------------------------------------------------------
# AnamScanSubstrate.candidates
# ---------------------------------------------------------------------------


class TestCandidates:
    def setup_method(self):
        self.sub = AnamScanSubstrate()

    def test_high_priority_with_many_correction_sessions(self):
        sensed = [
            {"kind": "corrections", "total": 20, "sessions": 12},
            {"kind": "sessions", "count": 15},
        ]
        result = self.sub.candidates(sensed)
        assert len(result) >= 1
        daily = next(c for c in result if c["action"] == "daily_scan")
        assert daily["priority"] == "high"

    def test_normal_priority_with_5_correction_sessions(self):
        sensed = [
            {"kind": "corrections", "total": 8, "sessions": 5},
        ]
        result = self.sub.candidates(sensed)
        daily = next(c for c in result if c["action"] == "daily_scan")
        assert daily["priority"] == "normal"

    def test_session_count_threshold_triggers_scan(self):
        sensed = [
            {"kind": "sessions", "count": 10},
        ]
        result = self.sub.candidates(sensed)
        actions = [c["action"] for c in result]
        assert "daily_scan" in actions

    def test_below_threshold_returns_empty(self):
        sensed = [
            {"kind": "sessions", "count": 3},
            {"kind": "corrections", "total": 2, "sessions": 1},
        ]
        result = self.sub.candidates(sensed)
        # daily_scan should NOT appear (sessions<10, correction_sessions<5)
        daily_actions = [c for c in result if c["action"] == "daily_scan"]
        assert len(daily_actions) == 0

    @patch("datetime.date")
    def test_weekly_synthesis_on_sunday(self, mock_date_cls):
        mock_date_cls.today.return_value.weekday.return_value = 6  # Sunday
        sensed = [{"kind": "sessions", "count": 2}]
        result = self.sub.candidates(sensed)
        weekly = [c for c in result if c["action"] == "weekly_synthesis"]
        assert len(weekly) == 1
        assert weekly[0]["priority"] == "normal"


# ---------------------------------------------------------------------------
# AnamScanSubstrate.act
# ---------------------------------------------------------------------------


class TestAct:
    def setup_method(self):
        self.sub = AnamScanSubstrate()

    @patch("metabolon.metabolism.substrates.mismatch_repair._run")
    def test_daily_scan_success(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="line1\nscan complete: 3 topics\n",
            stderr="",
        )
        result = self.sub.act({"action": "daily_scan"})
        assert result.startswith("completed:")
        assert "scan complete" in result

    @patch("metabolon.metabolism.substrates.mismatch_repair._run")
    def test_weekly_synthesis_success(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="synthesis done\nall good\n",
            stderr="",
        )
        result = self.sub.act({"action": "weekly_synthesis"})
        assert result.startswith("completed:")
        assert "all good" in result

    @patch("metabolon.metabolism.substrates.mismatch_repair._run")
    def test_act_failure(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="error: bad input"
        )
        result = self.sub.act({"action": "daily_scan"})
        assert result.startswith("failed:")
        assert "error: bad input" in result


# ---------------------------------------------------------------------------
# AnamScanSubstrate.report
# ---------------------------------------------------------------------------


class TestReport:
    def setup_method(self):
        self.sub = AnamScanSubstrate()

    def test_report_formats_all_sections(self):
        sensed = [
            {"kind": "sessions", "count": 8},
            {"kind": "corrections", "total": 15, "sessions": 4},
            {"kind": "session_prompts", "count": 23},
        ]
        acted = ["completed: daily_scan -- done"]
        report = self.sub.report(sensed, acted)
        assert "Sessions: 8" in report
        assert "Corrections: 15 across 4 sessions" in report
        assert "Prompt sets: 23" in report
        assert "Actions" in report
        assert "completed: daily_scan" in report

    def test_report_handles_empty_sensed(self):
        report = self.sub.report([], [])
        assert "Anam scan substrate report" in report

    def test_report_missing_optional_sections(self):
        sensed = [
            {"kind": "sessions", "count": 3},
        ]
        report = self.sub.report(sensed, [])
        assert "Sessions: 3" in report
        assert "Corrections" not in report
        assert "Actions" not in report
