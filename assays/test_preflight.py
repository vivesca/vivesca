from __future__ import annotations

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


# --- check_golem_ready tests ---


def test_check_golem_binary_found_in_path():
    from metabolon.metabolism.preflight import check_golem_binary
    with patch("metabolon.metabolism.preflight.shutil.which") as mock_which:
        mock_which.return_value = "/usr/local/bin/golem"
        result = check_golem_binary()
        assert result.passed
        assert "Found" in result.message


def test_check_golem_binary_found_in_default():
    from metabolon.metabolism.preflight import check_golem_binary
    with patch("metabolon.metabolism.preflight.shutil.which") as mock_which:
        mock_which.return_value = None
        with patch("metabolon.metabolism.preflight.HOME") as mock_home:
            mock_home.__truediv__ = lambda self, x: Path("/home/user/germline/effectors/golem")
            with patch("pathlib.Path.exists") as mock_exists:
                with patch("os.access") as mock_access:
                    mock_exists.return_value = True
                    mock_access.return_value = True
                    result = check_golem_binary()
                    assert result.passed


def test_check_golem_binary_not_found():
    from metabolon.metabolism.preflight import check_golem_binary
    with patch("metabolon.metabolism.preflight.shutil.which") as mock_which:
        mock_which.return_value = None
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False
            result = check_golem_binary()
            assert not result.passed
            assert result.severity == "critical"


def test_check_golem_api_key_valid_provider():
    from metabolon.metabolism.preflight import check_golem_api_key
    with patch.dict("os.environ", {"ZHIPU_API_KEY": "test-key-12345678"}):
        result = check_golem_api_key("zhipu")
        assert result.passed


def test_check_golem_api_key_unknown_provider():
    from metabolon.metabolism.preflight import check_golem_api_key
    result = check_golem_api_key("unknown_provider")
    assert not result.passed
    assert "Unknown provider" in result.message


def test_check_golem_api_key_missing():
    from metabolon.metabolism.preflight import check_golem_api_key
    with patch.dict("os.environ", {}, clear=True):
        result = check_golem_api_key("zhipu")
        assert not result.passed


def test_check_provider_health_success():
    from metabolon.metabolism.preflight import check_provider_health
    with patch.dict("os.environ", {"ZHIPU_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.__enter__ = lambda self: self
            mock_response.__exit__ = lambda self, *args: None
            mock_urlopen.return_value = mock_response
            result = check_provider_health("zhipu")
            assert result.passed


def test_check_provider_health_network_error():
    from metabolon.metabolism.preflight import check_provider_health
    import urllib.error
    with patch.dict("os.environ", {"ZHIPU_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("connection refused")
            result = check_provider_health("zhipu")
            assert not result.passed
            assert result.severity == "warning"


def test_check_provider_health_unknown_provider():
    from metabolon.metabolism.preflight import check_provider_health
    result = check_provider_health("unknown")
    assert not result.passed
    assert "Unknown provider" in result.message


def test_check_golem_log_freshness_missing():
    from metabolon.metabolism.preflight import check_golem_log_freshness
    with patch("metabolon.metabolism.preflight.GOLEM_LOG") as mock_log:
        mock_log.exists.return_value = False
        result = check_golem_log_freshness()
        assert not result.passed
        assert result.severity == "info"


def test_check_golem_log_freshness_recent():
    from metabolon.metabolism.preflight import check_golem_log_freshness
    with patch("metabolon.metabolism.preflight.GOLEM_LOG") as mock_log:
        mock_log.exists.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_mtime = time.time() - 3600  # 1 hour ago
        mock_log.stat.return_value = mock_stat
        result = check_golem_log_freshness()
        assert result.passed


def test_check_golem_log_freshness_stale():
    from metabolon.metabolism.preflight import check_golem_log_freshness
    with patch("metabolon.metabolism.preflight.GOLEM_LOG") as mock_log:
        mock_log.exists.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_mtime = time.time() - 86400 * 2  # 2 days ago
        mock_log.stat.return_value = mock_stat
        result = check_golem_log_freshness(max_hours=24)
        assert not result.passed


def test_check_golem_ready_comprehensive():
    from metabolon.metabolism.preflight import check_golem_ready
    with patch("metabolon.metabolism.preflight.check_golem_binary") as mock_binary:
        with patch("metabolon.metabolism.preflight.check_golem_api_key") as mock_key:
            with patch("metabolon.metabolism.preflight.check_provider_health") as mock_health:
                with patch("metabolon.metabolism.preflight.check_golem_log_freshness") as mock_log:
                    mock_binary.return_value = MagicMock(passed=True, name="golem_binary")
                    mock_key.return_value = MagicMock(passed=True, name="golem_api_key")
                    mock_health.return_value = MagicMock(passed=True, name="provider_health")
                    mock_log.return_value = MagicMock(passed=True, name="golem_log")
                    result = check_golem_ready(provider="zhipu")
                    assert len(result.checks) == 4


def test_check_golem_ready_skip_health():
    from metabolon.metabolism.preflight import check_golem_ready
    with patch("metabolon.metabolism.preflight.check_golem_binary") as mock_binary:
        with patch("metabolon.metabolism.preflight.check_golem_api_key") as mock_key:
            with patch("metabolon.metabolism.preflight.check_provider_health") as mock_health:
                with patch("metabolon.metabolism.preflight.check_golem_log_freshness") as mock_log:
                    mock_binary.return_value = MagicMock(passed=True)
                    mock_key.return_value = MagicMock(passed=True)
                    mock_log.return_value = MagicMock(passed=True)
                    result = check_golem_ready(provider="zhipu", skip_health_check=True)
                    mock_health.assert_not_called()
                    assert len(result.checks) == 3
