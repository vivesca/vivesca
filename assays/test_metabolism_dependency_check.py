from __future__ import annotations

"""Tests for metabolon.metabolism.dependency_check."""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from metabolon.metabolism.dependency_check import (
    DependencyStatus,
    check_binary,
    check_env_var,
    check_git_repo,
    report,
    run_dependency_check,
)

# ── DependencyStatus dataclass ──────────────────────────────────────


class TestDependencyStatus:
    def test_defaults(self):
        s = DependencyStatus(name="x", healthy=True, message="ok")
        assert s.category == "unknown"

    def test_fields(self):
        s = DependencyStatus(name="n", healthy=False, message="msg", category="api_key")
        assert s.name == "n"
        assert not s.healthy
        assert s.message == "msg"
        assert s.category == "api_key"


# ── check_env_var ───────────────────────────────────────────────────


class TestCheckEnvVar:
    def test_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            result = check_env_var("MISSING_KEY")
        assert not result.healthy
        assert result.message == "Not set"
        assert result.category == "api_key"
        assert result.name == "MISSING_KEY"

    def test_too_short(self):
        with patch.dict(os.environ, {"SHORT": "abc"}, clear=True):
            result = check_env_var("SHORT", min_length=10)
        assert not result.healthy
        assert "Too short" in result.message
        assert "3 chars" in result.message

    def test_valid(self):
        with patch.dict(os.environ, {"GOOD_KEY": "a" * 20}, clear=True):
            result = check_env_var("GOOD_KEY")
        assert result.healthy
        assert result.message == "Set"

    def test_custom_min_length(self):
        with patch.dict(os.environ, {"K": "12345"}, clear=True):
            assert check_env_var("K", min_length=3).healthy
            assert not check_env_var("K", min_length=10).healthy


# ── check_binary ────────────────────────────────────────────────────


class TestCheckBinary:
    @patch("metabolon.metabolism.dependency_check.subprocess.run")
    @patch("shutil.which", return_value=None)
    def test_not_found(self, mock_which, mock_run):
        result = check_binary("missing_bin")
        assert not result.healthy
        assert "Not found" in result.message
        assert result.category == "binary"
        mock_run.assert_not_called()

    @patch("metabolon.metabolism.dependency_check.subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/goose")
    def test_found_healthy(self, mock_which, mock_run):
        result = check_binary("goose")
        assert result.healthy
        assert "/usr/bin/goose" in result.message
        mock_run.assert_called_once()

    @patch(
        "metabolon.metabolism.dependency_check.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="goose", timeout=5),
    )
    @patch("shutil.which", return_value="/usr/bin/goose")
    def test_timeout(self, mock_which, mock_run):
        result = check_binary("goose")
        assert not result.healthy
        assert result.category == "binary"

    @patch(
        "metabolon.metabolism.dependency_check.subprocess.run",
        side_effect=OSError("permission denied"),
    )
    @patch("shutil.which", return_value="/usr/bin/goose")
    def test_oserror(self, mock_which, mock_run):
        result = check_binary("goose")
        assert not result.healthy
        assert "permission denied" in result.message


# ── check_git_repo ──────────────────────────────────────────────────


class TestCheckGitRepo:
    @patch("metabolon.metabolism.dependency_check.Path.exists", return_value=False)
    def test_path_missing(self, mock_exists):
        result = check_git_repo(Path("/no/such/path"), "myrepo")
        assert not result.healthy
        assert "Path missing" in result.message
        assert result.category == "git_repo"

    @patch(
        "metabolon.metabolism.dependency_check.Path.exists",
        side_effect=lambda self=False: "fake" in str(self),
    )
    def test_not_a_git_repo(self, mock_exists):
        """Simulate .git missing by having path exist but .git not exist."""
        # We need a more targeted mock: path exists → True, but .git exists → False
        # Use a simpler approach: patch at instance level
        fake_path = MagicMock(spec=Path)
        fake_path.exists.return_value = True
        fake_path.__truediv__ = lambda s, k: MagicMock(
            spec=Path, exists=MagicMock(return_value=False)
        )
        result = check_git_repo(fake_path, "broken")
        assert not result.healthy
        assert "Not a git repo" in result.message

    @patch("metabolon.metabolism.dependency_check.subprocess.run")
    def test_healthy_repo(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")
        fake_path = MagicMock(spec=Path)
        fake_path.exists.return_value = True
        git_sub = MagicMock(spec=Path)
        git_sub.exists.return_value = True
        fake_path.__truediv__ = lambda s, k: git_sub
        result = check_git_repo(fake_path, "myrepo")
        assert result.healthy
        assert result.message == "OK"

    @patch("metabolon.metabolism.dependency_check.subprocess.run")
    def test_rev_parse_fails(self, mock_run):
        mock_run.return_value = MagicMock(returncode=128, stderr="error")
        fake_path = MagicMock(spec=Path)
        fake_path.exists.return_value = True
        git_sub = MagicMock(spec=Path)
        git_sub.exists.return_value = True
        fake_path.__truediv__ = lambda s, k: git_sub
        result = check_git_repo(fake_path, "corrupt")
        assert not result.healthy
        assert "git rev-parse failed" in result.message

    @patch(
        "metabolon.metabolism.dependency_check.subprocess.run",
        side_effect=OSError("io error"),
    )
    def test_subprocess_exception(self, mock_run):
        fake_path = MagicMock(spec=Path)
        fake_path.exists.return_value = True
        git_sub = MagicMock(spec=Path)
        git_sub.exists.return_value = True
        fake_path.__truediv__ = lambda s, k: git_sub
        result = check_git_repo(fake_path, "myrepo")
        assert not result.healthy
        assert "io error" in result.message


# ── run_dependency_check ────────────────────────────────────────────


class TestRunDependencyCheck:
    @patch("metabolon.metabolism.dependency_check.check_git_repo")
    @patch("metabolon.metabolism.dependency_check.check_binary")
    @patch("metabolon.metabolism.dependency_check.check_env_var")
    def test_returns_all_categories(self, mock_env, mock_bin, mock_git):
        mock_env.return_value = DependencyStatus("k", True, "ok", "api_key")
        mock_bin.return_value = DependencyStatus("b", True, "ok", "binary")
        mock_git.return_value = DependencyStatus("g", True, "ok", "git_repo")
        results = run_dependency_check()
        # 2 env vars + 5 binaries + 2 git repos = 9
        assert len(results) == 9
        assert mock_env.call_count == 2
        assert mock_bin.call_count == 5
        assert mock_git.call_count == 2

    @patch("metabolon.metabolism.dependency_check.check_git_repo")
    @patch("metabolon.metabolism.dependency_check.check_binary")
    @patch("metabolon.metabolism.dependency_check.check_env_var")
    def test_checks_expected_env_keys(self, mock_env, mock_bin, mock_git):
        mock_env.return_value = DependencyStatus("x", False, "nope", "api_key")
        mock_bin.return_value = DependencyStatus("x", False, "nope", "binary")
        mock_git.return_value = DependencyStatus("x", False, "nope", "git_repo")
        run_dependency_check()
        env_keys = {c.args[0] for c in mock_env.call_args_list}
        assert env_keys == {"ZHIPU_API_KEY", "ANTHROPIC_API_KEY"}

    @patch("metabolon.metabolism.dependency_check.check_git_repo")
    @patch("metabolon.metabolism.dependency_check.check_binary")
    @patch("metabolon.metabolism.dependency_check.check_env_var")
    def test_checks_expected_binaries(self, mock_env, mock_bin, mock_git):
        mock_env.return_value = DependencyStatus("x", False, "nope", "api_key")
        mock_bin.return_value = DependencyStatus("x", False, "nope", "binary")
        mock_git.return_value = DependencyStatus("x", False, "nope", "git_repo")
        run_dependency_check()
        binaries = {c.args[0] for c in mock_bin.call_args_list}
        assert binaries == {"goose", "sortase", "cytokinesis", "engram", "assay"}


# ── report ──────────────────────────────────────────────────────────


class TestReport:
    @patch("metabolon.metabolism.dependency_check.check_git_repo")
    @patch("metabolon.metabolism.dependency_check.check_binary")
    @patch("metabolon.metabolism.dependency_check.check_env_var")
    def test_report_format(self, mock_env, mock_bin, mock_git):
        mock_env.return_value = DependencyStatus("KEY1", True, "Set", "api_key")
        mock_bin.return_value = DependencyStatus("bin1", False, "Not found", "binary")
        mock_git.return_value = DependencyStatus("repo1", True, "OK", "git_repo")
        text = report()
        assert "Dependency check:" in text
        # Count healthy: 2 env (healthy) + 5 binary (unhealthy) + 2 git (healthy) = 4 healthy, 9 total
        assert "healthy" in text
        assert "[OK]" in text
        assert "[FAIL]" in text

    @patch("metabolon.metabolism.dependency_check.check_git_repo")
    @patch("metabolon.metabolism.dependency_check.check_binary")
    @patch("metabolon.metabolism.dependency_check.check_env_var")
    def test_report_counts(self, mock_env, mock_bin, mock_git):
        mock_env.return_value = DependencyStatus("k", True, "ok", "api_key")
        mock_bin.return_value = DependencyStatus("b", True, "ok", "binary")
        mock_git.return_value = DependencyStatus("g", True, "ok", "git_repo")
        text = report()
        assert "9/9 healthy" in text
