from __future__ import annotations

"""Tests for update-compound-engineering — Interactive plugin update script."""

import os
import subprocess
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "update-compound-engineering"


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


def test_update_compound_engineering_script_exists():
    """Script file exists."""
    assert SCRIPT.exists()


def test_update_compound_engineering_script_is_executable():
    """Script file is executable."""
    assert os.access(SCRIPT, os.X_OK)


def test_update_compound_engineering_script_has_shebang():
    """Script starts with #!/usr/bin/env bash."""
    first_line = SCRIPT.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env bash"


# ── Help / usage tests ─────────────────────────────────────────────────


def test_update_compound_engineering_help_long_flag():
    """--help prints usage and exits 0."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout


def test_update_compound_engineering_help_short_flag():
    """-h prints usage and exits 0."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout


def test_help_mentions_opencode():
    """Help text mentions OpenCode."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "OpenCode" in r.stdout


def test_help_mentions_codex():
    """Help text mentions Codex."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Codex" in r.stdout


def test_help_mentions_requirements():
    """Help text mentions bunx or npx requirement."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "bunx" in r.stdout or "npx" in r.stdout or "bun" in r.stdout or "node" in r.stdout


# ── Runner detection tests ─────────────────────────────────────────────


def test_update_compound_engineering_exits_1_when_no_bunx_or_npx(tmp_path):
    """Script exits 1 with error when neither bunx nor npx is available."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()

    r = subprocess.run(
        [
            "env",
            "-i",
            f"PATH={empty_bin}",
            f"HOME={fake_home}",
            "/bin/bash",
            str(SCRIPT),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert r.returncode == 1
    assert "neither bunx nor npx" in r.stderr.lower() or "neither bunx nor npx" in r.stdout.lower()


def test_update_compound_engineering_uses_bunx_when_available(tmp_path):
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
    assert r.returncode == 0


def test_update_compound_engineering_falls_back_to_npx_when_bunx_missing(tmp_path):
    """Script falls back to npx when bunx is not available."""
    bindir = _make_fake_bin(tmp_path, "npx")
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:/bin:/usr/bin"
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert r.returncode == 0


def test_update_compound_engineering_prefers_bunx_over_npx(tmp_path):
    """Script prefers bunx when both bunx and npx are available."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    bunx = bindir / "bunx"
    bunx.write_text("#!/bin/bash\necho 'BUNX-CALLED' >> /tmp/test_runner_log.txt\nexit 0\n")
    bunx.chmod(bunx.stat().st_mode | 0o111)
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
        if log_file.exists():
            content = log_file.read_text()
            assert "BUNX-CALLED" in content
            assert "NPX-CALLED" not in content
    finally:
        log_file.unlink(missing_ok=True)


# ── Output tests ───────────────────────────────────────────────────────


def test_output_shows_updating_message():
    """Script shows updating message on stdout."""
    r = _run()
    assert "Updating" in r.stdout or "updating" in r.stdout.lower()


def test_output_mentions_opencode():
    """Script mentions OpenCode in output."""
    r = _run()
    assert "OpenCode" in r.stdout


def test_output_mentions_codex(tmp_path):
    """Script mentions Codex in output."""
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
    assert "Codex" in r.stdout


def test_output_shows_complete_message(tmp_path):
    """Script shows completion message."""
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
    assert "complete" in r.stdout.lower() or "done" in r.stdout.lower() or "✅" in r.stdout


# ── Runner invocation tests ─────────────────────────────────────────────


def test_update_compound_engineering_invokes_compound_plugin_for_opencode(tmp_path):
    """Script invokes compound-plugin with --to opencode."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    bunx = bindir / "bunx"
    bunx.write_text('#!/bin/bash\necho "$@" >> /tmp/test_invocations.txt\nexit 0\n')
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


def test_update_compound_engineering_invokes_compound_plugin_for_codex(tmp_path):
    """Script invokes compound-plugin with --to codex."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    bunx = bindir / "bunx"
    bunx.write_text('#!/bin/bash\necho "$@" >> /tmp/test_codex_invocations.txt\nexit 0\n')
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


def test_error_message_on_missing_runner(tmp_path):
    """Script prints error message when no runner is available."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()

    r = subprocess.run(
        [
            "env",
            "-i",
            f"PATH={empty_bin}",
            f"HOME={fake_home}",
            "/bin/bash",
            str(SCRIPT),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert r.returncode == 1
    combined = r.stdout + r.stderr
    assert "error" in combined.lower()
    assert "bunx" in combined.lower() or "npx" in combined.lower()
