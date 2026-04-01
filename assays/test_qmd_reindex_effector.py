from __future__ import annotations

"""Tests for effectors/qmd-reindex.sh — bash script tested via subprocess."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "qmd-reindex.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    *args: str,
    env: dict[str, str] | None = None,
    timeout: int = 10,
) -> subprocess.CompletedProcess:
    """Run script with given args and environment."""
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


def _create_mock_bin(tmp_path: Path, name: str, exit_code: int = 0, stdout: str = ""):
    """Create a mock binary in tmp_path/bin."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    bin_path = bin_dir / name
    bin_path.write_text(f"#!/bin/bash\necho -n '{stdout}'\nexit {exit_code}")
    bin_path.chmod(0o755)
    return bin_path


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def test_help_exits_zero(self):
        r = _run_script("--help")
        assert r.returncode == 0
        assert "Usage:" in r.stdout

    def test_help_short_flag_exits_zero(self):
        r = _run_script("-h")
        assert r.returncode == 0
        assert "Usage:" in r.stdout


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert "bash" in first

    def test_has_set_e(self):
        src = SCRIPT.read_text()
        assert "set -e" in src or "set -euo pipefail" in src

    def test_has_shebang(self):
        src = SCRIPT.read_text()
        assert src.startswith("#!")


# ── execution logic ─────────────────────────────────────────────────────


class TestExecution:
    def test_skips_if_already_running(self, tmp_path):
        """If pgrep -f 'qmd embed' returns 0, script should exit 0 without running qmd."""
        # Create mock pgrep that returns 0 (found process)
        _create_mock_bin(tmp_path, "pgrep", exit_code=0)
        
        # Create mock qmd that should NOT be called
        qmd_path = _create_mock_bin(tmp_path, "qmd", exit_code=0)
        qmd_call_log = tmp_path / "qmd_called"
        qmd_path.write_text(f"#!/bin/bash\ntouch {qmd_call_log}\nexit 0")
        
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"
        
        r = _run_script(env=env)
        assert r.returncode == 0
        assert not qmd_call_log.exists()

    def test_runs_qmd_if_not_running(self, tmp_path):
        """If pgrep returns 1, script should run qmd update and qmd embed."""
        # Create mock pgrep that returns 1 (no process found)
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)
        
        # Create mock qmd that records calls
        qmd_call_log = tmp_path / "qmd_calls"
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(f"#!/bin/bash\necho \"$@\" >> {qmd_call_log}\nexit 0")
        qmd_path.chmod(0o755)
        
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"
        
        r = _run_script(env=env)
        assert r.returncode == 0
        
        calls = qmd_call_log.read_text().splitlines()
        assert "update" in calls
        assert "embed" in calls

    def test_fails_if_qmd_update_fails(self, tmp_path):
        """Script should exit with non-zero if qmd update fails (due to set -e)."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)
        
        # Mock qmd to fail on 'update'
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text("""#!/bin/bash
if [[ "$1" == "update" ]]; then
    exit 1
fi
exit 0
""")
        qmd_path.chmod(0o755)
        
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"
        
        r = _run_script(env=env)
        assert r.returncode != 0

    def test_fails_if_qmd_embed_fails(self, tmp_path):
        """Script should exit with non-zero if qmd embed fails."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)
        
        # Mock qmd to fail on 'embed'
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text("""#!/bin/bash
if [[ "$1" == "embed" ]]; then
    exit 1
fi
exit 0
""")
        qmd_path.chmod(0o755)
        
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"
        
        r = _run_script(env=env)
        assert r.returncode != 0
