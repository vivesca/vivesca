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


def _make_env(tmp_path: Path) -> dict[str, str]:
    """Build a test environment with mock bin on PATH and HOME set to tmp_path."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"
    return env


# ── file basics ─────────────────────────────────────────────────────────


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

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_is_file_not_directory(self):
        assert SCRIPT.is_file()


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

    def test_help_exits_early(self):
        """--help prints help and exits without running qmd commands."""
        r = _run_script("--help")
        assert r.returncode == 0

    def test_help_mentions_reindex(self):
        r = _run_script("--help")
        lower = r.stdout.lower()
        assert "re-index" in lower or "reindex" in lower

    def test_help_mentions_skip(self):
        r = _run_script("--help")
        assert "skip" in r.stdout.lower()

    def test_help_output_multiline(self):
        r = _run_script("--help")
        lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
        assert len(lines) >= 2


# ── script structure ───────────────────────────────────────────────────


class TestScriptStructure:
    def test_help_before_pgrep(self):
        """Help check comes before pgrep (so --help works even if pgrep behaves oddly)."""
        src = SCRIPT.read_text()
        help_pos = src.find("--help")
        pgrep_pos = src.find("pgrep")
        assert help_pos < pgrep_pos, "--help check should precede pgrep check"

    def test_pgrep_before_qmd_commands(self):
        """pgrep check comes before qmd update/embed execution lines."""
        src = SCRIPT.read_text()
        pgrep_pos = src.find("pgrep -f")
        update_pos = src.find("\nqmd update")
        assert pgrep_pos < update_pos

    def test_update_before_embed(self):
        """qmd update runs before qmd embed."""
        src = SCRIPT.read_text()
        update_pos = src.find("qmd update")
        embed_pos = src.find("qmd embed")
        assert update_pos < embed_pos

    def test_update_stderr_suppressed(self):
        src = SCRIPT.read_text()
        assert "qmd update 2>/dev/null" in src

    def test_embed_stderr_suppressed(self):
        src = SCRIPT.read_text()
        assert "qmd embed 2>/dev/null" in src

    def test_uses_home_for_bun_path(self):
        src = SCRIPT.read_text()
        assert "$HOME/.bun/bin" in src


# ── pgrep skip logic ───────────────────────────────────────────────────


class TestSkipIfRunning:
    def test_skips_when_qmd_embed_running(self, tmp_path):
        """If pgrep finds 'qmd embed', script exits 0 without running qmd."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=0)
        # Provide a qmd that would fail if called (to prove it wasn't called)
        _create_mock_bin(tmp_path, "qmd", exit_code=99)

        r = _run_script(env=_make_env(tmp_path))
        assert r.returncode == 0
        assert r.stdout == ""
        assert r.stderr == ""

    def test_runs_when_not_running(self, tmp_path):
        """If pgrep doesn't find 'qmd embed', script proceeds to run qmd."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        log = tmp_path / "calls.log"
        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text(f'#!/bin/bash\necho "$@" >> {log}\nexit 0')
        qmd.chmod(0o755)

        r = _run_script(env=_make_env(tmp_path))
        assert r.returncode == 0
        calls = log.read_text().splitlines()
        assert "update" in calls
        assert "embed" in calls

    def test_pgrep_called_with_correct_args(self, tmp_path):
        """pgrep is invoked with -f 'qmd embed'."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        pgrep_log = tmp_path / "pgrep_args"
        pgrep = tmp_path / "bin" / "pgrep"
        pgrep.write_text(f'#!/bin/bash\necho "$@" >> {pgrep_log}\nexit 1')
        pgrep.chmod(0o755)

        _create_mock_bin(tmp_path, "qmd")

        _run_script(env=_make_env(tmp_path))
        args = pgrep_log.read_text().strip()
        assert "-f" in args
        assert "qmd embed" in args


# ── successful run ──────────────────────────────────────────────────────


class TestSuccessfulRun:
    def test_no_args_runs_normally(self, tmp_path):
        """Script runs qmd update && qmd embed when called with no arguments."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        log = tmp_path / "calls.log"
        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text(f'#!/bin/bash\necho "$@" >> {log}\nexit 0')
        qmd.chmod(0o755)

        r = _run_script(env=_make_env(tmp_path))
        assert r.returncode == 0
        calls = log.read_text().splitlines()
        assert calls == ["update", "embed"]

    def test_update_before_embed(self, tmp_path):
        """qmd update is called before qmd embed."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        log = tmp_path / "calls.log"
        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text(f'#!/bin/bash\necho "$@" >> {log}\nexit 0')
        qmd.chmod(0o755)

        _run_script(env=_make_env(tmp_path))
        calls = log.read_text().splitlines()
        assert calls.index("update") < calls.index("embed")

    def test_no_stdout_during_normal_run(self, tmp_path):
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)
        _create_mock_bin(tmp_path, "qmd")

        r = _run_script(env=_make_env(tmp_path))
        assert r.stdout == ""

    def test_suppresses_qmd_stderr(self, tmp_path):
        """Script redirects qmd stderr to /dev/null, so script stderr stays clean."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text('#!/bin/bash\necho "error output" >&2\nexit 0')
        qmd.chmod(0o755)

        r = _run_script(env=_make_env(tmp_path))
        assert r.returncode == 0
        assert r.stderr == ""

    def test_unknown_arg_is_not_help(self, tmp_path):
        """Unknown args do NOT trigger help — script proceeds to execution."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)
        _create_mock_bin(tmp_path, "qmd")

        r = _run_script("--random-flag", env=_make_env(tmp_path))
        assert r.returncode == 0


# ── PATH setup ──────────────────────────────────────────────────────────


class TestPathSetup:
    def test_sets_bun_path(self, tmp_path):
        """Script prepends $HOME/.bun/bin to PATH."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        path_log = tmp_path / "path_log"
        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text(f'#!/bin/bash\necho "$PATH" > {path_log}\nexit 0')
        qmd.chmod(0o755)

        _run_script(env=_make_env(tmp_path))
        recorded_path = path_log.read_text().strip()
        assert f"{tmp_path}/.bun/bin" in recorded_path

    def test_bun_path_prepend_order(self, tmp_path):
        """$HOME/.bun/bin is prepended (first in PATH), not appended."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        path_log = tmp_path / "path_log"
        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text(f'#!/bin/bash\necho "$PATH" > {path_log}\nexit 0')
        qmd.chmod(0o755)

        _run_script(env=_make_env(tmp_path))
        recorded_path = path_log.read_text().strip()
        assert recorded_path.startswith(f"{tmp_path}/.bun/bin")

    def test_home_used_for_bun_path(self, tmp_path):
        """Script uses $HOME to construct .bun/bin path."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        custom_home = tmp_path / "custom_home"
        custom_home.mkdir()

        path_log = tmp_path / "path_log"
        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text(f'#!/bin/bash\necho "$PATH" > {path_log}\nexit 0')
        qmd.chmod(0o755)

        env = _make_env(tmp_path)
        env["HOME"] = str(custom_home)

        _run_script(env=env)
        recorded_path = path_log.read_text().strip()
        assert f"{custom_home}/.bun/bin" in recorded_path


# ── qmd command failure ────────────────────────────────────────────────


class TestQmdFailure:
    def test_update_failure_causes_nonzero_exit(self, tmp_path):
        """If qmd update fails (set -e), script exits non-zero."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text('#!/bin/bash\nif [[ "$1" == "update" ]]; then\n    exit 1\nfi\nexit 0\n')
        qmd.chmod(0o755)

        r = _run_script(env=_make_env(tmp_path))
        assert r.returncode != 0

    def test_embed_failure_causes_nonzero_exit(self, tmp_path):
        """If qmd embed fails (set -e), script exits non-zero."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text('#!/bin/bash\nif [[ "$1" == "embed" ]]; then\n    exit 1\nfi\nexit 0\n')
        qmd.chmod(0o755)

        r = _run_script(env=_make_env(tmp_path))
        assert r.returncode != 0

    def test_embed_not_called_when_update_fails(self, tmp_path):
        """When qmd update fails, qmd embed is never called (set -e)."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        log = tmp_path / "calls.log"
        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text(
            '#!/bin/bash\n'
            f'echo "$@" >> {log}\n'
            'if [[ "$1" == "update" ]]; then\n'
            '    exit 1\n'
            'fi\n'
            'exit 0\n'
        )
        qmd.chmod(0o755)

        r = _run_script(env=_make_env(tmp_path))
        assert r.returncode != 0
        calls = log.read_text().splitlines()
        assert calls == ["update"]

    def test_qmd_update_stderr_suppressed_on_failure(self, tmp_path):
        """Even when qmd update fails, its stderr is swallowed by 2>/dev/null."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text('#!/bin/bash\necho "fatal error" >&2\nexit 1')
        qmd.chmod(0o755)

        r = _run_script(env=_make_env(tmp_path))
        assert r.returncode != 0
        assert r.stderr == ""


# ── qmd not in PATH ────────────────────────────────────────────────────


class TestQmdNotInPath:
    def test_fails_when_qmd_missing(self, tmp_path):
        """Without qmd on PATH, script fails (set -e)."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        r = _run_script(env=_make_env(tmp_path))
        assert r.returncode != 0


# ── pgrep edge cases ───────────────────────────────────────────────────


class TestPgrepEdgeCases:
    def test_pgrep_stderr_suppressed(self, tmp_path):
        """pgrep stderr does not leak into script stderr."""
        pgrep = tmp_path / "bin" / "pgrep"
        pgrep.parent.mkdir(parents=True, exist_ok=True)
        pgrep.write_text('#!/bin/bash\necho "pgrep error" >&2\nexit 1')
        pgrep.chmod(0o755)

        _create_mock_bin(tmp_path, "qmd")

        r = _run_script(env=_make_env(tmp_path))
        assert r.returncode == 0
        assert r.stderr == ""

    def test_pgrep_exit_2_allows_execution(self, tmp_path):
        """pgrep returning exit code 2 (usage/syntax error) still allows qmd to run."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=2)

        log = tmp_path / "calls.log"
        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text(f'#!/bin/bash\necho "$@" >> {log}\nexit 0')
        qmd.chmod(0o755)

        r = _run_script(env=_make_env(tmp_path))
        assert r.returncode == 0
        calls = log.read_text().splitlines()
        assert "update" in calls
        assert "embed" in calls


# ── idempotency ─────────────────────────────────────────────────────────


class TestIdempotency:
    def test_runs_twice_successfully(self, tmp_path):
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)
        _create_mock_bin(tmp_path, "qmd")

        env = _make_env(tmp_path)
        r1 = _run_script(env=env)
        r2 = _run_script(env=env)
        assert r1.returncode == 0
        assert r2.returncode == 0

    def test_second_run_after_skip(self, tmp_path):
        """First run skipped (already running), second run proceeds."""
        flag = tmp_path / "flag"

        pgrep = tmp_path / "bin" / "pgrep"
        pgrep.parent.mkdir(parents=True, exist_ok=True)
        pgrep.write_text(
            "#!/bin/bash\n"
            f"if [ -f {flag} ]; then\n"
            "    exit 1\n"
            "else\n"
            f"    touch {flag}\n"
            "    exit 0\n"
            "fi\n"
        )
        pgrep.chmod(0o755)

        log = tmp_path / "calls.log"
        qmd = tmp_path / "bin" / "qmd"
        qmd.write_text(f'#!/bin/bash\necho "$@" >> {log}\nexit 0')
        qmd.chmod(0o755)

        env = _make_env(tmp_path)
        r1 = _run_script(env=env)
        assert r1.returncode == 0
        assert not log.exists()

        r2 = _run_script(env=env)
        assert r2.returncode == 0
        calls = log.read_text().splitlines()
        assert "update" in calls
        assert "embed" in calls
