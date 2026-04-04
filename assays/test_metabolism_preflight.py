import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from metabolon.metabolism.preflight import (
    PROVIDER_CONFIG,
    CheckResult,
    PreflightResult,
    check_api_key,
    check_provider_health,
    check_repo_freshness,
    check_repo_reachable,
    check_ribosome_api_key,
    check_ribosome_binary,
    check_ribosome_log_freshness,
    check_ribosome_ready,
    check_signal_bus,
    run_preflight,
)


def test_check_result_creation():
    """Test CheckResult dataclass creation."""
    cr = CheckResult(name="test", passed=True, message="OK", severity="info")
    assert cr.name == "test"
    assert cr.passed is True
    assert cr.message == "OK"
    assert cr.severity == "info"


def test_preflight_result_add():
    """Test adding checks to PreflightResult."""
    pr = PreflightResult()
    assert pr.passed is True
    assert pr.critical_failures == 0
    assert pr.warnings == 0

    # Add passing check
    pr.add(CheckResult(name="pass1", passed=True, message="ok"))
    assert len(pr.checks) == 1
    assert pr.passed is True
    assert pr.critical_failures == 0
    assert pr.warnings == 0

    # Add critical failing check
    pr.add(CheckResult(name="fail1", passed=False, message="bad", severity="critical"))
    assert len(pr.checks) == 2
    assert pr.passed is False
    assert pr.critical_failures == 1
    assert pr.warnings == 0

    # Add warning failing check
    pr.add(CheckResult(name="warn1", passed=False, message="warning", severity="warning"))
    assert len(pr.checks) == 3
    assert pr.passed is False
    assert pr.critical_failures == 1
    assert pr.warnings == 1


def test_preflight_summary():
    """Test summary output formatting."""
    pr = PreflightResult()
    pr.add(CheckResult(name="test1", passed=True, message="OK"))
    pr.add(CheckResult(name="test2", passed=False, message="fail", severity="critical"))
    pr.add(CheckResult(name="test3", passed=False, message="warn", severity="warning"))

    summary = pr.summary()
    assert "Preflight: 1/3 passed" in summary
    assert "[OK] test1: OK" in summary
    assert "[CRITICAL] test2: fail" in summary
    assert "[WARN] test3: warn" in summary


def test_check_repo_reachable_not_exists():
    """Test check_repo_reachable when path doesn't exist."""
    with patch("pathlib.Path.exists", return_value=False):
        result = check_repo_reachable(Path("/fake/path"), "test")
        assert not result.passed
        assert result.severity == "critical"
        assert "not found" in result.message


def test_check_repo_reachable_not_git():
    """Test check_repo_reachable when path exists but isn't a git repo."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.__truediv__", return_value=MagicMock(exists=lambda: False)):
            result = check_repo_reachable(Path("/fake/path"), "test")
            assert not result.passed
            assert result.severity == "critical"
            assert "not a git repo" in result.message


def test_check_repo_reachable_ok():
    """Test check_repo_reachable when everything is good."""
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_git_dir = MagicMock()
    mock_git_dir.exists.return_value = True
    mock_path.__truediv__.return_value = mock_git_dir

    result = check_repo_reachable(mock_path, "test")
    assert result.passed
    assert result.message == "OK"


@patch("subprocess.run")
def test_check_repo_freshness_git_fails(mock_run):
    """Test check_repo_freshness when git command fails."""
    mock_run.return_value = MagicMock(returncode=1, stdout="")
    result = check_repo_freshness(Path("/fake/path"), "test")
    assert not result.passed
    assert result.severity == "warning"
    assert "git log failed" in result.message


@patch("subprocess.run")
@patch("time.time")
def test_check_repo_freshness_stale(mock_time, mock_run):
    """Test check_repo_freshness when repo is stale."""
    mock_time.return_value = 3600 * 10  # 10 hours
    mock_run.return_value = MagicMock(returncode=0, stdout="0\n")  # 0 timestamp = 10h old
    result = check_repo_freshness(Path("/fake/path"), "test", max_hours=4)
    assert not result.passed
    assert result.severity == "warning"
    assert "Last commit 10.0h ago" in result.message


@patch("subprocess.run")
@patch("time.time")
def test_check_repo_freshness_ok(mock_time, mock_run):
    """Test check_repo_freshness when repo is fresh."""
    current_time = 3600 * 10
    mock_time.return_value = current_time
    recent_ts = int(current_time - 3600 * 2)  # 2 hours ago
    mock_run.return_value = MagicMock(returncode=0, stdout=f"{recent_ts}\n")
    result = check_repo_freshness(Path("/fake/path"), "test", max_hours=4)
    assert result.passed
    assert "2.0h since last commit" in result.message


@patch("subprocess.run")
def test_check_repo_freshness_exception(mock_run):
    """Test check_repo_freshness handles exceptions."""
    mock_run.side_effect = Exception("Something went wrong")
    result = check_repo_freshness(Path("/fake/path"), "test")
    assert not result.passed
    assert "Something went wrong" in result.message


@patch("metabolon.metabolism.preflight.SIGNAL_BUS")
def test_check_signal_bus_missing(mock_signal_bus):
    """Test check_signal_bus when file missing."""
    mock_signal_bus.exists.return_value = False
    result = check_signal_bus()
    assert not result.passed
    assert result.severity == "warning"
    assert "missing" in result.message


@patch("metabolon.metabolism.preflight.SIGNAL_BUS")
def test_check_signal_bus_not_writable(mock_signal_bus):
    """Test check_signal_bus when file not writable."""
    mock_signal_bus.exists.return_value = True
    with patch("os.access", return_value=False):
        result = check_signal_bus()
        assert not result.passed
        assert result.severity == "critical"
        assert "not writable" in result.message


@patch("metabolon.metabolism.preflight.SIGNAL_BUS")
@patch("time.time")
def test_check_signal_bus_stale(mock_time, mock_signal_bus):
    """Test check_signal_bus when file is stale."""
    mock_signal_bus.exists.return_value = True
    mock_signal_bus.stat.return_value = MagicMock(st_mtime=0)
    mock_time.return_value = 3600 * 13  # 13 hours old
    with patch("os.access", return_value=True):
        result = check_signal_bus()
        assert not result.passed
        assert result.severity == "warning"
        assert "stale" in result.message


@patch("metabolon.metabolism.preflight.SIGNAL_BUS")
@patch("time.time")
def test_check_signal_bus_ok(mock_time, mock_signal_bus):
    """Test check_signal_bus when everything is good."""
    mock_signal_bus.exists.return_value = True
    mock_signal_bus.stat.return_value = MagicMock(st_mtime=3600 * 10)
    mock_time.return_value = 3600 * 15  # 5 hours old
    with patch("os.access", return_value=True):
        result = check_signal_bus()
        assert result.passed
        assert result.message == "OK"


def test_check_api_key_not_set():
    """Test check_api_key when env var not set."""
    with patch.dict(os.environ, {}, clear=True):
        result = check_api_key("TEST_KEY")
        assert not result.passed
        assert "not set" in result.message


def test_check_api_key_too_short():
    """Test check_api_key when env var has short value."""
    with patch.dict(os.environ, {"TEST_KEY": "short"}):
        result = check_api_key("TEST_KEY")
        assert not result.passed
        assert "suspiciously short" in result.message


def test_check_api_key_ok():
    """Test check_api_key when everything is good."""
    with patch.dict(os.environ, {"TEST_KEY": "thisisalongenoughkey"}):
        result = check_api_key("TEST_KEY")
        assert result.passed
        assert result.message == "Set"


@patch("metabolon.metabolism.preflight.check_repo_reachable")
@patch("metabolon.metabolism.preflight.check_repo_freshness")
@patch("metabolon.metabolism.preflight.check_signal_bus")
def test_run_preflight_default_keys(mock_signal, mock_fresh, mock_reach):
    """Test run_preflight with default API keys."""
    mock_reach.return_value = CheckResult(name="test", passed=True, message="ok")
    mock_fresh.return_value = CheckResult(name="test", passed=True, message="ok")
    mock_signal.return_value = CheckResult(name="signal_bus", passed=True, message="ok")

    with patch.dict(
        os.environ, {"ZHIPU_API_KEY": "fakekey", "ANTHROPIC_API_KEY": "fakelongerkey"}
    ):
        result = run_preflight()
        assert mock_reach.call_count == 2
        assert mock_fresh.call_count == 2
        assert mock_signal.call_count == 1
        assert len(result.checks) == 2 + 2 + 1 + 2  # 2 reach, 2 fresh, 1 signal, 2 api keys


@patch("shutil.which")
def test_check_ribosome_binary_not_found(mock_which):
    """Test check_ribosome_binary when binary not found."""
    mock_which.return_value = None
    with patch("pathlib.Path.exists", return_value=False):
        result = check_ribosome_binary()
        assert not result.passed
        assert result.severity == "critical"
        assert "not found" in result.message


@patch("shutil.which")
def test_check_ribosome_binary_not_executable(mock_which):
    """Test check_ribosome_binary when found but not executable."""
    mock_which.return_value = None
    with patch("pathlib.Path.exists", return_value=True):
        with patch("os.access", return_value=False):
            result = check_ribosome_binary()
            assert not result.passed
            assert result.severity == "critical"
            assert "not executable" in result.message


@patch("shutil.which")
def test_check_ribosome_binary_found_in_default(mock_which):
    """Test check_ribosome_binary when found in default location."""
    mock_which.return_value = None
    with patch("pathlib.Path.exists", return_value=True):
        with patch("os.access", return_value=True):
            result = check_ribosome_binary()
            assert result.passed
            assert "Found at" in result.message


@patch("shutil.which")
def test_check_ribosome_binary_found_in_path(mock_which):
    """Test check_ribosome_binary when found in PATH."""
    mock_which.return_value = "/usr/bin/ribosome"
    result = check_ribosome_binary()
    assert result.passed
    assert "Found at /usr/bin/ribosome" in result.message


def test_check_ribosome_api_key_unknown_provider():
    """Test check_ribosome_api_key with unknown provider."""
    result = check_ribosome_api_key("nonexistent")
    assert not result.passed
    assert "Unknown provider" in result.message


def test_check_ribosome_api_key_ok():
    """Test check_ribosome_api_key for known provider."""
    for provider, config in PROVIDER_CONFIG.items():
        with patch.dict(os.environ, {config["key_var"]: "validapikey123"}):
            result = check_ribosome_api_key(provider)
            assert result.passed


def test_check_provider_health_unknown_provider():
    """Test check_provider_health with unknown provider."""
    result = check_provider_health("nonexistent")
    assert not result.passed
    assert "Unknown provider" in result.message
    assert result.severity == "warning"


def test_check_provider_health_no_key():
    """Test check_provider_health when no API key set."""
    with patch.dict(os.environ, {}, clear=True):
        result = check_provider_health("zhipu")
        assert not result.passed
        assert "No API key" in result.message


@patch("urllib.request.urlopen")
def test_check_provider_health_ok(mock_urlopen):
    """Test check_provider_health when all good."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    with patch.dict(os.environ, {"ZHIPU_API_KEY": "validkey123"}):
        result = check_provider_health("zhipu")
        assert result.passed
        assert "API reachable" in result.message


@patch("urllib.request.urlopen")
def test_check_provider_health_non_200(mock_urlopen):
    """Test check_provider_health with non-200 status."""
    mock_response = MagicMock()
    mock_response.status = 500
    mock_urlopen.return_value.__enter__.return_value = mock_response

    with patch.dict(os.environ, {"ZHIPU_API_KEY": "validkey123"}):
        result = check_provider_health("zhipu")
        assert not result.passed
        assert "API returned status 500" in result.message


@patch("urllib.request.urlopen")
def test_check_provider_health_url_error(mock_urlopen):
    """Test check_provider_health with URL error."""
    import urllib.error

    mock_urlopen.side_effect = urllib.error.URLError("connection refused")

    with patch.dict(os.environ, {"ZHIPU_API_KEY": "validkey123"}):
        result = check_provider_health("zhipu")
        assert not result.passed
        assert "Network error" in result.message
        assert result.severity == "warning"


@patch("metabolon.metabolism.preflight.RIBOSOME_LOG")
def test_check_ribosome_log_freshness_missing(mock_ribosome_log):
    """Test check_ribosome_log_freshness when log doesn't exist."""
    mock_ribosome_log.exists.return_value = False
    result = check_ribosome_log_freshness()
    assert not result.passed
    assert result.severity == "info"
    assert "No ribosome log found" in result.message


@patch("metabolon.metabolism.preflight.RIBOSOME_LOG")
@patch("time.time")
def test_check_ribosome_log_freshness_stale(mock_time, mock_ribosome_log):
    """Test check_ribosome_log_freshness when stale."""
    mock_ribosome_log.exists.return_value = True
    mock_ribosome_log.stat.return_value = MagicMock(st_mtime=0)
    mock_time.return_value = 3600 * 25  # 25 hours
    result = check_ribosome_log_freshness(max_hours=24)
    assert not result.passed
    assert result.severity == "info"
    assert "Ribosome last used 25.0h ago" in result.message


@patch("metabolon.metabolism.preflight.RIBOSOME_LOG")
@patch("time.time")
def test_check_ribosome_log_freshness_ok(mock_time, mock_ribosome_log):
    """Test check_ribosome_log_freshness when fresh."""
    mock_ribosome_log.exists.return_value = True
    mock_ribosome_log.stat.return_value = MagicMock(st_mtime=3600 * 12)
    mock_time.return_value = 3600 * 20  # 8 hours
    result = check_ribosome_log_freshness(max_hours=24)
    assert result.passed
    assert "Last used 8.0h ago" in result.message


def test_check_ribosome_ready_skip_health():
    """Test check_ribosome_ready with health check skipped."""
    with patch("metabolon.metabolism.preflight.check_ribosome_binary") as mock_bin:
        with patch("metabolon.metabolism.preflight.check_ribosome_api_key") as mock_key:
            with patch("metabolon.metabolism.preflight.check_ribosome_log_freshness") as mock_log:
                mock_bin.return_value = CheckResult(name="bin", passed=True, message="ok")
                mock_key.return_value = CheckResult(name="key", passed=True, message="ok")
                mock_log.return_value = CheckResult(name="log", passed=True, message="ok")

                result = check_ribosome_ready("zhipu", skip_health_check=True)
                assert mock_bin.called
                assert mock_key.called
                assert mock_log.called
                assert len(result.checks) == 3
