from __future__ import annotations

"""Tests for agent-sync.sh — pulls config repos and syncs MEMORY.md."""

import subprocess
from pathlib import Path
import tempfile
import os

SCRIPT_PATH = Path.home() / "germline/effectors/agent-sync.sh"


def run_script(args: list[str] = None, env: dict = None) -> subprocess.CompletedProcess:
    """Run agent-sync.sh with optional args and custom env."""
    cmd = [str(SCRIPT_PATH)] + (args or [])
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, env=run_env)


# ── Help flag tests ─────────────────────────────────────────────────


def test_help_flag_exits_zero():
    """--help flag should exit with code 0."""
    result = run_script(["--help"])
    assert result.returncode == 0


def test_help_flag_shows_usage():
    """--help should show usage information."""
    result = run_script(["--help"])
    assert "Usage:" in result.stdout
    assert "agent-sync" in result.stdout


def test_help_flag_short():
    """-h should work the same as --help."""
    result = run_script(["-h"])
    assert result.returncode == 0
    assert "Usage:" in result.stdout


# ── Git repo handling tests ───────────────────────────────────────────


def test_skips_nonexistent_repos(tmp_path):
    """Script should skip repos that don't exist without error."""
    # Create a temp home with no repos
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    result = run_script(env={"HOME": str(fake_home)})
    # Should exit 0 even with no repos
    assert result.returncode == 0


def test_handles_git_repo_no_remote(tmp_path):
    """Script should handle git repos without remotes (pull fails gracefully)."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # Create agent-config repo with no remote
    repo = fake_home / "agent-config"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True, check=True)
    (repo / "file.txt").write_text("content")
    subprocess.run(["git", "add", "file.txt"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, capture_output=True, check=True)

    # Run agent-sync - should exit 0 despite no remote
    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0


def test_handles_multiple_repos(tmp_path):
    """Script should process all three repo paths."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # Create all three repo directories with .git
    for name in ["agent-config", "skills", "epigenome/chromatin"]:
        repo = fake_home / name
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True, check=True)
        # Need at least one commit for pull to work
        (repo / "readme.md").write_text(f"{name} repo")
        subprocess.run(["git", "add", "readme.md"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True, check=True)

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0


# ── MEMORY.md sync tests ──────────────────────────────────────────────


def test_syncs_memory_md(tmp_path):
    """Script should copy MEMORY.md to Claude project dir."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # Create agent-config with MEMORY.md
    agent_config = fake_home / "agent-config"
    agent_config.mkdir()
    subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=agent_config, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=agent_config, capture_output=True, check=True)

    memory_dir = agent_config / "claude" / "memory"
    memory_dir.mkdir(parents=True)
    memory_file = memory_dir / "MEMORY.md"
    memory_file.write_text("# Test Memory\n\nThis is test memory content.")

    # Run script
    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0

    # Check MEMORY.md was copied
    # For HOME=/tmp/test/home, project dir is ~/.claude/projects/-tmp-test-home/memory/
    expected_dst = Path.home() / ".claude/projects/-tmp-test-home/memory/MEMORY.md"
    # But the script uses $HOME from env, so it should be under fake_home
    project_dash = str(fake_home).lstrip("/").replace("/", "-")
    dst = fake_home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists(), f"MEMORY.md not found at {dst}"
    assert "Test Memory" in dst.read_text()


def test_no_error_when_memory_md_missing(tmp_path):
    """Script should not error if MEMORY.md doesn't exist."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # Create agent-config without MEMORY.md
    agent_config = fake_home / "agent-config"
    agent_config.mkdir()
    subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0
