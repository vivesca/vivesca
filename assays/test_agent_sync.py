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


# ── Default run (no args) tests ────────────────────────────────────────


def test_no_args_exits_zero(tmp_path):
    """Running with no arguments should exit 0."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0


def test_no_args_no_stdout(tmp_path):
    """Default run with empty home produces no stdout."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    result = run_script(env={"HOME": str(fake_home)})
    assert result.stdout.strip() == ""


# ── Partial repo existence ─────────────────────────────────────────────


def test_partial_repos_exist(tmp_path):
    """Only some repos exist — should handle gracefully."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # Only create skills repo, not agent-config or epigenome/chromatin
    repo = fake_home / "skills"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True, check=True)
    (repo / "readme.md").write_text("skills")
    subprocess.run(["git", "add", "readme.md"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True, check=True)

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0


# ── MEMORY.md fidelity and edge cases ──────────────────────────────────


def test_memory_md_content_preserved(tmp_path):
    """MEMORY.md content should be copied exactly, including special chars."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    agent_config = fake_home / "agent-config"
    agent_config.mkdir()
    subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

    memory_dir = agent_config / "claude" / "memory"
    memory_dir.mkdir(parents=True)

    # Content with special characters, unicode, long lines
    content = "# Memory\n\n- Item with 'quotes' and \"doubles\"\n- Unicode: café, 日本語\n- Empty lines below:\n\n\n- End\n"
    (memory_dir / "MEMORY.md").write_text(content)

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0

    project_dash = str(fake_home).lstrip("/").replace("/", "-")
    dst = fake_home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()
    assert dst.read_text() == content


def test_memory_md_sync_creates_deep_dirs(tmp_path):
    """Destination directory tree should be created if it doesn't exist."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    agent_config = fake_home / "agent-config"
    agent_config.mkdir()
    subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

    memory_dir = agent_config / "claude" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("data")

    # Ensure .claue/projects dir does NOT exist beforehand
    claude_dir = fake_home / ".claude"
    assert not claude_dir.exists()

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0

    project_dash = str(fake_home).lstrip("/").replace("/", "-")
    dst = fake_home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()


def test_memory_md_overwrites_existing(tmp_path):
    """MEMORY.md should be overwritten if it already exists at destination."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    agent_config = fake_home / "agent-config"
    agent_config.mkdir()
    subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

    memory_dir = agent_config / "claude" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("new content")

    # Pre-create destination with old content
    project_dash = str(fake_home).lstrip("/").replace("/", "-")
    dst_dir = fake_home / ".claude" / "projects" / f"-{project_dash}" / "memory"
    dst_dir.mkdir(parents=True)
    (dst_dir / "MEMORY.md").write_text("old content")

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0

    assert dst_dir.exists()
    assert (dst_dir / "MEMORY.md").read_text() == "new content"


def test_memory_sync_without_agent_config_repo(tmp_path):
    """If agent-config dir doesn't exist, no MEMORY.md sync should happen."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # Only create skills, not agent-config
    repo = fake_home / "skills"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0

    # No .claude dir should be created
    assert not (fake_home / ".claude").exists()


# ── Path derivation tests ──────────────────────────────────────────────


def test_project_dash_derivation(tmp_path):
    """Verify the HOME→project-dash path transformation."""
    fake_home = tmp_path / "deep" / "nested" / "home"
    fake_home.mkdir(parents=True)

    agent_config = fake_home / "agent-config"
    agent_config.mkdir()
    subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

    memory_dir = agent_config / "claude" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("nested test")

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0

    # e.g. HOME=/tmp/xxx/deep/nested/home → project_dash = tmp-xxx-deep-nested-home
    project_dash = str(fake_home).lstrip("/").replace("/", "-")
    dst = fake_home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists(), f"Expected MEMORY.md at {dst}"
    assert dst.read_text() == "nested test"


# ── Script sanity ───────────────────────────────────────────────────────


def test_script_is_executable():
    """agent-sync.sh must have execute permission."""
    assert SCRIPT_PATH.exists()
    assert os.access(str(SCRIPT_PATH), os.X_OK)


# ── Directory-without-.git guard ────────────────────────────────────────


def test_dir_exists_without_git_dir(tmp_path):
    """A plain directory (no .git) under a repo path should be skipped silently."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # Create agent-config as a plain dir (no .git)
    (fake_home / "agent-config").mkdir()
    # skills has a valid .git
    repo = fake_home / "skills"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, capture_output=True, check=True)
    (repo / "f.txt").write_text("x")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "i"], cwd=repo, capture_output=True, check=True)

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0


# ── stderr clean on happy path ──────────────────────────────────────────


def test_no_stderr_on_empty_home(tmp_path):
    """Default run with no repos produces no stderr."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    result = run_script(env={"HOME": str(fake_home)})
    assert result.stderr.strip() == ""


# ── Nested epigenome/chromatin path ─────────────────────────────────────


def test_nested_chromatin_repo(tmp_path):
    """epigenome/chromatin is a nested path — both dirs must be created."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    chromatin = fake_home / "epigenome" / "chromatin"
    chromatin.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=chromatin, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=chromatin, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=chromatin, capture_output=True, check=True)
    (chromatin / "r.md").write_text("c")
    subprocess.run(["git", "add", "r.md"], cwd=chromatin, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "i"], cwd=chromatin, capture_output=True, check=True)

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0


# ── MEMORY.md large content ─────────────────────────────────────────────


def test_memory_md_large_file(tmp_path):
    """MEMORY.md over 100KB should be copied in full."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    agent_config = fake_home / "agent-config"
    agent_config.mkdir()
    subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

    memory_dir = agent_config / "claude" / "memory"
    memory_dir.mkdir(parents=True)

    # ~200KB of repeated lines
    line = "- " + "x" * 500 + "\n"
    big_content = line * 400
    (memory_dir / "MEMORY.md").write_text(big_content)

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0

    project_dash = str(fake_home).lstrip("/").replace("/", "-")
    dst = fake_home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()
    assert dst.read_text() == big_content


# ── Empty / whitespace MEMORY.md ─────────────────────────────────────────


def test_memory_md_empty_file(tmp_path):
    """An empty (zero-byte) MEMORY.md should still be copied."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    agent_config = fake_home / "agent-config"
    agent_config.mkdir()
    subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

    memory_dir = agent_config / "claude" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("")

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0

    project_dash = str(fake_home).lstrip("/").replace("/", "-")
    dst = fake_home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()
    assert dst.read_text() == ""


def test_memory_md_whitespace_only(tmp_path):
    """MEMORY.md with only whitespace should be copied as-is."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    agent_config = fake_home / "agent-config"
    agent_config.mkdir()
    subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

    memory_dir = agent_config / "claude" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("   \n\n\t\n")

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0

    project_dash = str(fake_home).lstrip("/").replace("/", "-")
    dst = fake_home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()
    assert dst.read_text() == "   \n\n\t\n"


# ── Idempotency ──────────────────────────────────────────────────────────


def test_idempotent_double_run(tmp_path):
    """Running the script twice should produce identical results."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    agent_config = fake_home / "agent-config"
    agent_config.mkdir()
    subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

    memory_dir = agent_config / "claude" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("stable content\n")

    project_dash = str(fake_home).lstrip("/").replace("/", "-")
    dst = fake_home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"

    # First run
    r1 = run_script(env={"HOME": str(fake_home)})
    assert r1.returncode == 0
    content1 = dst.read_text()

    # Second run
    r2 = run_script(env={"HOME": str(fake_home)})
    assert r2.returncode == 0
    content2 = dst.read_text()

    assert content1 == content2 == "stable content\n"


# ── Unknown arguments ────────────────────────────────────────────────────


def test_unknown_args_still_exit_zero(tmp_path):
    """Unknown arguments are ignored; script still exits 0."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    result = run_script(["--bogus"], env={"HOME": str(fake_home)})
    assert result.returncode == 0


# ── agent-config has MEMORY.md but no .git ───────────────────────────────


def test_memory_md_sync_without_git_in_agent_config(tmp_path):
    """MEMORY.md is synced even when agent-config lacks .git directory."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # agent-config is a plain dir (no .git) but has MEMORY.md
    agent_config = fake_home / "agent-config"
    agent_config.mkdir()
    memory_dir = agent_config / "claude" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("no-git memory")

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0

    project_dash = str(fake_home).lstrip("/").replace("/", "-")
    dst = fake_home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()
    assert dst.read_text() == "no-git memory"


# ── git repo with no commits ─────────────────────────────────────────────


def test_git_repo_no_commits(tmp_path):
    """A bare git init (no commits) should not crash the script."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    repo = fake_home / "agent-config"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    # No commits — pull will fail but `|| true` should catch it

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0
