from __future__ import annotations

"""Tests for effectors/hetzner-bootstrap.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "hetzner-bootstrap.sh"


# ── script structure tests ──────────────────────────────────────────────


class TestScriptStructure:
    def test_script_exists(self):
        assert SCRIPT.exists()

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_has_shebang(self):
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line == "#!/usr/bin/env bash"

    def test_script_has_set_euo_pipefail(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src


# ── --help tests ────────────────────────────────────────────────────────


class TestHelpFlag:
    def _run_help(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_help_exits_zero(self):
        r = self._run_help("--help")
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self):
        r = self._run_help("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = self._run_help("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_hetzner(self):
        r = self._run_help("--help")
        assert "Hetzner" in r.stdout

    def test_help_mentions_ubuntu(self):
        r = self._run_help("--help")
        assert "Ubuntu" in r.stdout

    def test_help_no_stderr(self):
        r = self._run_help("--help")
        assert r.stderr == ""


# ── permission check tests ───────────────────────────────────────────────


class TestPermissionCheck:
    def test_fails_when_not_root(self):
        """Script fails with exit code 1 when EUID != 0."""
        # Mock EUID to non-root via a bash wrapper
        test_script = f"""
#!/usr/bin/env bash
EUID=1000  # Mock non-root user
{Path(SCRIPT).read_text()}
"""
        r = subprocess.run(
            ["bash", "-c", test_script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 1
        assert "ERROR: This script must be run as root" in r.stderr

    def test_passes_when_root_mock(self):
        """Script proceeds past check when EUID == 0."""
        test_script = f"""
#!/usr/bin/env bash
EUID=0
# Extract just the permission check part
{Path(SCRIPT).read_text().split('echo "=== Hetzner Claude Code Bootstrap ==="')[0]}
echo "PERMISSION_CHECK_PASSED"
exit 0
"""
        r = subprocess.run(
            ["bash", "-c", test_script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "PERMISSION_CHECK_PASSED" in r.stdout
