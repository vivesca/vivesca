"""Tests for chromatin-backup — git auto-commit/push for Obsidian vault."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

SRC = Path("/home/terry/germline/effectors/chromatin-backup.py")


def _load():
    ns: dict = {"__name__": "chromatin_backup"}
    exec(open(SRC).read(), ns)
    return ns


_mod = _load()
backup = _mod["backup"]
sync_remote = _mod["sync_remote"]
_has_changes = _mod["_has_changes"]
_git = _mod["_git"]
CHROMATIN_DIR = _mod["CHROMATIN_DIR"]


def _mock_run(stdout="", returncode=0):
    """Build a CompletedProcess mock."""
    return MagicMock(stdout=stdout, returncode=returncode, stderr="")


def _git_calls(mock_run):
    """Extract list of (args_tuple,) from subprocess.run calls."""
    return [tuple(c[0][0]) for c in mock_run.call_args_list]


# ── _has_changes tests ────────────────────────────────────────────────


def test_has_changes_no_changes():
    """Returns False when no diff, no cached diff, no untracked files."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            _mock_run(returncode=0),   # git diff --quiet
            _mock_run(returncode=0),   # git diff --cached --quiet
            _mock_run(stdout=""),      # git ls-files
        ]
        assert _has_changes() is False
        assert mock_run.call_count == 3


def test_has_changes_unstaged():
    """Returns True when there are unstaged changes (diff --quiet fails)."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_run(returncode=1)
        assert _has_changes() is True
        assert mock_run.call_count == 1


def test_has_changes_staged():
    """Returns True when there are staged changes (cached diff fails)."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            _mock_run(returncode=0),   # diff --quiet ok
            _mock_run(returncode=1),   # diff --cached --quiet fails
        ]
        assert _has_changes() is True
        assert mock_run.call_count == 2


def test_has_changes_untracked():
    """Returns True when there are untracked files."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            _mock_run(returncode=0),       # diff --quiet ok
            _mock_run(returncode=0),       # diff --cached --quiet ok
            _mock_run(stdout="newfile.md\n"),  # ls-files has output
        ]
        assert _has_changes() is True


# ── sync_remote tests ─────────────────────────────────────────────────


def test_sync_remote_no_diverge():
    """No-op when local and remote HEAD are the same."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            _mock_run(returncode=0),     # fetch
            _mock_run(stdout="abc123\n"),  # rev-parse HEAD
            _mock_run(stdout="abc123\n"),  # rev-parse origin/main
        ]
        sync_remote()
        assert mock_run.call_count == 3
        cmds = _git_calls(mock_run)
        assert ("git", "fetch", "origin", "main") in cmds


def test_sync_remote_rebase_succeeds():
    """Uses rebase when local != remote and rebase works."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            _mock_run(returncode=0),     # fetch
            _mock_run(stdout="aaa\n"),   # rev-parse HEAD
            _mock_run(stdout="bbb\n"),   # rev-parse origin/main
            _mock_run(returncode=0),     # rebase succeeds
        ]
        sync_remote()
        cmds = _git_calls(mock_run)
        assert ("git", "rebase", "origin/main") in cmds


def test_sync_remote_rebase_fails_merge_succeeds():
    """Falls back to merge when rebase fails."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            _mock_run(returncode=0),     # fetch
            _mock_run(stdout="aaa\n"),   # rev-parse HEAD
            _mock_run(stdout="bbb\n"),   # rev-parse origin/main
            _mock_run(returncode=1),     # rebase fails
            _mock_run(returncode=0),     # rebase --abort
            _mock_run(returncode=0),     # merge succeeds
        ]
        sync_remote()
        cmds = _git_calls(mock_run)
        assert ("git", "rebase", "--abort") in cmds
        assert ("git", "merge", "origin/main", "--no-edit") in cmds


def test_sync_remote_merge_fails_accept_theirs():
    """Last resort: checkout --theirs when both rebase and merge fail."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            _mock_run(returncode=0),     # fetch
            _mock_run(stdout="aaa\n"),   # rev-parse HEAD
            _mock_run(stdout="bbb\n"),   # rev-parse origin/main
            _mock_run(returncode=1),     # rebase fails
            _mock_run(returncode=0),     # rebase --abort
            _mock_run(returncode=1),     # merge fails
            _mock_run(returncode=0),     # checkout --theirs .
            _mock_run(returncode=0),     # add -A
            _mock_run(returncode=0),     # commit
        ]
        sync_remote()
        cmds = _git_calls(mock_run)
        assert ("git", "checkout", "--theirs", ".") in cmds
        assert ("git", "add", "-A") in cmds


# ── backup tests ──────────────────────────────────────────────────────


def test_backup_no_changes():
    """Returns False when no changes to commit."""
    with patch("subprocess.run") as mock_run, \
         patch.object(Path, "is_dir", return_value=True):
        # sync_remote calls: fetch, rev-parse HEAD, rev-parse origin/main (same)
        mock_run.side_effect = [
            _mock_run(returncode=0),     # fetch
            _mock_run(stdout="abc\n"),   # rev-parse HEAD
            _mock_run(stdout="abc\n"),   # rev-parse origin/main (same → no rebase)
            _mock_run(returncode=0),     # diff --quiet (no changes)
            _mock_run(returncode=0),     # diff --cached --quiet
            _mock_run(stdout=""),        # ls-files (empty)
        ]
        assert backup() is False


def test_backup_with_changes():
    """Commits and pushes when changes exist."""
    with patch("subprocess.run") as mock_run, \
         patch.object(Path, "is_dir", return_value=True):
        mock_run.side_effect = [
            _mock_run(returncode=0),     # fetch (sync_remote)
            _mock_run(stdout="abc\n"),   # rev-parse HEAD
            _mock_run(stdout="abc\n"),   # rev-parse origin/main
            _mock_run(returncode=1),     # diff --quiet (has changes)
            _mock_run(returncode=0),     # add -A
            _mock_run(returncode=0),     # commit
            _mock_run(returncode=0),     # push
        ]
        assert backup() is True
        cmds = _git_calls(mock_run)
        assert ("git", "add", "-A") in cmds
        assert ("git", "push", "origin", "main") in cmds
        # Verify commit message format
        commit_calls = [c for c in mock_run.call_args_list if c[0][0][1] == "commit"]
        assert len(commit_calls) == 1
        msg = commit_calls[0][0][0][3]  # ["git", "commit", "-m", "<msg>"]
        assert msg.startswith("chromatin backup: ")


def test_backup_missing_dir_exits():
    """Exits with code 1 if chromatin dir doesn't exist."""
    with patch.object(Path, "is_dir", return_value=False):
        with pytest.raises(SystemExit) as exc_info:
            backup()
        assert exc_info.value.code == 1


# ── _git helper tests ────────────────────────────────────────────────


def test_git_runs_in_chromatin_dir():
    """_git passes cwd as CHROMATIN_DIR."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_run(stdout="ok\n")
        _git("status")
        _, kwargs = mock_run.call_args
        assert kwargs["cwd"] == CHROMATIN_DIR


def test_git_passes_all_args():
    """_git forwards all positional args to git."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_run(stdout="")
        _git("log", "--oneline", "-5")
        args = mock_run.call_args[0][0]
        assert args == ["git", "log", "--oneline", "-5"]
