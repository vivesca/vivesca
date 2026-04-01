#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/tmux-url-select.sh — tmux URL selector + OSC 52 copier."""

import base64
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

EFFECTOR = Path(__file__).resolve().parents[1] / "effectors" / "tmux-url-select.sh"
BUFFER = Path("/tmp/tmux-url-select-test-buffer")
FAKE_BIN_DIR: Path | None = None


@pytest.fixture(autouse=True)
def _setup_fake_bins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Create fake fzf and tmux binaries; point PATH at them."""
    global FAKE_BIN_DIR
    FAKE_BIN_DIR = tmp_path / "fakebin"
    FAKE_BIN_DIR.mkdir()

    # fake fzf: select first line of stdin (simulates user picking top entry)
    (FAKE_BIN_DIR / "fzf").write_text("#!/usr/bin/env bash\nhead -1\n")
    (FAKE_BIN_DIR / "fzf").chmod(0o755)

    # fake tmux: log all invocations
    log_file = tmp_path / "tmux-calls.log"
    (FAKE_BIN_DIR / "tmux").write_text(
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" >> {log_file}\n"
    )
    (FAKE_BIN_DIR / "tmux").chmod(0o755)

    # Prepend fake bin dir to PATH
    real_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", f"{FAKE_BIN_DIR}:{real_path}")

    # Override buffer path via symlinking — script hardcodes /tmp/tmux-url-buffer
    # We'll manage that file directly in tests, restoring after.
    old_buffer = Path("/tmp/tmux-url-buffer")
    old_exists = old_buffer.exists()
    old_content = old_buffer.read_bytes() if old_exists else b""

    yield  # test runs

    # Restore original buffer
    if old_exists:
        old_buffer.write_bytes(old_content)
    elif old_buffer.exists():
        old_buffer.unlink()


def _run(args: list[str] | None = None, stdin_data: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run the effector script via subprocess."""
    cmd = ["bash", str(EFFECTOR)]
    if args:
        cmd.extend(args)
    return subprocess.run(
        cmd,
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=5,
    )


def _write_buffer(content: str) -> None:
    Path("/tmp/tmux-url-buffer").write_text(content)


def _read_tmux_calls(tmp_path: Path) -> list[str]:
    log = tmp_path / "tmux-calls.log"
    if not log.exists():
        return []
    return log.read_text().strip().splitlines()


# ── File basics ──────────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert EFFECTOR.exists()
        assert EFFECTOR.is_file()

    def test_is_bash_script(self):
        first_line = EFFECTOR.read_text().split("\n")[0]
        assert first_line.startswith("#!/usr/bin/env bash")

    def test_is_executable(self):
        assert os.access(EFFECTOR, os.X_OK)

    def test_has_set_strict_mode(self):
        src = EFFECTOR.read_text()
        assert "set -euo pipefail" in src


# ── --help flag ──────────────────────────────────────────────────────────────


class TestHelp:
    def test_help_long_flag(self):
        r = _run(["--help"])
        assert r.returncode == 0
        assert "Usage:" in r.stdout
        assert "tmux-url-select.sh" in r.stdout

    def test_help_short_flag(self):
        r = _run(["-h"])
        assert r.returncode == 0
        assert "Usage:" in r.stdout

    def test_help_mentions_fzf(self):
        r = _run(["--help"])
        assert "fzf" in r.stdout

    def test_help_mentions_osc52(self):
        r = _run(["--help"])
        assert "OSC 52" in r.stdout or "clipboard" in r.stdout.lower()


# ── No URLs found ────────────────────────────────────────────────────────────


class TestNoURLs:
    def test_empty_buffer_exits_nonzero(self):
        """grep returns 1 on no match → script exits due to set -e."""
        _write_buffer("")
        r = _run()
        # With set -e, grep returning 1 causes script exit
        assert r.returncode != 0

    def test_buffer_with_no_urls(self):
        _write_buffer("just some plain text without any links")
        r = _run()
        assert r.returncode != 0  # grep finds no match → set -e exit

    def test_missing_buffer_file(self):
        buf = Path("/tmp/tmux-url-buffer")
        if buf.exists():
            buf.unlink()
        r = _run()
        assert r.returncode != 0  # file doesn't exist → grep error


# ── URL extraction ───────────────────────────────────────────────────────────


class TestURLExtraction:
    def test_single_url_selected(self, tmp_path: Path):
        _write_buffer("visit https://example.com today\n")
        r = _run()
        assert r.returncode == 0

    def test_osc52_emitted(self, tmp_path: Path):
        _write_buffer("visit https://example.com today\n")
        r = _run()
        # OSC 52 escape sequence: \033]52;c;<base64>\a
        assert "52;c;" in r.stdout
        assert "\a" in r.stdout or r.stdout.endswith("\x07") or "\x1b" in r.stdout

    def test_osc52_base64_correct(self, tmp_path: Path):
        url = "https://example.com"
        _write_buffer(f"visit {url} today\n")
        r = _run()
        # Extract base64 between "52;c;" and ESC-bell
        output = r.stdout
        idx = output.index("52;c;") + len("52;c;")
        end = output.index("\x07", idx)
        b64 = output[idx:end]
        decoded = base64.b64decode(b64).decode()
        assert decoded == url

    def test_deduplication(self, tmp_path: Path):
        """Duplicate URLs should be deduplicated by awk."""
        _write_buffer("see https://dup.com and https://dup.com again\n")
        r = _run()
        assert r.returncode == 0
        # fake fzf selects first line → the only URL after dedup
        b64_part = r.stdout.split("52;c;")[1].split("\x07")[0]
        decoded = base64.b64decode(b64_part).decode()
        assert decoded == "https://dup.com"

    def test_multiple_unique_urls_first_selected(self, tmp_path: Path):
        _write_buffer("links: https://first.com https://second.com\n")
        r = _run()
        assert r.returncode == 0
        b64_part = r.stdout.split("52;c;")[1].split("\x07")[0]
        decoded = base64.b64decode(b64_part).decode()
        # fake fzf returns first line (first URL)
        assert decoded == "https://first.com"

    def test_tmux_display_message_called(self, tmp_path: Path):
        _write_buffer("visit https://example.com now\n")
        _run()
        calls = _read_tmux_calls(tmp_path)
        assert any("display-message" in c for c in calls)

    def test_tmux_message_contains_url(self, tmp_path: Path):
        _write_buffer("visit https://my-site.org/page?q=1 now\n")
        _run()
        calls = _read_tmux_calls(tmp_path)
        assert any("https://my-site.org/page?q=1" in c for c in calls)

    def test_url_with_query_params(self, tmp_path: Path):
        url = "https://host.com/path?key=val&other=2"
        _write_buffer(f"check {url}\n")
        r = _run()
        assert r.returncode == 0
        b64_part = r.stdout.split("52;c;")[1].split("\x07")[0]
        decoded = base64.b64decode(b64_part).decode()
        assert decoded == url

    def test_url_with_fragment(self, tmp_path: Path):
        url = "https://docs.example.com/section#anchor"
        _write_buffer(f"see {url}\n")
        r = _run()
        assert r.returncode == 0
        b64_part = r.stdout.split("52;c;")[1].split("\x07")[0]
        decoded = base64.b64decode(b64_part).decode()
        assert decoded == url

    def test_http_url(self, tmp_path: Path):
        """http:// URLs should also be extracted."""
        _write_buffer("legacy http://old.example.com\n")
        r = _run()
        assert r.returncode == 0
        b64_part = r.stdout.split("52;c;")[1].split("\x07")[0]
        decoded = base64.b64decode(b64_part).decode()
        assert decoded == "http://old.example.com"

    def test_url_stops_at_angle_bracket(self, tmp_path: Path):
        """URL extraction should stop at > character."""
        _write_buffer('<a href="https://example.com">link</a>\n')
        r = _run()
        assert r.returncode == 0
        b64_part = r.stdout.split("52;c;")[1].split("\x07")[0]
        decoded = base64.b64decode(b64_part).decode()
        assert decoded == "https://example.com"

    def test_url_stops_at_paren(self, tmp_path: Path):
        """URL extraction should stop at ) character."""
        _write_buffer("see (https://example.com) for info\n")
        r = _run()
        assert r.returncode == 0
        b64_part = r.stdout.split("52;c;")[1].split("\x07")[0]
        decoded = base64.b64decode(b64_part).decode()
        assert decoded == "https://example.com"


# ── fzf selection: no selection ──────────────────────────────────────────────


class TestFzfNoSelection:
    def test_fzf_returns_empty_no_osc52(self, tmp_path: Path):
        """If fzf returns nothing, no OSC 52 or tmux call should happen."""
        _write_buffer("visit https://example.com\n")
        # Replace fzf with one that outputs nothing
        fake_fzf = FAKE_BIN_DIR / "fzf"
        fake_fzf.write_text("#!/usr/bin/env bash\ntrue\n")
        fake_fzf.chmod(0o755)
        r = _run()
        assert r.returncode == 0
        assert "52;c;" not in r.stdout
        calls = _read_tmux_calls(tmp_path)
        assert len(calls) == 0

    def test_fzf_returns_empty_no_tmux(self, tmp_path: Path):
        _write_buffer("visit https://example.com\n")
        fake_fzf = FAKE_BIN_DIR / "fzf"
        fake_fzf.write_text("#!/usr/bin/env bash\ntrue\n")
        fake_fzf.chmod(0o755)
        _run()
        calls = _read_tmux_calls(tmp_path)
        assert not any("display-message" in c for c in calls)
