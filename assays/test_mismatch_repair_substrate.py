from __future__ import annotations

"""Tests for AnamScanSubstrate (mismatch_repair)."""


import subprocess
from unittest.mock import patch, MagicMock
from metabolon.metabolism.substrates.mismatch_repair import AnamScanSubstrate, _run


# --- _run helper ---

def test_mismatch_repair_substrate_run_success():
    with patch("metabolon.metabolism.substrates.mismatch_repair.subprocess.run") as mock:
        mock.return_value = subprocess.CompletedProcess(args=["x"], returncode=0, stdout="ok", stderr="")
        result = _run(["x"])
        assert result.returncode == 0
        assert result.stdout == "ok"


def test_mismatch_repair_substrate_run_timeout():
    with patch("metabolon.metabolism.substrates.mismatch_repair.subprocess.run",
               side_effect=subprocess.TimeoutExpired("x", 5)):
        result = _run(["x"], timeout=5)
        assert result.returncode == 1
        assert "timeout" in result.stderr


def test_run_not_found():
    with patch("metabolon.metabolism.substrates.mismatch_repair.subprocess.run",
               side_effect=FileNotFoundError("x")):
        result = _run(["x"])
        assert result.returncode == 1
        assert "not found" in result.stderr


# --- AnamScanSubstrate ---

def test_mismatch_repair_substrate_name():
    s = AnamScanSubstrate()
    assert s.name == "mismatch_repair"


def test_sense_error():
    with patch("metabolon.metabolism.substrates.mismatch_repair._run") as mock:
        mock.return_value = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="bad")
        result = s = AnamScanSubstrate()
        signals = s.sense()
        assert len(signals) == 1
        assert signals[0]["kind"] == "error"


def test_sense_parses_sessions():
    with patch("metabolon.metabolism.substrates.mismatch_repair._run") as mock:
        mock.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Sessions: 15\nCorrections: 8 across 5 sessions\n", stderr=""
        )
        s = AnamScanSubstrate()
        signals = s.sense()
        kinds = [sig["kind"] for sig in signals]
        assert "sessions" in kinds
        assert "corrections" in kinds
        sessions = next(sig for sig in signals if sig["kind"] == "sessions")
        assert sessions["count"] == 15


def test_sense_no_data():
    with patch("metabolon.metabolism.substrates.mismatch_repair._run") as mock:
        mock.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        s = AnamScanSubstrate()
        signals = s.sense()
        assert signals[0]["kind"] == "no_data"


def test_candidates_high_corrections():
    s = AnamScanSubstrate()
    sensed = [{"kind": "corrections", "total": 20, "sessions": 10}]
    cands = s.candidates(sensed)
    assert len(cands) >= 1
    assert cands[0]["action"] == "daily_scan"
    assert cands[0]["priority"] == "high"


def test_candidates_enough_sessions():
    s = AnamScanSubstrate()
    sensed = [{"kind": "sessions", "count": 12}]
    cands = s.candidates(sensed)
    assert len(cands) >= 1
    assert cands[0]["action"] == "daily_scan"


def test_candidates_not_enough():
    s = AnamScanSubstrate()
    sensed = [{"kind": "sessions", "count": 3}]
    cands = s.candidates(sensed)
    # May be empty or just a Sunday synthesis entry
    daily = [c for c in cands if c["action"] == "daily_scan"]
    assert len(daily) == 0


def test_act_daily():
    with patch("metabolon.metabolism.substrates.mismatch_repair._run") as mock:
        mock.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="done\n", stderr="")
        s = AnamScanSubstrate()
        result = s.act({"action": "daily_scan"})
        assert "completed" in result


def test_act_weekly():
    with patch("metabolon.metabolism.substrates.mismatch_repair._run") as mock:
        mock.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="synth done\n", stderr="")
        s = AnamScanSubstrate()
        result = s.act({"action": "weekly_synthesis"})
        assert "completed" in result


def test_act_failure():
    with patch("metabolon.metabolism.substrates.mismatch_repair._run") as mock:
        mock.return_value = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="crash")
        s = AnamScanSubstrate()
        result = s.act({"action": "daily_scan"})
        assert "failed" in result


def test_mismatch_repair_substrate_report_format():
    s = AnamScanSubstrate()
    sensed = [
        {"kind": "sessions", "count": 10},
        {"kind": "corrections", "total": 5, "sessions": 3},
    ]
    report = s.report(sensed, ["completed: daily_scan"])
    assert "Sessions: 10" in report
    assert "Corrections: 5" in report
    assert "daily_scan" in report
