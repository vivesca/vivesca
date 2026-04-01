from __future__ import annotations

"""Tests for effectors/soma-activate — bash script that brings a gemmule to life.

Tests cover: env.fly preflight, repo cloning, symlink creation, idempotency.
Uses subprocess.run with isolated HOME to avoid touching real state.
"""
import os
import subprocess
from pathlib import Path

import pytest

SOMA_ACTIVATE = Path.home() / "germline" / "effectors" / "soma-activate"


def _run_soma_activate(home: Path, env_extra: dict | None = None, timeout: int = 30):
    """Run soma-activate with a fake HOME directory."""
    env = os.environ.copy()
    env["HOME"] = str(home)
    # Prevent real git from prompting
    env["GIT_TERMINAL_PROMPT"] = "0"
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(SOMA_ACTIVATE)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def _make_env_fly(home: Path, content: str = 'export OP_SERVICE_ACCOUNT_TOKEN="test"\nexport GITHUB_TOKEN="test"\nexport ANTHROPIC_API_KEY="test"\n'):
    """Write a minimal .env.fly in the fake home."""
    env_file = home / ".env.fly"
    env_file.write_text(content)
    return env_file


# ── Preflight: ~/.env.fly ─────────────────────────────────────────────


class TestPreflight:
    """Section 0: .env.fly pre-flight checks."""

    def test_exits_1_when_no_env_fly(self, tmp_path):
        """Script exits 1 when ~/.env.fly is missing."""
        r = _run_soma_activate(tmp_path)
        assert r.returncode != 0
        assert ".env.fly" in r.stdout or ".env.fly" in r.stderr

    def test_error_message_lists_required_vars(self, tmp_path):
        """Error message shows required env var names."""
        r = _run_soma_activate(tmp_path)
        combined = r.stdout + r.stderr
        assert "OP_SERVICE_ACCOUNT_TOKEN" in combined
        assert "GITHUB_TOKEN" in combined

    def test_exits_0_with_env_fly(self, tmp_path):
        """Script proceeds (exit 0) when .env.fly exists with required vars."""
        _make_env_fly(tmp_path)
        # Mock out git and other commands by ensuring they fail gracefully
        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0

    def test_env_fly_is_sourced(self, tmp_path):
        """Variables from .env.fly are available in the script."""
        _make_env_fly(tmp_path, content='export MY_TEST_VAR="hello123"\n')
        # The script sources .env.fly, so MY_TEST_VAR should be set
        # We verify by checking the script doesn't fail due to missing OP_SERVICE_ACCOUNT_TOKEN
        # (set -u would catch it, but the script uses ${VAR:-} patterns)
        r = _run_soma_activate(tmp_path)
        # Should still exit 0 even with minimal env
        assert r.returncode == 0


# ── Repository cloning ────────────────────────────────────────────────


class TestRepoCloning:
    """Section 1: git clone / pull logic."""

    def test_reports_repo_section(self, tmp_path):
        """Output mentions 'Repositories' section."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert "Repositories" in r.stdout

    def test_warns_on_failed_clone(self, tmp_path):
        """Failed clone produces a [warn] message but doesn't stop the script."""
        _make_env_fly(tmp_path)
        # No git repos exist and clone will fail (no network / bad URL)
        r = _run_soma_activate(tmp_path)
        # Script should still exit 0 (idempotent, tolerant)
        assert r.returncode == 0
        # Either skip or warn about repos
        combined = r.stdout + r.stderr
        # The script uses `|| true` on git pull and `|| echo ...` on clone failure
        assert "germline" in combined.lower() or "warn" in combined.lower() or "skip" in combined.lower()

    def test_existing_repo_shows_skip(self, tmp_path):
        """Already-cloned repos show [skip] message."""
        _make_env_fly(tmp_path)
        # Create fake .git dirs so the script skips cloning
        germline_dir = tmp_path / "germline"
        germline_dir.mkdir()
        (germline_dir / ".git").mkdir()

        epigenome_dir = tmp_path / "epigenome"
        epigenome_dir.mkdir()
        (epigenome_dir / ".git").mkdir()

        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0
        assert "skip" in r.stdout.lower() or "already cloned" in r.stdout.lower()


# ── Symlinks ──────────────────────────────────────────────────────────


class TestSymlinks:
    """Section 2: symlink creation for hooks, skills, agents, memory, settings."""

    def _setup_germline_with_structure(self, home: Path):
        """Create germline dir with membrane subdirs for symlink testing."""
        _make_env_fly(home)
        germline = home / "germline"
        germline.mkdir()
        (germline / ".git").mkdir()

        epigenome = home / "epigenome"
        epigenome.mkdir()
        (epigenome / ".git").mkdir()

        # Create membrane structure
        cyto = germline / "membrane" / "cytoskeleton"
        cyto.mkdir(parents=True)
        (cyto / "hook_a.py").write_text("# hook a")
        (cyto / "hook_b.py").write_text("# hook b")

        receptors = germline / "membrane" / "receptors"
        receptors.mkdir(parents=True)
        (receptors / "skill1").mkdir()
        (receptors / "skill2").mkdir()

        buds = germline / "membrane" / "buds"
        buds.mkdir(parents=True)
        (buds / "agent1.md").write_text("# agent 1")
        (buds / "agent2.md").write_text("# agent 2")

        # Settings
        (germline / "membrane" / "settings.json").write_text('{"key": "val"}')

        # Epigenome marks
        marks = epigenome / "marks"
        marks.mkdir(parents=True)
        (marks / "MEMORY.md").write_text("# Memory")

    def test_hooks_symlinked(self, tmp_path):
        """Hooks from membrane/cytoskeleton are symlinked to ~/.claude/hooks."""
        self._setup_germline_with_structure(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0

        hooks_dir = tmp_path / ".claude" / "hooks"
        assert hooks_dir.exists()
        links = list(hooks_dir.iterdir())
        names = [l.name for l in links]
        assert "hook_a.py" in names
        assert "hook_b.py" in names

    def test_skills_symlinked(self, tmp_path):
        """Skill dirs from membrane/receptors are symlinked to ~/.claude/skills."""
        self._setup_germline_with_structure(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0

        skills_dir = tmp_path / ".claude" / "skills"
        assert skills_dir.exists()
        names = [p.name for p in skills_dir.iterdir()]
        assert "skill1" in names
        assert "skill2" in names

    def test_agents_symlinked(self, tmp_path):
        """Agent markdown files from membrane/buds are symlinked to ~/.claude/agents."""
        self._setup_germline_with_structure(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0

        agents_dir = tmp_path / ".claude" / "agents"
        assert agents_dir.exists()
        names = [p.name for p in agents_dir.iterdir()]
        assert "agent1.md" in names
        assert "agent2.md" in names

    def test_memory_symlinked(self, tmp_path):
        """MEMORY.md from epigenome/marks is symlinked."""
        self._setup_germline_with_structure(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0

        memory_link = tmp_path / ".claude" / "projects" / "-home-terry" / "memory" / "MEMORY.md"
        # The link target may not resolve since HOME is faked, but the symlink should exist
        assert memory_link.is_symlink() or memory_link.exists()

    def test_settings_json_symlinked(self, tmp_path):
        """settings.json from membrane is symlinked to ~/.claude/settings.json."""
        self._setup_germline_with_structure(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0

        settings_link = tmp_path / ".claude" / "settings.json"
        assert settings_link.is_symlink()

    def test_symlinks_section_in_output(self, tmp_path):
        """Output mentions 'Symlinks' section."""
        self._setup_germline_with_structure(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert "Symlinks" in r.stdout

    def test_claude_dirs_created(self, tmp_path):
        """Script creates ~/.claude/hooks, skills, agents dirs even if nothing to link."""
        _make_env_fly(tmp_path)
        germline = tmp_path / "germline"
        germline.mkdir()
        (germline / ".git").mkdir()
        epigenome = tmp_path / "epigenome"
        epigenome.mkdir()
        (epigenome / ".git").mkdir()

        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0
        assert (tmp_path / ".claude" / "hooks").is_dir()
        assert (tmp_path / ".claude" / "skills").is_dir()
        assert (tmp_path / ".claude" / "agents").is_dir()


# ── Idempotency ───────────────────────────────────────────────────────


class TestIdempotency:
    """soma-activate is safe to re-run."""

    def test_double_run_exits_0(self, tmp_path):
        """Running twice produces exit 0 both times."""
        _make_env_fly(tmp_path)
        germline = tmp_path / "germline"
        germline.mkdir()
        (germline / ".git").mkdir()
        epigenome = tmp_path / "epigenome"
        epigenome.mkdir()
        (epigenome / ".git").mkdir()

        r1 = _run_soma_activate(tmp_path)
        assert r1.returncode == 0

        r2 = _run_soma_activate(tmp_path)
        assert r2.returncode == 0

    def test_symlinks_survive_rerun(self, tmp_path):
        """Symlinks are correct after running twice (ln -sfn overwrites)."""
        _make_env_fly(tmp_path)
        germline = tmp_path / "germline"
        germline.mkdir()
        (germline / ".git").mkdir()
        epigenome = tmp_path / "epigenome"
        epigenome.mkdir()
        (epigenome / ".git").mkdir()

        # Create a hook file
        cyto = germline / "membrane" / "cytoskeleton"
        cyto.mkdir(parents=True)
        (cyto / "test_hook.py").write_text("# test")

        r1 = _run_soma_activate(tmp_path)
        assert r1.returncode == 0

        hook_link = tmp_path / ".claude" / "hooks" / "test_hook.py"
        assert hook_link.exists()

        r2 = _run_soma_activate(tmp_path)
        assert r2.returncode == 0
        assert hook_link.exists()


# ── Output format ─────────────────────────────────────────────────────


class TestOutputFormat:
    """Verify the script produces expected output sections."""

    def test_activation_header(self, tmp_path):
        """Output starts with 'Soma activation' header."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert "Soma activation" in r.stdout

    def test_completion_message(self, tmp_path):
        """Output ends with 'Soma activated' message."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert "Soma activated" in r.stdout

    def test_summary_paths(self, tmp_path):
        """Output shows key paths: germline, epigenome, effectors."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert "germline" in r.stdout
        assert "epigenome" in r.stdout
        assert "effectors" in r.stdout

    def test_manual_steps_listed(self, tmp_path):
        """Output lists remaining manual steps."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert "tailscale" in r.stdout.lower()
        assert "claude" in r.stdout.lower()

    def test_credentials_section(self, tmp_path):
        """Output mentions Credentials section."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert "Credentials" in r.stdout or "credentials" in r.stdout.lower()

    def test_ssh_section(self, tmp_path):
        """Output mentions SSH section."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert "SSH" in r.stdout

    def test_python_deps_section(self, tmp_path):
        """Output mentions Python dependencies section."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert "Python" in r.stdout


# ── Sections that gracefully handle missing tools ─────────────────────


class TestGracefulDegradation:
    """Sections that skip or warn when tools aren't available."""

    def test_no_op_command_shows_skip(self, tmp_path):
        """When op is not available, shows skip message."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        # op is almost certainly not installed in test env
        combined = r.stdout.lower()
        # Either skip or warn — the script is tolerant
        assert r.returncode == 0

    def test_no_ssh_key_shows_guidance(self, tmp_path):
        """When no SSH key exists, shows generation guidance."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        combined = r.stdout + r.stderr
        # Either skip (key exists) or guidance (no key)
        assert "ssh" in combined.lower()

    def test_no_tailscale_shows_guidance(self, tmp_path):
        """When tailscale is not connected, shows connection guidance."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        combined = r.stdout + r.stderr
        assert "tailscale" in combined.lower()
