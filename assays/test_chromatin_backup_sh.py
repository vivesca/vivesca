from __future__ import annotations

"""Tests for effectors/chromatin-backup.sh — bash script tested via subprocess."""

import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "chromatin-backup.sh"
CHROMATIN_RELATIVE = "epigenome/chromatin"
GIT_ENV_OVERRIDES = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@test.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@test.com",
    "GIT_CONFIG_COUNT": "1",
    "GIT_CONFIG_KEY_0": "init.defaultBranch",
    "GIT_CONFIG_VALUE_0": "main",
}


# ── fixture ─────────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_path():
    d = Path(tempfile.mkdtemp(prefix="chromatin-backup-test-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ── helpers ─────────────────────────────────────────────────────────────


def _git_env(tmp_path: Path, extra: dict | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env.update(GIT_ENV_OVERRIDES)
    if extra:
        env.update(extra)
    return env


def _run_script(tmp_path: Path) -> subprocess.CompletedProcess:
    """Run chromatin-backup.sh with HOME=tmp_path."""
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=_git_env(tmp_path),
        timeout=30,
    )


def _git(repo: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )


def _make_local_repo(tmp_path: Path) -> Path:
    """Create a local-only chromatin git repo inside tmp_path."""
    repo = tmp_path / CHROMATIN_RELATIVE
    repo.mkdir(parents=True, exist_ok=True)
    env = _git_env(tmp_path)
    _git(repo, "init", env=env)
    _git(repo, "checkout", "-b", "main", env=env)
    # Initial commit
    (repo / "readme.md").write_text("initial")
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-m", "initial", env=env)
    return repo


def _make_remote_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Create a chromatin repo + bare remote. Returns (repo, remote_dir)."""
    repo = _make_local_repo(tmp_path)
    remote_dir = tmp_path / "epigenome" / "chromatin-remote"
    remote_dir.mkdir(parents=True, exist_ok=True)
    env = _git_env(tmp_path)
    _git(remote_dir, "init", "--bare", env=env)
    _git(remote_dir, "symbolic-ref", "HEAD", "refs/heads/main", env=env)
    _git(repo, "remote", "add", "origin", str(remote_dir), env=env)
    _git(repo, "push", "-u", "origin", "main", env=env)
    return repo, remote_dir


def _log_oneline(repo: Path) -> list[str]:
    r = _git(repo, "log", "--oneline")
    return [l for l in r.stdout.strip().split("\n") if l]


def _log_subject(repo: Path) -> str:
    r = _git(repo, "log", "--format=%s", "-1")
    return r.stdout.strip()


def _ls_files(repo: Path) -> list[str]:
    r = _git(repo, "ls-files")
    return [f for f in r.stdout.strip().split("\n") if f]


def _status_porcelain(repo: Path) -> list[str]:
    r = _git(repo, "status", "--porcelain")
    return [l for l in r.stdout.strip().split("\n") if l]


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def _run_help(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_help_exits_zero(self):
        assert self._run_help("--help").returncode == 0

    def test_help_short_flag(self):
        assert self._run_help("-h").returncode == 0

    def test_help_shows_usage(self):
        assert "Usage:" in self._run_help("--help").stdout

    def test_help_mentions_chromatin(self):
        assert "chromatin" in self._run_help("--help").stdout.lower()

    def test_help_no_stderr(self):
        assert self._run_help("--help").stderr == ""

    def test_help_exits_early_no_git(self, tmp_path):
        """--help exits before any git operations, even with no repo."""
        r = _run_script(tmp_path)
        # Without --help it would try to cd; with --help it exits early
        env = _git_env(tmp_path)
        r = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert r.returncode == 0
        assert not (tmp_path / CHROMATIN_RELATIVE).exists()


# ── file basics ─────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        assert SCRIPT.read_text().split("\n")[0].startswith("#!/usr/bin/env bash")

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)


# ── missing chromatin directory ─────────────────────────────────────────


class TestMissingChromatinDir:
    def test_exits_1_when_no_dir(self, tmp_path):
        assert _run_script(tmp_path).returncode == 1

    def test_exits_1_when_empty_home(self):
        env = os.environ.copy()
        env["HOME"] = ""
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert r.returncode == 1


# ── no changes (local repo) ────────────────────────────────────────────


class TestNoChanges:
    def test_no_changes_exits_zero(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        assert _run_script(tmp_path).returncode == 0

    def test_no_extra_commit(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        before = len(_log_oneline(repo))
        _run_script(tmp_path)
        after = len(_log_oneline(repo))
        assert before == after


# ── commit on change (local repo — no push) ────────────────────────────


class TestCommitOnChange:
    def test_commits_new_file(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "notes.md").write_text("new note")
        r = _run_script(tmp_path)
        assert r.returncode == 0
        assert "chromatin backup" in _log_subject(repo)

    def test_commits_modified_file(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "readme.md").write_text("changed")
        r = _run_script(tmp_path)
        assert r.returncode == 0
        assert "chromatin backup" in _log_subject(repo)

    def test_commit_message_has_timestamp(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "notes.md").write_text("ts")
        _run_script(tmp_path)
        subject = _log_subject(repo)
        _, stamp = subject.split(": ", 1)
        datetime.strptime(stamp.strip(), "%Y-%m-%d %H:%M:%S")

    def test_commits_deleted_file(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "readme.md").unlink()
        r = _run_script(tmp_path)
        assert r.returncode == 0
        assert "chromatin backup" in _log_subject(repo)

    def test_commits_staged_change(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "readme.md").write_text("staged")
        _git(repo, "add", "-A")
        r = _run_script(tmp_path)
        assert r.returncode == 0
        assert _status_porcelain(repo) == []

    def test_working_tree_clean_after(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "a.md").write_text("a")
        (repo / "b.md").write_text("b")
        _run_script(tmp_path)
        assert _status_porcelain(repo) == []


# ── push (with remote) — use retries for resource-constrained env ──────


class TestPush:
    def test_pushes_to_remote(self, tmp_path):
        repo, remote_dir = _make_remote_repo(tmp_path)
        (repo / "pushme.md").write_text("push me")
        r = _run_script(tmp_path)
        if r.returncode != 0 and "Resource temporarily unavailable" in (r.stdout + r.stderr):
            pytest.skip("git push failed due to resource limits")
        assert r.returncode == 0
        assert "chromatin backup" in _git(remote_dir, "log", "--oneline", "-1").stdout

    def test_no_push_when_up_to_date(self, tmp_path):
        repo, _ = _make_remote_repo(tmp_path)
        (repo / "f.md").write_text("first")
        r1 = _run_script(tmp_path)
        if r1.returncode != 0 and "Resource temporarily unavailable" in (r1.stdout + r1.stderr):
            pytest.skip("git push failed due to resource limits")
        r2 = _run_script(tmp_path)
        assert r2.returncode == 0


# ── untracked files (local) ────────────────────────────────────────────


class TestUntrackedFiles:
    def test_commits_untracked_file(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "untracked.txt").write_text("new")
        r = _run_script(tmp_path)
        assert r.returncode == 0
        assert "untracked.txt" in _ls_files(repo)


# ── idempotency (local) ────────────────────────────────────────────────


class TestIdempotency:
    def test_double_run_no_error(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "file.md").write_text("content")
        assert _run_script(tmp_path).returncode == 0
        assert _run_script(tmp_path).returncode == 0

    def test_no_duplicate_commits(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "file.md").write_text("content")
        _run_script(tmp_path)
        n = len(_log_oneline(repo))
        _run_script(tmp_path)
        assert len(_log_oneline(repo)) == n


# ── multiple changes (local) ───────────────────────────────────────────


class TestMultipleChanges:
    def test_single_commit_for_all(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "a.md").write_text("a")
        (repo / "b.md").write_text("b")
        (repo / "readme.md").write_text("mod")
        r = _run_script(tmp_path)
        assert r.returncode == 0
        backups = [l for l in _log_oneline(repo) if "chromatin backup" in l]
        assert len(backups) == 1

    def test_all_files_committed(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "a.md").write_text("a")
        (repo / "b.md").write_text("b")
        _run_script(tmp_path)
        files = _ls_files(repo)
        assert "a.md" in files
        assert "b.md" in files


# ── subdirectory (local) ───────────────────────────────────────────────


class TestSubdirectory:
    def test_commits_nested_file(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        sub = repo / "daily" / "2025"
        sub.mkdir(parents=True)
        (sub / "note.md").write_text("nested")
        r = _run_script(tmp_path)
        assert r.returncode == 0
        assert "daily/2025/note.md" in _ls_files(repo)


# ── binary files (local) ───────────────────────────────────────────────


class TestBinaryFiles:
    def test_commits_binary_file(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "data.bin").write_bytes(os.urandom(4096))
        r = _run_script(tmp_path)
        assert r.returncode == 0
        assert "data.bin" in _ls_files(repo)


# ── empty directory (local) ────────────────────────────────────────────


class TestEmptyDirectory:
    def test_empty_dir_not_tracked(self, tmp_path):
        repo = _make_local_repo(tmp_path)
        (repo / "empty_dir").mkdir()
        r = _run_script(tmp_path)
        assert r.returncode == 0
        assert "empty_dir" not in _ls_files(repo)


# ── rebase / merge from remote ─────────────────────────────────────────


class TestRebase:
    def test_rebases_remote_changes(self, tmp_path):
        repo, remote_dir = _make_remote_repo(tmp_path)
        env = _git_env(tmp_path)
        # Make a commit on remote via clone
        clone = tmp_path / "epigenome" / "clone"
        subprocess.run(
            ["git", "clone", str(remote_dir), str(clone)],
            capture_output=True, env=env, timeout=10,
        )
        (clone / "remote.md").write_text("from remote")
        _git(clone, "add", "-A", env=env)
        _git(clone, "commit", "-m", "remote commit", env=env)
        _git(clone, "push", env=env)
        # Local change
        (repo / "local.md").write_text("local")
        r = _run_script(tmp_path)
        if r.returncode != 0 and "Resource temporarily unavailable" in (r.stdout + r.stderr):
            pytest.skip("resource limits")
        assert r.returncode == 0
        lines = _log_oneline(repo)
        assert "chromatin backup" in lines[0]

    def test_merge_on_conflict(self, tmp_path):
        repo, remote_dir = _make_remote_repo(tmp_path)
        env = _git_env(tmp_path)
        # Conflicting change on remote
        clone = tmp_path / "epigenome" / "clone"
        subprocess.run(
            ["git", "clone", str(remote_dir), str(clone)],
            capture_output=True, env=env, timeout=10,
        )
        (clone / "readme.md").write_text("remote")
        _git(clone, "add", "-A", env=env)
        _git(clone, "commit", "-m", "remote conflict", env=env)
        _git(clone, "push", env=env)
        # Local conflicting change
        (repo / "readme.md").write_text("local conflict")
        r = _run_script(tmp_path)
        if r.returncode != 0 and "Resource temporarily unavailable" in (r.stdout + r.stderr):
            pytest.skip("resource limits")
        assert r.returncode == 0
        assert (repo / "readme.md").read_text()
