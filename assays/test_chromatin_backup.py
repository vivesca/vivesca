from __future__ import annotations

"""Tests for chromatin-backup.sh — auto-commit and push chromatin changes."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline" / "effectors" / "chromatin-backup.sh"


# ── Helper ────────────────────────────────────────────────────────────


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run the script with given args, capturing output."""
    return subprocess.run(
        ["/usr/bin/bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
        **kwargs,
    )


def _init_fake_chromatin(tmp_path: Path, with_remote: bool = False) -> Path:
    """Create a fake $HOME/epigenome/chromatin git repo.

    Returns the path to the fake home directory so callers can set HOME.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    chromatin_dir = fake_home / "epigenome" / "chromatin"
    chromatin_dir.mkdir(parents=True)

    subprocess.run(["git", "init"], cwd=chromatin_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=chromatin_dir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=chromatin_dir,
        capture_output=True,
        check=True,
    )

    # Create an initial commit so HEAD exists
    readme = chromatin_dir / "README.md"
    readme.write_text("# chromatin\n")
    subprocess.run(["git", "add", "-A"], cwd=chromatin_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=chromatin_dir,
        capture_output=True,
        check=True,
    )

    if with_remote:
        # Create a bare "remote" and push initial commit
        remote_dir = tmp_path / "remote.git"
        subprocess.run(
            ["git", "clone", "--bare", str(chromatin_dir), str(remote_dir)],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote_dir)],
            cwd=chromatin_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=chromatin_dir,
            capture_output=True,
            check=True,
        )
        # Push with --force since there's no upstream tracking yet
        subprocess.run(
            ["git", "push", "-u", "origin", "main", "--force"],
            cwd=chromatin_dir,
            capture_output=True,
            check=True,
            env={**os.environ, "HOME": str(fake_home)},
        )

    return fake_home


# ── --help ────────────────────────────────────────────────────────────


def test_help_flag():
    """--help prints usage and exits 0."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "chromatin-backup.sh" in r.stdout


def test_h_short_flag():
    """-h prints usage and exits 0."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout


def test_help_mentions_purpose():
    """Help text describes auto-commit and push."""
    r = _run(["--help"])
    assert "Auto-commit" in r.stdout or "push" in r.stdout


# ── Missing repo directory ────────────────────────────────────────────


def test_exits_if_chromatin_dir_missing(tmp_path):
    """Script exits 1 when $HOME/epigenome/chromatin does not exist."""
    fake_home = tmp_path / "empty_home"
    fake_home.mkdir()
    # No epigenome/chromatin created
    r = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r.returncode == 1


# ── Clean working tree (no changes) ──────────────────────────────────


def test_no_changes_exits_clean(tmp_path):
    """Script exits 0 when there are no changes to commit."""
    fake_home = _init_fake_chromatin(tmp_path)
    r = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r.returncode == 0


# ── Dirty working tree: new file ──────────────────────────────────────


def test_commits_new_file(tmp_path):
    """Script stages and commits a new file."""
    fake_home = _init_fake_chromatin(tmp_path, with_remote=True)
    chromatin_dir = fake_home / "epigenome" / "chromatin"

    # Add a new file
    (chromatin_dir / "notes.md").write_text("my notes")

    r = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r.returncode == 0

    # Verify the file was committed
    log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=chromatin_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "chromatin backup:" in log.stdout
    assert "notes.md" in subprocess.run(
        ["git", "show", "--stat", "HEAD"],
        cwd=chromatin_dir,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


# ── Dirty working tree: modified file ────────────────────────────────


def test_commits_modified_file(tmp_path):
    """Script stages and commits modifications to tracked files."""
    fake_home = _init_fake_chromatin(tmp_path, with_remote=True)
    chromatin_dir = fake_home / "epigenome" / "chromatin"

    # Modify existing file
    (chromatin_dir / "README.md").write_text("# chromatin\n\nupdated content")

    r = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r.returncode == 0

    log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=chromatin_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "chromatin backup:" in log.stdout


# ── Dirty working tree: deleted file ──────────────────────────────────


def test_commits_deleted_file(tmp_path):
    """Script stages and commits deleted files."""
    fake_home = _init_fake_chromatin(tmp_path, with_remote=True)
    chromatin_dir = fake_home / "epigenome" / "chromatin"

    # Delete existing file
    (chromatin_dir / "README.md").unlink()

    r = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r.returncode == 0

    log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=chromatin_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "chromatin backup:" in log.stdout


# ── Commit message format ────────────────────────────────────────────


def test_commit_message_contains_timestamp(tmp_path):
    """Commit message includes date and time in expected format."""
    fake_home = _init_fake_chromatin(tmp_path, with_remote=True)
    chromatin_dir = fake_home / "epigenome" / "chromatin"

    (chromatin_dir / "new.md").write_text("content")

    r = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r.returncode == 0

    log = subprocess.run(
        ["git", "log", "--format=%s", "-1"],
        cwd=chromatin_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    # Format: "chromatin backup: YYYY-MM-DD HH:MM:SS"
    msg = log.stdout.strip()
    assert msg.startswith("chromatin backup: ")
    # Verify the timestamp portion looks like a date+time
    ts = msg.removeprefix("chromatin backup: ")
    assert len(ts) == 19  # "YYYY-MM-DD HH:MM:SS"
    assert ts[4] == "-" and ts[7] == "-" and ts[10] == " "


# ── Staged but uncommitted changes ────────────────────────────────────


def test_commits_already_staged_changes(tmp_path):
    """Script commits changes that were already git-add'd."""
    fake_home = _init_fake_chromatin(tmp_path, with_remote=True)
    chromatin_dir = fake_home / "epigenome" / "chromatin"

    (chromatin_dir / "staged.md").write_text("already staged")
    subprocess.run(
        ["git", "add", "staged.md"],
        cwd=chromatin_dir,
        capture_output=True,
        check=True,
    )

    r = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r.returncode == 0

    log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=chromatin_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "chromatin backup:" in log.stdout


# ── Multiple files ────────────────────────────────────────────────────


def test_commits_multiple_new_files(tmp_path):
    """Script stages all new files in one commit."""
    fake_home = _init_fake_chromatin(tmp_path, with_remote=True)
    chromatin_dir = fake_home / "epigenome" / "chromatin"

    (chromatin_dir / "a.md").write_text("file a")
    (chromatin_dir / "b.md").write_text("file b")
    (chromatin_dir / "c.md").write_text("file c")

    r = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r.returncode == 0

    stat = subprocess.run(
        ["git", "show", "--stat", "HEAD"],
        cwd=chromatin_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "a.md" in stat.stdout
    assert "b.md" in stat.stdout
    assert "c.md" in stat.stdout


# ── Subdirectory files ────────────────────────────────────────────────


def test_commits_files_in_subdirectories(tmp_path):
    """Script picks up files nested in subdirectories."""
    fake_home = _init_fake_chromatin(tmp_path, with_remote=True)
    chromatin_dir = fake_home / "epigenome" / "chromatin"

    subdir = chromatin_dir / "daily"
    subdir.mkdir()
    (subdir / "2024-01-01.md").write_text("daily note")

    r = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r.returncode == 0

    stat = subprocess.run(
        ["git", "show", "--stat", "HEAD"],
        cwd=chromatin_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "daily/2024-01-01.md" in stat.stdout


# ── Repeated runs ─────────────────────────────────────────────────────


def test_second_run_no_changes(tmp_path):
    """After committing, a second run exits cleanly with no new commit."""
    fake_home = _init_fake_chromatin(tmp_path, with_remote=True)
    chromatin_dir = fake_home / "epigenome" / "chromatin"

    (chromatin_dir / "once.md").write_text("content")

    r1 = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r1.returncode == 0

    # Get commit count after first run
    count1 = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=chromatin_dir,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    r2 = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r2.returncode == 0

    count2 = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=chromatin_dir,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert count1 == count2  # No new commit on clean tree


# ── Rebase: remote ahead of local ─────────────────────────────────────


def test_rebases_on_remote_changes(tmp_path):
    """Script rebases when remote has commits local doesn't."""
    fake_home = _init_fake_chromatin(tmp_path, with_remote=True)
    chromatin_dir = fake_home / "epigenome" / "chromatin"
    remote_dir = tmp_path / "remote.git"

    # Push a commit from a clone of the remote (simulating Obsidian push)
    work = tmp_path / "other_clone"
    subprocess.run(
        ["git", "clone", str(remote_dir), str(work)],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "obsidian@test.com"],
        cwd=work,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Obsidian"],
        cwd=work,
        capture_output=True,
        check=True,
    )
    # Ensure the clone uses 'main' branch (git defaults to 'master')
    subprocess.run(
        ["git", "checkout", "-b", "main"],
        cwd=work,
        capture_output=True,
        check=True,
    )
    (work / "from-obsidian.md").write_text("obsidian note")
    subprocess.run(["git", "add", "-A"], cwd=work, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "obsidian push"],
        cwd=work,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=work,
        capture_output=True,
        check=True,
    )

    # Now local adds a file and runs backup (should rebase onto remote change)
    (chromatin_dir / "local.md").write_text("local note")

    r = _run([], env={**os.environ, "HOME": str(fake_home)})
    assert r.returncode == 0

    # Both the remote file and local file should be present
    assert (chromatin_dir / "from-obsidian.md").exists()
    assert (chromatin_dir / "local.md").exists()
    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=chromatin_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "chromatin backup:" in log.stdout
