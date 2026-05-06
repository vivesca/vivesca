"""Assays for synapse recent-git-log injection.

Per spec: synapse-recent-git-log-injection.md.
Function name expected: _inject_recent_git_log (matches existing synapse convention
for internal helpers: leading underscore + verb_phrase).
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess

SYNAPSE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / "membrane" / "cytoskeleton" / "synapse.py"
)

_spec = importlib.util.spec_from_file_location("synapse", str(SYNAPSE_PATH))
_synapse = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_synapse)

_inject_recent_git_log = _synapse._inject_recent_git_log


def _make_repo(tmpdir: pathlib.Path, name: str, with_commit: bool = True) -> pathlib.Path:
    """Create a tiny git repo with one optional commit."""
    repo = tmpdir / name
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@test.test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "test"], check=True)
    if with_commit:
        (repo / "README.md").write_text("test")
        subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-q", "-m", "initial test commit"],
            check=True,
        )
    return repo


class TestInjectRecentGitLog:
    def test_two_repos_with_recent_commits(self, tmp_path, monkeypatch):
        """POS: both repos have commits → both appear in injected block."""
        _make_repo(tmp_path, "germline", with_commit=True)
        _make_repo(tmp_path, "epigenome", with_commit=True)
        monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
        result = _inject_recent_git_log()
        assert "germline" in result
        assert "epigenome" in result
        assert "initial test commit" in result

    def test_no_recent_commits(self, tmp_path, monkeypatch):
        """NEG: neither repo has recent commits → empty (no header)."""
        # Repos exist but with no commits in last 48h
        _make_repo(tmp_path, "germline", with_commit=False)
        _make_repo(tmp_path, "epigenome", with_commit=False)
        monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
        assert _inject_recent_git_log() == ""

    def test_missing_repo_silent_skip(self, tmp_path, monkeypatch):
        """NEG: a repo path doesn't exist → skipped silently, no error."""
        _make_repo(tmp_path, "germline", with_commit=True)
        # epigenome intentionally not created
        monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
        result = _inject_recent_git_log()
        # Should still contain germline; should not raise
        assert "germline" in result
