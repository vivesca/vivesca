"""Tests for effectors/pharos-env.sh — bash script tested via subprocess."""
from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-env.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run(
    tmp_path: Path,
    command: list[str],
    have_local_env: bool = False,
) -> subprocess.CompletedProcess:
    """Run pharos-env.sh with given command in a testable environment."""
    env = os.environ.copy()

    # Create the .zshenv.local in the real HOME location (pharos is /home/terry)
    if have_local_env:
        # We create it even though it doesn't exist by default in tests
        zshenv = Path("/home/terry") / ".zshenv.local"
        if not zshenv.exists():
            zshenv.write_text(
                "export PHAROS_TEST_VAR=test-value\n"
                "export ANOTHER_VAR=another-value\n"
            )

    result = subprocess.run(
        ["bash", str(SCRIPT)] + command,
        capture_output=True, text=True, env=env, timeout=10,
    )

    # Clean up if we created it
    if have_local_env:
        zshenv = Path("/home/terry") / ".zshenv.local"
        if zshenv.exists() and zshenv.read_text().strip() == "export PHAROS_TEST_VAR=test-value\nexport ANOTHER_VAR=another-value":
            zshenv.unlink()

    return result


# ── Basic functionality tests ───────────────────────────────────────────


class TestPharosEnv:
    """Test the environment wrapper script."""

    def test_script_is_executable(self):
        """The script should have executable permissions."""
        assert SCRIPT.exists()
        stat_info = SCRIPT.stat()
        assert stat_info.st_mode & stat.S_IEXEC != 0, "Script should be executable"

    def test_sets_correct_home(self, tmp_path: Path):
        """HOME should be set to /home/terry (hardcoded for pharos)."""
        r = _run(tmp_path, ["printenv", "HOME"])
        assert r.returncode == 0
        assert r.stdout.strip() == "/home/terry"

    def test_sets_extended_path(self, tmp_path: Path):
        """PATH should include all expected directories."""
        r = _run(tmp_path, ["printenv", "PATH"])
        assert r.returncode == 0
        path = r.stdout.strip()
        expected_dirs = [
            "/home/terry/.local/bin",
            "/home/terry/.cargo/bin",
            "/home/terry/.bun/bin",
            "/home/terry/go/bin",
            "/home/terry/.nix-profile/bin",
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
