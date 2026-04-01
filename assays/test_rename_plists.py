from __future__ import annotations

"""Tests for effectors/rename-plists — rename com.terry.* LaunchAgents to com.vivesca.*.

rename-plists is a script (effectors/rename-plists), not an importable module.
It is loaded via exec() so that module-level constants can be patched per test.
"""

import glob
import os
import plistlib
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

RENAME_PLISTS_PATH = Path(__file__).resolve().parents[1] / "effectors" / "rename-plists"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def rp(tmp_path):
    """Load rename-plists via exec, redirect all path constants to tmp_path."""
    ns: dict = {"__name__": "test_rename_plists"}
    source = RENAME_PLISTS_PATH.read_text(encoding="utf-8")
    exec(source, ns)

    # Redirect path constants
    oscillators_dir = tmp_path / "oscillators"
    oscillators_dir.mkdir()
    launch_agents_dir = tmp_path / "LaunchAgents"
    launch_agents_dir.mkdir()

    ns["OSCILLATORS_DIR"] = oscillators_dir
    ns["LAUNCH_AGENTS_DIR"] = launch_agents_dir
    ns["OLD_PREFIX"] = "com.terry"
    ns["NEW_PREFIX"] = "com.vivesca"

    return ns


# ── deep_replace ─────────────────────────────────────────────────────────────


class TestDeepReplace:
    def test_replaces_string_in_top_level_str(self, rp):
        result = rp["deep_replace"]("com.terry.blog-sync")
        assert result == "com.vivesca.blog-sync"

    def test_replaces_string_in_dict_keys_and_values(self, rp):
        input_dict = {
            "com.terry.label": "com.terry.program",
            "Label": "com.terry.my-agent",
        }
        result = rp["deep_replace"](input_dict)
        assert result["com.vivesca.label"] == "com.vivesca.program"
        assert result["Label"] == "com.vivesca.my-agent"

    def test_replaces_string_in_lists(self, rp):
        input_list = ["com.terry/one", "normal", "com.terry/two"]
        result = rp["deep_replace"](input_list)
        assert result == ["com.vivesca/one", "normal", "com.vivesca/two"]

    def test_unchanged_non_string_non_container(self, rp):
        assert rp["deep_replace"](123) == 123
        assert rp["deep_replace"](True) is True
        assert rp["deep_replace"](None) is None


# ── run_cmd ────────────────────────────────────────────────────────────────────


class TestRunCmd:
    def test_dry_run_prints_returns_zero(self, rp, capsys):
        rc, err = rp["run_cmd"](["echo", "hello"], dry_run=True)
        out = capsys.readouterr().out
        assert "echo hello" in out
        assert rc == 0
        assert err == ""

    def test_exec_runs_returns_result(self, rp):
        rc, err = rp["run_cmd"](["echo", "test"], dry_run=False)
        assert rc == 0
        # echo writes to stdout, so stderr is empty
        assert err == ""

    def test_exec_nonzero_returns_rc(self, rp):
        rc, err = rp["run_cmd"](["false"], dry_run=False)
        assert rc == 1


# ── rename_one ────────────────────────────────────────────────────────────────


class TestRenameOne:
    @staticmethod
    def create_test_plist(dir: Path, name: str) -> Path:
        """Create a test com.terry plist file."""
        plist_path = dir / f"{name}.plist"
        data = {
            "Label": name,
            "ProgramArguments": [str(Path.home() / "run/com.terry-helper"), "--debug"],
            "KeepAlive": True,
        }
        with open(plist_path, "wb") as f:
            plistlib.dump(data, f)
        return plist_path

    def test_dry_run_no_changes_to_disk(self, rp, tmp_path):
        oscillators = rp["OSCILLATORS_DIR"]
        plist_path = self.create_test_plist(oscillators, "com.terry.test-agent")
        original_content = plist_path.read_bytes()
        original_exists = plist_path.exists()

        errors = rp["rename_one"](plist_path, dry_run=True)

        assert errors == []
        # Original file still exists and unchanged
        assert plist_path.exists() == original_exists
        assert plist_path.read_bytes() == original_content
        # New file shouldn't exist
        new_plist = oscillators / "com.vivesca.test-agent.plist"
        assert not new_plist.exists()

    def test_dry_run_shows_changes(self, rp, tmp_path, capsys):
        oscillators = rp["OSCILLATORS_DIR"]
        plist_path = self.create_test_plist(oscillators, "com.terry.test-agent")
        rp["rename_one"](plist_path, dry_run=True)
        out = capsys.readouterr().out
        assert "com.terry.test-agent -> com.vivesca.test-agent" in out
        assert "Label" in out
        assert "ProgramArguments" in out

    def test_execute_renames_and_updates(self, rp, tmp_path):
        """Execute actually renames the file and updates plist content."""
        oscillators = rp["OSCILLATORS_DIR"]
        launch_agents = rp["LAUNCH_AGENTS_DIR"]
        plist_path = self.create_test_plist(oscillators, "com.terry.test-agent")

        # Mock run_cmd to avoid actually calling launchctl
        mock_run = MagicMock(return_value=(0, ""))
        with patch.dict(rp, {"run_cmd": mock_run}):
            errors = rp["rename_one"](plist_path, dry_run=False)

        assert errors == []
        # Old file is gone
        assert not plist_path.exists()
        # New file exists
        new_plist = oscillators / "com.vivesca.test-agent.plist"
        assert new_plist.exists()
        # Check that plist content was updated
        with open(new_plist, "rb") as f:
            data = plistlib.load(f)
        assert data["Label"] == "com.vivesca.test-agent"
        assert "com.vivesca-helper" in data["ProgramArguments"][0]
        # Symlink created in LaunchAgents
        new_symlink = launch_agents / "com.vivesca.test-agent.plist"
        assert new_symlink.is_symlink()
        assert new_symlink.resolve() == new_plist

    def test_execute_handles_existing_symlink_old(self, rp, tmp_path):
        oscillators = rp["OSCILLATORS_DIR"]
        launch_agents = rp["LAUNCH_AGENTS_DIR"]
        plist_path = self.create_test_plist(oscillators, "com.terry.test-agent")
        # Create old symlink
        old_symlink = launch_agents / "com.terry.test-agent.plist"
        os.symlink(plist_path, old_symlink)
        assert old_symlink.exists()

        mock_run = MagicMock(return_value=(0, ""))
        with patch.dict(rp, {"run_cmd": mock_run}):
            errors = rp["rename_one"](plist_path, dry_run=False)

        assert errors == []
        # Old symlink is gone
        assert not old_symlink.exists()
        # New symlink exists
        new_symlink = launch_agents / "com.vivesca.test-agent.plist"
        assert new_symlink.exists()

    def test_bootout_error_non_fatal_if_service_not_found(self, rp, tmp_path):
        """Error that contains 'Could not find service' is not added to errors."""
        oscillators = rp["OSCILLATORS_DIR"]
        plist_path = self.create_test_plist(oscillators, "com.terry.test-agent")

        # First call (bootout) returns error, second call (bootstrap) succeeds
        mock_run = MagicMock(side_effect=[
            (1, "Could not find service specified"),
            (0, ""),
        ])
        with patch.dict(rp, {"run_cmd": mock_run}):
            errors = rp["rename_one"](plist_path, dry_run=False)

        # Only bootout error is skipped; bootstrap passes
        assert errors == []

    def test_bootout_other_error_added_to_errors(self, rp, tmp_path):
        """Other errors (not 'Could not find service') are added to errors."""
        oscillators = rp["OSCILLATORS_DIR"]
        plist_path = self.create_test_plist(oscillators, "com.terry.test-agent")

        # First call (bootout) returns other error, bootstrap will still be checked
        mock_run = MagicMock(side_effect=[
            (1, "Permission denied"),
            (0, ""),
        ])
        with patch.dict(rp, {"run_cmd": mock_run}):
            errors = rp["rename_one"](plist_path, dry_run=False)

        assert len(errors) == 1
        assert "bootout failed" in errors[0]


# ── main (argument parsing, discovery) ───────────────────────────────────────


class TestMain:
    def test_no_plists_found_exits_nonzero(self, rp, capsys):
        # No plists in empty oscillators dir
        pattern = str(rp["OSCILLATORS_DIR"] / f"{rp['OLD_PREFIX']}.*.plist")
        assert len(glob.glob(pattern)) == 0
        with patch.object(rp["sys"], "argv", ["rename-plists"]):
            with pytest.raises(SystemExit):
                rp["main"]()

    def test_dry_run_prints_summary(self, rp, tmp_path, capsys):
        # Create two test plists
        oscillators = rp["OSCILLATORS_DIR"]
        TestRenameOne.create_test_plist(oscillators, "com.terry.agent1")
        TestRenameOne.create_test_plist(oscillators, "com.terry.agent2")
        with patch.object(rp["sys"], "argv", ["rename-plists"]):
            # Does not exit since no errors
            try:
                rp["main"]()
            except SystemExit as e:
                assert e.code is None or e.code == 0
        out = capsys.readouterr().out
        assert "DRY RUN" in out
        assert "Renaming 2 plists" in out
        assert "Run with --execute to perform" in out

    def test_execute_all_success_exits_zero(self, rp, tmp_path, capsys):
        oscillators = rp["OSCILLATORS_DIR"]
        TestRenameOne.create_test_plist(oscillators, "com.terry.agent1")

        # Mock run_cmd everywhere it's called
        mock_run = MagicMock(return_value=(0, ""))
        with patch.dict(rp, {"run_cmd": mock_run}):
            with patch.object(rp["sys"], "argv", ["rename-plists", "--execute"]):
                rp["main"]()
        out = capsys.readouterr().out
        assert "EXECUTING" in out
        assert "renamed successfully" in out

    def test_errors_during_rename_exits_nonzero(self, rp, tmp_path, capsys):
        oscillators = rp["OSCILLATORS_DIR"]
        TestRenameOne.create_test_plist(oscillators, "com.terry.bad-agent")

        def mock_run_cmd(cmd, dry_run):
            if "bootstrap" in cmd:
                return (1, "bootstrap error")
            return (0, "")

        with patch.dict(rp, {"run_cmd": mock_run_cmd}):
            with patch.object(rp["sys"], "argv", ["rename-plists", "--execute"]):
                with pytest.raises(SystemExit) as excinfo:
                    rp["main"]()
        assert excinfo.value.code != 0
        out = capsys.readouterr().out
        assert "Errors encountered" in out
        assert "bootstrap error" in out


# ── CLI subprocess (integration) ──────────────────────────────────────────────


class TestCLISubprocess:
    def test_help_exits_zero(self):
        r = subprocess.run(
            ["uv", "run", "--script", str(RENAME_PLISTS_PATH), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0
        assert "rename" in r.stdout.lower()
        assert "com.terry" in r.stdout

    def test_no_plists_exits_nonzero(self):
        # Without matching plists, the script exits non-zero
        r = subprocess.run(
            ["uv", "run", "--script", str(RENAME_PLISTS_PATH), "--execute"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode != 0
        assert "No plists found" in r.stdout
