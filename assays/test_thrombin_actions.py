from __future__ import annotations

"""Comprehensive tests for thrombin enzyme — all actions and branches."""


import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.thrombin import ProcessListResult, thrombin
from metabolon.morphology import EffectorResult

# Patch target: mock where subprocess is looked up, not where it is defined.
_SUB_RUN = "metabolon.enzymes.thrombin.subprocess.run"


# ---------------------------------------------------------------------------
# Return-type helpers
# ---------------------------------------------------------------------------


def _is_effector(r):
    return isinstance(r, EffectorResult)


def _is_process_list(r):
    return isinstance(r, ProcessListResult)


# ===========================================================================
# Action: unknown / fallback
# ===========================================================================


class TestUnknownAction:
    def test_returns_effector_result(self):
        result = thrombin(action="nonexistent")
        assert _is_effector(result)
        assert not result.success
        assert "Unknown action" in result.message

    def test_valid_actions_listed_in_message(self):
        result = thrombin(action="bogus")
        for a in ("ps", "kill", "launchagent", "handoff"):
            assert a in result.message

    @pytest.mark.parametrize("action", ["PS", "Kill", "LAUNCHAGENT", "HANDOFF", " Ps "])
    def test_action_is_case_insensitive_and_stripped(self, action):
        """Upper/mixed case still routes correctly (not 'unknown')."""
        # These should NOT fall through to the unknown branch.
        with patch(_SUB_RUN, return_value=MagicMock(stdout="", returncode=0)):
            result = thrombin(action=action, pattern="test")
        # ps returns ProcessListResult (has summary), others return EffectorResult (has message)
        text = result.summary if _is_process_list(result) else result.message
        assert "Unknown action" not in text


# ===========================================================================
# Action: ps
# ===========================================================================


class TestPsAction:
    def test_returns_process_list_result(self):
        with patch(
            _SUB_RUN, return_value=MagicMock(stdout="123 python\n456 node\n", returncode=0)
        ):
            result = thrombin(action="ps", pattern="python")
        assert _is_process_list(result)
        assert result.count == 2
        assert result.matches == ["123 python", "456 node"]
        assert result.pattern == "python"

    def test_empty_output(self):
        with patch(_SUB_RUN, return_value=MagicMock(stdout="", returncode=0)):
            result = thrombin(action="ps", pattern="nothing_matches")
        assert result.count == 0
        assert result.matches == []
        assert "(none)" in result.summary

    def test_summary_contains_pattern(self):
        with patch(_SUB_RUN, return_value=MagicMock(stdout="1 foo\n", returncode=0)):
            result = thrombin(action="ps", pattern="myapp")
        assert "myapp" in result.summary
        assert "1 found" in result.summary

    def test_blank_lines_filtered(self):
        with patch(
            _SUB_RUN, return_value=MagicMock(stdout="100 proc\n\n\n200 other\n", returncode=0)
        ):
            result = thrombin(action="ps", pattern="proc")
        assert result.count == 2
        assert "" not in result.matches

    def test_timeout_returns_empty(self):
        with patch(_SUB_RUN, side_effect=subprocess.TimeoutExpired(cmd="pgrep", timeout=5)):
            result = thrombin(action="ps", pattern="slow")
        assert _is_process_list(result)
        assert result.count == 0
        assert result.matches == []

    def test_subprocess_called_with_pgrep(self):
        with patch(_SUB_RUN, return_value=MagicMock(stdout="", returncode=0)) as mock:
            thrombin(action="ps", pattern="test")
        mock.assert_called_once()
        args = mock.call_args[0][0]
        assert args[0] == "pgrep"
        assert "-l" in args
        assert "-a" in args
        assert "-f" in args
        assert "test" in args


# ===========================================================================
# Action: kill
# ===========================================================================


class TestKillAction:
    def test_success_returns_effector(self):
        with patch(_SUB_RUN, return_value=MagicMock(returncode=0)):
            result = thrombin(action="kill", pattern="zombie-proc", signal="TERM")
        assert _is_effector(result)
        assert result.success
        assert "TERM" in result.message
        assert result.data["pattern"] == "zombie-proc"

    def test_no_match(self):
        with patch(_SUB_RUN, return_value=MagicMock(returncode=1, stderr="")):
            result = thrombin(action="kill", pattern="nonexistent")
        assert not result.success
        assert "No processes" in result.message

    def test_pkill_error_exit_code(self):
        with patch(_SUB_RUN, return_value=MagicMock(returncode=2, stderr="permission denied")):
            result = thrombin(action="kill", pattern="protected")
        assert not result.success
        assert "pkill error" in result.message
        assert result.data["stderr"] == "permission denied"

    def test_timeout(self):
        with patch(_SUB_RUN, side_effect=subprocess.TimeoutExpired(cmd="pkill", timeout=10)):
            result = thrombin(action="kill", pattern="hung")
        assert not result.success
        assert "timed out" in result.message

    @pytest.mark.parametrize("signal", ["TERM", "KILL", "HUP", "INT", "QUIT", "USR1", "USR2"])
    def test_all_valid_signals(self, signal):
        with patch(_SUB_RUN, return_value=MagicMock(returncode=0)):
            result = thrombin(action="kill", pattern="target", signal=signal)
        assert result.success
        assert signal in result.message

    def test_invalid_signal(self):
        result = thrombin(action="kill", pattern="test", signal="INVALID")
        assert not result.success
        assert "Invalid signal" in result.message

    def test_invalid_signal_lists_valid_ones(self):
        result = thrombin(action="kill", pattern="test", signal="BOOM")
        for sig in ("TERM", "KILL", "HUP"):
            assert sig in result.message

    def test_signal_case_insensitive(self):
        with patch(_SUB_RUN, return_value=MagicMock(returncode=0)) as mock:
            result = thrombin(action="kill", pattern="proc", signal="term")
        assert result.success
        # Verify pkill was called with uppercase signal
        called_args = mock.call_args[0][0]
        assert "-TERM" in called_args

    def test_subprocess_called_with_pkill(self):
        with patch(_SUB_RUN, return_value=MagicMock(returncode=0)) as mock:
            thrombin(action="kill", pattern="myproc", signal="KILL")
        args = mock.call_args[0][0]
        assert args[0] == "pkill"
        assert "-KILL" in args
        assert "-f" in args
        assert "myproc" in args


# ===========================================================================
# Action: launchagent
# ===========================================================================


class TestLaunchAgentAction:
    def test_invalid_sub_action(self):
        result = thrombin(action="launchagent", launchagent_action="restart")
        assert _is_effector(result)
        assert not result.success
        assert "Invalid action" in result.message

    @pytest.mark.parametrize("bad_action", ["load", "unload"])
    def test_missing_plist(self, bad_action):
        result = thrombin(
            action="launchagent", plist_path="/no/such/file.plist", launchagent_action=bad_action
        )
        assert not result.success
        assert "not found" in result.message.lower() or "not found" in result.message

    def test_unload_success(self, tmp_path):
        plist = tmp_path / "com.test.plist"
        plist.write_text("<plist></plist>")
        with patch(_SUB_RUN, return_value=MagicMock(returncode=0)):
            result = thrombin(
                action="launchagent",
                plist_path=str(plist),
                launchagent_action="unload",
            )
        assert result.success
        assert "Unloaded" in result.message
        assert result.data["action"] == "unload"

    def test_load_success(self, tmp_path):
        plist = tmp_path / "com.test.plist"
        plist.write_text("<plist></plist>")
        with patch(_SUB_RUN, return_value=MagicMock(returncode=0)):
            result = thrombin(
                action="launchagent",
                plist_path=str(plist),
                launchagent_action="load",
            )
        assert result.success
        assert "Loaded" in result.message
        assert result.data["action"] == "load"

    def test_unload_failure(self, tmp_path):
        plist = tmp_path / "com.test.plist"
        plist.write_text("<plist></plist>")
        with patch(_SUB_RUN, return_value=MagicMock(returncode=1, stderr="operation failed")):
            result = thrombin(
                action="launchagent",
                plist_path=str(plist),
                launchagent_action="unload",
            )
        assert not result.success
        assert "failed" in result.message.lower()
        assert result.data["stderr"] == "operation failed"

    def test_timeout(self, tmp_path):
        plist = tmp_path / "com.test.plist"
        plist.write_text("<plist></plist>")
        with patch(_SUB_RUN, side_effect=subprocess.TimeoutExpired(cmd="launchctl", timeout=15)):
            result = thrombin(
                action="launchagent",
                plist_path=str(plist),
                launchagent_action="unload",
            )
        assert not result.success
        assert "timed out" in result.message

    def test_launchctl_called_correctly(self, tmp_path):
        plist = tmp_path / "com.test.plist"
        plist.write_text("<plist></plist>")
        with patch(_SUB_RUN, return_value=MagicMock(returncode=0)) as mock:
            thrombin(
                action="launchagent",
                plist_path=str(plist),
                launchagent_action="unload",
            )
        args = mock.call_args[0][0]
        assert args[0] == "launchctl"
        assert args[1] == "unload"
        assert str(plist) in args

    def test_tilde_expansion(self):
        """plist_path with ~ should be expanded."""
        with patch(_SUB_RUN, return_value=MagicMock(returncode=0)) as mock:
            # Use a real file via tmp_path trick: we patch Path.exists to return True
            with patch.object(Path, "exists", return_value=True):
                result = thrombin(
                    action="launchagent",
                    plist_path="~/Library/LaunchAgents/com.test.plist",
                    launchagent_action="load",
                )
        # Even if the file doesn't truly exist, Path.exists is patched to True
        assert result.success
        called_path = mock.call_args[0][0][2]
        assert "~" not in called_path  # should be expanded


# ===========================================================================
# Action: handoff
# ===========================================================================


class TestHandoffAction:
    def test_writes_file(self, tmp_path):
        with patch("metabolon.enzymes.thrombin._HANDOFF_DIR", tmp_path):
            result = thrombin(
                action="handoff",
                what_stopped="killed rogue cron",
                known_gaps="cron not restarted",
                next_steps="investigate root cause",
            )
        assert result.success
        files = list(tmp_path.glob("thrombin-*.md"))
        assert len(files) == 1

    def test_file_content_sections(self, tmp_path):
        with patch("metabolon.enzymes.thrombin._HANDOFF_DIR", tmp_path):
            thrombin(
                action="handoff",
                what_stopped="killed rogue cron",
                known_gaps="cron not restarted",
                next_steps="investigate root cause",
            )
        content = (tmp_path / next(tmp_path.glob("thrombin-*.md"))).read_text()
        assert "killed rogue cron" in content
        assert "cron not restarted" in content
        assert "investigate root cause" in content

    def test_file_has_frontmatter(self, tmp_path):
        with patch("metabolon.enzymes.thrombin._HANDOFF_DIR", tmp_path):
            thrombin(
                action="handoff",
                what_stopped="stopped X",
                known_gaps="gap Y",
                next_steps="do Z",
            )
        content = (tmp_path / next(tmp_path.glob("thrombin-*.md"))).read_text()
        assert content.startswith("---")
        assert "thrombin-handoff" in content

    def test_file_name_pattern(self, tmp_path):
        with patch("metabolon.enzymes.thrombin._HANDOFF_DIR", tmp_path):
            thrombin(
                action="handoff",
                what_stopped="a",
                known_gaps="b",
                next_steps="c",
            )
        files = list(tmp_path.glob("thrombin-????-??-??-????.md"))
        assert len(files) == 1

    def test_creates_directory_if_missing(self, tmp_path):
        subdir = tmp_path / "nested" / "dir"
        with patch("metabolon.enzymes.thrombin._HANDOFF_DIR", subdir):
            result = thrombin(
                action="handoff",
                what_stopped="a",
                known_gaps="b",
                next_steps="c",
            )
        assert result.success
        assert subdir.exists()
        assert list(subdir.glob("thrombin-*.md"))

    def test_result_message_contains_path(self, tmp_path):
        with patch("metabolon.enzymes.thrombin._HANDOFF_DIR", tmp_path):
            result = thrombin(
                action="handoff",
                what_stopped="a",
                known_gaps="b",
                next_steps="c",
            )
        assert str(tmp_path) in result.message
        assert result.data["path"] == str(next(tmp_path.glob("thrombin-*.md")))

    def test_empty_fields_allowed(self, tmp_path):
        with patch("metabolon.enzymes.thrombin._HANDOFF_DIR", tmp_path):
            result = thrombin(
                action="handoff",
                what_stopped="",
                known_gaps="",
                next_steps="",
            )
        assert result.success
