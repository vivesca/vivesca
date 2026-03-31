from __future__ import annotations

"""Tests for tmux-osc52.sh — copy tmux pane to clipboard via OSC 52."""

import base64
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "tmux-osc52.sh"


# ── helpers ───────────────────────────────────────────────────────────


def _run(args: list[str], env: dict | None = None, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    """Run the script with given args, capturing output."""
    return subprocess.run(
        ["/usr/bin/bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


def _make_fake_tmux_dir(output: str, use_printf: bool = False) -> tuple[str, str]:
    """Create a temp dir with a fake ``tmux`` that prints *output*.

    Returns ``(dir_path, tmux_path)`` so the caller can prepend to PATH
    and clean up with ``shutil.rmtree``.
    """
    tmp = tempfile.mkdtemp()
    tmux_path = os.path.join(tmp, "tmux")
    cmd = f'printf "%s" "{output}"' if use_printf else f'echo -n "{output}"'
    with open(tmux_path, "w") as f:
        f.write(f"#!/bin/bash\nif [[ $1 == capture-pane ]]; then\n  {cmd}\nfi\n")
    os.chmod(tmux_path, 0o755)
    return tmp, tmux_path


def _env_with_fake_tmux(fake_dir: str) -> dict:
    """Return a copy of os.environ with *fake_dir* first on PATH."""
    e = os.environ.copy()
    e["PATH"] = fake_dir + ":" + e.get("PATH", "")
    return e


def _make_tty() -> str:
    """Create a temp file to use as a fake TTY and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False)
    f.close()
    return f.name


def _read_tty(path: str) -> bytes:
    return open(path, "rb").read()


def _extract_b64(osc_bytes: bytes) -> str:
    """Extract the base64 portion from an OSC 52 sequence."""
    seq = osc_bytes.decode()
    start = seq.index("52;c;") + 5
    end = seq.index("\007", start)
    return seq[start:end]


def _expected_osc52(raw: bytes) -> bytes:
    """Build the expected OSC 52 escape sequence for given raw content."""
    b64 = base64.b64encode(raw).decode().replace("\n", "")
    return f"\033]52;c;{b64}\007".encode()


# ── help flag tests ───────────────────────────────────────────────────


def test_help_flag_short():
    """-h prints usage from the script header and exits 0."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout or "tmux-osc52.sh" in r.stdout


def test_help_flag_long():
    """--help prints usage from the script header and exits 0."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout or "tmux-osc52.sh" in r.stdout


def test_help_prints_lines_2_and_3():
    """Help extracts exactly lines 2-3 of the script."""
    r = _run(["-h"])
    lines = r.stdout.strip().splitlines()
    assert len(lines) == 2
    assert "Copy current tmux pane" in lines[0]
    assert "Usage:" in lines[1]


def test_help_exits_zero_even_with_extra_args():
    """--help exits 0 regardless of additional arguments."""
    r = _run(["--help", "extra", "args"])
    assert r.returncode == 0


# ── normal operation tests ────────────────────────────────────────────


def test_writes_osc52_to_tty():
    """Script writes OSC 52 escape sequence with base64'd pane content to TTY."""
    pane_content = "hello world"
    d, _ = _make_fake_tmux_dir(pane_content)
    tty = _make_tty()
    try:
        r = _run(["test-pane", tty], env=_env_with_fake_tmux(d))
        assert r.returncode == 0, f"stderr: {r.stderr}"
        written = _read_tty(tty)
        expected = _expected_osc52(pane_content.encode())
        assert written == expected, f"got {written!r}, expected {expected!r}"
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)


def test_multiline_content():
    """Multi-line pane content is properly base64'd and written."""
    pane_content = "line1\nline2\nline3"
    d, _ = _make_fake_tmux_dir(pane_content, use_printf=True)
    tty = _make_tty()
    try:
        r = _run(["my-pane", tty], env=_env_with_fake_tmux(d))
        assert r.returncode == 0, f"stderr: {r.stderr}"
        written = _read_tty(tty)
        expected = _expected_osc52(pane_content.encode())
        assert written == expected
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)


def test_empty_pane():
    """Empty pane content still produces a valid OSC 52 sequence."""
    d, _ = _make_fake_tmux_dir("")
    tty = _make_tty()
    try:
        r = _run(["pane0", tty], env=_env_with_fake_tmux(d))
        assert r.returncode == 0, f"stderr: {r.stderr}"
        written = _read_tty(tty)
        expected = _expected_osc52(b"")
        assert written == expected
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)


def test_unicode_and_special_chars():
    """Unicode and special chars in pane content survive the round trip."""
    pane_content = "hello 🌍 café"
    d, _ = _make_fake_tmux_dir(pane_content, use_printf=True)
    tty = _make_tty()
    try:
        r = _run(["%0", tty], env=_env_with_fake_tmux(d))
        assert r.returncode == 0
        written = _read_tty(tty)
        expected = _expected_osc52(pane_content.encode())
        assert written == expected
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)


# ── escape sequence structure tests ───────────────────────────────────


def test_output_starts_with_osc52_escape():
    """Output always begins with ESC ]52;c; and ends with BEL."""
    d, _ = _make_fake_tmux_dir("abc")
    tty = _make_tty()
    try:
        _run(["p", tty], env=_env_with_fake_tmux(d))
        written = _read_tty(tty)
        assert written[:7] == b"\033]52;c;"
        assert written[-1:] == b"\007"
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)


def test_base64_payload_is_valid_chars():
    """Middle portion should be pure base64 characters."""
    d, _ = _make_fake_tmux_dir("test data", use_printf=True)
    tty = _make_tty()
    try:
        _run(["%0", tty], env=_env_with_fake_tmux(d))
        written = _read_tty(tty)
        b64_part = written[7:-1].decode()  # between \033]52;c; and \007
        valid = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
        assert all(c in valid for c in b64_part)
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)


def test_base64_has_no_newlines():
    """The base64 payload must contain no newlines (tr -d '\n')."""
    pane_content = "A" * 200  # enough to trigger base64 line wrapping
    d, _ = _make_fake_tmux_dir(pane_content)
    tty = _make_tty()
    try:
        _run(["p", tty], env=_env_with_fake_tmux(d))
        written = _read_tty(tty)
        payload = written[7:-1].decode()
        assert "\n" not in payload
        assert "\r" not in payload
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)


# ── large content and binary ──────────────────────────────────────────


def test_large_content_base64_no_newlines():
    """Large pane content (>4KB) produces base64 without embedded newlines."""
    long_content = "A" * 10000
    d, _ = _make_fake_tmux_dir(long_content, use_printf=True)
    tty = _make_tty()
    try:
        r = _run(["%0", tty], env=_env_with_fake_tmux(d))
        assert r.returncode == 0
        written = _read_tty(tty)
        b64_part = _extract_b64(written)
        assert "\n" not in b64_part
        decoded = base64.b64decode(b64_part)
        assert decoded == long_content.encode()
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)


def test_null_bytes_roundtrip():
    """Pane output containing null bytes is correctly base64-encoded."""
    d = tempfile.mkdtemp()
    tmux_path = os.path.join(d, "tmux")
    with open(tmux_path, "w") as f:
        f.write('#!/bin/bash\nprintf "before\\x00after"')
    os.chmod(tmux_path, 0o755)
    tty = _make_tty()
    try:
        r = _run(["%0", tty], env=_env_with_fake_tmux(d))
        assert r.returncode == 0
        written = _read_tty(tty)
        b64_part = _extract_b64(written)
        decoded = base64.b64decode(b64_part)
        assert decoded == b"before\x00after"
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)


# ── pane ID passthrough tests ─────────────────────────────────────────


def _make_logging_tmux(log_path: str) -> tuple[str, str]:
    """Create a fake tmux that logs its args and returns 'output'."""
    d = tempfile.mkdtemp()
    tmux_path = os.path.join(d, "tmux")
    with open(tmux_path, "w") as f:
        f.write(f'#!/bin/bash\necho "$@" > {log_path}\necho "output"')
    os.chmod(tmux_path, 0o755)
    return d, tmux_path


def test_passes_pane_id_to_tmux():
    """Script passes the correct pane ID to tmux capture-pane -t."""
    log_path = os.path.join(tempfile.gettempdir(), "tmux_args_test.log")
    d, _ = _make_logging_tmux(log_path)
    tty = _make_tty()
    try:
        r = _run(["%42", tty], env=_env_with_fake_tmux(d))
        assert r.returncode == 0
        logged = open(log_path).read().strip()
        assert "capture-pane" in logged
        assert "-p" in logged
        assert "-t" in logged
        assert "%42" in logged
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)
        if os.path.exists(log_path):
            os.unlink(log_path)


def test_various_pane_id_formats():
    """Script passes different pane ID formats correctly to tmux."""
    log_path = os.path.join(tempfile.gettempdir(), "tmux_pane_ids.log")
    d, _ = _make_logging_tmux(log_path)
    try:
        for pane_id in ["%0", "%99", "session:0.0", "my-session:1.2"]:
            tty = _make_tty()
            try:
                r = _run([pane_id, tty], env=_env_with_fake_tmux(d))
                assert r.returncode == 0, f"Failed for pane_id={pane_id}: {r.stderr}"
                logged = open(log_path).read()
                assert f"-t {pane_id}" in logged, f"pane_id={pane_id} not in: {logged}"
            finally:
                os.unlink(tty)
    finally:
        shutil.rmtree(d, ignore_errors=True)
        if os.path.exists(log_path):
            os.unlink(log_path)


def test_capture_pane_includes_p_flag():
    """Script includes -p flag (print to stdout) in tmux capture-pane."""
    log_path = os.path.join(tempfile.gettempdir(), "tmux_p_flag.log")
    d, _ = _make_logging_tmux(log_path)
    tty = _make_tty()
    try:
        r = _run(["%0", tty], env=_env_with_fake_tmux(d))
        assert r.returncode == 0
        logged = open(log_path).read().strip()
        parts = logged.split()
        assert "capture-pane" in parts
        assert "-p" in parts
        assert "-t" in parts
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)
        if os.path.exists(log_path):
            os.unlink(log_path)


def test_tmux_subcommand_is_capture_pane():
    """Script calls tmux with capture-pane, not other subcommands."""
    log_path = os.path.join(tempfile.gettempdir(), "tmux_subcmd.log")
    d, _ = _make_logging_tmux(log_path)
    tty = _make_tty()
    try:
        _run(["%0", tty], env=_env_with_fake_tmux(d))
        logged = open(log_path).read().strip()
        assert logged.startswith("capture-pane")
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)
        if os.path.exists(log_path):
            os.unlink(log_path)


# ── missing / invalid argument tests ──────────────────────────────────


def test_no_args_fails():
    """Script exits non-zero when called with no arguments."""
    r = _run([])
    # Without args, printf redirect to empty string fails
    assert r.returncode != 0 or r.stderr != ""


def test_missing_tty_arg_fails():
    """Script fails when only pane_id is provided (no TTY path)."""
    d, _ = _make_fake_tmux_dir("hello")
    try:
        r = _run(["%0"], env=_env_with_fake_tmux(d))
        assert r.returncode != 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_nonexistent_tty_path_creates_file():
    """Script creates the TTY file via shell redirect even if it didn't exist."""
    tty_path = os.path.join(tempfile.gettempdir(), "test_osc52_nonexist.tty")
    if os.path.exists(tty_path):
        os.unlink(tty_path)
    d, _ = _make_fake_tmux_dir("hello", use_printf=True)
    try:
        r = _run(["%0", tty_path], env=_env_with_fake_tmux(d))
        assert r.returncode == 0
        assert os.path.exists(tty_path)
        written = _read_tty(tty_path)
        assert written.startswith(b"\033]52;c;")
    finally:
        shutil.rmtree(d, ignore_errors=True)
        if os.path.exists(tty_path):
            os.unlink(tty_path)


# ── missing tmux on PATH ──────────────────────────────────────────────


def test_missing_tmux_writes_empty_osc52():
    """When tmux is not on PATH, script still writes a valid (empty-payload) OSC 52."""
    tty = _make_tty()
    try:
        env = os.environ.copy()
        # Use a PATH directory that definitely has no tmux
        env["PATH"] = tempfile.gettempdir()
        r = _run(["%0", tty], env=env)
        # Script doesn't explicitly fail — DATA is empty, but printf still works
        assert r.returncode == 0
        written = _read_tty(tty)
        # Should still be a valid OSC 52 sequence with empty base64
        assert written.startswith(b"\033]52;c;")
        assert written[-1:] == b"\007"
        # The base64 of empty string
        b64_part = _extract_b64(written)
        assert base64.b64decode(b64_part) == b""
    finally:
        os.unlink(tty)


# ── TTY write behavior tests ──────────────────────────────────────────


def test_tty_file_overwritten_not_appended():
    """Script overwrites (not appends to) the TTY file."""
    d, _ = _make_fake_tmux_dir("new content", use_printf=True)
    tty = _make_tty()
    try:
        # Pre-populate TTY with old data
        with open(tty, "w") as f:
            f.write("old content that is very long")
        r = _run(["%0", tty], env=_env_with_fake_tmux(d))
        assert r.returncode == 0
        written = _read_tty(tty)
        assert b"old content" not in written
        assert written.startswith(b"\033]52;c;")
    finally:
        shutil.rmtree(d, ignore_errors=True)
        os.unlink(tty)


def test_tty_directory_not_file_fails():
    """Script fails when TTY path is a directory."""
    d, _ = _make_fake_tmux_dir("hello")
    with tempfile.TemporaryDirectory() as td:
        try:
            r = _run(["%0", td], env=_env_with_fake_tmux(d))
            assert r.returncode != 0
        finally:
            shutil.rmtree(d, ignore_errors=True)


# ── script structure tests ────────────────────────────────────────────


def test_script_is_executable():
    """Script file has execute permission."""
    assert SCRIPT.exists()
    assert os.access(SCRIPT, os.X_OK)


def test_script_has_bash_shebang():
    """Script starts with #!/bin/bash shebang."""
    first_line = SCRIPT.read_text().splitlines()[0]
    assert first_line == "#!/bin/bash"
