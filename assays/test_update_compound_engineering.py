from __future__ import annotations

"""Tests for effectors/update-compound-engineering — Plugin update script."""

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "update-compound-engineering"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    path_dirs: list[Path] | None = None,
    tmp_path: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run the script with an optional custom PATH."""
    env = os.environ.copy()
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if path_dirs is not None:
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


# ── script structure tests ───────────────────────────────────────────────


class TestScriptStructure:
    def test_script_exists(self):
        """Script file exists."""
        assert SCRIPT.exists()

    def test_script_is_executable(self):
        """Script file is executable."""
        assert os.access(SCRIPT, os.X_OK)

    def test_script_has_shebang(self):
        """Script starts with #!/usr/bin/env bash."""
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line == "#!/usr/bin/env bash"


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

    def test_help_mentions_opencode(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "OpenCode" in r.stdout or "opencode" in r.stdout

    def test_help_mentions_codex(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "Codex" in r.stdout or "codex" in r.stdout

    def test_help_mentions_bunx_or_npx(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "bunx" in r.stdout or "npx" in r.stdout or "bun or node" in r.stdout


# ── runner selection tests ──────────────────────────────────────────────


class TestRunnerSelection:
    def test_no_runner_exits_1(self, tmp_path):
        """Script exits 1 when neither bunx nor npx is on PATH."""
        # Create an isolated environment with empty PATH
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        empty_bin = tmp_path / "bin"
        empty_bin.mkdir()
        # Use env -i to run with clean environment
        r = subprocess.run(
            [
                "env", "-i",
                f"PATH={empty_bin}",
                f"HOME={fake_home}",
                "/bin/bash", str(SCRIPT),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 1

    def test_no_runner_prints_error(self, tmp_path):
        """Script prints error message when no runner found."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        empty_bin = tmp_path / "bin"
        empty_bin.mkdir()
        r = subprocess.run(
            [
                "env", "-i",
                f"PATH={empty_bin}",
                f"HOME={fake_home}",
                "/bin/bash", str(SCRIPT),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "neither bunx nor npx found" in r.stderr.lower() or "bun or node" in r.stderr.lower()

    def test_uses_bunx_when_available(self, tmp_path):
        """bunx on PATH -> uses bunx as runner."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        calls = record.read_text()
        assert "@every-env/compound-plugin" in calls

    def test_uses_npx_when_bunx_missing(self, tmp_path):
        """npx on PATH (no bunx) -> uses npx."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "npx", record)
        # Filter system PATH to remove any dir that contains bunx
        filtered_path = [bindir]
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            if not (Path(dir_path) / "bunx").exists():
                filtered_path.append(Path(dir_path))
        r = _run_script(path_dirs=filtered_path, tmp_path=tmp_path)
        assert r.returncode == 0
        calls = record.read_text()
        assert "@every-env/compound-plugin" in calls

    def test_prefers_bunx_over_npx(self, tmp_path):
        """Both bunx and npx available -> bunx is used."""
        bunx_record = tmp_path / "bunx_calls.log"
        npx_record = tmp_path / "npx_calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", bunx_record)
        _make_recording_bin(tmp_path, "npx", npx_record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert bunx_record.exists() and bunx_record.read_text().strip() != ""
        assert not npx_record.exists() or npx_record.read_text().strip() == ""


# ── update targets tests ────────────────────────────────────────────────


class TestUpdateTargets:
    def test_runs_opencode_update(self, tmp_path):
        """Script runs compound-plugin install --to opencode."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = record.read_text()
        assert "--to opencode" in calls

    def test_runs_codex_update(self, tmp_path):
        """Script runs compound-plugin install --to codex."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = record.read_text()
        assert "--to codex" in calls

    def test_runs_both_updates(self, tmp_path):
        """Script runs both opencode and codex updates."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = record.read_text().strip().splitlines()
        assert len(calls) == 2

    def test_prints_update_message(self, tmp_path):
        """Script prints updating message."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert "Updating" in r.stdout or "updating" in r.stdout.lower()

    def test_prints_complete_message(self, tmp_path):
        """Script prints completion message."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert "complete" in r.stdout.lower() or "done" in r.stdout.lower()


# ── output locations tests ──────────────────────────────────────────────


class TestOutputLocations:
    def test_mentions_opencode_location(self, tmp_path):
        """Script mentions OpenCode config location."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert ".config/opencode" in r.stdout or "opencode" in r.stdout.lower()

    def test_mentions_codex_location(self, tmp_path):
        """Script mentions Codex config location."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert ".codex" in r.stdout or "codex" in r.stdout.lower()
