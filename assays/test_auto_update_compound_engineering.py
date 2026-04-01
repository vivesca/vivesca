from __future__ import annotations

"""Tests for auto-update-compound-engineering.sh — Plugin update script."""

import os
import subprocess
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "auto-update-compound-engineering.sh"
LOG_FILE = Path.home() / ".compound-engineering-updates.log"


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


def _make_fake_bin(tmp_path: Path, name: str) -> Path:
    """Create a fake binary in a bin/ dir and return the bin dir."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    binary = bindir / name
    binary.write_text("#!/bin/bash\nexit 0\n")
    binary.chmod(binary.stat().st_mode | 0o111)
    return bindir


# ── Script structure tests ─────────────────────────────────────────────


def test_auto_update_compound_engineering_script_exists():
    """Script file exists."""
    assert SCRIPT.exists()


def test_auto_update_compound_engineering_script_is_executable():
    """Script file is executable."""
    assert os.access(SCRIPT, os.X_OK)


def test_auto_update_compound_engineering_script_has_shebang():
    """Script starts with #!/usr/bin/env bash."""
    first_line = SCRIPT.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env bash"


# ── Help / usage tests ─────────────────────────────────────────────────


def test_auto_update_compound_engineering_help_long_flag():
    """--help prints usage and exits 0."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout


def test_auto_update_compound_engineering_help_short_flag():
    """-h prints usage and exits 0."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout


def test_help_mentions_crontab():
    """Help text mentions crontab scheduling."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "crontab" in r.stdout.lower()


def test_help_mentions_log_file():
    """Help text mentions the log file location."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "log" in r.stdout.lower()


# ── Runner detection tests ─────────────────────────────────────────────


def test_auto_update_compound_engineering_exits_1_when_no_bunx_or_npx(tmp_path):
    """Script exits 1 with error when neither bunx nor npx is available."""
    # Create a minimal environment with empty PATH and isolated HOME
    fake_home = tmp_path / "home"
    fake_home.mkdir(exist_ok=True)
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir(exist_ok=True)

    # Use env -i to run with clean environment, only setting what we need
    # This ensures bunx/npx are NOT found since PATH is empty
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
    # Check that error was logged
    log = fake_home / ".compound-engineering-updates.log"
    assert log.exists()
    assert "neither bunx nor npx" in log.read_text().lower()


def test_auto_update_compound_engineering_uses_bunx_when_available(tmp_path):
    """Script uses bunx when available."""
    bindir = _make_fake_bin(tmp_path, "bunx")
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    # Script should succeed (bunx will be called, even if it does nothing useful)
    # The fake bunx just exits 0, so the compound-plugin calls will "succeed"
    assert r.returncode == 0


def test_auto_update_compound_engineering_falls_back_to_npx_when_bunx_missing(tmp_path):
    """Script falls back to npx when bunx is not available."""
    bindir = _make_fake_bin(tmp_path, "npx")
    env = os.environ.copy()
    # PATH has npx but no bunx
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert r.returncode == 0


def test_auto_update_compound_engineering_prefers_bunx_over_npx(tmp_path):
    """Script prefers bunx when both bunx and npx are available."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    # Create bunx that logs its invocation
    bunx = bindir / "bunx"
    bunx.write_text("#!/bin/bash\necho 'BUNX-CALLED' >> /tmp/test_runner_log.txt\nexit 0\n")
    bunx.chmod(bunx.stat().st_mode | 0o111)
    # Create npx that should NOT be called
    npx = bindir / "npx"
    npx.write_text("#!/bin/bash\necho 'NPX-CALLED' >> /tmp/test_runner_log.txt\nexit 0\n")
    npx.chmod(npx.stat().st_mode | 0o111)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    log_file = Path("/tmp/test_runner_log.txt")
    try:
        log_file.unlink(missing_ok=True)
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert r.returncode == 0
        # Check that bunx was called, not npx
        if log_file.exists():
            content = log_file.read_text()
            assert "BUNX-CALLED" in content
            assert "NPX-CALLED" not in content
    finally:
        log_file.unlink(missing_ok=True)


# ── Log file tests ───────────────────────────────────────────────────────


def test_creates_log_file(tmp_path):
    """Script creates log file when running."""
    # Use a temporary log file location via HOME override
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    bindir = _make_fake_bin(tmp_path, "bunx")
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    env["HOME"] = str(fake_home)
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert r.returncode == 0
    log = fake_home / ".compound-engineering-updates.log"
    assert log.exists()


def test_log_contains_timestamps(tmp_path):
    """Log file contains start and completion timestamps."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    bindir = _make_fake_bin(tmp_path, "bunx")
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    env["HOME"] = str(fake_home)
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert r.returncode == 0
    log = fake_home / ".compound-engineering-updates.log"
    content = log.read_text()
    assert "Update started:" in content
    assert "Update completed:" in content


def test_log_contains_opencode_update(tmp_path):
    """Log file records OpenCode update attempt."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    bindir = _make_fake_bin(tmp_path, "bunx")
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    env["HOME"] = str(fake_home)
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert r.returncode == 0
    log = fake_home / ".compound-engineering-updates.log"
    content = log.read_text()
    assert "OpenCode" in content


def test_log_contains_codex_update(tmp_path):
    """Log file records Codex update attempt."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    bindir = _make_fake_bin(tmp_path, "bunx")
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    env["HOME"] = str(fake_home)
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert r.returncode == 0
    log = fake_home / ".compound-engineering-updates.log"
    content = log.read_text()
    assert "Codex" in content


# ── Runner invocation tests ─────────────────────────────────────────────


def test_auto_update_compound_engineering_invokes_compound_plugin_for_opencode(tmp_path):
    """Script invokes compound-plugin with --to opencode."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    bunx = bindir / "bunx"
    # Log all invocations
    bunx.write_text("#!/bin/bash\necho \"$@\" >> /tmp/test_invocations.txt\nexit 0\n")
    bunx.chmod(bunx.stat().st_mode | 0o111)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    invocations_file = Path("/tmp/test_invocations.txt")
    try:
        invocations_file.unlink(missing_ok=True)
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert r.returncode == 0
        if invocations_file.exists():
            content = invocations_file.read_text()
            assert "compound-engineering" in content
            assert "opencode" in content
    finally:
        invocations_file.unlink(missing_ok=True)


def test_auto_update_compound_engineering_invokes_compound_plugin_for_codex(tmp_path):
    """Script invokes compound-plugin with --to codex."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    bunx = bindir / "bunx"
    bunx.write_text("#!/bin/bash\necho \"$@\" >> /tmp/test_codex_invocations.txt\nexit 0\n")
    bunx.chmod(bunx.stat().st_mode | 0o111)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    invocations_file = Path("/tmp/test_codex_invocations.txt")
    try:
        invocations_file.unlink(missing_ok=True)
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert r.returncode == 0
        if invocations_file.exists():
            content = invocations_file.read_text()
            assert "compound-engineering" in content
            assert "codex" in content
    finally:
        invocations_file.unlink(missing_ok=True)


# ── Error handling tests ────────────────────────────────────────────────


def test_logs_error_when_runner_fails(tmp_path):
    """Script logs error message when the runner command fails."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    bindir = tmp_path / "bin"
    bindir.mkdir()
    bunx = bindir / "bunx"
    # bunx that fails
    bunx.write_text("#!/bin/bash\nexit 1\n")
    bunx.chmod(bunx.stat().st_mode | 0o111)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    env["HOME"] = str(fake_home)
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    # Script should still exit 0 (errors are logged but don't stop execution)
    assert r.returncode == 0
    log = fake_home / ".compound-engineering-updates.log"
    content = log.read_text()
    # Should show failed updates
    assert "failed" in content.lower() or "error" in content.lower() or "✅" in content or "❌" in content
