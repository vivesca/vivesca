"""Tests for dependency integrity checker."""
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest

def test_check_env_var_set():
    from metabolon.metabolism.dependency_check import check_env_var
    with patch.dict("os.environ", {"TEST_VAR": "a_long_enough_value_here"}):
        result = check_env_var("TEST_VAR")
        assert result.healthy

def test_check_env_var_missing():
    from metabolon.metabolism.dependency_check import check_env_var
    with patch.dict("os.environ", {}, clear=True):
        result = check_env_var("MISSING_VAR")
        assert not result.healthy

def test_check_env_var_too_short():
    from metabolon.metabolism.dependency_check import check_env_var
    with patch.dict("os.environ", {"SHORT": "abc"}):
        result = check_env_var("SHORT")
        assert not result.healthy

def test_check_binary_exists():
    from metabolon.metabolism.dependency_check import check_binary
    # python3 should always exist
    result = check_binary("python3")
    assert result.healthy

def test_check_binary_missing():
    from metabolon.metabolism.dependency_check import check_binary
    result = check_binary("nonexistent_binary_xyz_123")
    assert not result.healthy

def test_check_git_repo_valid(tmp_path):
    from metabolon.metabolism.dependency_check import check_git_repo
    import subprocess
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=str(tmp_path), capture_output=True)
    result = check_git_repo(tmp_path, "test")
    assert result.healthy

def test_check_git_repo_missing():
    from metabolon.metabolism.dependency_check import check_git_repo
    result = check_git_repo(Path("/nonexistent"), "test")
    assert not result.healthy

def test_dependency_status_dataclass():
    from metabolon.metabolism.dependency_check import DependencyStatus
    d = DependencyStatus(name="test", healthy=True, message="ok")
    assert d.category == "unknown"

def test_report_returns_string():
    from metabolon.metabolism.dependency_check import report
    result = report()
    assert isinstance(result, str)
    assert "Dependency check" in result
