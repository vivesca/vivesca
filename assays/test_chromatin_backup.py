"""Tests for chromatin-backup — git auto-commit/push for Obsidian vault."""
from __future__ import annotations

import os
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


# ── _has_changes tests ────────────────────────────────────────────────


def test_has_changes_no_changes():
    """Returns False when no diff, no cached diff, no untracked files."""
    with patch.object(_mod, "_git") as mock_git:
        # git diff --quiet returns 0, git diff --cached --quiet returns 0,
        # git ls-files returns empty string
        mock_git.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0),
            MagicMock(stdout=""),
        ]
        assert _has_changes() is False
        assert mock_git.call_count == 3


def test_has_changes_unstaged():
    """Returns True when there are unstaged changes."""
    with patch.object(_mod, "_git") as mock_git:
        mock_git.return_value = MagicMock(returncode=1)
        assert _has_changes() is True
        assert mock_git.call_count == 1


def test_has_changes_staged():
    """Returns True when there are staged changes."""
    with patch.object(_mod, "_git") as mock_git:
        mock_git.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=1),
        ]
        assert _has_changes() is True
        assert mock_git.call_count == 2


def test_has_changes_untracked():
    """Returns True when there are untracked files."""
    with patch.object(_mod, "_git") as mock_git:
        mock_git.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0),
            MagicMock(stdout="newfile.md\n"),
        ]
        assert _has_changes() is True


# ── sync_remote tests ─────────────────────────────────────────────────


def test_sync_remote_no_diverge():
    """No-op when local and remote are the same."""
    with patch.object(_mod, "_git") as mock_git:
        mock_git.side_effect = [
            MagicMock(returncode=0),       # fetch
            MagicMock(stdout="abc123\n"),  # rev-parse HEAD
            MagicMock(stdout="abc123\n"),  # rev-parse origin/main
        ]
        sync_remote()
        assert mock_git.call_count == 3
        mock_git.assert_any_call("fetch", "origin", "main", check=False)
        mock_git.assert_any_call("rev-parse", "HEAD")
        mock_git.assert_any_call("rev-parse", "origin/main", check=False)


def test_sync_remote_rebase_succeeds():
    """Uses rebase when local != remote and rebase works."""
    with patch.object(_mod, "_git") as mock_git:
        mock_git.side_effect = [
            MagicMock(returncode=0),       # fetch
            MagicMock(stdout="aaa\n"),     # rev-parse HEAD
            MagicMock(stdout="bbb\n"),     # rev-parse origin/main
            MagicMock(returncode=0),       # rebase
        ]
        sync_remote()
        calls = [c[0] for c in mock_git.call_args_list]
        assert ("rebase", "origin/main") in calls or any("rebase" in str(c) for c in calls)


def test_sync_remote_rebase_fails_merge_succeeds():
    """Falls back to merge when rebase fails."""
    with patch.object(_mod, "_git") as mock_git:
        mock_git.side_effect = [
            MagicMock(returncode=0),       # fetch
            MagicMock(stdout="aaa\n"),     # rev-parse HEAD
            MagicMock(stdout="bbb\n"),     # rev-parse origin/main
            MagicMock(returncode=1),       # rebase fails
            MagicMock(returncode=0),       # rebase --abort
            MagicMock(returncode=0),       # merge succeeds
        ]
        sync_remote()
        call_args = [c[0][:2] for c in mock_git.call_args_list]
        assert ("rebase", "--abort") in [c[:2] for c in call_args if len(c) >= 2] or \
               any(c[0] == "rebase" and c[1] == "--abort" for c in call_args if len(c) >= 2)


def test_sync_remote_merge_fails_accept_theirs():
    """Last resort: checkout --theirs when both rebase and merge fail."""
    with patch.object(_mod, "_git") as mock_git:
        mock_git.side_effect = [
            MagicMock(returncode=0),       # fetch
            MagicMock(stdout="aaa\n"),     # rev-parse HEAD
            MagicMock(stdout="bbb\n"),     # rev-parse origin/main
            MagicMock(returncode=1),       # rebase fails
            MagicMock(returncode=0),       # rebase --abort
            MagicMock(returncode=1),       # merge fails
            MagicMock(returncode=0),       # checkout --theirs
            MagicMock(returncode=0),       # add -A
            MagicMock(returncode=0),       # commit
        ]
        sync_remote()
        # Verify checkout --theirs was called
        call_strs = [str(c) for c in mock_git.call_args_list]
        assert any("--theirs" in s for s in call_strs)


# ── backup tests ──────────────────────────────────────────────────────


def test_backup_no_changes():
    """Returns False when no changes to commit."""
    with patch.object(_mod, "_git") as mock_git, \
         patch.object(_mod, "sync_remote"), \
         patch.object(_mod, "_has_changes", return_value=False), \
         patch.object(Path, "is_dir", return_value=True):
        assert backup() is False


def test_backup_with_changes():
    """Commits and pushes when changes exist."""
    with patch.object(_mod, "_git") as mock_git, \
         patch.object(_mod, "sync_remote"), \
         patch.object(_mod, "_has_changes", return_value=True), \
         patch.object(Path, "is_dir", return_value=True):
        assert backup() is True
        call_args = [c[0] for c in mock_git.call_args_list]
        # Should: add -A, commit -m ..., push origin main
        assert ("add", "-A") in call_args
        assert ("push", "origin", "main") in call_args
        # Commit message should contain timestamp pattern
        commit_calls = [c for c in mock_git.call_args_list if c[0][0] == "commit"]
        assert len(commit_calls) == 1
        msg = commit_calls[0][0][2]
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
        mock_run.return_value = MagicMock(stdout="ok\n", returncode=0)
        _git("status")
        _, kwargs = mock_run.call_args
        assert kwargs["cwd"] == CHROMATIN_DIR


def test_git_passes_all_args():
    """_git forwards all positional args to git."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        _git("log", "--oneline", "-5")
        args = mock_run.call_args[0][0]
        assert args == ["git", "log", "--oneline", "-5"]
