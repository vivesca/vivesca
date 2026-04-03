from __future__ import annotations

"""Tests for effectors/chromatin-backup.sh — auto-commit and push chromatin changes."""

import os
import subprocess
from pathlib import Path
import shutil

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "effectors" / "chromatin-backup.sh"


@pytest.fixture
def mock_home(tmp_path):
    """Set up a mock HOME with epigenome/chromatin git repo."""
    home = tmp_path / "home"
    home.mkdir()
    repo_dir = home / "epigenome" / "chromatin"
    repo_dir.mkdir(parents=True)

    # Initialize a "remote" repo to push to
    remote_dir = tmp_path / "remote"
    remote_dir.mkdir()
    subprocess.run(["git", "init", "--bare", "-b", "main"], cwd=remote_dir, check=True)

    # Initialize local repo
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote_dir)], cwd=repo_dir, check=True)

    # Create an initial commit and push to remote
    (repo_dir / "init.txt").write_text("initial")
    subprocess.run(["git", "add", "init.txt"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=repo_dir, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=repo_dir, check=True)

    return home


def test_help():
    """Test --help and -h flags."""
    result = subprocess.run([str(SCRIPT_PATH), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Usage: chromatin-backup.sh" in result.stdout

    result = subprocess.run([str(SCRIPT_PATH), "-h"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Usage: chromatin-backup.sh" in result.stdout


def test_no_changes(mock_home):
    """Test script when there are no changes to commit."""
    env = os.environ.copy()
    env["HOME"] = str(mock_home)

    result = subprocess.run([str(SCRIPT_PATH)], env=env, capture_output=True, text=True)
    assert result.returncode == 0
    # Should not have made any new commits
    repo_dir = mock_home / "epigenome" / "chromatin"
    log = subprocess.run(["git", "log", "--oneline"], cwd=repo_dir, capture_output=True, text=True).stdout
    assert len(log.strip().split("\n")) == 1


def test_backup_changes(mock_home):
    """Test script when there are new changes to commit."""
    env = os.environ.copy()
    env["HOME"] = str(mock_home)
    repo_dir = mock_home / "epigenome" / "chromatin"

    # Create a new file
    (repo_dir / "new_file.txt").write_text("new content")

    result = subprocess.run([str(SCRIPT_PATH)], env=env, capture_output=True, text=True)
    assert result.returncode == 0

    # Should have a new commit
    log = subprocess.run(["git", "log", "--oneline"], cwd=repo_dir, capture_output=True, text=True).stdout
    assert "chromatin backup:" in log
    assert len(log.strip().split("\n")) == 2

    # Should have pushed to remote
    remote_dir = mock_home.parent / "remote"
    remote_log = subprocess.run(["git", "log", "--oneline"], cwd=remote_dir, capture_output=True, text=True).stdout
    assert "chromatin backup:" in remote_log


def test_remote_conflict_resolution(mock_home):
    """Test script handles remote changes by merging/rebasing."""
    env = os.environ.copy()
    env["HOME"] = str(mock_home)
    repo_dir = mock_home / "epigenome" / "chromatin"
    remote_dir = mock_home.parent / "remote"

    # 1. Create a remote commit that conflicts with a local change
    # Local change
    (repo_dir / "conflict.txt").write_text("local version")
    # Actually, the script pulls first, then checks for changes.
    # If I have uncommitted local changes, rebase might fail.

    # Let's simulate a remote change first.
    temp_clone = mock_home.parent / "temp_clone"
    subprocess.run(["git", "clone", str(remote_dir), str(temp_clone)], check=True)
    subprocess.run(["git", "config", "user.email", "other@example.com"], cwd=temp_clone, check=True)
    subprocess.run(["git", "config", "user.name", "Other User"], cwd=temp_clone, check=True)
    (temp_clone / "remote_file.txt").write_text("remote content")
    subprocess.run(["git", "add", "remote_file.txt"], cwd=temp_clone, check=True)
    subprocess.run(["git", "commit", "-m", "remote commit"], cwd=temp_clone, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=temp_clone, check=True)

    # 2. Local has changes
    (repo_dir / "local_file.txt").write_text("local content")

    # 3. Run script
    result = subprocess.run([str(SCRIPT_PATH)], env=env, capture_output=True, text=True)
    assert result.returncode == 0

    # Should have both remote and local changes
    assert (repo_dir / "remote_file.txt").exists()
    assert (repo_dir / "local_file.txt").exists()

    # Log should show: initial, remote, local backup
    log = subprocess.run(["git", "log", "--oneline"], cwd=repo_dir, capture_output=True, text=True).stdout
    assert "remote commit" in log
    assert "chromatin backup:" in log


def test_conflict_accept_theirs(mock_home):
    """Test script handles unresolvable conflicts by accepting remote changes."""
    env = os.environ.copy()
    env["HOME"] = str(mock_home)
    repo_dir = mock_home / "epigenome" / "chromatin"
    remote_dir = mock_home.parent / "remote"

    # 1. Create a file in local
    (repo_dir / "conflict.txt").write_text("local content")
    subprocess.run(["git", "add", "conflict.txt"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "local commit"], cwd=repo_dir, check=True)
    # Actually push it to remote so remote also has it.
    subprocess.run(["git", "push", "origin", "main"], cwd=repo_dir, check=True)

    # 2. Modify locally
    (repo_dir / "conflict.txt").write_text("modified local")
    subprocess.run(["git", "add", "conflict.txt"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "another local"], cwd=repo_dir, check=True)

    # 3. Modify on remote (via temp clone) to cause a hard conflict
    temp_clone = mock_home.parent / "temp_clone"
    subprocess.run(["git", "clone", str(remote_dir), str(temp_clone)], check=True)
    subprocess.run(["git", "config", "user.email", "other@example.com"], cwd=temp_clone, check=True)
    subprocess.run(["git", "config", "user.name", "Other User"], cwd=temp_clone, check=True)
    (temp_clone / "conflict.txt").write_text("modified remote")
    subprocess.run(["git", "add", "conflict.txt"], cwd=temp_clone, check=True)
    subprocess.run(["git", "commit", "-m", "remote conflict"], cwd=temp_clone, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=temp_clone, check=True)

    # Remote has: 'initial', 'local commit', 'remote conflict' -> 3 commits.
    initial_remote_log = subprocess.run(["git", "log", "--oneline"], cwd=remote_dir, capture_output=True, text=True).stdout
    initial_remote_commits = initial_remote_log.strip().split("\n")
    assert len(initial_remote_commits) == 3

    # Now repo_dir has "modified local" and remote has "modified remote" on the same line/file.
    # Rebase and merge should fail if not careful.

    # 4. Run script
    result = subprocess.run([str(SCRIPT_PATH)], env=env, capture_output=True, text=True)
    assert result.returncode == 0

    # Should have accepted remote content as last resort
    # The script uses 'git checkout --theirs .'
    content = (repo_dir / "conflict.txt").read_text().strip()
    assert content == "modified remote"

    # Verify it was pushed to remote
    remote_log = subprocess.run(["git", "log", "--oneline"], cwd=remote_dir, capture_output=True, text=True).stdout
    remote_commits = remote_log.strip().split("\n")
    # If it was pushed, it should have 4 or more commits.
    assert len(remote_commits) > 3, f"Remote log only has: {remote_log}"
