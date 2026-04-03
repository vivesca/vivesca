from __future__ import annotations

"""Tests for effectors/tmux-osc52.sh — bash script tested via subprocess."""

import base64
import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "tmux-osc52.sh"


def _run(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


# ── help flag ───────────────────────────────────────────────────────────
class TestHelp:
    def test_help_exits_zero(self):
        r = _run("--help")
        assert r.returncode == 0

    def test_help_short_flag_exits_zero(self):
        r = _run("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_tmux(self):
        r = _run("--help")
        assert "tmux" in r.stdout

    def test_help_mentions_osc52(self):
        r = _run("--help")
        assert "OSC 52" in r.stdout

    def test_help_no_stderr(self):
        r = _run("--help")
        assert r.stderr == ""


# ── file basics ────────────────────────────────────────────────────────
class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/bin/bash")


# ── script permissions ──────────────────────────────────────────────────
class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()


# ── missing arguments ──────────────────────────────────────────────────
class TestMissingArgs:
    def test_no_args_nonzero_exit(self):
        """Without pane_id and tty the script should fail."""
        r = _run()
        assert r.returncode != 0

    def test_only_pane_id_nonzero_exit(self):
        """Only pane_id, no tty — printf redirect to empty path fails."""
        r = _run("%0")
        assert r.returncode != 0


# ── functional: mocked tmux + real tty file ────────────────────────────
class TestFunctional:
    @pytest.fixture()
    def fake_tmux_dir(self, tmp_path: Path):
        """Create a fake ``tmux`` that prints deterministic pane content."""
        fake = tmp_path / "tmux"
        fake.write_text("#!/bin/bash\necho 'hello pane'\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        return tmp_path

    @pytest.fixture()
    def tty_file(self, tmp_path: Path) -> Path:
        """A temp file that stands in for a TTY device."""
        return tmp_path / "tty"

    def _run_with_mock(
        self,
        pane: str,
        tty: Path,
        fake_tmux_dir: Path,
    ) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["PATH"] = str(fake_tmux_dir) + ":" + env.get("PATH", "/usr/bin:/bin")
        return _run(pane, str(tty), env=env)

    def test_writes_to_tty_file(self, fake_tmux_dir, tty_file):
        self._run_with_mock("%0", tty_file, fake_tmux_dir)
        assert tty_file.exists()
        content = tty_file.read_bytes()
        assert len(content) > 0

    def test_output_starts_with_osc52_escape(self, fake_tmux_dir, tty_file):
        self._run_with_mock("%0", tty_file, fake_tmux_dir)
        raw = tty_file.read_bytes()
        # OSC 52 sequence: ESC ] 52 ; c ; <base64> BEL
        assert raw[:4] == b"\x1b]52"
        assert raw[4:6] == b";c"

    def test_output_ends_with_bell(self, fake_tmux_dir, tty_file):
        self._run_with_mock("%0", tty_file, fake_tmux_dir)
        raw = tty_file.read_bytes()
        assert raw[-1:] == b"\x07"  # BEL character

    def test_base64_payload_roundtrips(self, fake_tmux_dir, tty_file):
        self._run_with_mock("%0", tty_file, fake_tmux_dir)
        raw = tty_file.read_bytes()
        # Extract between ";c;" and BEL
        payload = raw.split(b";c;", 1)[1].rstrip(b"\x07")
        decoded = base64.b64decode(payload).decode()
        assert decoded.strip() == "hello pane"

    def test_exit_code_zero_on_success(self, fake_tmux_dir, tty_file):
        r = self._run_with_mock("%0", tty_file, fake_tmux_dir)
        assert r.returncode == 0

    def test_no_stdout_on_success(self, fake_tmux_dir, tty_file):
        r = self._run_with_mock("%0", tty_file, fake_tmux_dir)
        assert r.stdout == ""

    def test_no_stderr_on_success(self, fake_tmux_dir, tty_file):
        r = self._run_with_mock("%0", tty_file, fake_tmux_dir)
        assert r.stderr == ""


# ── edge cases ──────────────────────────────────────────────────────────
class TestEdgeCases:
    @pytest.fixture()
    def fake_tmux_dir(self, tmp_path: Path):
        """Create a fake ``tmux`` that prints deterministic pane content."""
        fake = tmp_path / "tmux"
        fake.write_text("#!/bin/bash\necho 'hello pane'\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        return tmp_path

    @pytest.fixture()
    def tty_file(self, tmp_path: Path) -> Path:
        return tmp_path / "tty"

    def _run_with_mock(
        self,
        pane: str,
        tty: Path,
        fake_tmux_dir: Path,
    ) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["PATH"] = str(fake_tmux_dir) + ":" + env.get("PATH", "/usr/bin:/bin")
        return _run(pane, str(tty), env=env)

    def test_empty_pane_content(self, tmp_path, tty_file):
        """Fake tmux outputs nothing — OSC 52 sequence still written with empty payload."""
        fake = tmp_path / "tmux"
        fake.write_text("#!/bin/bash\ntrue\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        r = self._run_with_mock("%0", tty_file, tmp_path)
        assert r.returncode == 0
        raw = tty_file.read_bytes()
        assert raw[:4] == b"\x1b]52"
        assert raw[-1:] == b"\x07"

    def test_multiline_pane_roundtrips(self, tmp_path, tty_file):
        """Multiline pane content survives base64 round-trip."""
        fake = tmp_path / "tmux"
        fake.write_text("#!/bin/bash\necho 'line1\nline2\nline3'\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self._run_with_mock("%0", tty_file, tmp_path)
        raw = tty_file.read_bytes()
        payload = raw.split(b";c;", 1)[1].rstrip(b"\x07")
        decoded = base64.b64decode(payload).decode()
        assert "line1" in decoded
        assert "line2" in decoded
        assert "line3" in decoded

    def test_special_chars_in_pane(self, tmp_path, tty_file):
        """Pane content with unicode survives the OSC 52 pipeline."""
        content = "hello café ☕ naïve"
        fake = tmp_path / "tmux"
        # Write content to a file and cat it to avoid shell quoting issues
        data_file = tmp_path / "pane_data.txt"
        data_file.write_text(content + "\n")
        fake.write_text(f"#!/bin/bash\ncat '{data_file}'\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self._run_with_mock("%0", tty_file, tmp_path)
        raw = tty_file.read_bytes()
        payload = raw.split(b";c;", 1)[1].rstrip(b"\x07")
        decoded = base64.b64decode(payload).decode()
        assert "café" in decoded
        assert "naïve" in decoded

    def test_base64_payload_has_no_newlines(self, fake_tmux_dir, tty_file):
        """The tr -d '\\n' ensures no newlines in the base64 payload."""
        self._run_with_mock("%0", tty_file, fake_tmux_dir)
        raw = tty_file.read_bytes()
        payload = raw.split(b";c;", 1)[1].rstrip(b"\x07")
        assert b"\n" not in payload


# ── tmux invocation flags ───────────────────────────────────────────────
class TestTmuxFlags:
    def test_tmux_called_with_capture_pane_flags(self, tmp_path):
        """Verify tmux is invoked with capture-pane -p -t <pane>."""
        tty_file = tmp_path / "tty"
        args_file = tmp_path / "tmux_args.txt"
        fake = tmp_path / "tmux"
        fake.write_text(f"#!/bin/bash\necho \"$@\" > {args_file}\nexit 0\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        env = os.environ.copy()
        env["PATH"] = str(tmp_path) + ":" + env.get("PATH", "/usr/bin:/bin")
        _run("mypane42", str(tty_file), env=env)
        args = args_file.read_text().strip()
        assert "capture-pane" in args
        assert "-p" in args
        assert "-t" in args
        assert "mypane42" in args


# ── help content accuracy ───────────────────────────────────────────────
class TestHelpContent:
    def test_help_matches_script_header_lines(self):
        """--help outputs exactly lines 2–3 of the script (the usage comment)."""
        script_lines = SCRIPT.read_text().splitlines()
        r = _run("--help")
        help_lines = r.stdout.strip().splitlines()
        assert help_lines == script_lines[1:3]
