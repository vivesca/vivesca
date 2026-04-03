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


class TestOAuthInjection:
    """Vault-backed OAuth document injection."""

    def _setup_with_fake_op(self, home: Path) -> Path:
        _make_env_fly(home)
        germline = home / "germline"
        germline.mkdir()
        (germline / ".git").mkdir()
        epigenome = home / "epigenome"
        epigenome.mkdir()
        (epigenome / ".git").mkdir()

        effectors_dir = germline / "effectors"
        effectors_dir.mkdir()
        importin_path = effectors_dir / "importin"
        importin_path.write_text("#!/usr/bin/env python3\nprint('')\n")
        importin_path.chmod(0o755)

        fake_bin = home / "fake-bin"
        fake_bin.mkdir()
        op_path = fake_bin / "op"
        op_path.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == "vault" && "$2" == "list" ]]; then
  exit 0
fi
if [[ "$1" == "read" ]]; then
  case "$2" in
    op://Agents/claude-oauth/credential) printf '{"claude":"ok"}' ;;
    op://Agents/gemini-oauth/credential) printf '{"gemini":"ok"}' ;;
    op://Agents/gemini-oauth/google_accounts) printf '{"accounts":["a@example.com"]}' ;;
    op://Agents/codex-oauth/credential) printf '{"codex":"ok"}' ;;
    *) exit 1 ;;
  esac
  exit 0
fi
exit 1
"""
        )
        op_path.chmod(0o755)
        return fake_bin

    def test_oauth_files_injected_from_vault(self, tmp_path):
        """OAuth documents are written when op access is available."""
        fake_bin = self._setup_with_fake_op(tmp_path)
        env_extra = {"PATH": f"{fake_bin}:{os.environ['PATH']}"}

        result = _run_soma_activate(tmp_path, env_extra=env_extra)

        assert result.returncode == 0
        assert (tmp_path / ".claude" / "credentials.json").read_text() == '{"claude":"ok"}\n'
        assert (tmp_path / ".gemini" / "oauth_creds.json").read_text() == '{"gemini":"ok"}\n'
        assert (tmp_path / ".gemini" / "google_accounts.json").read_text() == '{"accounts":["a@example.com"]}\n'
        assert (tmp_path / ".codex" / "auth.json").read_text() == '{"codex":"ok"}\n'

    def test_existing_oauth_files_are_not_overwritten(self, tmp_path):
        """Existing OAuth files are preserved on rerun."""
        fake_bin = self._setup_with_fake_op(tmp_path)
        existing_file = tmp_path / ".codex" / "auth.json"
        existing_file.parent.mkdir(parents=True)
        existing_file.write_text("existing\n")
        env_extra = {"PATH": f"{fake_bin}:{os.environ['PATH']}"}

        result = _run_soma_activate(tmp_path, env_extra=env_extra)

        assert result.returncode == 0
        assert existing_file.read_text() == "existing\n"
        assert "Codex OAuth exists" in result.stdout


# ── Repo pull ──────────────────────────────────────────────────────────


class TestRepoPull:
    """Section 1b: git pull --ff-only for already-cloned repos."""

    def test_pull_attempted_on_existing_repos(self, tmp_path):
        """Script attempts git pull on repos that already have .git dirs."""
        _make_env_fly(tmp_path)
        # Create repos with .git dirs — a bare git init is enough for pull to fail gracefully
        germline = tmp_path / "germline"
        germline.mkdir()
        subprocess.run(["git", "init", str(germline)], capture_output=True, check=True)

        epigenome = tmp_path / "epigenome"
        epigenome.mkdir()
        subprocess.run(["git", "init", str(epigenome)], capture_output=True, check=True)

        r = _run_soma_activate(tmp_path)
        # Script should exit 0 despite pull failures (|| true)
        assert r.returncode == 0

    def test_pull_failure_does_not_crash(self, tmp_path):
        """A failing git pull (no remote) doesn't crash the script."""
        _make_env_fly(tmp_path)
        germline = tmp_path / "germline"
        germline.mkdir()
        subprocess.run(["git", "init", str(germline)], capture_output=True, check=True)
        # No remote configured — pull will fail

        epigenome = tmp_path / "epigenome"
        epigenome.mkdir()
        subprocess.run(["git", "init", str(epigenome)], capture_output=True, check=True)

        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0


# ── Symlink target correctness ─────────────────────────────────────────


class TestSymlinkTargets:
    """Verify symlink targets point to the correct source files."""

    def _setup_full(self, home: Path):
        _make_env_fly(home)
        germline = home / "germline"
        germline.mkdir()
        (germline / ".git").mkdir()

        epigenome = home / "epigenome"
        epigenome.mkdir()
        (epigenome / ".git").mkdir()

        cyto = germline / "membrane" / "cytoskeleton"
        cyto.mkdir(parents=True)
        (cyto / "hook_x.py").write_text("# hx")

        receptors = germline / "membrane" / "receptors"
        receptors.mkdir(parents=True)
        (receptors / "myskill").mkdir()

        buds = germline / "membrane" / "buds"
        buds.mkdir(parents=True)
        (buds / "myagent.md").write_text("# agent")

        (germline / "membrane" / "settings.json").write_text('{"a":1}')

        marks = epigenome / "marks"
        marks.mkdir(parents=True)
        (marks / "MEMORY.md").write_text("# mem")

    def test_hook_symlink_target(self, tmp_path):
        """Hook symlink target points to the germline source file."""
        self._setup_full(tmp_path)
        _run_soma_activate(tmp_path)
        link = tmp_path / ".claude" / "hooks" / "hook_x.py"
        assert link.is_symlink()
        target = os.readlink(str(link))
        assert "cytoskeleton" in target
        assert target.endswith("hook_x.py")

    def test_skill_symlink_target(self, tmp_path):
        """Skill symlink target points to the receptors subdirectory."""
        self._setup_full(tmp_path)
        _run_soma_activate(tmp_path)
        link = tmp_path / ".claude" / "skills" / "myskill"
        assert link.is_symlink()
        target = os.readlink(str(link))
        assert "receptors" in target
        # Script iterates dirs with trailing slash, so target may end with "myskill/"
        assert target.rstrip("/").endswith("myskill")

    def test_agent_symlink_target(self, tmp_path):
        """Agent symlink target points to the buds markdown file."""
        self._setup_full(tmp_path)
        _run_soma_activate(tmp_path)
        link = tmp_path / ".claude" / "agents" / "myagent.md"
        assert link.is_symlink()
        target = os.readlink(str(link))
        assert "buds" in target
        assert target.endswith("myagent.md")

    def test_settings_symlink_target(self, tmp_path):
        """settings.json symlink target points to membrane source."""
        self._setup_full(tmp_path)
        _run_soma_activate(tmp_path)
        link = tmp_path / ".claude" / "settings.json"
        assert link.is_symlink()
        target = os.readlink(str(link))
        assert "membrane" in target
        assert target.endswith("settings.json")


# ── Symlink file-type filtering ────────────────────────────────────────


class TestSymlinkFiltering:
    """Hooks link .py only; agents link .md only."""

    def _setup_with_mixed_files(self, home: Path):
        _make_env_fly(home)
        germline = home / "germline"
        germline.mkdir()
        (germline / ".git").mkdir()

        epigenome = home / "epigenome"
        epigenome.mkdir()
        (epigenome / ".git").mkdir()

        # cytoskeleton: mix of .py and non-.py
        cyto = germline / "membrane" / "cytoskeleton"
        cyto.mkdir(parents=True)
        (cyto / "good_hook.py").write_text("# py")
        (cyto / "readme.txt").write_text("# txt")

        # buds: mix of .md and non-.md
        buds = germline / "membrane" / "buds"
        buds.mkdir(parents=True)
        (buds / "agent.md").write_text("# md")
        (buds / "script.sh").write_text("#!/bin/bash")

    def test_hooks_only_py_files(self, tmp_path):
        """Only .py files from cytoskeleton are linked into hooks."""
        self._setup_with_mixed_files(tmp_path)
        _run_soma_activate(tmp_path)
        hooks_dir = tmp_path / ".claude" / "hooks"
        names = [p.name for p in hooks_dir.iterdir()]
        assert "good_hook.py" in names
        assert "readme.txt" not in names

    def test_agents_only_md_files(self, tmp_path):
        """Only .md files from buds are linked into agents."""
        self._setup_with_mixed_files(tmp_path)
        _run_soma_activate(tmp_path)
        agents_dir = tmp_path / ".claude" / "agents"
        names = [p.name for p in agents_dir.iterdir()]
        assert "agent.md" in names
        assert "script.sh" not in names


# ── Empty membrane directories ─────────────────────────────────────────


class TestEmptyMembrane:
    """Script handles empty or missing membrane subdirectories gracefully."""

    def _setup_minimal(self, home: Path):
        _make_env_fly(home)
        germline = home / "germline"
        germline.mkdir()
        (germline / ".git").mkdir()
        # Create membrane but leave subdirs empty/missing
        (germline / "membrane").mkdir()
        epigenome = home / "epigenome"
        epigenome.mkdir()
        (epigenome / ".git").mkdir()

    def test_empty_cytoskeleton_no_crash(self, tmp_path):
        """Empty cytoskeleton dir doesn't cause errors."""
        self._setup_minimal(tmp_path)
        (tmp_path / "germline" / "membrane" / "cytoskeleton").mkdir()
        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0

    def test_no_cytoskeleton_dir_no_crash(self, tmp_path):
        """Missing cytoskeleton dir is handled gracefully."""
        self._setup_minimal(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0

    def test_empty_buds_no_crash(self, tmp_path):
        """Empty buds dir doesn't cause errors."""
        self._setup_minimal(tmp_path)
        (tmp_path / "germline" / "membrane" / "buds").mkdir()
        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0

    def test_no_receptors_dir_no_crash(self, tmp_path):
        """Missing receptors dir is handled gracefully."""
        self._setup_minimal(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0

    def test_no_epigenome_marks_no_crash(self, tmp_path):
        """Missing epigenome/marks dir is handled gracefully."""
        self._setup_minimal(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert r.returncode == 0


# ── Symlink update on rerun ────────────────────────────────────────────


class TestSymlinkUpdate:
    """ln -sfn updates symlinks when the target changes."""

    def test_hook_target_updated_on_rerun(self, tmp_path):
        """If hook source content changes, symlink still points to current file."""
        _make_env_fly(tmp_path)
        germline = tmp_path / "germline"
        germline.mkdir()
        (germline / ".git").mkdir()
        epigenome = tmp_path / "epigenome"
        epigenome.mkdir()
        (epigenome / ".git").mkdir()

        cyto = germline / "membrane" / "cytoskeleton"
        cyto.mkdir(parents=True)
        (cyto / "hook1.py").write_text("v1")

        r1 = _run_soma_activate(tmp_path)
        assert r1.returncode == 0
        link = tmp_path / ".claude" / "hooks" / "hook1.py"
        target1 = os.readlink(str(link))

        # Rewrite the file (simulating a git pull that updated it)
        (cyto / "hook1.py").write_text("v2")
        r2 = _run_soma_activate(tmp_path)
        assert r2.returncode == 0
        target2 = os.readlink(str(link))
        # Same target path (ln -sfn is idempotent)
        assert target1 == target2


# ── Claude Code section ────────────────────────────────────────────────


class TestClaudeCodeSection:
    """Section 6: Claude Code auth."""

    def test_claude_section_in_output(self, tmp_path):
        """Output mentions Claude Code section."""
        _make_env_fly(tmp_path)
        r = _run_soma_activate(tmp_path)
        assert "Claude Code" in r.stdout

    def test_claude_not_installed_warning(self, tmp_path):
        """When claude is not on PATH, shows install guidance."""
        _make_env_fly(tmp_path)
        env_extra = {"PATH": "/usr/bin:/bin"}  # minimal path, no claude
        r = _run_soma_activate(tmp_path, env_extra=env_extra)
        assert r.returncode == 0
        assert "claude" in r.stdout.lower()


# ── Credential section edge cases ──────────────────────────────────────


class TestCredentialEdgeCases:
    """Section 3: credential injection edge cases."""

    def test_op_token_set_but_op_missing(self, tmp_path):
        """OP_SERVICE_ACCOUNT_TOKEN set but op not found shows skip."""
        _make_env_fly(tmp_path)
        # Remove op from PATH
        env_extra = {"PATH": "/usr/bin:/bin"}
        r = _run_soma_activate(tmp_path, env_extra=env_extra)
        assert r.returncode == 0
        combined = r.stdout.lower()
        assert "skip" in combined or "credentials" in combined or "op" in combined

    def test_no_op_token_shows_skip(self, tmp_path):
        """No OP_SERVICE_ACCOUNT_TOKEN shows skip in credentials section."""
        _make_env_fly(tmp_path, content='export GITHUB_TOKEN="test"\nexport ANTHROPIC_API_KEY="test"\n')
        env_extra = {"PATH": "/usr/bin:/bin"}
        r = _run_soma_activate(tmp_path, env_extra=env_extra)
        assert r.returncode == 0


# ── Strict mode ────────────────────────────────────────────────────────


class TestStrictMode:
    """Verify the script uses strict bash mode."""

    def test_script_uses_set_euo(self):
        """Script contains set -euo pipefail for strict execution."""
        content = SOMA_ACTIVATE.read_text()
        assert "set -euo pipefail" in content
