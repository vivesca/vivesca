from __future__ import annotations

"""Tests for effectors/qmd-reindex.sh — bash script tested via subprocess."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "qmd-reindex.sh"


# ── fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_path(tmp_path):
    """Override built-in tmp_path to avoid asyncio retention-policy race."""
    return tmp_path


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


# ── additional edge cases ─────────────────────────────────────────────────


class TestIdempotency:
    def test_runs_twice_successfully(self, tmp_path):
        """Script can be run multiple times in sequence without error."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text("#!/bin/bash\nexit 0")
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r1 = _run_script(env=env)
        r2 = _run_script(env=env)
        assert r1.returncode == 0
        assert r2.returncode == 0

    def test_second_run_after_skip(self, tmp_path):
        """First run skipped (already running), second run proceeds."""
        call_count = tmp_path / "call_count"

        # pgrep returns 0 (running) then 1 (not running)
        pgrep_path = tmp_path / "bin" / "pgrep"
        pgrep_path.parent.mkdir(parents=True, exist_ok=True)
        pgrep_path.write_text(
            "#!/bin/bash\n"
            f"if [ -f {call_count} ]; then\n"
            f"    exit 1\n"
            f"else\n"
            f"    touch {call_count}\n"
            f"    exit 0\n"
            f"fi\n"
        )
        pgrep_path.chmod(0o755)

        qmd_call_log = tmp_path / "qmd_calls"
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.write_text(f'#!/bin/bash\necho "$@" >> {qmd_call_log}\nexit 0')
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r1 = _run_script(env=env)
        assert r1.returncode == 0
        assert not qmd_call_log.exists()

        r2 = _run_script(env=env)
        assert r2.returncode == 0
        calls = qmd_call_log.read_text().splitlines()
        assert "update" in calls
        assert "embed" in calls


class TestPgrepEdgeCases:
    def test_pgrep_stderr_suppressed(self, tmp_path):
        """pgrep stderr does not leak into script stderr."""
        pgrep_path = tmp_path / "bin" / "pgrep"
        pgrep_path.parent.mkdir(parents=True, exist_ok=True)
        pgrep_path.write_text('#!/bin/bash\necho "pgrep error" >&2\nexit 1')
        pgrep_path.chmod(0o755)

        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.write_text("#!/bin/bash\nexit 0")
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode == 0
        assert r.stderr == ""

    def test_pgrep_exit_2_allows_execution(self, tmp_path):
        """pgrep returning exit code 2 (usage/syntax error) still allows qmd to run."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=2)

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


class TestHomePath:
    def test_home_used_for_bun_path(self, tmp_path):
        """Script uses $HOME to construct .bun/bin path."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        custom_home = tmp_path / "custom_home"
        custom_home.mkdir()

        path_log = tmp_path / "path_log"
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(f'#!/bin/bash\necho "$PATH" > {path_log}\nexit 0')
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(custom_home)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        _run_script(env=env)

        recorded_path = path_log.read_text().strip()
        assert f"{custom_home}/.bun/bin" in recorded_path

    def test_no_stdout_on_skip(self, tmp_path):
        """When already running (pgrep matches), produces no stdout or stderr."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=0)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode == 0
        assert r.stdout == ""
        assert r.stderr == ""


class TestUpdateFailureStopsEmbed:
    def test_embed_not_called_when_update_fails(self, tmp_path):
        """When qmd update fails, qmd embed is never called (set -e)."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_call_log = tmp_path / "qmd_calls"
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(
            '#!/bin/bash\n'
            f'echo "$@" >> {qmd_call_log}\n'
            'if [[ "$1" == "update" ]]; then\n'
            '    exit 1\n'
            'fi\n'
            'exit 0\n'
        )
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode != 0
        calls = qmd_call_log.read_text().splitlines()
        assert calls == ["update"]


# ── new tests — behaviors not covered in test_qmd_reindex_sh.py ───────


class TestQmdStdoutForwarded:
    """Only stderr is suppressed (2>/dev/null); stdout passes through."""

    def test_update_stdout_visible(self, tmp_path):
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(
            '#!/bin/bash\n'
            'if [[ "$1" == "update" ]]; then\n'
            '    echo "updated 42 notes"\n'
            'fi\n'
            'exit 0\n'
        )
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode == 0
        assert "updated 42 notes" in r.stdout

    def test_embed_stdout_visible(self, tmp_path):
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(
            '#!/bin/bash\n'
            'if [[ "$1" == "embed" ]]; then\n'
            '    echo "embedded 99 chunks"\n'
            'fi\n'
            'exit 0\n'
        )
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode == 0
        assert "embedded 99 chunks" in r.stdout


class TestEmbedFailureStderrClean:
    """Embed failure still suppresses stderr."""

    def test_embed_failure_no_stderr(self, tmp_path):
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(
            '#!/bin/bash\n'
            'if [[ "$1" == "embed" ]]; then\n'
            '    echo "embed crash" >&2\n'
            '    exit 1\n'
            'fi\n'
            'exit 0\n'
        )
        qmd_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode != 0
        assert r.stderr == ""


class TestHelpDoesNotModifyPath:
    """Help flag exits before the PATH export line."""

    def test_help_skips_path_export(self, tmp_path):
        """After --help, $PATH in the environment is unchanged."""
        env = os.environ.copy()
        original_path = env.get("PATH", "")
        r = _run_script("--help", env=env)
        assert r.returncode == 0
        # The script process is gone, but we can verify structurally:
        # the help block exits before the `export PATH=...` line.
        src = SCRIPT.read_text()
        help_pos = src.find("${1:-}")
        path_export_pos = src.find("export PATH=")
        assert help_pos < path_export_pos


class TestPgrepStdoutSuppressed:
    """pgrep stdout should not leak into script output."""

    def test_pgrep_match_stdout_not_leaked(self, tmp_path):
        """When pgrep finds a match (exit 0), its stdout is swallowed."""
        pgrep_path = tmp_path / "bin" / "pgrep"
        pgrep_path.parent.mkdir(parents=True, exist_ok=True)
        pgrep_path.write_text('#!/bin/bash\necho "12345"\nexit 0')
        pgrep_path.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode == 0
        assert "12345" not in r.stdout

    def test_pgrep_no_match_stdout_not_leaked(self, tmp_path):
        """When pgrep finds no match (exit 1), its stdout is swallowed."""
        pgrep_path = tmp_path / "bin" / "pgrep"
        pgrep_path.parent.mkdir(parents=True, exist_ok=True)
        pgrep_path.write_text('#!/bin/bash\necho "no match"\nexit 1')
        pgrep_path.chmod(0o755)

        _create_mock_bin(tmp_path, "qmd")

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{env['PATH']}"

        r = _run_script(env=env)
        assert r.returncode == 0
        assert "no match" not in r.stdout


class TestHelpContent:
    def test_help_mentions_embed(self):
        r = _run_script("--help")
        lower = r.stdout.lower()
        assert "embed" in lower

    def test_help_mentions_semantic_search(self):
        r = _run_script("--help")
        lower = r.stdout.lower()
        assert "semantic" in lower or "search" in lower

    def test_help_first_line_is_usage(self):
        r = _run_script("--help")
        first_line = r.stdout.strip().splitlines()[0]
        assert first_line.startswith("Usage:")


class TestPathPreservation:
    def test_existing_path_segments_survive(self, tmp_path):
        """Original PATH segments are still present after bun prepend."""
        _create_mock_bin(tmp_path, "pgrep", exit_code=1)

        path_log = tmp_path / "path_log"
        qmd_path = tmp_path / "bin" / "qmd"
        qmd_path.parent.mkdir(parents=True, exist_ok=True)
        qmd_path.write_text(f'#!/bin/bash\necho "$PATH" > {path_log}\nexit 0')
        qmd_path.chmod(0o755)

        original_path = "/usr/bin:/usr/local/bin"
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{tmp_path}/bin:{original_path}"

        _run_script(env=env)

        recorded_path = path_log.read_text().strip()
        # Original segments must still be present
        assert "/usr/bin" in recorded_path
        assert "/usr/local/bin" in recorded_path
        # And bun bin is first
        assert recorded_path.startswith(f"{tmp_path}/.bun/bin")
