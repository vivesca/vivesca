from __future__ import annotations

"""Tests for metabolon/organelles/mitosis.py — asymmetric cell division sync."""

import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.mitosis import (
    SYNC_TARGETS,
    FidelityReport,
    ReplicationResult,
    _build_commit_message,
    _expand,
    _fly_cmd,
    _git_pull_remote,
    _git_push,
    _is_soma_reachable,
    _running_on_soma,
    _sync_target,
    setup,
    smoketest,
    status,
    sync,
)

# ── Dataclass tests ──────────────────────────────────────────────────


class TestReplicationResult:
    def test_fields(self):
        r = ReplicationResult("germline", True, 1.5, "pushed")
        assert r.target == "germline"
        assert r.success is True
        assert r.elapsed_s == 1.5
        assert r.message == "pushed"

    def test_default_message(self):
        r = ReplicationResult("germline", False, 0.0)
        assert r.message == ""


class TestFidelityReport:
    def test_elapsed_s(self):
        r = FidelityReport(started=100.0, finished=103.5)
        assert r.elapsed_s == pytest.approx(3.5)

    def test_ok_all_critical_succeed(self):
        report = FidelityReport(
            results=[
                ReplicationResult("germline", True, 0.1),
                ReplicationResult("epigenome", True, 0.2),
            ]
        )
        assert report.ok is True

    def test_ok_critical_failure(self):
        report = FidelityReport(
            results=[
                ReplicationResult("germline", True, 0.1),
                ReplicationResult("epigenome", False, 0.2, "pull failed"),
            ]
        )
        assert report.ok is False

    def test_ok_noncritical_failure_ignored(self):
        report = FidelityReport(
            results=[
                ReplicationResult("germline", True, 0.1),
                ReplicationResult("epigenome", True, 0.2),
                ReplicationResult("cc-auth", False, 0.0, "no creds"),
            ]
        )
        assert report.ok is True

    def test_ok_empty_results(self):
        report = FidelityReport()
        assert report.ok is True

    def test_summary(self):
        report = FidelityReport(
            started=10.0,
            finished=12.5,
            results=[
                ReplicationResult("germline", True, 0.1),
                ReplicationResult("epigenome", False, 0.2, "err"),
            ],
        )
        s = report.summary
        assert "1/2 targets synced" in s
        assert "1 failed" in s
        assert "2.5s" in s

    def test_summary_all_ok(self):
        report = FidelityReport(
            started=0.0,
            finished=1.0,
            results=[ReplicationResult("germline", True, 0.1)],
        )
        assert "1/1 targets synced" in report.summary
        assert "0 failed" in report.summary


# ── _expand tests ─────────────────────────────────────────────────────


class TestExpand:
    def test_expands_tilde(self):
        result = _expand("~/germline")
        assert result == str(Path.home() / "germline")

    def test_no_tilde(self):
        assert _expand("/tmp/test") == "/tmp/test"


# ── _fly_cmd tests ────────────────────────────────────────────────────


class TestFlyCmd:
    @patch("metabolon.organelles.mitosis.subprocess.run")
    def test_wraps_in_bash_c(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="ok")
        _fly_cmd("ls /tmp")
        args = mock_run.call_args[0][0]
        assert args[:5] == ["fly", "ssh", "console", "-a", "soma"]
        assert args[5:7] == ["-u", "terry"]
        assert args[7:9] == ["-q", "-C"]
        assert args[9] == 'bash -c "ls /tmp"'

    @patch("metabolon.organelles.mitosis.subprocess.run")
    def test_default_timeout(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="")
        _fly_cmd("echo hi")
        assert mock_run.call_args[1]["timeout"] == 60

    @patch("metabolon.organelles.mitosis.subprocess.run")
    def test_custom_timeout(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="")
        _fly_cmd("echo hi", timeout=120)
        assert mock_run.call_args[1]["timeout"] == 120

    @patch("metabolon.organelles.mitosis.subprocess.run")
    def test_returns_completed_process(self, mock_run):
        expected = subprocess.CompletedProcess([], 0, stdout="result")
        mock_run.return_value = expected
        result = _fly_cmd("echo hi")
        assert result is expected


# ── _running_on_soma tests ────────────────────────────────────────────


class TestRunningOnSoma:
    @patch("metabolon.organelles.mitosis.Path")
    def test_on_soma(self, mock_path):
        mock_path.return_value.is_dir.return_value = True
        assert _running_on_soma() is True

    @patch("metabolon.organelles.mitosis.Path")
    def test_not_on_soma(self, mock_path):
        mock_path.return_value.is_dir.return_value = False
        assert _running_on_soma() is False


# ── _is_soma_reachable tests ──────────────────────────────────────────


class TestIsSomaReachable:
    @patch("metabolon.organelles.mitosis._running_on_soma", return_value=True)
    def test_on_soma_returns_true(self, _):
        assert _is_soma_reachable() is True

    @patch("metabolon.organelles.mitosis.time.sleep")
    @patch("metabolon.organelles.mitosis.subprocess.run")
    @patch("metabolon.organelles.mitosis._running_on_soma", return_value=False)
    def test_reachable_on_first_try(self, _, mock_run, mock_sleep):
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="machine started")
        assert _is_soma_reachable() is True
        mock_sleep.assert_not_called()

    @patch("metabolon.organelles.mitosis.time.sleep")
    @patch("metabolon.organelles.mitosis.subprocess.run")
    @patch("metabolon.organelles.mitosis._running_on_soma", return_value=False)
    def test_reachable_after_retry(self, _, mock_run, mock_sleep):
        fail_result = subprocess.CompletedProcess([], 1, stdout="error")
        ok_result = subprocess.CompletedProcess([], 0, stdout="machine started")
        mock_run.side_effect = [fail_result, ok_result]
        assert _is_soma_reachable() is True
        mock_sleep.assert_called_once()

    @patch("metabolon.organelles.mitosis.time.sleep")
    @patch("metabolon.organelles.mitosis.subprocess.run")
    @patch("metabolon.organelles.mitosis._running_on_soma", return_value=False)
    def test_unreachable_after_all_retries(self, _, mock_run, mock_sleep):
        mock_run.return_value = subprocess.CompletedProcess([], 1, stdout="stopped")
        assert _is_soma_reachable(retries=2) is False
        assert mock_sleep.call_count == 1  # no sleep after last attempt

    @patch("metabolon.organelles.mitosis.time.sleep")
    @patch("metabolon.organelles.mitosis.subprocess.run")
    @patch("metabolon.organelles.mitosis._running_on_soma", return_value=False)
    def test_timeout_expired_handled(self, _, mock_run, mock_sleep):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="fly", timeout=15)
        assert _is_soma_reachable(retries=1) is False

    @patch("metabolon.organelles.mitosis.time.sleep")
    @patch("metabolon.organelles.mitosis.subprocess.run")
    @patch("metabolon.organelles.mitosis._running_on_soma", return_value=False)
    def test_filenotfound_handled(self, _, mock_run, mock_sleep):
        mock_run.side_effect = FileNotFoundError("fly not installed")
        assert _is_soma_reachable(retries=1) is False

    @patch("metabolon.organelles.mitosis.time.sleep")
    @patch("metabolon.organelles.mitosis.subprocess.run")
    @patch("metabolon.organelles.mitosis._running_on_soma", return_value=False)
    def test_started_not_in_stdout(self, _, mock_run, mock_sleep):
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="machine stopped")
        assert _is_soma_reachable(retries=1) is False


# ── _build_commit_message tests ───────────────────────────────────────


class TestBuildCommitMessage:
    @patch("metabolon.organelles.mitosis.subprocess.run")
    def test_no_changes(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="")
        msg = _build_commit_message("/fake/repo")
        assert msg == "mitosis: sync checkpoint"

    @patch("metabolon.organelles.mitosis.subprocess.run")
    def test_single_file_in_dir(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            [], 0, stdout="metabolon/organelles/mitosis.py"
        )
        msg = _build_commit_message("/fake/repo")
        assert "1 file in metabolon/" in msg
        assert "sync checkpoint" in msg

    @patch("metabolon.organelles.mitosis.subprocess.run")
    def test_multiple_files_multiple_dirs(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            [], 0, stdout="metabolon/a.py\nmetabolon/b.py\nloci/c.md"
        )
        msg = _build_commit_message("/fake/repo")
        assert "2 files in metabolon/" in msg
        assert "1 file in loci/" in msg

    @patch("metabolon.organelles.mitosis.subprocess.run")
    def test_root_level_file(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="README.md")
        msg = _build_commit_message("/fake/repo")
        assert "1 file in (root)/" in msg


# ── _git_push tests ───────────────────────────────────────────────────


class TestGitPush:
    @patch("metabolon.organelles.mitosis.Path")
    def test_not_a_git_repo(self, mock_path_cls):
        # Make _expand return a plain path, then .joinpath(".git").exists() -> False
        mock_path_inst = MagicMock()
        mock_path_inst.joinpath.return_value.exists.return_value = False
        mock_path_cls.return_value = mock_path_inst
        ok, msg = _git_push("/not/a/repo")
        assert ok is False
        assert msg == "not a git repo"

    @patch("metabolon.organelles.mitosis._build_commit_message", return_value="test msg")
    @patch("metabolon.organelles.mitosis.subprocess.run")
    @patch("metabolon.organelles.mitosis.Path")
    def test_push_success(self, mock_path_cls, mock_run, _):
        mock_path_inst = MagicMock()
        mock_path_inst.joinpath.return_value.exists.return_value = True
        mock_path_cls.return_value = mock_path_inst
        mock_path_cls.side_effect = None

        # Three calls: git add, git commit, git push
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        ok, msg = _git_push("~/germline")
        assert ok is True
        assert msg == "pushed"

    @patch("metabolon.organelles.mitosis._build_commit_message", return_value="test msg")
    @patch("metabolon.organelles.mitosis.subprocess.run")
    @patch("metabolon.organelles.mitosis.Path")
    def test_push_everything_uptodate(self, mock_path_cls, mock_run, _):
        mock_path_inst = MagicMock()
        mock_path_inst.joinpath.return_value.exists.return_value = True
        mock_path_cls.return_value = mock_path_inst
        mock_path_cls.side_effect = None

        # add + commit succeed, push says up-to-date
        responses = [
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess(
                [], 1, stdout="Everything up-to-date", stderr="Everything up-to-date"
            ),
        ]
        mock_run.side_effect = responses
        ok, msg = _git_push("~/germline")
        assert ok is True
        assert msg == "up-to-date"

    @patch("metabolon.organelles.mitosis._build_commit_message", return_value="test msg")
    @patch("metabolon.organelles.mitosis.subprocess.run")
    @patch("metabolon.organelles.mitosis.Path")
    def test_push_failure(self, mock_path_cls, mock_run, _):
        mock_path_inst = MagicMock()
        mock_path_inst.joinpath.return_value.exists.return_value = True
        mock_path_cls.return_value = mock_path_inst
        mock_path_cls.side_effect = None

        responses = [
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 128, stdout="", stderr="error: push failed"),
        ]
        mock_run.side_effect = responses
        ok, msg = _git_push("~/germline")
        assert ok is False
        assert "error" in msg


# ── _git_pull_remote tests ────────────────────────────────────────────


class TestGitPullRemote:
    @patch("metabolon.organelles.mitosis._fly_cmd")
    def test_pull_success(self, mock_fly):
        mock_fly.return_value = subprocess.CompletedProcess(
            [], 0, stdout="Already up to date.\n1234567890"
        )
        ok, msg = _git_pull_remote(str(Path.home() / "germline"))
        assert ok is True
        assert "Already up to date" in msg

    @patch("metabolon.organelles.mitosis._fly_cmd")
    def test_pull_failure(self, mock_fly):
        mock_fly.return_value = subprocess.CompletedProcess(
            [], 128, stdout="error: could not pull"
        )
        ok, _msg = _git_pull_remote(str(Path.home() / "germline"))
        assert ok is False

    @patch("metabolon.organelles.mitosis._fly_cmd")
    def test_pull_filters_fly_noise(self, mock_fly):
        mock_fly.return_value = subprocess.CompletedProcess(
            [],
            0,
            stdout="Connecting to soma...\nWarning: something\nAlready up to date.\n1234567890",
        )
        ok, msg = _git_pull_remote(str(Path.home() / "germline"))
        assert ok is True
        assert "Connecting to" not in msg
        assert "Warning:" not in msg

    @patch("metabolon.organelles.mitosis._fly_cmd")
    def test_pull_timeout(self, mock_fly):
        mock_fly.side_effect = subprocess.TimeoutExpired(cmd="fly", timeout=120)
        ok, msg = _git_pull_remote(str(Path.home() / "germline"))
        assert ok is False
        assert msg == "timeout"

    @patch("metabolon.organelles.mitosis._fly_cmd")
    def test_pull_generic_exception(self, mock_fly):
        mock_fly.side_effect = RuntimeError("unexpected")
        ok, msg = _git_pull_remote(str(Path.home() / "germline"))
        assert ok is False
        assert "unexpected" in msg


# ── _sync_target tests ────────────────────────────────────────────────


class TestSyncTarget:
    @patch("metabolon.organelles.mitosis._git_pull_remote")
    @patch("metabolon.organelles.mitosis._git_push")
    @patch("metabolon.organelles.mitosis.time.monotonic", return_value=100.0)
    def test_both_succeed(self, _, mock_push, mock_pull):
        mock_push.return_value = (True, "pushed")
        mock_pull.return_value = (True, "up to date")
        result = _sync_target(SYNC_TARGETS[0])
        assert result.success is True
        assert result.target == "germline"

    @patch("metabolon.organelles.mitosis._git_pull_remote")
    @patch("metabolon.organelles.mitosis._git_push")
    def test_push_fails_pull_ok(self, _, mock_pull):
        # time.monotonic needs to return increasing values
        with patch(
            "metabolon.organelles.mitosis.time.monotonic", side_effect=[100.0, 101.0, 102.0]
        ):
            pass
        # Simpler: just mock push/pull
        pass

    @patch("metabolon.organelles.mitosis._git_pull_remote")
    @patch("metabolon.organelles.mitosis._git_push")
    def test_push_fails_pull_ok_still_success(self, mock_push, mock_pull):
        mock_push.return_value = (False, "not a git repo")
        mock_pull.return_value = (True, "up to date")
        with patch("metabolon.organelles.mitosis.time.monotonic", return_value=0.0):
            result = _sync_target(SYNC_TARGETS[0])
        assert result.success is True
        assert "push skipped" in result.message

    @patch("metabolon.organelles.mitosis._git_pull_remote")
    @patch("metabolon.organelles.mitosis._git_push")
    def test_pull_fails_push_ok(self, mock_push, mock_pull):
        mock_push.return_value = (True, "pushed")
        mock_pull.return_value = (False, "timeout")
        with patch("metabolon.organelles.mitosis.time.monotonic", return_value=0.0):
            result = _sync_target(SYNC_TARGETS[0])
        assert result.success is False
        assert "pull failed" in result.message

    @patch("metabolon.organelles.mitosis._git_pull_remote")
    @patch("metabolon.organelles.mitosis._git_push")
    def test_both_fail(self, mock_push, mock_pull):
        mock_push.return_value = (False, "push err")
        mock_pull.return_value = (False, "pull err")
        with patch("metabolon.organelles.mitosis.time.monotonic", return_value=0.0):
            result = _sync_target(SYNC_TARGETS[0])
        assert result.success is False
        assert "push:" in result.message
        assert "pull:" in result.message


# ── sync tests ────────────────────────────────────────────────────────


class TestSync:
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=False)
    def test_soma_not_reachable(self, _):
        report = sync()
        # "connectivity" is not a critical target, so report.ok is still True
        # The key invariant: the connectivity result records the failure
        assert len(report.results) == 1
        assert report.results[0].target == "connectivity"
        assert report.results[0].success is False

    @patch("metabolon.organelles.mitosis.time.monotonic", return_value=0.0)
    @patch("metabolon.organelles.mitosis._sync_target")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_sync_all_targets(self, _, mock_sync_target, __):
        mock_sync_target.return_value = ReplicationResult("germline", True, 0.1)
        # Also mock creds file as non-existent
        with patch("metabolon.organelles.mitosis.Path") as mock_path:
            # Need home() / ".claude" / ".credentials.json" to not exist
            mock_creds = MagicMock()
            mock_creds.exists.return_value = False
            MagicMock()
            # Handle Path.home() call by making __truediv__ chain work
            mock_path.home.return_value.__truediv__.return_value.__truediv__.return_value = (
                mock_creds
            )
            report = sync()

        assert len(report.results) == len(SYNC_TARGETS)

    @patch("metabolon.organelles.mitosis.time.monotonic", return_value=0.0)
    @patch("metabolon.organelles.mitosis._sync_target")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_sync_specific_targets(self, _, mock_sync_target, __):
        mock_sync_target.return_value = ReplicationResult("germline", True, 0.1)
        with patch("metabolon.organelles.mitosis.Path") as mock_path:
            mock_creds = MagicMock()
            mock_creds.exists.return_value = False
            mock_path.home.return_value.__truediv__.return_value.__truediv__.return_value = (
                mock_creds
            )
            report = sync(targets=["germline"])

        assert mock_sync_target.call_count == 1
        assert report.results[0].target == "germline"

    @patch("metabolon.organelles.mitosis.time.monotonic", return_value=0.0)
    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._sync_target")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_sync_copies_credentials(self, _, mock_sync_target, mock_fly, __):
        mock_sync_target.return_value = ReplicationResult("germline", True, 0.1)
        mock_fly.return_value = subprocess.CompletedProcess([], 0, stdout="ok")
        fake_creds = b'{"token": "abc123"}'

        with patch("metabolon.organelles.mitosis.Path") as mock_path:
            mock_creds = MagicMock()
            mock_creds.exists.return_value = True
            mock_creds.read_bytes.return_value = fake_creds
            mock_path.home.return_value.__truediv__.return_value.__truediv__.return_value = (
                mock_creds
            )
            report = sync()

        auth_results = [r for r in report.results if r.target == "cc-auth"]
        assert len(auth_results) == 1
        assert auth_results[0].success is True


# ── status tests ──────────────────────────────────────────────────────


class TestStatus:
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=False)
    def test_not_reachable(self, _):
        info = status()
        assert info["reachable"] is False
        assert info["machine_state"] == "unknown"

    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_reachable_with_targets(self, _, mock_fly):
        epoch = str(int(time.time()) - 300)  # 5 min ago
        mock_fly.return_value = subprocess.CompletedProcess([], 0, stdout=f"{epoch}\n---\n{epoch}")
        info = status()
        assert info["reachable"] is True
        assert info["machine_state"] == "started"
        for target in SYNC_TARGETS:
            assert target["name"] in info["targets"]

    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_missing_target(self, _, mock_fly):
        mock_fly.return_value = subprocess.CompletedProcess([], 0, stdout="MISSING\n---\nMISSING")
        info = status()
        for target in SYNC_TARGETS:
            assert info["targets"][target["name"]]["state"] == "missing"

    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_fly_cmd_exception(self, _, mock_fly):
        mock_fly.side_effect = RuntimeError("SSH failed")
        info = status()
        assert info["reachable"] is True
        for target in SYNC_TARGETS:
            assert info["targets"][target["name"]]["state"] == "unknown"

    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_stale_target(self, _, mock_fly):
        epoch = str(int(time.time()) - 3600)  # 1 hour ago
        mock_fly.return_value = subprocess.CompletedProcess([], 0, stdout=f"{epoch}\n---\n{epoch}")
        info = status()
        for target in SYNC_TARGETS:
            assert info["targets"][target["name"]]["state"] == "stale"

    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_filters_fly_noise(self, _, mock_fly):
        epoch = str(int(time.time()) - 60)
        noisy = f"Connecting to soma...\nWarning: stuff\n{epoch}\n---\n{epoch}"
        mock_fly.return_value = subprocess.CompletedProcess([], 0, stdout=noisy)
        info = status()
        for target in SYNC_TARGETS:
            assert info["targets"][target["name"]]["state"] == "ok"


# ── setup tests ───────────────────────────────────────────────────────


class TestSetup:
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=False)
    def test_soma_not_reachable(self, _):
        result = setup()
        assert result["success"] is False
        assert "not running" in result["error"]

    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_clones_missing_repos(self, _, mock_fly):
        # First call: check if repo exists -> MISSING
        # Second call: clone the repo -> success
        # Repeat for each SYNC_TARGET, then mkdir, uv sync, symlinks, path
        responses = []
        for _t in SYNC_TARGETS:
            responses.append(subprocess.CompletedProcess([], 0, stdout="MISSING"))
            responses.append(subprocess.CompletedProcess([], 0, stdout="Cloning..."))
        # mkdir, uv sync, symlinks, path
        responses.append(subprocess.CompletedProcess([], 0, stdout="ok"))  # mkdir
        responses.append(subprocess.CompletedProcess([], 0, stdout="Resolved packages"))  # uv
        responses.append(subprocess.CompletedProcess([], 0, stdout="ok"))  # symlinks
        responses.append(subprocess.CompletedProcess([], 0, stdout="ok"))  # path
        mock_fly.side_effect = responses
        result = setup()
        assert result["success"] is True
        clone_steps = [s for s in result["steps"] if s["name"].startswith("clone-")]
        assert len(clone_steps) == len(SYNC_TARGETS)
        assert all(s["success"] for s in clone_steps)

    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_already_present_repos(self, _, mock_fly):
        responses = []
        for _t in SYNC_TARGETS:
            responses.append(subprocess.CompletedProcess([], 0, stdout="EXISTS"))
        # mkdir, uv sync, symlinks, path
        responses.append(subprocess.CompletedProcess([], 0, stdout="ok"))
        responses.append(subprocess.CompletedProcess([], 0, stdout="ok"))
        responses.append(subprocess.CompletedProcess([], 0, stdout="ok"))
        responses.append(subprocess.CompletedProcess([], 0, stdout="ok"))
        mock_fly.side_effect = responses
        result = setup()
        clone_steps = [s for s in result["steps"] if s["name"].startswith("clone-")]
        assert all(s["message"] == "already present" for s in clone_steps)

    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_clone_failure(self, _, mock_fly):
        responses = []
        for _t in SYNC_TARGETS:
            responses.append(subprocess.CompletedProcess([], 0, stdout="MISSING"))
            responses.append(subprocess.CompletedProcess([], 1, stdout="fatal: clone error"))
        responses.append(subprocess.CompletedProcess([], 0, stdout="ok"))
        responses.append(subprocess.CompletedProcess([], 0, stdout="ok"))
        responses.append(subprocess.CompletedProcess([], 0, stdout="ok"))
        responses.append(subprocess.CompletedProcess([], 0, stdout="ok"))
        mock_fly.side_effect = responses
        result = setup()
        assert result["success"] is False
        clone_steps = [s for s in result["steps"] if s["name"].startswith("clone-")]
        assert any(not s["success"] for s in clone_steps)

    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_mkdir_exception_recorded(self, _, mock_fly):
        responses = []
        for _t in SYNC_TARGETS:
            responses.append(subprocess.CompletedProcess([], 0, stdout="EXISTS"))
        # mkdir throws
        responses.append(RuntimeError("SSH timeout"))
        mock_fly.side_effect = responses
        result = setup()
        mkdir_step = next(s for s in result["steps"] if s["name"] == "create-dirs")
        assert mkdir_step["success"] is False


# ── smoketest tests ───────────────────────────────────────────────────


# ── Additional coverage tests ──────────────────────────────────────


class TestSyncCredException:
    """Cover lines 284-285: exception during credential copy in sync()."""

    @patch("metabolon.organelles.mitosis.time.monotonic", return_value=0.0)
    @patch("metabolon.organelles.mitosis._sync_target")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_credentials_copy_exception(self, _, mock_sync_target, __):
        mock_sync_target.return_value = ReplicationResult("germline", True, 0.1)
        mock_creds = MagicMock()
        mock_creds.exists.return_value = True
        mock_creds.read_bytes.side_effect = OSError("permission denied")

        with patch("metabolon.organelles.mitosis.Path") as mock_path:
            mock_path.home.return_value.__truediv__.return_value.__truediv__.return_value = (
                mock_creds
            )
            report = sync()

        auth_results = [r for r in report.results if r.target == "cc-auth"]
        assert len(auth_results) == 1
        assert auth_results[0].success is False
        assert "permission denied" in auth_results[0].message


class TestStatusFewerChunks:
    """Cover lines 334-335: fewer chunks than SYNC_TARGETS in status()."""

    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_fewer_chunks_than_targets(self, _, mock_fly):
        # Return only one chunk for two targets
        epoch = str(int(time.time()) - 60)
        mock_fly.return_value = subprocess.CompletedProcess([], 0, stdout=epoch)
        info = status()
        # First target should be parsed, second should be "unknown"
        names = [t["name"] for t in SYNC_TARGETS]
        assert info["targets"][names[0]]["state"] in ("ok", "stale")
        assert info["targets"][names[1]]["state"] == "unknown"


class TestSetupCloneException:
    """Cover lines 392-393: exception during clone check in setup()."""

    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_clone_check_exception(self, _, mock_fly):
        # First _fly_cmd call throws (during repo existence check)
        mock_fly.side_effect = RuntimeError("SSH connection lost")
        result = setup()
        clone_steps = [s for s in result["steps"] if s["name"].startswith("clone-")]
        assert len(clone_steps) >= 1
        assert clone_steps[0]["success"] is False
        assert "SSH connection lost" in clone_steps[0]["message"]


class TestSmoketestReadException:
    """Cover lines 524-526: exception reading passcode in smoketest()."""

    @patch("metabolon.organelles.mitosis.sync")
    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_read_passcode_exception(self, _, mock_fly, mock_sync):
        good_report = FidelityReport(results=[ReplicationResult("epigenome", True, 0.1)])
        mock_sync.side_effect = [good_report, FidelityReport()]
        # _fly_cmd raises when trying to cat the passcode file
        mock_fly.side_effect = [
            RuntimeError("SSH timeout"),  # cat passcode
        ]
        with patch("metabolon.organelles.mitosis.Path") as mock_path:
            mock_probe = MagicMock()
            mock_path.home.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_probe
            result = smoketest()

        assert result["success"] is False
        assert "read failed" in result["error"]
        mock_probe.unlink.assert_called()


class TestSmoketestAuthException:
    """Cover lines 536-537: exception during claude --version in smoketest()."""

    @patch("random.choices", return_value=list("testcode"))
    @patch("metabolon.organelles.mitosis.sync")
    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_claude_version_exception(self, _, mock_fly, mock_sync, __):
        passcode = "mitosis-testcode"

        good_report = FidelityReport(results=[ReplicationResult("epigenome", True, 0.1)])
        mock_sync.side_effect = [good_report, FidelityReport()]

        # First call: cat returns passcode; second call: claude --version throws
        mock_fly.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=f"---\nname: probe\nPasscode: {passcode}\n"),
            RuntimeError("command not found"),
        ]

        with patch("metabolon.organelles.mitosis.Path") as mock_path:
            mock_probe = MagicMock()
            mock_path.home.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_probe
            result = smoketest()

        assert result["success"] is True
        assert result["passcode"] == passcode
        assert result["claude_auth"] is False


class TestSmoketestFlyNoiseFiltered:
    """Cover line 521: fly noise lines filtered during smoketest read."""

    @patch("random.choices", return_value=list("noiseok1"))
    @patch("metabolon.organelles.mitosis.sync")
    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_fly_noise_in_read_response(self, _, mock_fly, mock_sync, __):
        passcode = "mitosis-noiseok1"

        good_report = FidelityReport(results=[ReplicationResult("epigenome", True, 0.1)])
        mock_sync.side_effect = [good_report, FidelityReport()]

        # First call: cat returns noisy output with passcode embedded
        # Second call: claude --version
        mock_fly.side_effect = [
            subprocess.CompletedProcess(
                [],
                0,
                stdout=f"Connecting to soma...\nWarning: stuff\nPasscode: {passcode}\n",
            ),
            subprocess.CompletedProcess([], 0, stdout="Claude Code v1.0"),
        ]

        with patch("metabolon.organelles.mitosis.Path") as mock_path:
            mock_probe = MagicMock()
            mock_path.home.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_probe
            result = smoketest()

        assert result["success"] is True
        assert result["passcode"] == passcode


# ── Smoketest tests ───────────────────────────────────────────────────


class TestSmoketest:
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=False)
    def test_soma_not_reachable(self, _):
        result = smoketest()
        assert result["success"] is False
        assert "not running" in result["error"]

    @patch("metabolon.organelles.mitosis.sync")
    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_sync_fails(self, _, mock_fly, mock_sync):
        bad_report = FidelityReport(results=[ReplicationResult("epigenome", False, 0.0, "err")])
        # sync called twice: once for test, once for cleanup
        mock_sync.side_effect = [bad_report, FidelityReport()]
        # Mock probe file: Path.home() / "epigenome" / "engrams" / "mitosis_probe.md"
        with patch("metabolon.organelles.mitosis.Path") as mock_path:
            mock_probe = MagicMock()
            mock_path.home.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_probe
            result = smoketest()

        assert result["success"] is False
        assert "sync failed" in result["error"]
        mock_probe.unlink.assert_called()

    @patch("metabolon.organelles.mitosis.sync")
    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_passcode_mismatch(self, _, mock_fly, mock_sync):
        good_report = FidelityReport(results=[ReplicationResult("epigenome", True, 0.1)])
        mock_sync.side_effect = [good_report, FidelityReport()]
        # _fly_cmd returns response without passcode
        mock_fly.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="wrong content"),
            subprocess.CompletedProcess([], 0, stdout="Claude Code v1.0"),
        ]
        with patch("metabolon.organelles.mitosis.Path") as mock_path:
            mock_probe = MagicMock()
            mock_path.home.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_probe
            result = smoketest()

        assert result["success"] is False
        assert "mismatch" in result["error"]

    @patch("random.choices", return_value=list("abcdefgh"))
    @patch("metabolon.organelles.mitosis.sync")
    @patch("metabolon.organelles.mitosis._fly_cmd")
    @patch("metabolon.organelles.mitosis._is_soma_reachable", return_value=True)
    def test_smoketest_success(self, _, mock_fly, mock_sync, __):
        passcode = "mitosis-abcdefgh"

        good_report = FidelityReport(results=[ReplicationResult("epigenome", True, 0.1)])
        mock_sync.side_effect = [good_report, FidelityReport()]

        passcode = "mitosis-abcdefgh"

        # First fly call: cat memory file (return the passcode)
        # Second fly call: claude --version
        mock_fly.side_effect = [
            subprocess.CompletedProcess(
                [], 0, stdout=f"---\nname: mitosis probe\nPasscode: {passcode}\n"
            ),
            subprocess.CompletedProcess([], 0, stdout="Claude Code v1.0"),
        ]

        with patch("metabolon.organelles.mitosis.Path") as mock_path:
            mock_probe = MagicMock()
            mock_path.home.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_probe
            result = smoketest()

        assert result["success"] is True
        assert result["passcode"] == passcode
        assert result["claude_auth"] is True
