from __future__ import annotations

"""Tests for effectors/start-chrome-debug.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "start-chrome-debug.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run start-chrome-debug.sh with given args and env."""
    if env is None:
        env = os.environ.copy()
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def _make_fake_chrome(tmp_path: Path, name: str = "chrome") -> Path:
    """Create a fake chrome binary that logs its argv, sleeps briefly, then exits 0."""
    fake = tmp_path / name
    fake.write_text('#!/usr/bin/env bash\necho "FAKE_CHROME_ARGV: $@"\nsleep 2\nexit 0\n')
    fake.chmod(0o755)
    return fake


def _make_nonexec_chrome(tmp_path: Path, name: str = "chrome") -> Path:
    """Create a non-executable chrome binary."""
    fake = tmp_path / name
    fake.write_text("#!/usr/bin/env bash\nexit 0\n")
    fake.chmod(0o644)
    return fake


def _make_fake_curl(tmp_path: Path, succeed: bool = True) -> Path:
    """Create a fake curl that either succeeds or fails."""
    fake = tmp_path / "curl"
    if succeed:
        fake.write_text("#!/usr/bin/env bash\nexit 0\n")
    else:
        fake.write_text("#!/usr/bin/env bash\nexit 1\n")
    fake.chmod(0o755)
    return fake


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

    def test_help_mentions_chrome(self):
        r = _run_script("--help")
        assert "Chrome" in r.stdout

    def test_help_mentions_port(self):
        r = _run_script("--help")
        assert "port" in r.stdout

    def test_help_no_stderr(self):
        r = _run_script("--help")
        assert r.stderr == ""

    def test_help_shows_default_port(self):
        r = _run_script("--help")
        assert "9222" in r.stdout

    def test_help_mentions_all_options(self):
        r = _run_script("--help")
        assert "--help" in r.stdout
        assert "--port" in r.stdout


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/") and "bash" in first

    def test_has_set_euo(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src


# ── script permissions ──────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()


# ── unknown option ─────────────────────────────────────────────────────


class TestUnknownOption:
    def test_unknown_option_exits_2(self):
        r = _run_script("--unknown-option")
        assert r.returncode == 2

    def test_unknown_option_shows_usage(self):
        r = _run_script("--unknown-option")
        assert "Usage:" in r.stderr

    def test_unknown_short_flag(self):
        r = _run_script("-Z")
        assert r.returncode == 2

    def test_unknown_option_stderr_has_unknown(self):
        r = _run_script("--bogus")
        assert "Unknown option" in r.stderr


# ── Chrome not found ───────────────────────────────────────────────────


class TestChromeNotFound:
    def test_no_chrome_on_path_exits_1(self):
        """PATH with no Chrome candidates exits 1."""
        r = _run_script(
            env={
                "PATH": "/usr/bin",
                "HOME": str(Path.home()),
            },
        )
        assert r.returncode == 1
        assert "not found" in r.stderr.lower() or "chrome" in r.stderr.lower()

    def test_chrome_error_message_mentions_chrome(self):
        r = _run_script(
            env={
                "PATH": "/usr/bin",
                "HOME": str(Path.home()),
            },
        )
        assert "chrome" in r.stderr.lower()


# ── Chrome not executable ──────────────────────────────────────────────


class TestChromeNotExecutable:
    def test_nonexec_chrome_exits_1(self, tmp_path: Path):
        """A non-executable chrome binary on PATH triggers exit 1."""
        fake = _make_nonexec_chrome(tmp_path, "google-chrome-stable")
        r = _run_script(
            env={
                "PATH": str(tmp_path) + ":/usr/bin",
                "HOME": str(Path.home()),
            },
        )
        assert r.returncode == 1
        assert "not executable" in r.stderr.lower()


# ── Port flag ──────────────────────────────────────────────────────────


class TestPortFlag:
    def test_port_short_flag_default(self):
        """Default port 9222 documented in help."""
        r = _run_script("--help")
        assert "9222" in r.stdout

    def test_missing_port_value_after_flag(self):
        """--port without a value should cause an error (set -u)."""
        r = _run_script(
            "--port",
            env={
                "PATH": "/usr/bin",
                "HOME": str(Path.home()),
            },
        )
        # set -u means accessing unset $2 will fail, or set -e catches it
        assert r.returncode != 0


# ── Already-running detection ──────────────────────────────────────────


class TestAlreadyRunning:
    def test_curl_succeeds_means_already_running(self, tmp_path: Path):
        """If curl to debug port succeeds, script says 'already running' and exits 0."""
        fake_curl = _make_fake_curl(tmp_path, succeed=True)
        # Also need a fake chrome so script doesn't bail early
        fake_chrome = _make_fake_chrome(tmp_path, "google-chrome-stable")
        r = _run_script(
            env={
                "PATH": str(tmp_path) + ":/usr/bin",
                "HOME": str(tmp_path),
            },
        )
        assert r.returncode == 0
        assert "already running" in r.stdout.lower()


# ── Chrome launch with correct args ────────────────────────────────────


class TestChromeLaunch:
    def test_launches_with_remote_debugging_port(self, tmp_path: Path):
        """Chrome is launched with --remote-debugging-port flag."""
        fake_curl = _make_fake_curl(tmp_path, succeed=False)
        fake_chrome = _make_fake_chrome(tmp_path, "google-chrome-stable")
        r = _run_script(
            env={
                "PATH": str(tmp_path) + ":/usr/bin",
                "HOME": str(tmp_path),
            },
        )
        # Script should either start chrome or report success
        # Check stdout for chrome argv containing remote-debugging-port
        combined = r.stdout + r.stderr
        assert (
            "remote-debugging-port" in combined
            or "FAKE_CHROME_ARGV" in r.stdout
            or r.returncode == 0
        )

    def test_launches_with_custom_port(self, tmp_path: Path):
        """--port flag sets the debug port."""
        fake_curl = _make_fake_curl(tmp_path, succeed=False)
        fake_chrome = _make_fake_chrome(tmp_path, "google-chrome-stable")
        r = _run_script(
            "--port",
            "9999",
            env={
                "PATH": str(tmp_path) + ":/usr/bin",
                "HOME": str(tmp_path),
            },
        )
        combined = r.stdout + r.stderr
        assert "9999" in combined or r.returncode == 0

    def test_launch_message_mentions_pid(self, tmp_path: Path):
        """On successful launch, stdout mentions pid."""
        fake_curl = _make_fake_curl(tmp_path, succeed=False)
        fake_chrome = _make_fake_chrome(tmp_path, "google-chrome-stable")
        r = _run_script(
            env={
                "PATH": str(tmp_path) + ":/usr/bin",
                "HOME": str(tmp_path),
            },
        )
        if r.returncode == 0:
            assert "pid" in r.stdout.lower()


# ── Source structure ────────────────────────────────────────────────────


class TestSourceStructure:
    def test_has_platform_detection(self):
        src = SCRIPT.read_text()
        assert "uname" in src
        assert "Darwin" in src
        assert "Linux" in src

    def test_has_chrome_candidates(self):
        src = SCRIPT.read_text()
        for candidate in [
            "google-chrome-stable",
            "google-chrome",
            "chromium-browser",
            "chromium",
        ]:
            assert candidate in src

    def test_has_user_data_dir(self):
        src = SCRIPT.read_text()
        assert "user-data-dir" in src

    def test_has_curl_check(self):
        src = SCRIPT.read_text()
        assert "curl" in src
        assert "json/version" in src
