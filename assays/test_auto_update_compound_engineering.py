"""Tests for effectors/auto-update-compound-engineering.sh — compound plugin updater."""
from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest


EFFECTOR = Path.home() / "germline" / "effectors" / "auto-update-compound-engineering.sh"


@pytest.fixture
def fake_home(tmp_path):
    """Provide a fake HOME directory with mock bunx/npx on PATH."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    # Create a mock bunx that simulates success
    bunx_script = bin_dir / "bunx"
    bunx_script.write_text(
        '#!/usr/bin/env bash\nexit 0\n'
    )
    bunx_script.chmod(bunx_script.stat().st_mode | stat.S_IEXEC)

    # Create a mock npx as fallback
    npx_script = bin_dir / "npx"
    npx_script.write_text(
        '#!/usr/bin/env bash\nexit 0\n'
    )
    npx_script.chmod(npx_script.stat().st_mode | stat.S_IEXEC)

    # Build a restricted PATH: only our fake bin + /usr/bin for bash/date
    env = {
        "HOME": str(tmp_path),
        "PATH": f"{bin_dir}:/usr/bin:/bin",
    }
    return tmp_path, env


@pytest.fixture
def fake_home_no_runners(tmp_path):
    """Provide a fake HOME directory with NO bunx or npx available.

    Excludes /usr/bin from PATH because npx lives there on this host.
    Only includes /bin so core utils like date still work.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    env = {
        "HOME": str(tmp_path),
        "PATH": f"{bin_dir}:/bin",
    }
    return tmp_path, env


def _run_script(args=None, env=None):
    """Run the effector script and return CompletedProcess."""
    cmd = ["bash", str(EFFECTOR)]
    if args:
        cmd.extend(args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


# ── --help tests ────────────────────────────────────────────────────────


class TestHelpFlag:
    """Tests for --help / -h flag behaviour."""

    def test_help_exits_zero(self):
        """Script exits 0 with --help."""
        result = _run_script(["--help"])
        assert result.returncode == 0

    def test_h_short_flag_exits_zero(self):
        """Script exits 0 with -h."""
        result = _run_script(["-h"])
        assert result.returncode == 0

    def test_help_mentions_usage(self):
        """--help output includes usage text."""
        result = _run_script(["--help"])
        assert "Usage:" in result.stdout

    def test_help_mentions_crontab(self):
        """--help output includes crontab scheduling hint."""
        result = _run_script(["--help"])
        assert "crontab" in result.stdout

    def test_help_mentions_opencode_and_codex(self):
        """--help output mentions OpenCode and Codex."""
        result = _run_script(["--help"])
        assert "OpenCode" in result.stdout or "opencode" in result.stdout
        assert "Codex" in result.stdout or "codex" in result.stdout


# ── runner selection tests ──────────────────────────────────────────────


class TestRunnerSelection:
    """Tests for bunx/npx runner selection logic."""

    def test_prefers_bunx_over_npx(self, fake_home):
        """Script uses bunx when both bunx and npx are available."""
        tmp_path, env = fake_home
        result = _run_script(env=env)
        assert result.returncode == 0

        log_file = tmp_path / ".compound-engineering-updates.log"
        assert log_file.exists()
        content = log_file.read_text()
        # bunx was available so it should have been used
        assert "Update started:" in content

    def test_falls_back_to_npx(self, tmp_path):
        """Script falls back to npx when bunx is unavailable."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        # Only provide npx
        npx_script = bin_dir / "npx"
        npx_script.write_text('#!/usr/bin/env bash\nexit 0\n')
        npx_script.chmod(npx_script.stat().st_mode | stat.S_IEXEC)

        env = {"HOME": str(tmp_path), "PATH": f"{bin_dir}:/usr/bin:/bin"}
        result = _run_script(env=env)
        assert result.returncode == 0

        log_file = tmp_path / ".compound-engineering-updates.log"
        assert log_file.exists()

    def test_exits_1_when_no_runner(self, fake_home_no_runners):
        """Script exits 1 when neither bunx nor npx is found."""
        tmp_path, env = fake_home_no_runners
        result = _run_script(env=env)
        assert result.returncode == 1

        log_file = tmp_path / ".compound-engineering-updates.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert "neither bunx nor npx found" in content


# ── log file format tests ──────────────────────────────────────────────


class TestLogFileFormat:
    """Tests for log file structure and content."""

    def test_log_contains_separator(self, fake_home):
        """Log file contains separator line."""
        tmp_path, env = fake_home
        _run_script(env=env)

        content = (tmp_path / ".compound-engineering-updates.log").read_text()
        assert "========================================" in content

    def test_log_contains_start_and_end_timestamps(self, fake_home):
        """Log file contains start and completed timestamps."""
        tmp_path, env = fake_home
        _run_script(env=env)

        content = (tmp_path / ".compound-engineering-updates.log").read_text()
        assert "Update started:" in content
        assert "Update completed:" in content

    def test_log_mentions_opencode_update(self, fake_home):
        """Log file mentions OpenCode update attempt."""
        tmp_path, env = fake_home
        _run_script(env=env)

        content = (tmp_path / ".compound-engineering-updates.log").read_text()
        assert "Updating OpenCode" in content

    def test_log_mentions_codex_update(self, fake_home):
        """Log file mentions Codex update attempt."""
        tmp_path, env = fake_home
        _run_script(env=env)

        content = (tmp_path / ".compound-engineering-updates.log").read_text()
        assert "Updating Codex" in content

    def test_opencode_success_with_mock_runner(self, fake_home):
        """Log shows OpenCode success when mock runner exits 0."""
        tmp_path, env = fake_home
        _run_script(env=env)

        content = (tmp_path / ".compound-engineering-updates.log").read_text()
        assert "OpenCode updated successfully" in content

    def test_codex_success_with_mock_runner(self, fake_home):
        """Log shows Codex success when mock runner exits 0."""
        tmp_path, env = fake_home
        _run_script(env=env)

        content = (tmp_path / ".compound-engineering-updates.log").read_text()
        assert "Codex updated successfully" in content

    def test_log_ends_with_blank_line(self, fake_home):
        """Log file ends with a blank line for separation between runs."""
        tmp_path, env = fake_home
        _run_script(env=env)

        content = (tmp_path / ".compound-engineering-updates.log").read_text()
        assert content.endswith("\n\n")


# ── update failure tests ────────────────────────────────────────────────


class TestUpdateFailure:
    """Tests for when the runner command fails."""

    def test_opencode_failure_logged(self, tmp_path):
        """Log shows OpenCode failure when runner exits non-zero for opencode."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        # Runner that fails when --to opencode is passed
        runner = bin_dir / "bunx"
        runner.write_text(
            '#!/usr/bin/env bash\n'
            'if [[ "$*" == *"--to opencode"* ]]; then\n'
            '    exit 1\n'
            'fi\n'
            'exit 0\n'
        )
        runner.chmod(runner.stat().st_mode | stat.S_IEXEC)

        env = {"HOME": str(tmp_path), "PATH": f"{bin_dir}:/usr/bin:/bin"}
        result = _run_script(env=env)
        # Script itself should still exit 0 — it logs failures but doesn't abort
        assert result.returncode == 0

        content = (tmp_path / ".compound-engineering-updates.log").read_text()
        assert "OpenCode update failed" in content

    def test_codex_failure_logged(self, tmp_path):
        """Log shows Codex failure when runner exits non-zero for codex."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        # Runner that fails when --to codex is passed
        runner = bin_dir / "bunx"
        runner.write_text(
            '#!/usr/bin/env bash\n'
            'if [[ "$*" == *"--to codex"* ]]; then\n'
            '    exit 1\n'
            'fi\n'
            'exit 0\n'
        )
        runner.chmod(runner.stat().st_mode | stat.S_IEXEC)

        env = {"HOME": str(tmp_path), "PATH": f"{bin_dir}:/usr/bin:/bin"}
        result = _run_script(env=env)
        assert result.returncode == 0

        content = (tmp_path / ".compound-engineering-updates.log").read_text()
        assert "Codex update failed" in content

    def test_both_failures_logged(self, tmp_path):
        """Log shows both failures when runner always exits non-zero."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        runner = bin_dir / "bunx"
        runner.write_text('#!/usr/bin/env bash\nexit 1\n')
        runner.chmod(runner.stat().st_mode | stat.S_IEXEC)

        env = {"HOME": str(tmp_path), "PATH": f"{bin_dir}:/usr/bin:/bin"}
        result = _run_script(env=env)
        assert result.returncode == 0

        content = (tmp_path / ".compound-engineering-updates.log").read_text()
        assert "OpenCode update failed" in content
        assert "Codex update failed" in content


# ── append behaviour tests ──────────────────────────────────────────────


class TestAppendBehaviour:
    """Tests that the script appends to (not overwrites) existing log."""

    def test_appends_to_existing_log(self, fake_home):
        """Script appends to existing log file, preserving previous entries."""
        tmp_path, env = fake_home
        log_file = tmp_path / ".compound-engineering-updates.log"

        # Pre-populate log with a previous run marker
        log_file.write_text("=== PREVIOUS RUN ===\n")

        _run_script(env=env)

        content = log_file.read_text()
        assert "=== PREVIOUS RUN ===" in content
        assert "Update started:" in content


# ── runner invocation tests ─────────────────────────────────────────────


class TestRunnerInvocation:
    """Tests that the runner is invoked with correct arguments."""

    def test_runner_receives_opencode_args(self, tmp_path):
        """Runner is called with @every-env/compound-plugin install compound-engineering --to opencode."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        # Runner that records its arguments
        arg_file = tmp_path / "args.log"
        runner = bin_dir / "bunx"
        runner.write_text(
            '#!/usr/bin/env bash\n'
            f'echo "$@" >> {arg_file}\n'
            'exit 0\n'
        )
        runner.chmod(runner.stat().st_mode | stat.S_IEXEC)

        env = {"HOME": str(tmp_path), "PATH": f"{bin_dir}:/usr/bin:/bin"}
        _run_script(env=env)

        calls = arg_file.read_text().strip().splitlines()
        assert any("--to opencode" in call for call in calls)
        assert any("--to codex" in call for call in calls)

    def test_runner_receives_correct_package(self, tmp_path):
        """Runner is called with the correct package specifier."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        arg_file = tmp_path / "args.log"
        runner = bin_dir / "bunx"
        runner.write_text(
            '#!/usr/bin/env bash\n'
            f'echo "$@" >> {arg_file}\n'
            'exit 0\n'
        )
        runner.chmod(runner.stat().st_mode | stat.S_IEXEC)

        env = {"HOME": str(tmp_path), "PATH": f"{bin_dir}:/usr/bin:/bin"}
        _run_script(env=env)

        calls = arg_file.read_text().strip().splitlines()
        for call in calls:
            assert "@every-env/compound-plugin" in call
            assert "install" in call
            assert "compound-engineering" in call
