from __future__ import annotations

"""Tests for start-chrome-debug.sh — Chrome remote-debugging launcher."""

import os
import stat
import subprocess
import textwrap
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "start-chrome-debug.sh"


def _run(args: list[str] | None = None, **kwargs) -> subprocess.CompletedProcess:
    """Run the script with optional args, capturing output."""
    cmd = ["bash", str(SCRIPT)]
    if args:
        cmd.extend(args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=10,
        **kwargs,
    )


def _make_fake_chrome(tmp_path: Path, name: str = "google-chrome-stable") -> Path:
    """Create a fake Chrome binary in a bin/ dir and return the bin dir."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    chrome = bindir / name
    chrome.write_text("#!/bin/bash\n# fake chrome for testing\necho 'chrome-launched'\n")
    chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_fake_chrome_that_serves_port(tmp_path: Path, port: int = 9222) -> Path:
    """Create a fake Chrome that serves a minimal /json/version endpoint."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    chrome = bindir / "google-chrome-stable"
    # Start a tiny HTTP server in the background that responds to /json/version
    chrome.write_text(textwrap.dedent(f"""\
        #!/bin/bash
        # Fake chrome: start a background listener on the debug port
        while true; do
            echo -e "HTTP/1.1 200 OK\\r\\nContent-Length: 2\\r\\n\\r\\n{{}}" | nc -l -p {port} -q 0 >/dev/null 2>&1 &
            sleep 0.2
        done &
        echo "chrome-launched port={port}"
    """))
    chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)
    return bindir


# ── Help / usage tests ─────────────────────────────────────────────────


def test_help_long_flag():
    """--help prints usage and exits 0."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "--port" in r.stdout
    assert "9222" in r.stdout


def test_help_short_flag():
    """-h prints usage and exits 0."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout


# ── Argument parsing tests ─────────────────────────────────────────────


def test_unknown_option_exits_2():
    """Unknown flag prints error to stderr and exits 2."""
    r = _run(["--bogus"])
    assert r.returncode == 2
    assert "Unknown option" in r.stderr
    assert "Usage:" in r.stderr


def test_port_option_requires_value():
    """--port without a value causes argument error."""
    r = _run(["--port"])
    # bash shifts past end of args — set -euo pipefail should cause failure
    assert r.returncode != 0


def test_custom_port_accepted():
    """Script accepts --port with a custom value (fails later at Chrome detection)."""
    r = _run(["--port", "9999"])
    # Will fail because no Chrome, but should NOT fail on arg parsing
    assert r.returncode != 0
    # Should not mention "Unknown option"
    assert "Unknown option" not in r.stderr


def test_port_short_flag_accepted():
    """Script accepts -p as short form of --port."""
    r = _run(["-p", "8080"])
    assert r.returncode != 0  # fails later at Chrome detection
    assert "Unknown option" not in r.stderr


# ── Chrome binary detection tests ──────────────────────────────────────


def test_no_chrome_found_exits_1():
    """When no Chrome binary is on PATH, exits 1 with error message."""
    r = _run(["--help"])  # just confirm script is runnable
    assert r.returncode == 0

    # Now run with minimal PATH (no chrome, but keep bash/uname/etc.)
    env = os.environ.copy()
    env["PATH"] = "/bin:/usr/bin"
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert r.returncode == 1
    assert "Chrome" in r.stderr or "not found" in r.stderr


def test_fake_chrome_detected_via_path(tmp_path):
    """Script detects fake Chrome when its dir is on PATH."""
    bindir = _make_fake_chrome(tmp_path)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    # Will launch Chrome (which exits immediately) → "failed to start" error
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    # Either Chrome "started" (unlikely with instant-exit fake) or failed
    # We just verify the script got past the "not found" check
    assert "Chrome/Chromium not found" not in r.stderr


def test_chromium_fallback(tmp_path):
    """Script finds 'chromium' if google-chrome-stable is absent."""
    bindir = _make_fake_chrome(tmp_path, name="chromium")
    env = os.environ.copy()
    # Only include our bindir plus system dirs (no real chrome)
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert "Chrome/Chromium not found" not in r.stderr


def test_chromium_browser_fallback(tmp_path):
    """Script finds 'chromium-browser' if others are absent."""
    bindir = _make_fake_chrome(tmp_path, name="chromium-browser")
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert "Chrome/Chromium not found" not in r.stderr


def test_google_chrome_fallback(tmp_path):
    """Script finds 'google-chrome' if others are absent."""
    bindir = _make_fake_chrome(tmp_path, name="google-chrome")
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert "Chrome/Chromium not found" not in r.stderr


# ── Already-running detection tests ────────────────────────────────────


def test_detects_already_running_on_port(tmp_path):
    """Script exits 0 when curl localhost:PORT/json/version succeeds."""
    bindir = _make_fake_chrome(tmp_path)
    # Also create a fake 'curl' that succeeds
    curl = bindir / "curl"
    curl.write_text("#!/bin/bash\n# fake curl that always succeeds\nexit 0\n")
    curl.chmod(curl.stat().st_mode | stat.S_IEXEC)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert r.returncode == 0
    assert "already running" in r.stdout.lower()


def test_already_running_with_custom_port(tmp_path):
    """Script checks the correct port when --port is given."""
    bindir = _make_fake_chrome(tmp_path)
    # Fake curl that checks which port was requested
    curl = bindir / "curl"
    curl.write_text(textwrap.dedent("""\
        #!/bin/bash
        # Verify we're called with port 8080
        if echo "$@" | grep -q "8080"; then
            exit 0
        fi
        exit 1
    """))
    curl.chmod(curl.stat().st_mode | stat.S_IEXEC)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    r = subprocess.run(
        ["bash", str(SCRIPT), "--port", "8080"],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert r.returncode == 0
    assert "already running" in r.stdout.lower()
    assert "8080" in r.stdout


# ── Chrome launch tests ────────────────────────────────────────────────


def test_chrome_launch_passes_debug_port(tmp_path):
    """Script passes --remote-debugging-port to Chrome binary."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    chrome = bindir / "google-chrome-stable"
    # Chrome that logs its args and sleeps briefly
    chrome.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "ARGS: $@" > /tmp/test_chrome_args.txt
        sleep 2
    """))
    chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)
    # Fake curl that fails (no existing Chrome)
    curl = bindir / "curl"
    curl.write_text("#!/bin/bash\nexit 1\n")
    curl.chmod(curl.stat().st_mode | stat.S_IEXEC)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    try:
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert r.returncode == 0
        assert "Chrome started" in r.stdout
        assert "9222" in r.stdout
        # Check args log
        args_log = Path("/tmp/test_chrome_args.txt")
        if args_log.exists():
            args = args_log.read_text()
            assert "--remote-debugging-port=9222" in args
            assert "--user-data-dir=" in args
    finally:
        Path("/tmp/test_chrome_args.txt").unlink(missing_ok=True)


def test_chrome_launch_custom_port(tmp_path):
    """Script passes custom --remote-debugging-port when --port is set."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    chrome = bindir / "google-chrome-stable"
    chrome.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "ARGS: $@" > /tmp/test_chrome_custom_port.txt
        sleep 2
    """))
    chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)
    curl = bindir / "curl"
    curl.write_text("#!/bin/bash\nexit 1\n")
    curl.chmod(curl.stat().st_mode | stat.S_IEXEC)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    try:
        r = subprocess.run(
            ["bash", str(SCRIPT), "--port", "9333"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert r.returncode == 0
        assert "9333" in r.stdout
        args_log = Path("/tmp/test_chrome_custom_port.txt")
        if args_log.exists():
            assert "--remote-debugging-port=9333" in args_log.read_text()
    finally:
        Path("/tmp/test_chrome_custom_port.txt").unlink(missing_ok=True)


def test_chrome_launch_includes_connect_url(tmp_path):
    """Script prints connect URL after successful launch."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    chrome = bindir / "google-chrome-stable"
    chrome.write_text("#!/bin/bash\nsleep 2\n")
    chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)
    curl = bindir / "curl"
    curl.write_text("#!/bin/bash\nexit 1\n")
    curl.chmod(curl.stat().st_mode | stat.S_IEXEC)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert r.returncode == 0
    assert "Connect via:" in r.stdout
    assert "http://localhost:9222" in r.stdout


# ── Chrome immediate-exit test ─────────────────────────────────────────


def test_chrome_exits_immediately(tmp_path):
    """Script exits 1 when Chrome process dies immediately."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    chrome = bindir / "google-chrome-stable"
    # Chrome that exits immediately
    chrome.write_text("#!/bin/bash\nexit 0\n")
    chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)
    curl = bindir / "curl"
    curl.write_text("#!/bin/bash\nexit 1\n")
    curl.chmod(curl.stat().st_mode | stat.S_IEXEC)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert r.returncode == 1
    assert "failed to start" in r.stderr.lower()


# ── Script structure tests ─────────────────────────────────────────────


def test_script_is_executable():
    """Script file exists and is executable."""
    assert SCRIPT.exists()
    assert os.access(SCRIPT, os.X_OK)


def test_script_has_shebang():
    """Script starts with #!/bin/bash."""
    first_line = SCRIPT.read_text().splitlines()[0]
    assert first_line == "#!/bin/bash"


def test_script_uses_strict_mode():
    """Script uses set -euo pipefail."""
    content = SCRIPT.read_text()
    assert "set -euo pipefail" in content


def test_usage_mentions_port_default():
    """Usage text documents default port 9222."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "9222" in r.stdout


def test_usage_mentions_help_option():
    """Usage text documents -h/--help options."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "--help" in r.stdout
    assert "-h" in r.stdout
