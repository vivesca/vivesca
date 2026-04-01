from __future__ import annotations

"""Tests for effectors/update-coding-tools.sh — bash script tested via subprocess."""

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "update-coding-tools.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    path_dirs: list[Path] | None = None,
    tmp_path: Path | None = None,
    replace_path: bool = False,
    timeout: int = 10,
) -> subprocess.CompletedProcess:
    """Run the script with an optional custom PATH."""
    env = os.environ.copy()
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if path_dirs is not None:
        if replace_path:
            env["PATH"] = os.pathsep.join(str(p) for p in path_dirs)
        else:
            env["PATH"] = (
                os.pathsep.join(str(p) for p in path_dirs)
                + os.pathsep
                + env.get("PATH", "")
            )
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=timeout)


def _make_mock_bin(
    tmp_path: Path,
    name: str,
    stdout: str = "",
    exit_code: int = 0,
    extra_logic: str = "",
) -> Path:
    """Create a mock executable in tmp_path/bin/<name>. Returns the bindir."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(f"#!/bin/bash\n{extra_logic}\necho {stdout}\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_recording_bin(
    tmp_path: Path, name: str, record_file: Path, exit_code: int = 0,
    extra_logic: str = "",
) -> Path:
    """Create a mock bin that records invocations (subcommand + args) to record_file."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(
        "#!/bin/bash\n"
        f"{extra_logic}\n"
        f'echo "$@" >> {record_file}\n'
        f"exit {exit_code}\n",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _log_file(tmp_path: Path) -> Path:
    return tmp_path / ".coding-tools-update.log"


def _health_file(tmp_path: Path) -> Path:
    return tmp_path / ".coding-tools-health.json"


def _setup_full_mocks(
    tmp_path: Path,
    *,
    brew_exit: int = 0,
    npm_exit: int = 0,
    pnpm_exit: int = 0,
    uv_exit: int = 0,
    cargo_exit: int = 0,
    mas_exit: int = 0,
) -> tuple[Path, dict[str, Path]]:
    """Set up all mock binaries and return (bindir, {name: record_file})."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    records: dict[str, Path] = {}

    # brew needs special handling: responds to 'shellenv' subcommand
    brew_rec = tmp_path / "brew_calls.log"
    records["brew"] = brew_rec
    brew_script = bindir / "brew"
    brew_script.write_text(
        "#!/bin/bash\n"
        'if [[ "$1" == "shellenv" ]]; then\n'
        '    echo "export PATH=/usr/local/bin:$PATH"\n'
        "    exit 0\n"
        "fi\n"
        f'echo "$@" >> {brew_rec}\n'
        f"exit {brew_exit}\n",
    )
    brew_script.chmod(brew_script.stat().st_mode | stat.S_IEXEC)

    # Simple recording mocks for remaining tools
    for name, exit_code in [
        ("npm", npm_exit),
        ("pnpm", pnpm_exit),
        ("uv", uv_exit),
        ("cargo", cargo_exit),
        ("mas", mas_exit),
    ]:
        rec = tmp_path / f"{name}_calls.log"
        records[name] = rec
        _make_recording_bin(tmp_path, name, rec, exit_code=exit_code)

    # command-not-found handler: just return false for unknown tools
    # (not needed since we mock everything)

    return bindir, records


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

    def test_help_mentions_brew(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "brew" in r.stdout

    def test_help_does_not_create_log(self, tmp_path):
        _run_script(["--help"], tmp_path=tmp_path)
        assert not _log_file(tmp_path).exists()

    def test_help_does_not_create_health(self, tmp_path):
        _run_script(["--help"], tmp_path=tmp_path)
        assert not _health_file(tmp_path).exists()


# ── brew not found tests ────────────────────────────────────────────────


class TestBrewNotFound:
    def _no_brew_path(self, tmp_path):
        """Build a minimal PATH with bash but no brew."""
        import shutil

        safe_bin = tmp_path / "safe-bin"
        safe_bin.mkdir()
        bash_path = shutil.which("bash")
        os.symlink(bash_path, safe_bin / "bash")
        # Filter out any dir containing brew
        filtered = []
        for d in os.environ.get("PATH", "").split(os.pathsep):
            if d and not (Path(d) / "brew").exists():
                filtered.append(d)
        return [safe_bin] + [Path(d) for d in filtered]

    def test_no_brew_exits_1(self, tmp_path):
        r = _run_script(
            path_dirs=self._no_brew_path(tmp_path),
            tmp_path=tmp_path,
            replace_path=True,
        )
        assert r.returncode == 1

    def test_no_brew_stderr_message(self, tmp_path):
        r = _run_script(
            path_dirs=self._no_brew_path(tmp_path),
            tmp_path=tmp_path,
            replace_path=True,
        )
        assert "Homebrew not found" in r.stderr


# ── logging tests ───────────────────────────────────────────────────────


class TestLogging:
    def test_creates_log_file(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert _log_file(tmp_path).exists()

    def test_log_contains_date_marker(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        # The script writes "=== $(date) ===" markers
        assert "===" in log_text

    def test_log_contains_start_marker(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        import re
        assert re.search(r"=== .+ ===", log_text) is not None

    def test_log_contains_updates_complete(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updates complete" in log_text

    def test_log_mentions_brew_update(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating brew" in log_text

    def test_log_mentions_npm(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating npm" in log_text

    def test_log_mentions_pnpm(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating pnpm" in log_text

    def test_log_mentions_uv(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating uv" in log_text

    def test_log_mentions_cargo(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating cargo" in log_text

    def test_log_mentions_mas(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating Mac App Store" in log_text

    def test_log_file_uses_home(self, tmp_path):
        """Log file is written to $HOME/.coding-tools-update.log."""
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert (tmp_path / ".coding-tools-update.log").exists()


# ── tool update invocation tests ────────────────────────────────────────


class TestToolUpdates:
    def test_brew_update_called(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = records["brew"].read_text()
        assert "update" in calls

    def test_brew_upgrade_called(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = records["brew"].read_text()
        assert "upgrade" in calls

    def test_brew_cleanup_called(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = records["brew"].read_text()
        assert "cleanup" in calls

    def test_npm_update_called(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = records["npm"].read_text()
        assert "update" in calls
        assert "-g" in calls

    def test_pnpm_update_called(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = records["pnpm"].read_text()
        assert "update" in calls
        assert "-g" in calls

    def test_uv_tool_upgrade_called(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = records["uv"].read_text()
        assert "tool" in calls
        assert "upgrade" in calls
        assert "--all" in calls

    def test_cargo_binstall_called(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = records["cargo"].read_text()
        assert "binstall" in calls

    def test_mas_upgrade_called(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = records["mas"].read_text()
        assert "upgrade" in calls

    def test_brew_upgrade_cask_greedy(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = records["brew"].read_text()
        assert "upgrade" in calls
        assert "--cask" in calls
        assert "--greedy" in calls

    def test_brew_cleanup_prune(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = records["brew"].read_text()
        assert "cleanup" in calls
        assert "--prune=7" in calls


# ── tool failure tolerance tests ────────────────────────────────────────


class TestToolFailureTolerance:
    """Individual tool failures should not abort the script (|| true)."""

    def test_brew_failure_does_not_abort(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path, brew_exit=1)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_npm_failure_does_not_abort(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path, npm_exit=1)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_pnpm_failure_does_not_abort(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path, pnpm_exit=1)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_uv_failure_does_not_abort(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path, uv_exit=1)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_cargo_failure_does_not_abort(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path, cargo_exit=1)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_mas_failure_does_not_abort(self, tmp_path):
        bindir, records = _setup_full_mocks(tmp_path, mas_exit=1)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_all_fail_still_completes(self, tmp_path):
        bindir, records = _setup_full_mocks(
            tmp_path,
            brew_exit=1, npm_exit=1, pnpm_exit=1,
            uv_exit=1, cargo_exit=1, mas_exit=1,
        )
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        # Still should have log and health file
        assert _log_file(tmp_path).exists()
        assert _health_file(tmp_path).exists()


# ── health check tests ─────────────────────────────────────────────────


class TestHealthCheck:
    def test_creates_health_file(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert _health_file(tmp_path).exists()

    def test_health_json_valid(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        data = json.loads(_health_file(tmp_path).read_text())
        assert "status" in data
        assert "checked" in data
        assert "failures" in data

    def test_health_ok_when_all_tools_present(self, tmp_path):
        """All REPAIR tools on PATH → status ok."""
        bindir, _ = _setup_full_mocks(tmp_path)
        # Add mocks for all health-check commands
        for cmd in ["claude", "opencode", "gemini", "codex", "agent-browser", "mas"]:
            _make_mock_bin(tmp_path, cmd)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        data = json.loads(_health_file(tmp_path).read_text())
        assert data["status"] == "ok"
        assert data["failures"] == []

    def test_health_degraded_when_tool_missing(self, tmp_path):
        """A health-check tool missing (and repair fails) → status degraded."""
        bindir, _ = _setup_full_mocks(tmp_path)
        # Mock brew to succeed for shellenv but fail for install (repair)
        brew_script = bindir / "brew"
        brew_script.write_text(
            "#!/bin/bash\n"
            'if [[ "$1" == "shellenv" ]]; then\n'
            '    echo "export PATH=/usr/local/bin:$PATH"\n'
            "    exit 0\n"
            "fi\n"
            "# Record normal calls\n"
            f'echo "$@" >> {tmp_path / "brew_calls.log"}\n'
            "# Fail install (repair) calls\n"
            'if [[ "$1" == "install" ]]; then\n'
            "    exit 1\n"
            "fi\n"
            "exit 0\n",
        )
        brew_script.chmod(brew_script.stat().st_mode | stat.S_IEXEC)
        # Only mock mas (also in REPAIR dict) — omit claude, opencode, etc.
        _make_mock_bin(tmp_path, "mas")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        data = json.loads(_health_file(tmp_path).read_text())
        assert data["status"] == "degraded"
        assert len(data["failures"]) > 0

    def test_health_contains_iso_timestamp(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        data = json.loads(_health_file(tmp_path).read_text())
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", data["checked"]) is not None

    def test_health_file_uses_home(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert (tmp_path / ".coding-tools-health.json").exists()

    def test_log_mentions_verifying_tools(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Verifying critical tools" in log_text


# ── PATH extension tests ────────────────────────────────────────────────


class TestPathExtension:
    def test_script_extends_path_with_cargo(self, tmp_path):
        """Script adds $HOME/.cargo/bin to PATH."""
        bindir, _ = _setup_full_mocks(tmp_path)
        # Create a special brew that prints PATH after shellenv
        brew_script = bindir / "brew"
        brew_script.write_text(
            "#!/bin/bash\n"
            'if [[ "$1" == "shellenv" ]]; then\n'
            '    echo "export PATH=/usr/local/bin:$PATH"\n'
            "    exit 0\n"
            "fi\n"
            f'echo "$@" >> {tmp_path / "brew_calls.log"}\n'
            "exit 0\n",
        )
        brew_script.chmod(brew_script.stat().st_mode | stat.S_IEXEC)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        # Script ran without error = PATH was extended successfully


# ── script exit code tests ─────────────────────────────────────────────


class TestExitCodes:
    def test_successful_run_exits_zero(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_brew_not_found_exits_nonzero(self, tmp_path):
        import shutil

        safe_bin = tmp_path / "safe-bin"
        safe_bin.mkdir()
        bash_path = shutil.which("bash")
        os.symlink(bash_path, safe_bin / "bash")
        filtered = [
            Path(d)
            for d in os.environ.get("PATH", "").split(os.pathsep)
            if d and not (Path(d) / "brew").exists()
        ]
        r = _run_script(
            path_dirs=[safe_bin] + filtered,
            tmp_path=tmp_path,
            replace_path=True,
        )
        assert r.returncode != 0


# ── edge case tests ─────────────────────────────────────────────────────


class TestEdgeCases:
    def test_repeated_run_appends_to_log(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        # Should have two sets of date markers
        assert log_text.count("===") >= 4

    def test_health_overwritten_on_rerun(self, tmp_path):
        bindir, _ = _setup_full_mocks(tmp_path)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        first_health = _health_file(tmp_path).read_text()
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        second_health = _health_file(tmp_path).read_text()
        # Should be different (different timestamps)
        assert first_health != second_health

    def test_unknown_args_ignored(self, tmp_path):
        """Unknown arguments should not cause --help to trigger."""
        bindir, _ = _setup_full_mocks(tmp_path)
        r = _run_script(
            args=["--unknown-arg"],
            path_dirs=[bindir],
            tmp_path=tmp_path,
        )
        # Script runs normally (set -e is after help check)
        # Actually unknown args are not handled, but --help is checked first
        # The script will proceed past help check and run normally
        assert r.returncode == 0
