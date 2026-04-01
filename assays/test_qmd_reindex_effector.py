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


def _create_mock_bin(
    tmp_path: Path, name: str, exit_code: int = 0, stdout: str = ""
) -> Path:
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

    def test_help_short_flag_exits_zero(self):
        r = _run_script("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run_script("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_qmd(self):
        r = _run_script("--help")
        assert "qmd" in r.stdout

    def test_help_no_stderr(self):
        r = _run_script("--help")
        assert r.stderr == ""


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/bin/bash")

    def test_has_shebang(self):
        src = SCRIPT.read_text()
        assert src.startswith("#!")

    def test_has_set_euo_pipefail(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src


# ── script permissions ──────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_is_file_not_directory(self):
        assert SCRIPT.is_file()


# ── execution logic ─────────────────────────────────────────────────────


class TestExecution:
    def test_skips_if_already_running(self, tmp_path):
        """If pgrep -f 'qmd embed' returns 0, script exits 0 without running qmd."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=0)

        # Mock qmd that should NOT be called
        qmd_call_log = tmp_path / "qmd_called"
        qmd_path = _create_mock_bin(tmp_path, "qmd")
        qmd_path.write_text(f"#!/bin/bash\ntouch {qmd_call_log}\nexit 0")
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode == 0
        assert not qmd_call_log.exists()

    def test_runs_qmd_if_not_running(self, tmp_path):
        """If pgrep returns 1, script runs both qmd update and qmd embed."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        # Mock qmd that records calls
        qmd_call_log = tmp_path / "qmd_calls"
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(f'#!/bin/bash\necho "$@" >> {qmd_call_log}\nexit 0')
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode == 0

        calls = qmd_call_log.read_text().splitlines()
        assert "update" in calls
        assert "embed" in calls

    def test_runs_update_before_embed(self, tmp_path):
        """qmd update is called before qmd embed."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_call_log = tmp_path / "qmd_calls"
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(f'#!/bin/bash\necho "$@" >> {qmd_call_log}\nexit 0')
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        _run_script(env=env)

        calls = qmd_call_log.read_text().splitlines()
        assert calls.index("update") < calls.index("embed")

    def test_fails_if_qmd_update_fails(self, tmp_path):
        """Script exits non-zero if qmd update fails (set -e)."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(
            '#!/bin/bash\nif [[ "$1" == "update" ]]; then\n    exit 1\nfi\nexit 0\n'
        )
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode != 0

    def test_fails_if_qmd_embed_fails(self, tmp_path):
        """Script exits non-zero if qmd embed fails (set -e)."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(
            '#!/bin/bash\nif [[ "$1" == "embed" ]]; then\n    exit 1\nfi\nexit 0\n'
        )
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode != 0

    def test_sets_bun_path(self, tmp_path):
        """Script prepends $HOME/.bun/bin to PATH."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        # Create a qmd mock that records the resolved PATH
        path_log = tmp_path / "path_log"
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(f'#!/bin/bash\necho "$PATH" > {path_log}\nexit 0')
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        _run_script(env=env)

        recorded_path = path_log.read_text().strip()
        assert f"{tmp_path}/.bun/bin" in recorded_path

    def test_suppresses_qmd_stderr(self, tmp_path):
        """Script redirects qmd stderr to /dev/null, so script stderr stays clean."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(
            '#!/bin/bash\necho "error output" >&2\nexit 0'
        )
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode == 0
        assert r.stderr == ""

    def test_pgrep_called_with_correct_args(self, tmp_path):
        """pgrep is invoked with -f 'qmd embed'."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        pgrep_log = tmp_path / "pgrep_args"
        pgrep_path = tmp_path / "bin" / "pgrep"
        pgrep_path.parent.mkdir(parents=True, exist_ok=True)
        pgrep_path.write_text(f'#!/bin/bash\necho "$@" >> {pgrep_log}\nexit 1')
        pgrep_path.chmod(0o755)

        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text('#!/bin/bash\nexit 0')
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        _run_script(env=env)

        args = pgrep_log.read_text().strip()
        assert "-f" in args
        assert "qmd embed" in args

    def test_no_args_runs_normally(self, tmp_path):
        """Script runs qmd update && qmd embed when called with no arguments."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_call_log = tmp_path / "qmd_calls"
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(f'#!/bin/bash\necho "$@" >> {qmd_call_log}\nexit 0')
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode == 0

        calls = qmd_call_log.read_text().splitlines()
        assert calls == ["update", "embed"]

    def test_qmd_update_stderr_suppressed_on_failure(self, tmp_path):
        """Even when qmd update fails, its stderr is swallowed by 2>/dev/null."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(
            '#!/bin/bash\necho "fatal error" >&2\nexit 1'
        )
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        # Script fails (set -e) but stderr is empty (2>/dev/null)
        assert r.returncode != 0
        assert r.stderr == ""

    def test_help_mentions_reindex(self):
        """Help output mentions re-index / reindex."""
        r = _run_script("--help")
        lower = r.stdout.lower()
        assert "re-index" in lower or "reindex" in lower

    def test_help_mentions_skip(self):
        """Help output mentions the skip-if-running behavior."""
        r = _run_script("--help")
        lower = r.stdout.lower()
        assert "skip" in lower

    def test_help_output_multiline(self):
        """Help output has multiple lines (Usage + description)."""
        r = _run_script("--help")
        lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
        assert len(lines) >= 2

    def test_unknown_arg_is_not_help(self, tmp_path):
        """Unknown args do NOT trigger help — script proceeds to execution."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_call_log = tmp_path / "qmd_calls"
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(f'#!/bin/bash\necho "$@" >> {qmd_call_log}\nexit 0')
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script("--random-flag", env=env)
        # Script should attempt to run qmd (not exit early with help)
        assert qmd_call_log.exists()

    def test_no_stdout_during_normal_run(self, tmp_path):
        """Normal execution (not --help) produces no stdout."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text('#!/bin/bash\nexit 0')
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.stdout == ""

    def test_bun_path_prepend_order(self, tmp_path):
        """$HOME/.bun/bin is prepended (first in PATH), not appended."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        path_log = tmp_path / "path_log"
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(f'#!/bin/bash\necho "$PATH" > {path_log}\nexit 0')
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        _run_script(env=env)

        recorded_path = path_log.read_text().strip()
        bun_segment = f"{tmp_path}/.bun/bin"
        # .bun/bin should be the very first entry in PATH
        assert recorded_path.startswith(bun_segment)
