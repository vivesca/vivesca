from __future__ import annotations

"""Tests for effectors/auto-update-compound-engineering.sh — bash script tested via subprocess."""

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "auto-update-compound-engineering.sh"


# ── script structure tests ──────────────────────────────────────────────


class TestScriptStructure:
    def test_script_exists(self):
        assert SCRIPT.exists()

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_has_shebang(self):
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line == "#!/usr/bin/env bash"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    path_dirs: list[Path] | None = None,
    tmp_path: Path | None = None,
    replace_path: bool = False,
) -> subprocess.CompletedProcess:
    """Run the script with an optional custom PATH.

    If replace_path=False (default) and path_dirs provided, prepend them to PATH
    keep system entries so essential commands like bash are still found.
    If replace_path=True, use exactly path_dirs as the new PATH (for filtered tests).
    """
    env = os.environ.copy()
    # Unset HOME override if present so script uses tmp_path as HOME
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if path_dirs is not None:
        if replace_path:
            # Use exactly the provided path dirs (already filtered)
            env["PATH"] = os.pathsep.join(str(p) for p in path_dirs)
        else:
            # Prepend custom path dirs, keep system PATH after
            # This ensures bash is still found but any system-level
            # bunx/npx comes AFTER our mocks and only gets used if
            # we don't provide a mock
            env["PATH"] = os.pathsep.join(str(p) for p in path_dirs) + os.pathsep + env.get("PATH", "")
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=10,
    )


def _make_mock_bin(tmp_path: Path, name: str, stdout: str = "", exit_code: int = 0) -> Path:
    """Create a mock executable script in tmp_path/bin/<name>."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(f"#!/bin/bash\necho {stdout}\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_recording_bin(tmp_path: Path, name: str, record_file: Path, exit_code: int = 0) -> Path:
    """Create a mock bin that records all args to record_file."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(
        "#!/bin/bash\n"
        f'echo "$@" >> {record_file}\n'
        f"exit {exit_code}\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _log_file(tmp_path: Path) -> Path:
    return tmp_path / ".compound-engineering-updates.log"


# ── --help tests ────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_exits_zero(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self, tmp_path):
        r = _run_script(["-h"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_help_shows_usage(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "Usage:" in r.stdout

    def test_help_mentions_crontab(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "crontab" in r.stdout

    def test_help_does_not_create_log(self, tmp_path):
        _run_script(["--help"], tmp_path=tmp_path)
        assert not _log_file(tmp_path).exists()

    def test_help_mentions_log_file(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "log" in r.stdout.lower()
        assert ".compound-engineering-updates.log" in r.stdout


# ── runner selection tests ──────────────────────────────────────────────


class TestRunnerSelection:
    def _no_runner_path(self, tmp_path):
        """Build a minimal PATH with bash but no bunx/npx."""
        safe_bin = tmp_path / "safe-bin"
        safe_bin.mkdir()
        # Symlink bash so the script can still run
        bash_path = shutil.which("bash")
        os.symlink(bash_path, safe_bin / "bash")
        # Include dirs needed for coreutils (date, echo, etc.)
        for cmd in ("date", "echo", "command", "test", "cat"):
            p = shutil.which(cmd)
            if p:
                d = os.path.dirname(p)
                if d not in str(safe_bin):
                    pass  # we'll just use PATH entries that don't have bunx/npx
        # Build filtered system PATH excluding dirs with bunx/npx
        filtered = []
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            has_bunx = (Path(dir_path) / "bunx").exists()
            has_npx = (Path(dir_path) / "npx").exists()
            if not has_bunx and not has_npx:
                filtered.append(dir_path)
        return str(safe_bin) + os.pathsep + os.pathsep.join(filtered)

    def test_no_runner_exits_1(self, tmp_path):
        """Script exits 1 when neither bunx nor npx is on PATH."""
        r = _run_script(
            env_extra={"PATH": self._no_runner_path(tmp_path)},
            tmp_path=tmp_path,
        )
        assert r.returncode == 1

    def test_no_runner_logs_error(self, tmp_path):
        _run_script(
            env_extra={"PATH": self._no_runner_path(tmp_path)},
            tmp_path=tmp_path,
        )
        log = _log_file(tmp_path)
        assert log.exists()
        assert "neither bunx nor npx found" in log.read_text()

    def test_uses_bunx_when_available(self, tmp_path):
        """bunx on PATH → uses bunx as runner."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        calls = record.read_text()
        # Should have been called twice (opencode + codex)
        assert "@every-env/compound-plugin" in calls

    def test_uses_npx_when_bunx_missing(self, tmp_path):
        """npx on PATH (no bunx) → uses npx."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "npx", record)
        # Filter system PATH to remove any dir that contains bunx
        filtered_path = [bindir]
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            if not (Path(dir_path) / "bunx").exists():
                filtered_path.append(Path(dir_path))
        r = _run_script(path_dirs=filtered_path, tmp_path=tmp_path, replace_path=True)
        assert r.returncode == 0
        calls = record.read_text()
        assert "@every-env/compound-plugin" in calls

    def test_prefers_bunx_over_npx(self, tmp_path):
        """Both bunx and npx available → bunx is used."""
        bunx_record = tmp_path / "bunx_calls.log"
        npx_record = tmp_path / "npx_calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", bunx_record)
        _make_recording_bin(tmp_path, "npx", npx_record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert bunx_record.exists() and bunx_record.read_text().strip() != ""
        assert not npx_record.exists() or npx_record.read_text().strip() == ""


# ── logging tests ───────────────────────────────────────────────────────


class TestLogging:
    def test_creates_log_file(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert _log_file(tmp_path).exists()

    def test_log_contains_start_marker(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Update started:" in log_text
        assert "========================================" in log_text

    def test_log_contains_end_marker(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Update completed:" in log_text

    def test_log_contains_dates(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        # Should contain a date-like string (e.g. "Mon 31 Mar 2026")
        # Just check that timestamps are present via the date command output
        # date outputs vary but always contain a year
        assert re.search(r"20\d{2}", log_text) is not None


# ── opencode / codex update tests ───────────────────────────────────────


class TestUpdateTargets:
    def test_runs_codex_update(self, tmp_path):
        """Script runs compound-engineering install --to codex."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = record.read_text()
        assert "--to codex" in calls

    def test_opencode_success_logged(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "OpenCode updated successfully" in log_text

    def test_codex_success_logged(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Codex updated successfully" in log_text

    def test_opencode_failure_logged(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx", exit_code=1)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "OpenCode update failed" in log_text

    def test_codex_failure_logged(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx", exit_code=1)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Codex update failed" in log_text

    def test_failure_does_not_stop_second_update(self, tmp_path):
        """Even if opencode fails, codex update still runs."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record, exit_code=1)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = record.read_text().strip().splitlines()
        assert len(calls) == 2  # Both opencode and codex attempted


# ── log file location ───────────────────────────────────────────────────


class TestLogFileLocation:
    def test_log_uses_home_env(self, tmp_path):
        """Log file is written to $HOME/.compound-engineering-updates.log."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log = tmp_path / ".compound-engineering-updates.log"
        assert log.exists()

    def test_script_exits_0_on_success(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_log_appends_on_repeated_runs(self, tmp_path):
        """Running the script twice appends to the same log file."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        # Two runs → two "Update started" lines
        assert log_text.count("Update started:") == 2

    def test_runs_opencode_update_records_args(self, tmp_path):
        """Script runs compound-engineering install --to opencode."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        assert record.exists(), f"Record file not created. stderr={r.stderr}"
        calls = record.read_text()
        assert "--to opencode" in calls


# ── command argument detail tests ─────────────────────────────────────────


class TestCommandArgs:
    def test_uses_full_package_name(self, tmp_path):
        """Runner is called with @every-env/compound-plugin."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = record.read_text()
        assert "@every-env/compound-plugin install compound-engineering" in calls

    def test_opencode_runs_before_codex(self, tmp_path):
        """OpenCode update is attempted before Codex update."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        lines = record.read_text().strip().splitlines()
        assert len(lines) >= 2
        assert "--to opencode" in lines[0]
        assert "--to codex" in lines[1]

    def test_exactly_two_invocations(self, tmp_path):
        """Runner is called exactly twice (once for each target)."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        lines = record.read_text().strip().splitlines()
        assert len(lines) == 2


# ── log structure tests ──────────────────────────────────────────────────


class TestLogStructure:
    def test_log_has_separator_line(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "========================================" in log_text

    def test_log_has_updating_opencode_status(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating OpenCode..." in log_text

    def test_log_has_updating_codex_status(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating Codex..." in log_text

    def test_log_ends_with_empty_line(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert log_text.endswith("\n\n"), "Log should end with an empty line"

    def test_success_uses_checkmark_emoji(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "✅" in log_text

    def test_failure_uses_cross_emoji(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx", exit_code=1)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "❌" in log_text

    def test_opencode_status_before_codex_status(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        oc_pos = log_text.index("Updating OpenCode...")
        cx_pos = log_text.index("Updating Codex...")
        assert oc_pos < cx_pos


# ── stderr / exit code tests ─────────────────────────────────────────────


class TestStderrAndExitCode:
    def test_no_stderr_on_success(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.stderr == ""

    def test_exits_0_even_on_update_failure(self, tmp_path):
        """Script exits 0 even when individual updates fail."""
        bindir = _make_mock_bin(tmp_path, "bunx", exit_code=1)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0


# ── source analysis tests ────────────────────────────────────────────────


class TestSourceAnalysis:
    def _src(self) -> str:
        return SCRIPT.read_text()

    def test_uses_home_variable_not_hardcoded(self):
        src = self._src()
        assert "$HOME" in src
        assert "/home/terry" not in src
        assert "/Users/terry" not in src

    def test_no_todo_fixme_markers(self):
        src = self._src()
        for marker in ("TODO", "FIXME"):
            assert marker not in src, f"Script contains {marker}"

    def test_help_mentions_opencode_and_codex(self):
        r = _run_script(["--help"])
        assert "OpenCode" in r.stdout
        assert "Codex" in r.stdout

    def test_uses_append_not_overwrite(self):
        """All log writes use >> (append), not > (overwrite)."""
        src = self._src()
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Lines that write to LOG_FILE should use >>
            if "LOG_FILE" in stripped and ">" in stripped:
                # >> is append, > (single) is overwrite — ensure >>
                assert ">>" in stripped, f"Line uses overwrite instead of append: {stripped}"

    def test_hash_r_clears_path_cache(self):
        """Script clears hash table to get fresh runner path."""
        src = self._src()
        assert "hash -r" in src


# ── stdout tests ──────────────────────────────────────────────────────────


class TestStdout:
    def test_no_stdout_on_success(self, tmp_path):
        """Script writes to log file, not stdout, during normal run."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.stdout == ""

    def test_no_stdout_on_update_failure(self, tmp_path):
        """Script writes failure messages to log, not stdout."""
        bindir = _make_mock_bin(tmp_path, "bunx", exit_code=1)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.stdout == ""

    def test_no_stdout_on_no_runner(self, tmp_path):
        """Script writes 'neither found' error to log, not stdout."""
        # Build a filtered PATH with no bunx/npx to avoid calling real ones
        no_runner = TestRunnerSelection()._no_runner_path(tmp_path)
        r = _run_script(
            env_extra={"PATH": no_runner},
            tmp_path=tmp_path,
        )
        # stdout should be empty (error message goes to log file only)
        assert r.stdout == ""


# ── runner output capture tests ───────────────────────────────────────────


class TestRunnerOutputCapture:
    def test_runner_stdout_captured_to_log(self, tmp_path):
        """Runner's stdout output appears in the log file."""
        bindir = _make_mock_bin(tmp_path, "bunx", stdout="installed-v1.2.3")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "installed-v1.2.3" in log_text

    def test_runner_stderr_captured_to_log(self, tmp_path):
        """Runner's stderr output appears in the log file."""
        bindir = tmp_path / "bin"
        bindir.mkdir()
        script = bindir / "bunx"
        script.write_text('#!/bin/bash\necho "warn: deprecated" >&2\nexit 0\n')
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "warn: deprecated" in log_text


# ── runner stdout appears once per invocation ────────────────────────────


class TestRunnerOutputPerInvocation:
    def test_runner_stdout_appears_twice_for_two_targets(self, tmp_path):
        """Each target invocation's output is captured separately."""
        bindir = tmp_path / "bin"
        bindir.mkdir()
        script = bindir / "bunx"
        script.write_text('#!/bin/bash\necho "pkg-output"\nexit 0\n')
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        # "pkg-output" should appear twice — once per target
        assert log_text.count("pkg-output") == 2


# ── log section ordering tests ────────────────────────────────────────────


class TestLogSectionOrdering:
    def test_separator_then_start_then_update_then_result(self, tmp_path):
        """Log sections appear in correct order: separator, start, updates, results, end."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        sep_pos = log_text.index("========================================")
        start_pos = log_text.index("Update started:")
        oc_update_pos = log_text.index("Updating OpenCode...")
        oc_result_pos = log_text.index("OpenCode updated successfully")
        cx_update_pos = log_text.index("Updating Codex...")
        cx_result_pos = log_text.index("Codex updated successfully")
        end_pos = log_text.index("Update completed:")
        assert sep_pos < start_pos < oc_update_pos < oc_result_pos
        assert oc_result_pos < cx_update_pos < cx_result_pos < end_pos


# ── npx runner with filtered path ─────────────────────────────────────────


class TestNpxRunner:
    def test_npx_records_correct_package(self, tmp_path):
        """When npx is used, it's called with the correct package name."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "npx", record)
        # Filter system PATH to remove bunx
        filtered_path = [bindir]
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            if not (Path(dir_path) / "bunx").exists():
                filtered_path.append(Path(dir_path))
        _run_script(path_dirs=filtered_path, tmp_path=tmp_path, replace_path=True)
        calls = record.read_text()
        assert "@every-env/compound-plugin install compound-engineering" in calls
        assert calls.count("@every-env/compound-plugin") == 2

    def test_npx_creates_log(self, tmp_path):
        """npx-based run still creates the log file."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "npx", record)
        filtered_path = [bindir]
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            if not (Path(dir_path) / "bunx").exists():
                filtered_path.append(Path(dir_path))
        _run_script(path_dirs=filtered_path, tmp_path=tmp_path, replace_path=True)
        assert _log_file(tmp_path).exists()


# ── help output detail tests ─────────────────────────────────────────────


class TestHelpDetails:
    def test_help_mentions_compound_engineering(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "compound-engineering" in r.stdout

    def test_help_mentions_plugin(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "plugin" in r.stdout.lower()

    def test_help_exit_code_zero(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_help_stderr_empty(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert r.stderr == ""


# ── log content on mixed success/failure ──────────────────────────────────


class TestMixedResults:
    def _make_flaky_bin(self, tmp_path: Path) -> Path:
        """Create a mock bunx that succeeds first call, fails second."""
        bindir = tmp_path / "bin"
        bindir.mkdir(exist_ok=True)
        count_file = tmp_path / ".call_count"
        count_file.write_text("0")
        script = bindir / "bunx"
        script.write_text(
            '#!/bin/bash\n'
            f'COUNT_FILE="{count_file}"\n'
            'COUNT=$(cat "$COUNT_FILE")\n'
            'COUNT=$((COUNT + 1))\n'
            'echo $COUNT > "$COUNT_FILE"\n'
            'if [ "$COUNT" -eq 1 ]; then\n'
            '    echo "success"\n'
            '    exit 0\n'
            'else\n'
            '    echo "failure"\n'
            '    exit 1\n'
            'fi\n'
        )
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        return bindir

    def test_mixed_success_failure_log(self, tmp_path):
        """First target succeeds, second fails: log shows both results."""
        bindir = self._make_flaky_bin(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "✅ OpenCode updated successfully" in log_text
        assert "❌ Codex update failed" in log_text

    def test_mixed_results_both_targets_attempted(self, tmp_path):
        """Both targets are attempted even when first succeeds and second fails."""
        bindir = self._make_flaky_bin(tmp_path)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        log_text = _log_file(tmp_path).read_text()
        assert "Updating OpenCode..." in log_text
        assert "Updating Codex..." in log_text


# ── source analysis: no hard-coded paths ──────────────────────────────────


class TestSourceNoHardcodedPaths:
    def test_no_hardcoded_usr_local(self):
        """Script doesn't hard-code /usr/local paths."""
        src = SCRIPT.read_text()
        assert "/usr/local/bin" not in src

    def test_log_file_uses_home(self):
        """LOG_FILE is derived from $HOME, not a hard-coded absolute path."""
        src = SCRIPT.read_text()
        assert 'LOG_FILE="$HOME/' in src


# ── extra arguments / robustness tests ──────────────────────────────────────


class TestExtraArguments:
    def test_unknown_args_still_run_updates(self, tmp_path):
        """Passing extra unknown args doesn't prevent the script from running."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        r = _run_script(args=["--unknown-flag"], path_dirs=[bindir], tmp_path=tmp_path)
        # Script doesn't validate extra args — still runs updates
        assert r.returncode == 0
        assert record.exists()
        calls = record.read_text()
        assert "@every-env/compound-plugin" in calls

    def test_no_args_runs_normally(self, tmp_path):
        """Running with no arguments performs updates normally."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        log_text = _log_file(tmp_path).read_text()
        assert "Update completed:" in log_text


# ── log file permissions tests ──────────────────────────────────────────────


class TestLogFilePermissions:
    def test_log_file_readable_by_user(self, tmp_path):
        """Log file is readable after creation."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log = _log_file(tmp_path)
        assert log.exists()
        assert os.access(log, os.R_OK)

    def test_log_file_is_regular_file(self, tmp_path):
        """Log file is a regular file, not a directory or symlink."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log = _log_file(tmp_path)
        assert log.is_file()


# ── runner command structure tests ──────────────────────────────────────────


class TestRunnerCommandStructure:
    def test_opencode_command_has_install_subcommand(self, tmp_path):
        """The opencode invocation uses 'install' subcommand."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        lines = record.read_text().strip().splitlines()
        assert "install" in lines[0]

    def test_codex_command_has_install_subcommand(self, tmp_path):
        """The codex invocation uses 'install' subcommand."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        lines = record.read_text().strip().splitlines()
        assert "install" in lines[1]

    def test_both_invocations_install_compound_engineering(self, tmp_path):
        """Both calls install 'compound-engineering' specifically."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        lines = record.read_text().strip().splitlines()
        for line in lines:
            assert "install compound-engineering" in line


# ── log content on no-runner error ──────────────────────────────────────────


class TestNoRunnerLogContent:
    def test_no_runner_log_has_no_update_markers(self, tmp_path):
        """When no runner is found, log should not contain update markers."""
        no_runner = TestRunnerSelection()._no_runner_path(tmp_path)
        _run_script(env_extra={"PATH": no_runner}, tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Update started:" not in log_text
        assert "Update completed:" not in log_text

    def test_no_runner_exits_before_update_section(self, tmp_path):
        """Script exits early before running any updates when no runner available."""
        no_runner = TestRunnerSelection()._no_runner_path(tmp_path)
        _run_script(env_extra={"PATH": no_runner}, tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating OpenCode" not in log_text
        assert "Updating Codex" not in log_text


# ── help vs run: side-effect isolation ──────────────────────────────────────


class TestHelpVsRunIsolation:
    def test_help_does_not_call_runner(self, tmp_path):
        """--help should not invoke bunx/npx at all."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(args=["--help"], path_dirs=[bindir], tmp_path=tmp_path)
        assert not record.exists() or record.read_text().strip() == ""

    def test_help_short_flag_does_not_call_runner(self, tmp_path):
        """-h should not invoke bunx/npx at all."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(args=["-h"], path_dirs=[bindir], tmp_path=tmp_path)
        assert not record.exists() or record.read_text().strip() == ""


# ── flaky runner: first fails, second succeeds ──────────────────────────────


class TestFlakyRunnerReversed:
    def _make_flaky_bin_reverse(self, tmp_path: Path) -> Path:
        """Create a mock bunx that fails first call, succeeds second."""
        bindir = tmp_path / "bin"
        bindir.mkdir(exist_ok=True)
        count_file = tmp_path / ".call_count"
        count_file.write_text("0")
        script = bindir / "bunx"
        script.write_text(
            '#!/bin/bash\n'
            f'COUNT_FILE="{count_file}"\n'
            'COUNT=$(cat "$COUNT_FILE")\n'
            'COUNT=$((COUNT + 1))\n'
            'echo $COUNT > "$COUNT_FILE"\n'
            'if [ "$COUNT" -eq 1 ]; then\n'
            '    echo "failure"\n'
            '    exit 1\n'
            'else\n'
            '    echo "success"\n'
            '    exit 0\n'
            'fi\n'
        )
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        return bindir

    def test_first_fails_second_succeeds_log(self, tmp_path):
        """First target (opencode) fails, second (codex) succeeds."""
        bindir = self._make_flaky_bin_reverse(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "❌ OpenCode update failed" in log_text
        assert "✅ Codex updated successfully" in log_text

    def test_reversed_failure_still_exits_0(self, tmp_path):
        """Script exits 0 even when first update fails and second succeeds."""
        bindir = self._make_flaky_bin_reverse(tmp_path)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
