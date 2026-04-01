from __future__ import annotations

"""Tests for effectors/pharos-sync.sh — bash script tested via subprocess."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-sync.sh"
RSYNC_AVAILABLE = shutil.which("rsync") is not None

# ── helpers ─────────────────────────────────────────────────────────────


def _run(
    tmp_path: Path, args: list[str] | None = None, env_extra: dict | None = None
) -> subprocess.CompletedProcess:
    """Run pharos-sync.sh with HOME=tmp_path."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["PATH"] = "/usr/bin:/bin"  # minimal PATH — no flyctl, no scp
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT)] + (args or []),
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def _source_sync_file(src: Path, dst: Path) -> subprocess.CompletedProcess:
    """Source the script (to load sync_file) then invoke it with given args."""
    return subprocess.run(
        ["bash", "-c", f'source "{SCRIPT}" && sync_file "$1" "$2"', "_test", str(src), str(dst)],
        capture_output=True,
        text=True,
        timeout=10,
    )


def _make_git_repo(path: Path) -> None:
    """Initialise a git repo so commit/push commands don't crash."""
    subprocess.run(["git", "init", str(path)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(path), "commit", "--allow-empty", "-m", "init"],
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )


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
        r = self._run_help("--help")
        assert r.returncode == 0

    def test_help_short_flag_exits_zero(self):
        r = self._run_help("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = self._run_help("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_sync(self):
        r = self._run_help("--help")
        assert "sync" in r.stdout.lower() or "Sync" in r.stdout


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/") and "bash" in first

    def test_has_set_uo_pipefail(self):
        src = SCRIPT.read_text()
        assert "set -uo pipefail" in src

    def test_has_sync_file_function(self):
        src = SCRIPT.read_text()
        assert "sync_file()" in src

    def test_main_guard_uses_bash_source(self):
        src = SCRIPT.read_text()
        assert "BASH_SOURCE" in src


# ── script permissions ──────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_is_regular_file(self):
        assert SCRIPT.is_file()


# ── sync_file() unit tests (sourced) ────────────────────────────────────


class TestSyncFileSourced:
    def test_copies_new_file(self, tmp_path):
        src = tmp_path / "a.txt"
        src.write_text("hello")
        dst = tmp_path / "out" / "a.txt"
        r = _source_sync_file(src, dst)
        assert r.returncode == 0
        assert dst.read_text() == "hello"

    def test_creates_parent_directory(self, tmp_path):
        src = tmp_path / "a.txt"
        src.write_text("data")
        dst = tmp_path / "deep" / "nested" / "dir" / "a.txt"
        r = _source_sync_file(src, dst)
        assert r.returncode == 0
        assert dst.exists()

    def test_returns_1_when_src_missing(self, tmp_path):
        src = tmp_path / "nonexistent.txt"
        dst = tmp_path / "out.txt"
        r = _source_sync_file(src, dst)
        assert r.returncode == 1

    def test_skips_identical_file(self, tmp_path):
        content = "unchanged"
        src = tmp_path / "a.txt"
        src.write_text(content)
        dst = tmp_path / "a_copy.txt"
        dst.write_text(content)
        r = _source_sync_file(src, dst)
        # sync_file returns 1 when file is unchanged
        assert r.returncode == 1

    def test_overwrites_changed_file(self, tmp_path):
        src = tmp_path / "src.txt"
        src.write_text("new content")
        dst = tmp_path / "dst.txt"
        dst.write_text("old content")
        r = _source_sync_file(src, dst)
        assert r.returncode == 0
        assert dst.read_text() == "new content"

    def test_prints_updated_on_success(self, tmp_path):
        src = tmp_path / "a.txt"
        src.write_text("data")
        dst = tmp_path / "out" / "a.txt"
        r = _source_sync_file(src, dst)
        assert "updated:" in r.stdout

    def test_no_output_when_unchanged(self, tmp_path):
        content = "same"
        src = tmp_path / "a.txt"
        src.write_text(content)
        dst = tmp_path / "a.txt"
        dst.write_text(content)
        r = _source_sync_file(src, dst)
        assert r.stdout.strip() == ""


# ── main script behaviour ──────────────────────────────────────────────


class TestMainExecution:
    def test_exits_zero_with_empty_home(self, tmp_path):
        r = _run(tmp_path)
        assert r.returncode == 0

    def test_syncs_settings_json(self, tmp_path):
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text('{"key": "val"}')
        officina = tmp_path / "officina"
        officina.mkdir()
        r = _run(tmp_path)
        assert (officina / "claude" / "settings.json").read_text() == '{"key": "val"}'

    def test_settings_sync_prints_updated(self, tmp_path):
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text('{"a": 1}')
        officina = tmp_path / "officina"
        officina.mkdir()
        r = _run(tmp_path)
        assert "updated: settings.json" in r.stdout

    def test_no_update_when_settings_unchanged(self, tmp_path):
        content = '{"unchanged": true}'
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text(content)
        officina = tmp_path / "officina"
        officina.mkdir()
        (officina / "claude").mkdir(parents=True)
        (officina / "claude" / "settings.json").write_text(content)
        r = _run(tmp_path)
        # The word "updated" should NOT appear for settings
        lines = [l for l in r.stdout.strip().splitlines() if "settings.json" in l]
        assert all("updated" not in l for l in lines)

    @pytest.mark.skipif(not RSYNC_AVAILABLE, reason="rsync not installed")
    def test_syncs_memory_directory(self, tmp_path):
        memory_src = tmp_path / ".claude" / "projects" / "-Users-terry" / "memory"
        memory_src.mkdir(parents=True)
        (memory_src / "notes.md").write_text("# Notes")
        (memory_src / "tips.md").write_text("# Tips")
        officina = tmp_path / "officina"
        officina.mkdir()
        r = _run(tmp_path)
        dst = officina / "claude" / "memory"
        assert (dst / "notes.md").read_text() == "# Notes"
        assert (dst / "tips.md").read_text() == "# Tips"

    @pytest.mark.skipif(not RSYNC_AVAILABLE, reason="rsync not installed")
    def test_memory_sync_prints_synced(self, tmp_path):
        memory_src = tmp_path / ".claude" / "projects" / "-Users-terry" / "memory"
        memory_src.mkdir(parents=True)
        (memory_src / "a.md").write_text("x")
        officina = tmp_path / "officina"
        officina.mkdir()
        r = _run(tmp_path)
        assert "synced: memory/" in r.stdout

    def test_skips_memory_when_no_source_dir(self, tmp_path):
        officina = tmp_path / "officina"
        officina.mkdir()
        r = _run(tmp_path)
        assert "synced: memory/" not in r.stdout

    def test_git_commit_on_change(self, tmp_path):
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text('{"x": 1}')
        officina = tmp_path / "officina"
        officina.mkdir()
        _make_git_repo(officina)
        r = _run(tmp_path, env_extra={
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
        })
        assert r.returncode == 0
        log = subprocess.run(
            ["git", "-C", str(officina), "log", "--oneline"],
            capture_output=True, text=True,
        )
        # Should have a "sync:" commit beyond the initial empty one
        commits = [l for l in log.stdout.strip().splitlines() if "sync:" in l.lower()]
        assert len(commits) >= 1

    def test_no_git_commit_when_no_changes(self, tmp_path):
        officina = tmp_path / "officina"
        officina.mkdir()
        _make_git_repo(officina)
        r = _run(tmp_path, env_extra={
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
        })
        assert r.returncode == 0
        log = subprocess.run(
            ["git", "-C", str(officina), "log", "--oneline"],
            capture_output=True, text=True,
        )
        # Only the initial commit — no "sync:" commit
        commits = [l for l in log.stdout.strip().splitlines() if "sync:" in l.lower()]
        assert len(commits) == 0

    def test_sourcing_does_not_run_main(self, tmp_path):
        """Sourcing the script should not execute any sync logic."""
        r = subprocess.run(
            ["bash", "-c", f'source "{SCRIPT}" && echo "sourced ok"'],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "sourced ok" in r.stdout
        # No sync output when sourced
        assert "updated:" not in r.stdout
        assert "synced:" not in r.stdout
