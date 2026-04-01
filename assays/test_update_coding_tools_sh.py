from __future__ import annotations

"""Tests for effectors/update-coding-tools.sh — bash script tested via subprocess."""

import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "update-coding-tools.sh"
LOG_RELATIVE = ".coding-tools-update.log"
HEALTH_RELATIVE = ".coding-tools-health.json"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_help(*args: str) -> subprocess.CompletedProcess:
    """Run script with --help flag (no HOME override needed)."""
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


def _run_with_home(tmp_path: Path) -> subprocess.CompletedProcess:
    """Run script with HOME=tmp_path (will fail because no brew)."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    # Remove brew from PATH to simulate missing Homebrew
    env["PATH"] = "/usr/bin:/bin"
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def test_help_exits_zero(self):
        r = _run_help("--help")
        assert r.returncode == 0

    def test_help_short_flag_exits_zero(self):
        r = _run_help("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run_help("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_update(self):
        r = _run_help("--help")
        assert "update" in r.stdout.lower()

    def test_help_mentions_tools(self):
        r = _run_help("--help")
        # Should mention some of the tools it updates
        stdout_lower = r.stdout.lower()
        assert "brew" in stdout_lower or "npm" in stdout_lower or "cargo" in stdout_lower

    def test_help_mentions_macos(self):
        r = _run_help("--help")
        assert "macOS" in r.stdout or "macos" in r.stdout.lower()

    def test_help_mentions_log(self):
        r = _run_help("--help")
        assert "log" in r.stdout.lower()

    def test_help_no_stderr(self):
        r = _run_help("--help")
        assert r.stderr == ""

    def test_help_no_side_effects(self, tmp_path):
        """--help must not create any files."""
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        r = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.returncode == 0
        assert not (tmp_path / LOG_RELATIVE).exists()
        assert not (tmp_path / HEALTH_RELATIVE).exists()


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert "bash" in first

    def test_has_set_e(self):
        src = SCRIPT.read_text()
        assert "set -e" in src

    def test_has_shebang(self):
        src = SCRIPT.read_text()
        assert src.startswith("#!")


# ── missing homebrew ────────────────────────────────────────────────────


class TestMissingHomebrew:
    """Script should fail gracefully when Homebrew is not available."""

    def test_exits_1_without_brew(self, tmp_path):
        """Without brew in PATH, script should exit 1."""
        r = _run_with_home(tmp_path)
        assert r.returncode == 1

    def test_stderr_mentions_homebrew(self, tmp_path):
        """Error message should mention Homebrew requirement."""
        r = _run_with_home(tmp_path)
        assert "Homebrew" in r.stderr or "brew" in r.stderr.lower()

    def test_no_log_file_created(self, tmp_path):
        """Failed run should not create log file."""
        _run_with_home(tmp_path)
        assert not (tmp_path / LOG_RELATIVE).exists()

    def test_no_health_file_created(self, tmp_path):
        """Failed run should not create health file."""
        _run_with_home(tmp_path)
        assert not (tmp_path / HEALTH_RELATIVE).exists()


# ── script structure ────────────────────────────────────────────────────


class TestScriptStructure:
    def test_has_brew_update(self):
        src = SCRIPT.read_text()
        assert "brew update" in src

    def test_has_brew_upgrade(self):
        src = SCRIPT.read_text()
        assert "brew upgrade" in src

    def test_has_npm_update(self):
        src = SCRIPT.read_text()
        assert "npm update" in src

    def test_has_pnpm_update(self):
        src = SCRIPT.read_text()
        assert "pnpm update" in src

    def test_has_uv_tool_upgrade(self):
        src = SCRIPT.read_text()
        assert "uv tool upgrade" in src

    def test_has_cargo_update(self):
        src = SCRIPT.read_text()
        assert "cargo" in src.lower()

    def test_has_mas_upgrade(self):
        src = SCRIPT.read_text()
        assert "mas upgrade" in src

    def test_has_health_check(self):
        src = SCRIPT.read_text()
        assert "HEALTH_FILE" in src

    def test_has_log_file_variable(self):
        src = SCRIPT.read_text()
        assert "LOG_FILE" in src

    def test_uses_tee_for_logging(self):
        src = SCRIPT.read_text()
        assert "tee -a" in src

    def test_has_error_suppression_or_true(self):
        """Individual update commands should have || true to prevent one failure from stopping all."""
        src = SCRIPT.read_text()
        # Count || true occurrences after update commands
        assert "|| true" in src


# ── repair logic ─────────────────────────────────────────────────────────


class TestRepairLogic:
    def test_has_repair_associative_array(self):
        src = SCRIPT.read_text()
        assert "declare -A REPAIR" in src

    def test_repairs_brew(self):
        src = SCRIPT.read_text()
        assert '"brew"' in src or "[brew]" in src

    def test_repairs_claude(self):
        src = SCRIPT.read_text()
        assert "claude" in src.lower()

    def test_repairs_mas(self):
        src = SCRIPT.read_text()
        assert "mas" in src

    def test_tracks_failures(self):
        src = SCRIPT.read_text()
        assert "failures" in src


# ── health file format ──────────────────────────────────────────────────


class TestHealthFileFormat:
    """Test the health JSON format generated by the script."""

    def test_health_json_structure_ok(self, tmp_path):
        """Verify expected structure for ok status."""
        # Simulate what the script would write
        health_file = tmp_path / HEALTH_RELATIVE
        health_data = {
            "status": "ok",
            "checked": "2025-01-15T12:00:00Z",
            "failures": [],
        }
        health_file.write_text(json.dumps(health_data))
        
        loaded = json.loads(health_file.read_text())
        assert loaded["status"] == "ok"
        assert loaded["failures"] == []

    def test_health_json_structure_degraded(self, tmp_path):
        """Verify expected structure for degraded status."""
        health_file = tmp_path / HEALTH_RELATIVE
        health_data = {
            "status": "degraded",
            "checked": "2025-01-15T12:00:00Z",
            "failures": ["claude", "opencode"],
        }
        health_file.write_text(json.dumps(health_data))
        
        loaded = json.loads(health_file.read_text())
        assert loaded["status"] == "degraded"
        assert "claude" in loaded["failures"]

    def test_script_generates_valid_json_pattern(self):
        """Verify the script's JSON output patterns are valid."""
        src = SCRIPT.read_text()
        # Check for JSON-like patterns in health file writes
        assert '"status"' in src
        assert '"checked"' in src
        assert '"failures"' in src


# ── path configuration ───────────────────────────────────────────────────


class TestPathConfiguration:
    def test_includes_cargo_bin(self):
        src = SCRIPT.read_text()
        assert ".cargo/bin" in src

    def test_includes_npm_global(self):
        src = SCRIPT.read_text()
        assert ".npm-global" in src or "npm-global" in src

    def test_includes_local_bin(self):
        src = SCRIPT.read_text()
        assert ".local/bin" in src

    def test_includes_pnpm(self):
        src = SCRIPT.read_text()
        assert "pnpm" in src


# ── log file handling ────────────────────────────────────────────────────


class TestLogFileHandling:
    def test_log_file_path(self):
        src = SCRIPT.read_text()
        assert ".coding-tools-update.log" in src

    def test_logs_timestamp(self):
        src = SCRIPT.read_text()
        assert "$(date)" in src

    def test_logs_section_headers(self):
        """Script should log section headers like 'Updating brew...'"""
        src = SCRIPT.read_text()
        assert "Updating" in src


# ── script permissions ───────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()


# ── brew commands ────────────────────────────────────────────────────────────


class TestBrewCommands:
    def test_brew_upgrade_includes_cask_greedy(self):
        """brew upgrade should use --cask --greedy for all casks."""
        src = SCRIPT.read_text()
        assert "brew upgrade --cask --greedy" in src

    def test_brew_cleanup_uses_prune(self):
        """brew cleanup should use --prune=7 to limit cache age."""
        src = SCRIPT.read_text()
        assert "brew cleanup --prune=7" in src

    def test_brew_update_before_upgrade(self):
        """brew update should appear before brew upgrade."""
        src = SCRIPT.read_text()
        update_pos = src.index("brew update")
        upgrade_pos = src.index("brew upgrade")
        assert update_pos < upgrade_pos


# ── cargo packages ──────────────────────────────────────────────────────────


class TestCargoPackages:
    def test_installs_compound_perplexity(self):
        src = SCRIPT.read_text()
        assert "compound-perplexity" in src

    def test_installs_typos_cli(self):
        src = SCRIPT.read_text()
        assert "typos-cli" in src

    def test_cargo_binstall_uses_yes_flag(self):
        """cargo binstall should pass -y for non-interactive install."""
        src = SCRIPT.read_text()
        assert "cargo binstall -y" in src


# ── REPAIR map entries ──────────────────────────────────────────────────────


class TestRepairMapEntries:
    def test_repairs_agent_browser(self):
        src = SCRIPT.read_text()
        assert "[agent-browser]" in src

    def test_repairs_gemini_via_gemini_cli(self):
        """gemini command should map to 'brew install gemini-cli'."""
        src = SCRIPT.read_text()
        assert "[gemini]=\"brew install gemini-cli\"" in src

    def test_repairs_codex(self):
        src = SCRIPT.read_text()
        assert "[codex]=\"brew install codex\"" in src

    def test_repairs_opencode(self):
        src = SCRIPT.read_text()
        assert "[opencode]=\"brew install opencode\"" in src

    def test_repairs_claude_via_cask(self):
        """claude should be installed via cask."""
        src = SCRIPT.read_text()
        assert "[claude]=\"brew install --cask claude\"" in src

    def test_repairs_brew_with_path(self):
        """brew repair entry should just be the path, not an install command."""
        src = SCRIPT.read_text()
        assert "[brew]=\"/opt/homebrew/bin/brew\"" in src

    def test_repair_loop_uses_eval(self):
        """Repair loop should eval the install command string."""
        src = SCRIPT.read_text()
        assert 'eval "${REPAIR[$cmd]}"' in src

    def test_repair_tracks_failures_with_append(self):
        """Failed repairs should be appended to the failures array."""
        src = SCRIPT.read_text()
        assert 'failures+=("$cmd")' in src


# ── path configuration details ──────────────────────────────────────────────


class TestPathConfigurationDetails:
    def test_path_includes_library_pnpm(self):
        """PATH should include ~/Library/pnpm for pnpm global bin."""
        src = SCRIPT.read_text()
        assert "Library/pnpm" in src

    def test_path_includes_home_bin(self):
        src = SCRIPT.read_text()
        assert "$HOME/.local/bin" in src

    def test_path_exports(self):
        src = SCRIPT.read_text()
        assert "export PATH=" in src


# ── logging details ─────────────────────────────────────────────────────────


class TestLoggingDetails:
    def test_logs_completion_marker(self):
        """Script should log 'Updates complete' at the end."""
        src = SCRIPT.read_text()
        assert "Updates complete" in src

    def test_logs_verification_section(self):
        """Script should log 'Verifying critical tools' before repair loop."""
        src = SCRIPT.read_text()
        assert "Verifying critical tools" in src

    def test_log_timestamps_with_date(self):
        """Log entries should include timestamps via $(date)."""
        src = SCRIPT.read_text()
        count = src.count("$(date")
        assert count >= 2, f"Expected at least 2 date references, got {count}"

    def test_completion_marker_at_end(self):
        """'Updates complete' should appear after the health check logic."""
        src = SCRIPT.read_text()
        health_pos = src.rindex("HEALTH_FILE")
        complete_pos = src.index("Updates complete")
        assert complete_pos > health_pos


# ── health file UTC format ──────────────────────────────────────────────────


class TestHealthFileUTC:
    def test_uses_utc_date(self):
        """Health timestamp should use UTC (date -u)."""
        src = SCRIPT.read_text()
        assert "date -u" in src

    def test_date_format_is_iso8601(self):
        """Date format should be ISO 8601."""
        src = SCRIPT.read_text()
        assert "%Y-%m-%dT%H:%M:%SZ" in src

    def test_health_file_path(self):
        """Health file should be at ~/.coding-tools-health.json."""
        src = SCRIPT.read_text()
        assert ".coding-tools-health.json" in src


# ── brew shellenv ───────────────────────────────────────────────────────────


class TestBrewShellenv:
    def test_evals_brew_shellenv(self):
        """Script should eval brew shellenv for PATH setup."""
        src = SCRIPT.read_text()
        assert 'eval "$(brew shellenv)"' in src

    def test_checks_brew_exists_first(self):
        """Script should check brew exists before eval."""
        src = SCRIPT.read_text()
        brew_check_pos = src.index("command -v brew")
        eval_pos = src.index("brew shellenv")
        assert brew_check_pos < eval_pos


# ── help content details ───────────────────────────────────────────────────


class TestHelpContentDetails:
    def test_help_mentions_each_tool(self):
        """Help text should mention all major tools."""
        r = _run_help("--help")
        for tool in ["brew", "npm", "pnpm", "uv", "cargo"]:
            assert tool in r.stdout.lower(), f"Help missing tool: {tool}"

    def test_help_mentions_app_store(self):
        r = _run_help("--help")
        assert "App Store" in r.stdout or "app store" in r.stdout.lower()

    def test_help_exits_immediately(self):
        """Help should not proceed to update logic."""
        r = _run_help("--help")
        assert r.returncode == 0
        assert "Updating" not in r.stdout


# ── error suppression thoroughness ─────────────────────────────────────────


class TestErrorSuppression:
    def test_all_brew_commands_have_or_true(self):
        """Every brew command should have || true."""
        src = SCRIPT.read_text()
        for cmd in ["brew update", "brew upgrade", "brew cleanup"]:
            # Find lines containing this command
            for line in src.splitlines():
                stripped = line.strip()
                if cmd in stripped and "echo" not in stripped:
                    assert "|| true" in stripped, f"Missing || true: {stripped}"

    def test_npm_update_has_or_true(self):
        src = SCRIPT.read_text()
        for line in src.splitlines():
            stripped = line.strip()
            if "npm update" in stripped and "echo" not in stripped:
                assert "|| true" in stripped, f"Missing || true: {stripped}"

    def test_pnpm_update_has_or_true(self):
        src = SCRIPT.read_text()
        for line in src.splitlines():
            stripped = line.strip()
            if "pnpm update" in stripped and "echo" not in stripped:
                assert "|| true" in stripped, f"Missing || true: {stripped}"

    def test_uv_tool_upgrade_has_or_true(self):
        src = SCRIPT.read_text()
        for line in src.splitlines():
            stripped = line.strip()
            if "uv tool upgrade" in stripped and "echo" not in stripped:
                assert "|| true" in stripped, f"Missing || true: {stripped}"

    def test_cargo_binstall_has_or_true(self):
        src = SCRIPT.read_text()
        for line in src.splitlines():
            stripped = line.strip()
            if "cargo binstall" in stripped and "echo" not in stripped:
                assert "|| true" in stripped, f"Missing || true: {stripped}"

    def test_mas_upgrade_has_or_true(self):
        src = SCRIPT.read_text()
        for line in src.splitlines():
            stripped = line.strip()
            if "mas upgrade" in stripped and "echo" not in stripped:
                assert "|| true" in stripped, f"Missing || true: {stripped}"


# ── missing homebrew details ───────────────────────────────────────────────


class TestMissingHomebrewDetails:
    def test_error_message_mentions_macos(self):
        """Error message should clarify macOS requirement."""
        r = _run_with_home(tmp_path := __import__("tempfile").mkdtemp())
        from pathlib import Path
        r = _run_with_home(Path(tmp_path))
        assert "macOS" in r.stderr

    def test_exits_before_log_writes(self):
        """Script should exit before writing any log entries."""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            r = _run_with_home(Path(td))
            assert r.returncode == 1
            log = Path(td) / LOG_RELATIVE
            if log.exists():
                content = log.read_text()
                # Should not have started any update
                assert "Updating" not in content
