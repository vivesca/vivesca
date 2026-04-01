from __future__ import annotations

"""Tests for soma-activate — bash effector that activates a gemmule image."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path("/home/terry/germline/effectors/soma-activate")


def _run_activate(home: Path, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run soma-activate with HOME overridden to a temp directory."""
    env = os.environ.copy()
    env["HOME"] = str(home)
    # Suppress git credential prompts and color
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["NO_COLOR"] = "1"
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["/usr/bin/env", "bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def _make_env_fly(home: Path, content: str = "") -> Path:
    """Create a minimal ~/.env.fly."""
    env_file = home / ".env.fly"
    env_file.write_text(content or "export OP_SERVICE_ACCOUNT_TOKEN=ops_test\n")
    return env_file


def _make_germline(home: Path) -> Path:
    """Create a minimal ~/germline with .git dir and key subdirs."""
    germline = home / "germline"
    (germline / ".git").mkdir(parents=True)
    (germline / "membrane" / "cytoskeleton").mkdir(parents=True)
    (germline / "membrane" / "receptors").mkdir(parents=True)
    (germline / "membrane" / "buds").mkdir(parents=True)
    (germline / "membrane" / "settings.json").write_text("{}")
    # Add a sample hook
    (germline / "membrane" / "cytoskeleton" / "hook1.py").write_text("# hook\n")
    # Add a sample skill dir
    (germline / "membrane" / "receptors" / "skill-a").mkdir()
    # Add a sample agent
    (germline / "membrane" / "buds" / "agent1.md").write_text("# agent\n")
    return germline


def _make_epigenome(home: Path) -> Path:
    """Create a minimal ~/epigenome with .git dir and marks."""
    epigenome = home / "epigenome"
    (epigenome / ".git").mkdir(parents=True)
    (epigenome / "marks").mkdir(parents=True)
    (epigenome / "marks" / "MEMORY.md").write_text("# Memory\n")
    return epigenome


# ── Pre-flight: missing ~/.env.fly ───────────────────────────────────


def test_exits_1_when_env_fly_missing(tmp_path):
    """soma-activate exits 1 when ~/.env.fly is not found."""
    result = _run_activate(tmp_path)
    assert result.returncode == 1
    assert ".env.fly not found" in result.stdout


def test_env_fly_missing_prints_guidance(tmp_path):
    """soma-activate prints setup guidance when .env.fly is missing."""
    result = _run_activate(tmp_path)
    assert "OP_SERVICE_ACCOUNT_TOKEN" in result.stdout
    assert "GITHUB_TOKEN" in result.stdout


# ── Pre-flight: ~/.env.fly present ───────────────────────────────────


def test_succeeds_with_env_fly(tmp_path):
    """soma-activate succeeds (exit 0) when .env.fly exists."""
    _make_env_fly(tmp_path)
    result = _run_activate(tmp_path)
    assert result.returncode == 0


def test_prints_activation_banner(tmp_path):
    """soma-activate prints 'Soma activation' banner."""
    _make_env_fly(tmp_path)
    result = _run_activate(tmp_path)
    assert "Soma activation" in result.stdout


def test_prints_soma_activated_at_end(tmp_path):
    """soma-activate prints 'Soma activated' completion message."""
    _make_env_fly(tmp_path)
    result = _run_activate(tmp_path)
    assert "Soma activated" in result.stdout


# ── Symlinks: hooks ──────────────────────────────────────────────────


def test_links_hooks_from_cytoskeleton(tmp_path):
    """soma-activate symlinks .py hooks from membrane/cytoskeleton."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    result = _run_activate(tmp_path)
    hook_link = tmp_path / ".claude" / "hooks" / "hook1.py"
    assert hook_link.is_symlink()
    assert hook_link.resolve().name == "hook1.py"


def test_hooks_output_count(tmp_path):
    """soma-activate reports linked hooks count."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    result = _run_activate(tmp_path)
    assert "hooks linked" in result.stdout


# ── Symlinks: skills ─────────────────────────────────────────────────


def test_links_skills_from_receptors(tmp_path):
    """soma-activate symlinks skill dirs from membrane/receptors."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    result = _run_activate(tmp_path)
    skill_link = tmp_path / ".claude" / "skills" / "skill-a"
    assert skill_link.is_symlink()


def test_skills_output_count(tmp_path):
    """soma-activate reports linked skills count."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    result = _run_activate(tmp_path)
    assert "skills linked" in result.stdout


# ── Symlinks: agents ─────────────────────────────────────────────────


def test_links_agents_from_buds(tmp_path):
    """soma-activate symlinks agent .md files from membrane/buds."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    result = _run_activate(tmp_path)
    agent_link = tmp_path / ".claude" / "agents" / "agent1.md"
    assert agent_link.is_symlink()


def test_agents_output_message(tmp_path):
    """soma-activate reports agents linked."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    result = _run_activate(tmp_path)
    assert "agents linked" in result.stdout


# ── Symlinks: settings.json ──────────────────────────────────────────


def test_links_settings_json(tmp_path):
    """soma-activate symlinks membrane/settings.json to ~/.claude/settings.json."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    result = _run_activate(tmp_path)
    settings_link = tmp_path / ".claude" / "settings.json"
    assert settings_link.is_symlink()
    assert settings_link.resolve().name == "settings.json"


def test_settings_json_output(tmp_path):
    """soma-activate reports settings.json linked."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    result = _run_activate(tmp_path)
    assert "settings.json linked" in result.stdout


# ── Symlinks: memory ─────────────────────────────────────────────────


def test_links_memory_marks(tmp_path):
    """soma-activate links MEMORY.md from epigenome/marks."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    _make_epigenome(tmp_path)
    result = _run_activate(tmp_path)
    memory_link = tmp_path / ".claude" / "projects" / "-home-terry" / "memory" / "MEMORY.md"
    assert memory_link.is_symlink()


def test_memory_output(tmp_path):
    """soma-activate reports memory linked."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    _make_epigenome(tmp_path)
    result = _run_activate(tmp_path)
    assert "memory linked" in result.stdout


# ── Symlinks: creates directories ────────────────────────────────────


def test_creates_claude_subdirs(tmp_path):
    """soma-activate creates ~/.claude/hooks, skills, agents dirs."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    result = _run_activate(tmp_path)
    assert (tmp_path / ".claude" / "hooks").is_dir()
    assert (tmp_path / ".claude" / "skills").is_dir()
    assert (tmp_path / ".claude" / "agents").is_dir()


# ── Symlinks: idempotent ─────────────────────────────────────────────


def test_idempotent_symlink_creation(tmp_path):
    """Running soma-activate twice does not fail on existing symlinks."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    # Run once
    result1 = _run_activate(tmp_path)
    assert result1.returncode == 0
    # Run again — ln -sfn should overwrite without error
    result2 = _run_activate(tmp_path)
    assert result2.returncode == 0
    # Symlink should still point to correct target
    hook_link = tmp_path / ".claude" / "hooks" / "hook1.py"
    assert hook_link.is_symlink()


# ── Repo: clone_if_missing skips existing ────────────────────────────


def test_skips_already_cloned_repos(tmp_path):
    """soma-activate skips repos that already have .git dirs."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    _make_epigenome(tmp_path)
    result = _run_activate(tmp_path)
    assert "already cloned" in result.stdout


def test_pulls_existing_repos(tmp_path):
    """soma-activate attempts git pull on already-cloned repos."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    _make_epigenome(tmp_path)
    result = _run_activate(tmp_path)
    # git pull --ff-only will fail (not a real repo), but script uses || true
    assert "updated" in result.stdout or result.returncode == 0


# ── SSH section ───────────────────────────────────────────────────────


def test_reports_no_ssh_key(tmp_path):
    """soma-activate reports when no SSH key exists."""
    _make_env_fly(tmp_path)
    result = _run_activate(tmp_path)
    assert "No SSH key found" in result.stdout


def test_reports_existing_ssh_key(tmp_path):
    """soma-activate reports skip when SSH key already exists."""
    _make_env_fly(tmp_path)
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "id_ed25519").write_text("fake key")
    result = _run_activate(tmp_path)
    assert "SSH key exists" in result.stdout


# ── Tailscale section ─────────────────────────────────────────────────


def test_tailscale_section_outputs(tmp_path):
    """soma-activate outputs tailscale guidance when not connected."""
    _make_env_fly(tmp_path)
    result = _run_activate(tmp_path)
    # Either "tailscale connected" (if installed and running) or guidance
    assert "tailscale" in result.stdout.lower()


# ── Claude Code section ───────────────────────────────────────────────


def test_claude_section_outputs(tmp_path):
    """soma-activate outputs claude code status."""
    _make_env_fly(tmp_path)
    result = _run_activate(tmp_path)
    # Either "claude installed" or install guidance
    assert "claude" in result.stdout.lower()


# ── Summary output ────────────────────────────────────────────────────


def test_prints_remaining_manual_steps(tmp_path):
    """soma-activate lists remaining manual steps."""
    _make_env_fly(tmp_path)
    result = _run_activate(tmp_path)
    assert "Remaining manual steps" in result.stdout


def test_prints_directory_summary(tmp_path):
    """soma-activate prints directory summary."""
    _make_env_fly(tmp_path)
    result = _run_activate(tmp_path)
    assert "germline:" in result.stdout
    assert "epigenome:" in result.stdout
    assert "effectors:" in result.stdout


# ── Missing germline dirs: graceful ──────────────────────────────────


def test_no_hooks_dir_graceful(tmp_path):
    """soma-activate handles missing cytoskeleton dir gracefully."""
    _make_env_fly(tmp_path)
    germline = tmp_path / "germline"
    (germline / ".git").mkdir(parents=True)
    # No membrane/cytoskeleton dir
    result = _run_activate(tmp_path)
    assert result.returncode == 0
    # Should not have "hooks linked"
    assert "hooks linked" not in result.stdout


def test_no_receptors_dir_graceful(tmp_path):
    """soma-activate handles missing receptors dir gracefully."""
    _make_env_fly(tmp_path)
    germline = tmp_path / "germline"
    (germline / ".git").mkdir(parents=True)
    result = _run_activate(tmp_path)
    assert result.returncode == 0
    assert "skills linked" not in result.stdout


def test_no_buds_dir_graceful(tmp_path):
    """soma-activate handles missing buds dir gracefully."""
    _make_env_fly(tmp_path)
    germline = tmp_path / "germline"
    (germline / ".git").mkdir(parents=True)
    result = _run_activate(tmp_path)
    assert result.returncode == 0
    assert "agents linked" not in result.stdout


def test_no_epigenome_marks_graceful(tmp_path):
    """soma-activate handles missing epigenome marks gracefully."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    # No epigenome at all
    result = _run_activate(tmp_path)
    assert result.returncode == 0


# ── Credentials section ───────────────────────────────────────────────


def test_credentials_section_skips_without_op(tmp_path):
    """soma-activate skips credentials when OP_SERVICE_ACCOUNT_TOKEN not set or op not installed."""
    _make_env_fly(tmp_path, content="export DUMMY=1\n")
    result = _run_activate(tmp_path)
    # Should show skip or warn — not crash
    assert result.returncode == 0


# ── Python deps section ──────────────────────────────────────────────


def test_python_deps_no_pyproject(tmp_path):
    """soma-activate skips uv sync when pyproject.toml missing."""
    _make_env_fly(tmp_path)
    germline = tmp_path / "germline"
    (germline / ".git").mkdir(parents=True)
    result = _run_activate(tmp_path)
    assert result.returncode == 0
    assert "germline deps synced" not in result.stdout


def test_python_deps_with_pyproject(tmp_path):
    """soma-activate attempts uv sync when pyproject.toml exists."""
    _make_env_fly(tmp_path)
    germline = tmp_path / "germline"
    (germline / ".git").mkdir(parents=True)
    (germline / "pyproject.toml").write_text("[project]\nname='test'\n")
    result = _run_activate(tmp_path)
    # uv sync will fail (not a real project), but script uses || true
    assert result.returncode == 0


# ── Log output format ────────────────────────────────────────────────


def test_log_sections_appear(tmp_path):
    """soma-activate prints all expected section headers."""
    _make_env_fly(tmp_path)
    result = _run_activate(tmp_path)
    for section in ["Repositories", "Symlinks", "Credentials", "SSH", "Tailscale", "Claude Code", "Python dependencies"]:
        assert section in result.stdout, f"Missing section: {section}"


# ── Full integration: happy path ─────────────────────────────────────


def test_full_activation_happy_path(tmp_path):
    """Full activation with germline + epigenome creates all expected state."""
    _make_env_fly(tmp_path)
    _make_germline(tmp_path)
    _make_epigenome(tmp_path)
    result = _run_activate(tmp_path)
    assert result.returncode == 0

    # Verify all expected symlinks were created
    assert (tmp_path / ".claude" / "hooks" / "hook1.py").is_symlink()
    assert (tmp_path / ".claude" / "skills" / "skill-a").is_symlink()
    assert (tmp_path / ".claude" / "agents" / "agent1.md").is_symlink()
    assert (tmp_path / ".claude" / "settings.json").is_symlink()
    assert (tmp_path / ".claude" / "projects" / "-home-terry" / "memory" / "MEMORY.md").is_symlink()

    # Verify all section messages appeared
    assert "hooks linked" in result.stdout
    assert "skills linked" in result.stdout
    assert "agents linked" in result.stdout
    assert "settings.json linked" in result.stdout
    assert "memory linked" in result.stdout
    assert "Soma activated" in result.stdout
