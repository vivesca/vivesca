"""Tests for preflight health validator."""
from unittest.mock import patch, MagicMock
from pathlib import Path
import time
import pytest

def test_check_result_dataclass():
    from metabolon.metabolism.preflight import CheckResult
    c = CheckResult(name="test", passed=True, message="OK")
    assert c.passed
    assert c.severity == "info"

def test_preflight_result_add_critical():
    from metabolon.metabolism.preflight import PreflightResult, CheckResult
    r = PreflightResult()
    r.add(CheckResult(name="bad", passed=False, message="fail", severity="critical"))
    assert r.passed is False
    assert r.critical_failures == 1

def test_preflight_result_add_warning():
    from metabolon.metabolism.preflight import PreflightResult, CheckResult
    r = PreflightResult()
    r.add(CheckResult(name="meh", passed=False, message="warn", severity="warning"))
    assert r.passed is True  # warnings don't block
    assert r.warnings == 1

def test_preflight_result_summary():
    from metabolon.metabolism.preflight import PreflightResult, CheckResult
    r = PreflightResult()
    r.add(CheckResult(name="a", passed=True, message="ok"))
    r.add(CheckResult(name="b", passed=False, message="bad", severity="critical"))
    s = r.summary()
    assert "1/2 passed" in s
    assert "CRITICAL" in s

def test_check_repo_reachable_exists(tmp_path):
    from metabolon.metabolism.preflight import check_repo_reachable
    (tmp_path / ".git").mkdir()
    result = check_repo_reachable(tmp_path, "test")
    assert result.passed

def test_check_repo_reachable_missing():
    from metabolon.metabolism.preflight import check_repo_reachable
    result = check_repo_reachable(Path("/nonexistent/path"), "test")
    assert not result.passed
    assert result.severity == "critical"

def test_check_api_key_set():
    from metabolon.metabolism.preflight import check_api_key
    with patch.dict("os.environ", {"TEST_KEY": "sk-1234567890abcdef"}):
        result = check_api_key("TEST_KEY")
        assert result.passed

def test_check_api_key_missing():
    from metabolon.metabolism.preflight import check_api_key
    with patch.dict("os.environ", {}, clear=True):
        result = check_api_key("NONEXISTENT_KEY")
        assert not result.passed

def test_check_api_key_too_short():
    from metabolon.metabolism.preflight import check_api_key
    with patch.dict("os.environ", {"SHORT_KEY": "abc"}):
        result = check_api_key("SHORT_KEY")
        assert not result.passed

def test_check_signal_bus_missing():
    from metabolon.metabolism.preflight import check_signal_bus
    with patch("metabolon.metabolism.preflight.SIGNAL_BUS", Path("/nonexistent")):
        result = check_signal_bus()
        assert not result.passed

def test_run_preflight_returns_result():
    from metabolon.metabolism.preflight import run_preflight
    # Run against real system — should at minimum not crash
    result = run_preflight(api_keys=[])
    assert hasattr(result, "passed")
    assert hasattr(result, "checks")
    assert len(result.checks) > 0
