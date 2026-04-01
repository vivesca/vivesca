from __future__ import annotations

"""Tests for effectors/pharos-env.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

ORIGINAL_SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-env.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _prepare_script(tmp_path: Path) -> Path:
    """Copy the script and replace /home/terry with tmp_path for testing."""
    script_content = ORIGINAL_SCRIPT.read_text()
    script_content = script_content.replace('/home/terry', str(tmp_path))
    script_path = tmp_path / "pharos-env.sh"
    script_path.write_text(script_content)
    script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    return script_path


def _run(
    tmp_path: Path,
    command: list[str],
    have_local_env: bool = False,
) -> subprocess.CompletedProcess:
    """Run pharos-env.sh with given command in a testable environment."""
    env = os.environ.copy()
    script_path = _prepare_script(tmp_path)

    # Create the .zshenv.local if requested
    if have_local_env:
        zshenv = tmp_path / ".zshenv.local"
        zshenv.write_text(
            "export PHAROS_TEST_VAR=test-value\n"
            "export ANOTHER_VAR=another-value\n"
        )

    return subprocess.run(
        ["bash", str(script_path)] + command,
        capture_output=True, text=True, env=env, timeout=10,
    )


# ── Basic functionality tests ───────────────────────────────────────────


class TestPharosEnv:
    """Test the environment wrapper script."""

    def test_script_is_executable(self):
        """The script should have executable permissions."""
        assert ORIGINAL_SCRIPT.exists()
        stat_info = ORIGINAL_SCRIPT.stat()
        assert stat_info.st_mode & stat.S_IEXEC != 0, "Script should be executable"

    def test_sets_correct_home(self, tmp_path: Path):
        """HOME should be set correctly."""
        r = _run(tmp_path, ["printenv", "HOME"])
        assert r.returncode == 0
        assert r.stdout.strip() == str(tmp_path)

    def test_sets_extended_path(self, tmp_path: Path):
        """PATH should include all expected directories."""
        r = _run(tmp_path, ["printenv", "PATH"])
        assert r.returncode == 0
        path = r.stdout.strip()
        expected_dirs = [
            f"{tmp_path}/.local/bin",
            f"{tmp_path}/.cargo/bin",
            f"{tmp_path}/.bun/bin",
            f"{tmp_path}/go/bin",
            f"{tmp_path}/.nix-profile/bin",
            "/nix/var/nix/profiles/default/bin",
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
        ]
        for expected in expected_dirs:
            assert expected in path, f"Expected {expected} in PATH"

    def test_sources_local_secrets_when_present(self, tmp_path: Path):
        """When .zshenv.local exists, variables should be exported from it."""
        r = _run(tmp_path, ["printenv", "PHAROS_TEST_VAR"], have_local_env=True)
        assert r.returncode == 0
        assert r.stdout.strip() == "test-value"

    def test_works_without_local_secrets(self, tmp_path: Path):
        """When .zshenv.local doesn't exist, script still works fine."""
        # Check that we don't get an error
        r = _run(tmp_path, ["echo", "hello world"])
        assert r.returncode == 0
        assert r.stdout.strip() == "hello world"

    def test_executes_command_successfully(self, tmp_path: Path):
        """The script should exec the given command and pass through exit code."""
        # Exit 0
        r = _run(tmp_path, ["true"])
        assert r.returncode == 0

        # Exit non-zero should pass through
        r = _run(tmp_path, ["false"])
        assert r.returncode != 0

    def test_passes_arguments_correctly(self, tmp_path: Path):
        """Arguments should be passed through correctly to the command."""
        r = _run(tmp_path, ["echo", "one", "two three", "four"])
        assert r.returncode == 0
        assert r.stdout.strip() == "one two three four"

    # ── Help flag tests ────────────────────────────────────────────────────

    def test_help_long_flag(self, tmp_path: Path):
        """--help should print usage text and exit 0."""
        script_path = _prepare_script(tmp_path)
        r = subprocess.run(
            ["bash", str(script_path), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "Usage:" in r.stdout
        assert "pharos-env.sh" in r.stdout

    def test_help_short_flag(self, tmp_path: Path):
        """-h should print usage text and exit 0."""
        script_path = _prepare_script(tmp_path)
        r = subprocess.run(
            ["bash", str(script_path), "-h"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "Usage:" in r.stdout

    # ── Error handling tests ───────────────────────────────────────────────

    def test_no_arguments_exits_cleanly(self, tmp_path: Path):
        """Running with no arguments: exec with empty $@ is a no-op, exits 0."""
        script_path = _prepare_script(tmp_path)
        r = subprocess.run(
            ["bash", str(script_path)],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert r.stdout == ""
        assert r.stderr == ""

    # ── .zshenv.local multi-variable test ──────────────────────────────────

    def test_sources_multiple_vars_from_local_secrets(self, tmp_path: Path):
        """Both variables from .zshenv.local should be exported."""
        r = _run(tmp_path, ["printenv", "ANOTHER_VAR"], have_local_env=True)
        assert r.returncode == 0
        assert r.stdout.strip() == "another-value"

    # ── PATH ordering test ─────────────────────────────────────────────────

    def test_path_order_prefers_local_bin(self, tmp_path: Path):
        """$HOME/.local/bin should be the first entry in PATH."""
        r = _run(tmp_path, ["printenv", "PATH"])
        assert r.returncode == 0
        path = r.stdout.strip()
        first_entry = path.split(":")[0]
        assert first_entry == f"{tmp_path}/.local/bin"

    # ── Additional edge-case tests ────────────────────────────────────────

    def test_stderr_passthrough(self, tmp_path: Path):
        """stderr from the executed command should pass through unchanged."""
        r = _run(tmp_path, ["bash", "-c", "echo err >&2; echo out"])
        assert r.returncode == 0
        assert r.stdout.strip() == "out"
        assert r.stderr.strip() == "err"

    def test_set_a_exports_vars_to_child(self, tmp_path: Path):
        """Variables from .zshenv.local must be exported (visible to child processes)."""
        zshenv = tmp_path / ".zshenv.local"
        zshenv.write_text("export EXPORTED_VAR=visible\n")
        # Use a nested bash -c to confirm the var is in the environment
        r = _run(
            tmp_path,
            ["bash", "-c", "printenv EXPORTED_VAR"],
            have_local_env=False,
        )
        # Re-prepare with the custom zshenv already written above
        script_path = _prepare_script(tmp_path)
        env = os.environ.copy()
        r = subprocess.run(
            ["bash", str(script_path), "bash", "-c", "printenv EXPORTED_VAR"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == "visible"

    def test_empty_zshenv_local_no_error(self, tmp_path: Path):
        """An empty .zshenv.local should not cause any errors."""
        zshenv = tmp_path / ".zshenv.local"
        zshenv.write_text("")
        script_path = _prepare_script(tmp_path)
        env = os.environ.copy()
        r = subprocess.run(
            ["bash", str(script_path), "echo", "ok"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == "ok"
        assert r.stderr == ""

    def test_command_with_special_characters_in_args(self, tmp_path: Path):
        """Arguments with spaces and special characters should pass through."""
        r = _run(tmp_path, ["printf", "%s\\n", "hello world", "foo$bar"])
        assert r.returncode == 0
        assert r.stdout == "hello world\nfoo$bar\n"

    def test_path_contains_nix_dirs(self, tmp_path: Path):
        """PATH should include Nix profile directories."""
        r = _run(tmp_path, ["printenv", "PATH"])
        assert r.returncode == 0
        path = r.stdout.strip()
        assert f"{tmp_path}/.nix-profile/bin" in path
        assert "/nix/var/nix/profiles/default/bin" in path

    def test_path_order_cargo_before_system(self, tmp_path: Path):
        """Cargo bin should come before /usr/bin to allow custom tool versions."""
        r = _run(tmp_path, ["printenv", "PATH"])
        assert r.returncode == 0
        path = r.stdout.strip()
        assert path.index(f"{tmp_path}/.cargo/bin") < path.index("/usr/bin")

    def test_exit_code_propagation_nonzero(self, tmp_path: Path):
        """Non-zero exit codes (e.g., 42) should propagate through exec."""
        r = _run(tmp_path, ["bash", "-c", "exit 42"])
        assert r.returncode == 42

    def test_no_zshenv_local_does_not_source(self, tmp_path: Path):
        """Without .zshenv.local, PHAROS_TEST_VAR should not be set."""
        r = _run(tmp_path, ["printenv", "PHAROS_TEST_VAR"])
        # printenv exits 1 when variable not found
        assert r.returncode != 0
        assert r.stdout.strip() == ""
