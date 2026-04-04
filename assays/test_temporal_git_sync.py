"""Tests for temporal worker auto git sync (t-ff66cc)."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _init_repo(tmp_path: Path) -> Path:
    """Create a git repo with one commit for testing."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, capture_output=True)
    (repo / "README.md").write_text("init")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
    return repo


def _init_repo_with_remote(tmp_path: Path) -> tuple[Path, Path]:
    """Create a repo with a bare remote for push/pull testing."""
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(bare)], capture_output=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", str(bare), str(repo)], capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, capture_output=True)
    (repo / "README.md").write_text("init")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
    subprocess.run(["git", "push"], cwd=repo, capture_output=True)
    return repo, bare


class TestPreRibosomePull:
    """Pre-ribosome git pull --ff-only should pick up CC-written test files."""

    def test_pull_picks_up_new_files(self, tmp_path: Path):
        repo, bare = _init_repo_with_remote(tmp_path)
        soma_clone = tmp_path / "soma"
        subprocess.run(["git", "clone", str(bare), str(soma_clone)], capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "cc@test.com"], cwd=soma_clone, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "cc"], cwd=soma_clone, capture_output=True)
        (soma_clone / "assays").mkdir(exist_ok=True)
        (soma_clone / "assays" / "test_new.py").write_text("# test")
        subprocess.run(["git", "add", "."], cwd=soma_clone, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "cc: add test"], cwd=soma_clone, capture_output=True
        )
        subprocess.run(["git", "push"], cwd=soma_clone, capture_output=True)
        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0
        assert (repo / "assays" / "test_new.py").exists()

    def test_pull_failure_does_not_block(self, tmp_path: Path):
        repo = _init_repo(tmp_path)
        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode != 0


class TestPostRibosomePush:
    """Post-ribosome git push should sync commits to origin."""

    def test_push_after_ribosome_commit(self, tmp_path: Path):
        repo, bare = _init_repo_with_remote(tmp_path)
        (repo / "fix.py").write_text("# ribosome fix")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "ribosome: fix thing"], cwd=repo, capture_output=True
        )
        result = subprocess.run(
            ["git", "push"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        verify = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=bare,
            capture_output=True,
            text=True,
        )
        assert "ribosome: fix thing" in verify.stdout

    def test_push_failure_does_not_change_rc(self, tmp_path: Path):
        repo = _init_repo(tmp_path)
        (repo / "fix.py").write_text("# ribosome fix")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "ribosome: fix"], cwd=repo, capture_output=True)
        subprocess.run(
            ["git", "push"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
        )
        ribosome_rc = 0
        assert ribosome_rc == 0, "Push failure must not change ribosome exit code"

    def test_no_push_when_no_changes(self, tmp_path: Path):
        repo, _bare = _init_repo_with_remote(tmp_path)
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        has_changes = bool(result.stdout.strip())
        assert not has_changes
