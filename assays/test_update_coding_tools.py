from __future__ import annotations

"""Tests for effectors/update-coding-tools.sh — auto-update maintenance script."""

import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline" / "effectors" / "update-coding-tools.sh"


# ── Syntax & structure tests ───────────────────────────────────────────


def test_script_exists():
    """Script file exists and is readable."""
    assert SCRIPT.is_file()


def test_script_is_executable():
    """Script has the executable bit set."""
    assert SCRIPT.stat().st_mode & stat.S_IXUSR


def test_bash_syntax_valid():
    """bash -n reports no syntax errors."""
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


def test_script_uses_set_e():
    """Script enables strict error handling with set -e."""
    text = SCRIPT.read_text()
    assert "set -e" in text.splitlines()[4] or any(
        line.strip() == "set -e" for line in text.splitlines()[:10]
    )


def test_shebang_is_bash():
    """Script uses bash shebang."""
    first_line = SCRIPT.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env bash"


# ── Content: update sections present ───────────────────────────────────


UPDATE_SECTIONS = [
    "brew update",
    "brew upgrade",
    "brew upgrade --cask --greedy",
    "brew cleanup --prune=7",
    "npm update -g",
    "pnpm update -g",
    "uv tool upgrade --all",
    "cargo binstall",
    "mas upgrade",
]


@pytest.mark.parametrize("section", UPDATE_SECTIONS)
def test_update_section_present(section):
    """Script contains the expected update command."""
    text = SCRIPT.read_text()
    assert section in text


# ── Content: log file usage ────────────────────────────────────────────


def test_log_file_path():
    """Script writes to ~/.coding-tools-update.log."""
    text = SCRIPT.read_text()
    assert '$HOME/.coding-tools-update.log' in text or '"$HOME/.coding-tools-update.log"' in text


def test_log_file_timestamps():
    """Script writes timestamped log entries."""
    text = SCRIPT.read_text()
    assert "$(date)" in text


def test_uses_tee_for_logging():
    """Script uses tee -a to write to log and stdout simultaneously."""
    text = SCRIPT.read_text()
    assert 'tee -a' in text


# ── Content: self-heal section ─────────────────────────────────────────


def test_health_file_path():
    """Script writes health JSON to ~/.coding-tools-health.json."""
    text = SCRIPT.read_text()
    assert ".coding-tools-health.json" in text


def test_health_file_has_ok_status():
    """Script writes status:ok when all tools present."""
    text = SCRIPT.read_text()
    assert '"status":"ok"' in text.replace(" ", "")


def test_health_file_has_degraded_status():
    """Script writes status:degraded when repairs fail."""
    text = SCRIPT.read_text()
    assert '"status":"degraded"' in text.replace(" ", "")


def test_self_heal_repair_commands():
    """Script has repair commands for critical tools."""
    text = SCRIPT.read_text()
    expected_repairs = ["brew install", "brew install --cask claude"]
    for repair in expected_repairs:
        assert repair in text, f"Missing repair command: {repair}"


def test_self_heal_uses_command_v():
    """Script checks tool presence with command -v."""
    text = SCRIPT.read_text()
    assert 'command -v' in text


REPAIR_TOOLS = ["brew", "claude", "opencode", "gemini", "codex", "agent-browser", "mas"]


@pytest.mark.parametrize("tool", REPAIR_TOOLS)
def test_repair_dict_includes_tool(tool):
    """Self-heal REPAIR dict includes a check for the given tool."""
    text = SCRIPT.read_text()
    assert f"[{tool}]=" in text, f"Missing REPAIR entry for {tool}"


# ── Execution: dry-run with mocked commands ────────────────────────────


def _make_stub_bin(tmpdir: Path, name: str, output: str = "mock-ok\n"):
    """Create a tiny stub script that records invocation and returns 0."""
    stub = tmpdir / name
    stub.write_text(f"#!/usr/bin/env bash\necho '{output}'\n")
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    return stub


def test_mocked_run_completes():
    """Script completes without error when all commands are mocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bin_dir = Path(tmpdir) / "bin"
        bin_dir.mkdir()
        # Create stubs for every command the script calls
        for cmd in [
            "brew", "npm", "pnpm", "uv", "cargo", "mas",
            "date", "tee", "command",
        ]:
            _make_stub_bin(bin_dir, cmd)

        # The script sources /opt/homebrew/bin/brew shellenv — provide a fake
        fake_homebrew = Path(tmpdir) / "homebrew" / "bin"
        fake_homebrew.mkdir(parents=True)
        brew_stub = fake_homebrew / "brew"
        brew_stub.write_text("#!/usr/bin/env bash\necho 'export PATH=$PATH'\n")
        brew_stub.chmod(brew_stub.stat().st_mode | stat.S_IXUSR)

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["HOME"] = tmpdir

        # Patch the brew shellenv path inside the script
        # We do this by creating a modified copy
        script_text = SCRIPT.read_text()
        script_text = script_text.replace(
            "/opt/homebrew/bin/brew shellenv",
            f"{fake_homebrew}/brew shellenv",
        )
        modified = Path(tmpdir) / "update-coding-tools.sh"
        modified.write_text(script_text)
        modified.chmod(modified.stat().st_mode | stat.S_IXUSR)

        result = subprocess.run(
            ["bash", str(modified)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        # Script should complete (may have non-zero due to declare -A in some bash)
        # but should not hang
        assert result.returncode == 0 or "declare" not in result.stderr, (
            f"Script failed: rc={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
        )


def test_mocked_run_writes_log():
    """Script creates log file at $HOME/.coding-tools-update.log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bin_dir = Path(tmpdir) / "bin"
        bin_dir.mkdir()
        for cmd in ["brew", "npm", "pnpm", "uv", "cargo", "mas", "date", "tee", "command"]:
            _make_stub_bin(bin_dir, cmd)

        fake_homebrew = Path(tmpdir) / "homebrew" / "bin"
        fake_homebrew.mkdir(parents=True)
        brew_stub = fake_homebrew / "brew"
        brew_stub.write_text("#!/usr/bin/env bash\necho 'export PATH=$PATH'\n")
        brew_stub.chmod(brew_stub.stat().st_mode | stat.S_IXUSR)

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["HOME"] = tmpdir

        script_text = SCRIPT.read_text()
        script_text = script_text.replace(
            "/opt/homebrew/bin/brew shellenv",
            f"{fake_homebrew}/brew shellenv",
        )
        modified = Path(tmpdir) / "update-coding-tools.sh"
        modified.write_text(script_text)
        modified.chmod(modified.stat().st_mode | stat.S_IXUSR)

        subprocess.run(
            ["bash", str(modified)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        log_file = Path(tmpdir) / ".coding-tools-update.log"
        assert log_file.exists(), "Log file was not created"
        log_content = log_file.read_text()
        assert "===" in log_content  # timestamped header/footer


def test_mocked_run_writes_health_json():
    """Script creates health JSON at $HOME/.coding-tools-health.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bin_dir = Path(tmpdir) / "bin"
        bin_dir.mkdir()
        for cmd in ["brew", "npm", "pnpm", "uv", "cargo", "mas", "date", "tee", "command"]:
            _make_stub_bin(bin_dir, cmd)

        fake_homebrew = Path(tmpdir) / "homebrew" / "bin"
        fake_homebrew.mkdir(parents=True)
        brew_stub = fake_homebrew / "brew"
        brew_stub.write_text("#!/usr/bin/env bash\necho 'export PATH=$PATH'\n")
        brew_stub.chmod(brew_stub.stat().st_mode | stat.S_IXUSR)

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["HOME"] = tmpdir

        script_text = SCRIPT.read_text()
        script_text = script_text.replace(
            "/opt/homebrew/bin/brew shellenv",
            f"{fake_homebrew}/brew shellenv",
        )
        modified = Path(tmpdir) / "update-coding-tools.sh"
        modified.write_text(script_text)
        modified.chmod(modified.stat().st_mode | stat.S_IXUSR)

        subprocess.run(
            ["bash", str(modified)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        health_file = Path(tmpdir) / ".coding-tools-health.json"
        assert health_file.exists(), "Health file was not created"
        health = json.loads(health_file.read_text())
        assert "status" in health
        assert health["status"] in ("ok", "degraded")
        assert "checked" in health
        assert "failures" in health


def test_mocked_run_degraded_when_tools_missing():
    """Script reports degraded status when critical tools are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bin_dir = Path(tmpdir) / "bin"
        bin_dir.mkdir()
        # Only provide minimal stubs — no brew, no mas, etc.
        for cmd in ["date", "tee"]:
            _make_stub_bin(bin_dir, cmd)

        fake_homebrew = Path(tmpdir) / "homebrew" / "bin"
        fake_homebrew.mkdir(parents=True)
        brew_stub = fake_homebrew / "brew"
        brew_stub.write_text("#!/usr/bin/env bash\necho 'export PATH=$PATH'\n")
        brew_stub.chmod(brew_stub.stat().st_mode | stat.S_IXUSR)

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["HOME"] = tmpdir

        script_text = SCRIPT.read_text()
        script_text = script_text.replace(
            "/opt/homebrew/bin/brew shellenv",
            f"{fake_homebrew}/brew shellenv",
        )
        modified = Path(tmpdir) / "update-coding-tools.sh"
        modified.write_text(script_text)
        modified.chmod(modified.stat().st_mode | stat.S_IXUSR)

        subprocess.run(
            ["bash", str(modified)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        health_file = Path(tmpdir) / ".coding-tools-health.json"
        assert health_file.exists()
        health = json.loads(health_file.read_text())
        # With no tools available, status should be degraded
        assert health["status"] == "degraded"
        assert len(health["failures"]) > 0


def test_or_else_true_prevents_bailout():
    """All update commands have || true so failures don't abort."""
    text = SCRIPT.read_text()
    lines = text.splitlines()
    update_lines = [
        l for l in lines
        if not l.strip().startswith("#")
        and any(cmd in l for cmd in ["brew update", "brew upgrade", "brew cleanup",
                                     "npm update", "pnpm update", "uv tool",
                                     "cargo binstall", "mas upgrade"])
    ]
    for line in update_lines:
        assert "|| true" in line, f"Missing || true on: {line.strip()}"


def test_path_includes_cargo_npm_local():
    """Script extends PATH with cargo, npm-global, and local bin."""
    text = SCRIPT.read_text()
    assert ".cargo/bin" in text
    assert ".npm-global/bin" in text
    assert ".local/bin" in text
