from __future__ import annotations

"""Tests for update-coding-tools.sh — macOS tool auto-updater."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path("/home/terry/germline/effectors/update-coding-tools.sh")


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run the script with given args, capturing output."""
    return subprocess.run(
        [str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
        **kwargs,
    )


# ── --help tests ──────────────────────────────────────────────────────


class TestHelp:
    def test_help_flag_exits_zero(self):
        result = _run(["--help"])
        assert result.returncode == 0

    def test_h_short_flag_exits_zero(self):
        result = _run(["-h"])
        assert result.returncode == 0

    def test_help_output_contains_usage(self):
        result = _run(["--help"])
        assert "Usage: update-coding-tools.sh" in result.stdout

    def test_help_mentions_brew(self):
        result = _run(["--help"])
        assert "brew" in result.stdout

    def test_help_mentions_npm(self):
        result = _run(["--help"])
        assert "npm" in result.stdout

    def test_help_mentions_cargo(self):
        result = _run(["--help"])
        assert "cargo" in result.stdout

    def test_help_mentions_mac_app_store(self):
        result = _run(["--help"])
        assert "Mac App Store" in result.stdout


# ── missing brew ──────────────────────────────────────────────────────


class TestMissingBrew:
    def test_no_brew_exits_nonzero(self):
        """Script exits 1 when brew is not found on PATH."""
        env = dict(os.environ)
        # Set PATH to essential system dirs but remove any brew location
        env["PATH"] = "/usr/bin:/bin"
        result = _run([], env=env)
        assert result.returncode != 0

    def test_no_brew_prints_error_to_stderr(self):
        """Script prints error message to stderr when brew missing."""
        env = dict(os.environ)
        env["PATH"] = "/usr/bin:/bin"
        result = _run([], env=env)
        assert "Homebrew not found" in result.stderr or "Error" in result.stderr


# ── script structure tests (via grep, not execution) ──────────────────


class TestScriptStructure:
    @pytest.fixture(autouse=True)
    def _read_source(self):
        self.source = SCRIPT.read_text()

    def test_uses_set_e(self):
        assert "set -e" in self.source

    def test_has_brew_update(self):
        assert "brew update" in self.source

    def test_has_brew_upgrade(self):
        assert "brew upgrade" in self.source

    def test_has_npm_update(self):
        assert "npm update -g" in self.source

    def test_has_pnpm_update(self):
        assert "pnpm update -g" in self.source

    def test_has_uv_tool_upgrade(self):
        assert "uv tool upgrade --all" in self.source

    def test_has_cargo_binstall(self):
        assert "cargo binstall" in self.source

    def test_has_mas_upgrade(self):
        assert "mas upgrade" in self.source

    def test_has_health_file_variable(self):
        assert "HEALTH_FILE" in self.source

    def test_has_repair_dict(self):
        assert "declare -A REPAIR" in self.source

    def test_health_json_has_status_ok(self):
        assert '"status":"ok"' in self.source

    def test_health_json_has_status_degraded(self):
        assert '"status":"degraded"' in self.source

    def test_log_file_variable_defined(self):
        assert 'LOG_FILE="$HOME/.coding-tools-update.log"' in self.source

    def test_or_true_on_all_update_commands(self):
        """Every update command has || true to prevent set -e bail."""
        lines = [l.strip() for l in self.source.splitlines()]
        update_lines = [
            l for l in lines
            if any(cmd in l for cmd in ["brew update", "brew upgrade",
                                         "npm update", "pnpm update",
                                         "uv tool upgrade", "cargo binstall",
                                         "mas upgrade", "brew cleanup"])
            and "echo" not in l
            and not l.startswith("#")
        ]
        for line in update_lines:
            assert "|| true" in line, f"Missing || true: {line}"

    def test_cargo_installs_typos_cli(self):
        assert "typos-cli" in self.source

    def test_repair_includes_claude(self):
        assert "[claude]=" in self.source

    def test_repair_includes_opencode(self):
        assert "[opencode]=" in self.source

    def test_repair_includes_codex(self):
        assert "[codex]=" in self.source

    def test_repair_includes_gemini(self):
        assert "[gemini]=" in self.source

    def test_repair_includes_mas(self):
        assert "[mas]=" in self.source

    def test_path_includes_cargo_bin(self):
        assert ".cargo/bin" in self.source

    def test_path_includes_npm_global(self):
        assert ".npm-global/bin" in self.source

    def test_path_includes_pnpm(self):
        assert "Library/pnpm" in self.source or "pnpm" in self.source


# ── health JSON structure tests ───────────────────────────────────────


class TestHealthJsonStructure:
    @pytest.fixture(autouse=True)
    def _read_source(self):
        self.source = SCRIPT.read_text()

    def test_ok_json_is_valid_structure(self):
        """The 'ok' health JSON in source has correct fields."""
        for line in self.source.splitlines():
            if '"status":"ok"' in line and "HEALTH_FILE" in line:
                # The template uses shell interpolation — just verify structure
                assert '"status":"ok"' in line
                assert "checked" in line
                assert '"failures":[]' in line
                break

    def test_degraded_json_has_failures_array(self):
        """The 'degraded' health JSON template uses failures array."""
        assert '"failures":[' in self.source
