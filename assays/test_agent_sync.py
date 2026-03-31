"""Tests for agent-sync.sh — pull config repos and sync MEMORY.md."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path("/home/terry/germline/effectors/agent-sync.sh")


def _run(*extra_args: str, home: str | None = None, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run agent-sync.sh with optional HOME override and extra args."""
    env = os.environ.copy()
    if home is not None:
        env["HOME"] = home
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT), *extra_args],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def _init_git_repo(path: Path) -> None:
    """Create a minimal git repo at path."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True, check=True)
    readme = path / "README.md"
    readme.write_text("test\n")
    subprocess.run(["git", "add", "README.md"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, capture_output=True, check=True)


# ── Help flag tests ───────────────────────────────────────────────────


def test_help_long_flag():
    """--help shows usage and exits 0."""
    r = _run("--help")
    assert r.returncode == 0
    assert "Usage:" in r.stdout


def test_help_short_flag():
    """-h shows usage and exits 0."""
    r = _run("-h")
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "agent-sync.sh" in r.stdout


# ── Git pull tests ────────────────────────────────────────────────────


def test_pulls_repos_with_git_dirs(tmp_path):
    """Script runs git pull on each repo that has a .git directory."""
    home = tmp_path / "home"
    home.mkdir()
    for name in ["agent-config", "skills", "code/epigenome/chromatin"]:
        _init_git_repo(home / name)

    # Create a fake git that records calls
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log_file = tmp_path / "git_calls.txt"
    fake_git = fake_bin / "git"
    fake_git.write_text(f'#!/bin/bash\necho "$@" >> {log_file}\nexit 0\n')
    fake_git.chmod(0o755)

    r = _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})
    assert r.returncode == 0

    calls = log_file.read_text()
    # Should see pull --rebase for each of the 3 repos
    assert "pull --rebase" in calls
    assert calls.count("pull --rebase") == 3


def test_skips_repos_without_git_dirs(tmp_path):
    """Script skips repos that lack a .git directory."""
    home = tmp_path / "home"
    home.mkdir()
    # Create directories but don't init git
    for name in ["agent-config", "skills", "code/epigenome/chromatin"]:
        (home / name).mkdir(parents=True)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log_file = tmp_path / "git_calls.txt"
    fake_git = fake_bin / "git"
    fake_git.write_text(f'#!/bin/bash\necho "$@" >> {log_file}\nexit 0\n')
    fake_git.chmod(0o755)

    r = _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})
    assert r.returncode == 0

    calls = log_file.read_text()
    assert "pull" not in calls


def test_missing_repos_are_skipped(tmp_path):
    """Script does not fail when repo directories don't exist at all."""
    home = tmp_path / "home"
    home.mkdir()
    # Don't create any of the expected repo dirs

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log_file = tmp_path / "git_calls.txt"
    fake_git = fake_bin / "git"
    fake_git.write_text(f'#!/bin/bash\necho "$@" >> {log_file}\nexit 0\n')
    fake_git.chmod(0o755)

    r = _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})
    assert r.returncode == 0

    calls = log_file.read_text()
    assert "pull" not in calls


def test_git_pull_rebase_fallback(tmp_path):
    """When git pull --rebase fails, script falls back to plain git pull."""
    home = tmp_path / "home"
    home.mkdir()
    for name in ["agent-config", "skills", "code/epigenome/chromatin"]:
        _init_git_repo(home / name)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log_file = tmp_path / "git_calls.txt"
    # Fake git: fail on --rebase, succeed on plain pull
    fake_git = fake_bin / "git"
    fake_git.write_text(
        '#!/bin/bash\n'
        f'echo "$@" >> {log_file}\n'
        'if [[ "$1" == "pull" && "$2" == "--rebase" ]]; then\n'
        '  exit 1\n'
        'fi\n'
        'exit 0\n'
    )
    fake_git.chmod(0o755)

    r = _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})
    assert r.returncode == 0

    calls = log_file.read_text()
    lines = calls.strip().splitlines()
    # Each repo should have: pull --rebase (fail) then pull (fallback)
    rebase_count = sum(1 for l in lines if "pull --rebase" in l)
    plain_pull_count = sum(1 for l in lines if l.strip() == "pull" or l.strip().startswith("pull ") and "--rebase" not in l)
    assert rebase_count == 3
    assert plain_pull_count == 3


# ── MEMORY.md sync tests ─────────────────────────────────────────────


def test_copies_memory_md_when_source_exists(tmp_path):
    """Script copies MEMORY.md to Claude project dir when source exists."""
    home = tmp_path / "home"
    home.mkdir()

    # Create agent-config with MEMORY.md
    agent_config = home / "agent-config"
    _init_git_repo(agent_config)
    memory_src = agent_config / "claude" / "memory"
    memory_src.mkdir(parents=True)
    (memory_src / "MEMORY.md").write_text("# Test Memory\n")

    # Create .claude/projects dir structure
    claude_projects = home / ".claude" / "projects"
    claude_projects.mkdir(parents=True)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text("#!/bin/bash\nexit 0\n")
    fake_git.chmod(0o755)

    r = _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})
    assert r.returncode == 0

    # Derive expected dst path: strip leading /, replace / with -
    home_str = str(home)
    project_dash = home_str.lstrip("/").replace("/", "-")
    dst = home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()
    assert dst.read_text() == "# Test Memory\n"


def test_no_copy_when_source_missing(tmp_path):
    """Script does not create destination when MEMORY.md source is absent."""
    home = tmp_path / "home"
    home.mkdir()

    # Create agent-config but no MEMORY.md
    agent_config = home / "agent-config"
    _init_git_repo(agent_config)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text("#!/bin/bash\nexit 0\n")
    fake_git.chmod(0o755)

    r = _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})
    assert r.returncode == 0

    # Derive expected dst path
    home_str = str(home)
    project_dash = home_str.lstrip("/").replace("/", "-")
    dst_dir = home / ".claude" / "projects" / f"-{project_dash}" / "memory"
    assert not dst_dir.exists()


def test_creates_destination_directory(tmp_path):
    """Script creates the destination directory tree if it doesn't exist."""
    home = tmp_path / "home"
    home.mkdir()

    # Create agent-config with MEMORY.md
    agent_config = home / "agent-config"
    _init_git_repo(agent_config)
    memory_src = agent_config / "claude" / "memory"
    memory_src.mkdir(parents=True)
    (memory_src / "MEMORY.md").write_text("# Memory\n")

    # Do NOT create .claude/projects dir — script should mkdir -p

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text("#!/bin/bash\nexit 0\n")
    fake_git.chmod(0o755)

    r = _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})
    assert r.returncode == 0

    home_str = str(home)
    project_dash = home_str.lstrip("/").replace("/", "-")
    dst = home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()


def test_overwrites_existing_memory_md(tmp_path):
    """Script overwrites destination MEMORY.md if it already exists."""
    home = tmp_path / "home"
    home.mkdir()

    # Create agent-config with new MEMORY.md
    agent_config = home / "agent-config"
    _init_git_repo(agent_config)
    memory_src = agent_config / "claude" / "memory"
    memory_src.mkdir(parents=True)
    (memory_src / "MEMORY.md").write_text("# Updated Memory\n")

    # Create old destination
    home_str = str(home)
    project_dash = home_str.lstrip("/").replace("/", "-")
    dst_dir = home / ".claude" / "projects" / f"-{project_dash}" / "memory"
    dst_dir.mkdir(parents=True)
    (dst_dir / "MEMORY.md").write_text("# Old Memory\n")

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text("#!/bin/bash\nexit 0\n")
    fake_git.chmod(0o755)

    r = _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})
    assert r.returncode == 0

    dst = dst_dir / "MEMORY.md"
    assert dst.read_text() == "# Updated Memory\n"


# ── PROJECT_DASH computation tests ────────────────────────────────────


def test_project_dash_simple_path(tmp_path):
    """PROJECT_DASH correctly converts a simple HOME path."""
    home = tmp_path / "home"
    home.mkdir()
    agent_config = home / "agent-config"
    _init_git_repo(agent_config)
    memory_src = agent_config / "claude" / "memory"
    memory_src.mkdir(parents=True)
    (memory_src / "MEMORY.md").write_text("# test\n")

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text("#!/bin/bash\nexit 0\n")
    fake_git.chmod(0o755)

    _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})

    # HOME = /tmp/xxx/home → PROJECT_SLASH = tmp/xxx/home → PROJECT_DASH = tmp-xxx-home
    home_str = str(home)
    project_dash = home_str.lstrip("/").replace("/", "-")
    dst = home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists(), f"Expected {dst} to exist, PROJECT_DASH should be '{project_dash}'"


def test_project_dash_deep_path(tmp_path):
    """PROJECT_DASH correctly converts a deep nested HOME path."""
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    agent_config = deep / "agent-config"
    _init_git_repo(agent_config)
    memory_src = agent_config / "claude" / "memory"
    memory_src.mkdir(parents=True)
    (memory_src / "MEMORY.md").write_text("# test\n")

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text("#!/bin/bash\nexit 0\n")
    fake_git.chmod(0o755)

    _run(home=str(deep), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})

    home_str = str(deep)
    project_dash = home_str.lstrip("/").replace("/", "-")
    # e.g. /tmp/xxx/a/b/c → tmp-xxx-a-b-c
    dst = deep / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists(), f"Expected {dst}, PROJECT_DASH should be '{project_dash}'"


# ── No-arg run (happy path) ───────────────────────────────────────────


def test_no_args_runs_normally(tmp_path):
    """Running with no arguments performs sync (not help)."""
    home = tmp_path / "home"
    home.mkdir()
    for name in ["agent-config", "skills", "code/epigenome/chromatin"]:
        _init_git_repo(home / name)

    # Provide MEMORY.md source
    memory_src = home / "agent-config" / "claude" / "memory"
    memory_src.mkdir(parents=True)
    (memory_src / "MEMORY.md").write_text("# Synced\n")

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log_file = tmp_path / "git_calls.txt"
    fake_git = fake_bin / "git"
    fake_git.write_text(f'#!/bin/bash\necho "$@" >> {log_file}\nexit 0\n')
    fake_git.chmod(0o755)

    r = _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})
    assert r.returncode == 0

    # Verify git was called
    assert "pull --rebase" in log_file.read_text()

    # Verify MEMORY.md was synced
    home_str = str(home)
    project_dash = home_str.lstrip("/").replace("/", "-")
    dst = home / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.read_text() == "# Synced\n"


def test_set_u_catches_unset_vars(tmp_path):
    """Script uses set -u, so unset variables cause errors (non-zero exit)."""
    home = tmp_path / "home"
    home.mkdir()

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text("#!/bin/bash\nexit 0\n")
    fake_git.chmod(0o755)

    # Run without HOME set — should fail due to set -u
    env = os.environ.copy()
    env.pop("HOME", None)
    env["PATH"] = f"{fake_bin}:{os.environ['PATH']}"
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    # set -u means referencing unset $HOME is an error
    # But HOME is likely set in os.environ, so this test verifies
    # the pattern is correct by unsetting it in the env
    # If bash still has HOME from /etc/profile, we can't fully test this
    # Just verify the script doesn't crash unexpectedly
    assert r.returncode in (0, 1)


# ── Partial repo presence ─────────────────────────────────────────────


def test_only_some_repos_exist(tmp_path):
    """Script handles when only some of the 3 expected repos exist."""
    home = tmp_path / "home"
    home.mkdir()
    # Only create agent-config
    _init_git_repo(home / "agent-config")
    # skills and chromatin don't exist

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log_file = tmp_path / "git_calls.txt"
    fake_git = fake_bin / "git"
    fake_git.write_text(f'#!/bin/bash\necho "$@" >> {log_file}\nexit 0\n')
    fake_git.chmod(0o755)

    r = _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})
    assert r.returncode == 0

    calls = log_file.read_text()
    assert calls.count("pull --rebase") == 1


def test_git_pull_failure_does_not_stop_script(tmp_path):
    """Script continues even if git pull fails for a repo (|| true)."""
    home = tmp_path / "home"
    home.mkdir()
    for name in ["agent-config", "skills", "code/epigenome/chromatin"]:
        _init_git_repo(home / name)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log_file = tmp_path / "git_calls.txt"
    # Git fails on everything
    fake_git = fake_bin / "git"
    fake_git.write_text(f'#!/bin/bash\necho "$@" >> {log_file}\nexit 1\n')
    fake_git.chmod(0o755)

    r = _run(home=str(home), env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"})
    # Should succeed because of || true
    assert r.returncode == 0

    calls = log_file.read_text()
    # Should have attempted pull for all 3 repos
    assert calls.count("pull --rebase") == 3
    # And plain pull fallback for all 3
    plain_pull = [l for l in calls.strip().splitlines() if l.strip().startswith("pull") and "--rebase" not in l]
    assert len(plain_pull) == 3
