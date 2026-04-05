"""Tests for metabolon/enzymes/thrombin.py"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestPsAction:
    """Tests for the 'ps' action of thrombin."""

    def test_ps_returns_matching_processes(self):
        from metabolon.enzymes.thrombin import thrombin

        mock_result = MagicMock()
        mock_result.stdout = "1234 /usr/bin/python app.py\n5678 /usr/bin/python worker.py\n"
        with patch("metabolon.enzymes.thrombin.subprocess.run", return_value=mock_result):
            result = thrombin(action="ps", pattern="python")

        assert result.count == 2
        assert result.matches == [
            "1234 /usr/bin/python app.py",
            "5678 /usr/bin/python worker.py",
        ]
        assert "python" in result.summary

    def test_ps_no_matches(self):
        from metabolon.enzymes.thrombin import thrombin

        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("metabolon.enzymes.thrombin.subprocess.run", return_value=mock_result):
            result = thrombin(action="ps", pattern="nonexistent_xyz")

        assert result.count == 0
        assert result.matches == []
        assert "(none)" in result.summary

    def test_ps_timeout_returns_empty(self):
        import subprocess

        from metabolon.enzymes.thrombin import thrombin

        with patch(
            "metabolon.enzymes.thrombin.subprocess.run",
            side_effect=subprocess.TimeoutExpired("pgrep", 5),
        ):
            result = thrombin(action="ps", pattern="slow_proc")

        assert result.count == 0
        assert result.matches == []

    def test_ps_strips_blank_lines(self):
        from metabolon.enzymes.thrombin import thrombin

        mock_result = MagicMock()
        mock_result.stdout = "1234 proc1\n\n\n5678 proc2\n\n"
        with patch("metabolon.enzymes.thrombin.subprocess.run", return_value=mock_result):
            result = thrombin(action="ps", pattern="proc")

        assert result.count == 2


class TestKillAction:
    """Tests for the 'kill' action of thrombin."""

    def test_kill_success(self):
        from metabolon.enzymes.thrombin import thrombin

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        with patch("metabolon.enzymes.thrombin.subprocess.run", return_value=mock_result):
            result = thrombin(action="kill", pattern="rogue_proc", signal="TERM")

        assert result.success is True
        assert "TERM" in result.message
        assert "rogue_proc" in result.message

    def test_kill_no_match(self):
        from metabolon.enzymes.thrombin import thrombin

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = ""
        with patch("metabolon.enzymes.thrombin.subprocess.run", return_value=mock_result):
            result = thrombin(action="kill", pattern="nonexistent")

        assert result.success is False
        assert "No processes found" in result.message

    def test_kill_pkill_error(self):
        from metabolon.enzymes.thrombin import thrombin

        mock_result = MagicMock()
        mock_result.returncode = 2
        mock_result.stderr = "permission denied"
        with patch("metabolon.enzymes.thrombin.subprocess.run", return_value=mock_result):
            result = thrombin(action="kill", pattern="something")

        assert result.success is False
        assert "pkill error" in result.message

    def test_kill_invalid_signal(self):
        from metabolon.enzymes.thrombin import thrombin

        result = thrombin(action="kill", pattern="proc", signal="BADSIG")

        assert result.success is False
        assert "Invalid signal" in result.message

    def test_kill_timeout(self):
        import subprocess

        from metabolon.enzymes.thrombin import thrombin

        with patch(
            "metabolon.enzymes.thrombin.subprocess.run",
            side_effect=subprocess.TimeoutExpired("pkill", 10),
        ):
            result = thrombin(action="kill", pattern="hung_proc")

        assert result.success is False
        assert "timed out" in result.message

    def test_kill_accepts_valid_signals(self):
        from metabolon.enzymes.thrombin import thrombin

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        with patch(
            "metabolon.enzymes.thrombin.subprocess.run", return_value=mock_result
        ) as mock_run:
            result = thrombin(action="kill", pattern="proc", signal="KILL")

        assert result.success is True
        mock_run.assert_called_once_with(
            ["pkill", "-KILL", "-f", "proc"],
            capture_output=True,
            text=True,
            timeout=10,
        )


class TestLaunchagentAction:
    """Tests for the 'launchagent' action of thrombin."""

    def test_unload_success(self):
        from metabolon.enzymes.thrombin import thrombin

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        with (
            patch("metabolon.enzymes.thrombin.subprocess.run", return_value=mock_result),
            patch("metabolon.enzymes.thrombin.Path.exists", return_value=True),
            patch("metabolon.enzymes.thrombin.platform.system", return_value="Darwin"),
        ):
            result = thrombin(
                action="launchagent",
                plist_path="/Library/LaunchAgents/com.example.agent.plist",
                launchagent_action="unload",
            )

        assert result.success is True
        assert "Unloaded" in result.message

    def test_load_success(self):
        from metabolon.enzymes.thrombin import thrombin

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        with (
            patch("metabolon.enzymes.thrombin.subprocess.run", return_value=mock_result),
            patch("metabolon.enzymes.thrombin.Path.exists", return_value=True),
            patch("metabolon.enzymes.thrombin.platform.system", return_value="Darwin"),
        ):
            result = thrombin(
                action="launchagent",
                plist_path="/Library/LaunchAgents/com.example.agent.plist",
                launchagent_action="load",
            )

        assert result.success is True
        assert "Loaded" in result.message

    def test_plist_not_found(self):
        from metabolon.enzymes.thrombin import thrombin

        with (
            patch("metabolon.enzymes.thrombin.Path.exists", return_value=False),
            patch("metabolon.enzymes.thrombin.platform.system", return_value="Darwin"),
        ):
            result = thrombin(
                action="launchagent",
                plist_path="/nonexistent/plist.plist",
            )

        assert result.success is False
        assert "not found" in result.message.lower()

    def test_invalid_launchagent_action(self):
        from metabolon.enzymes.thrombin import thrombin

        with (
            patch("metabolon.enzymes.thrombin.Path.exists", return_value=True),
            patch("metabolon.enzymes.thrombin.platform.system", return_value="Darwin"),
        ):
            result = thrombin(
                action="launchagent",
                plist_path="/Library/LaunchAgents/com.test.plist",
                launchagent_action="restart",
            )

        assert result.success is False
        assert "Invalid action" in result.message

    def test_launchctl_failure(self):
        from metabolon.enzymes.thrombin import thrombin

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "operation not permitted"
        with (
            patch("metabolon.enzymes.thrombin.subprocess.run", return_value=mock_result),
            patch("metabolon.enzymes.thrombin.Path.exists", return_value=True),
            patch("metabolon.enzymes.thrombin.platform.system", return_value="Darwin"),
        ):
            result = thrombin(
                action="launchagent",
                plist_path="/Library/LaunchAgents/com.test.plist",
                launchagent_action="unload",
            )

        assert result.success is False
        assert "failed" in result.message.lower()

    def test_launchagent_timeout(self):
        import subprocess

        from metabolon.enzymes.thrombin import thrombin

        with (
            patch(
                "metabolon.enzymes.thrombin.subprocess.run",
                side_effect=subprocess.TimeoutExpired("launchctl", 15),
            ),
            patch("metabolon.enzymes.thrombin.Path.exists", return_value=True),
        ):
            result = thrombin(
                action="launchagent",
                plist_path="/Library/LaunchAgents/com.test.plist",
            )

        assert result.success is False
        assert "timed out" in result.message

    def test_launchagent_non_darwin_rejected(self):
        """On non-Darwin platforms, launchagent action should be rejected."""
        from metabolon.enzymes.thrombin import thrombin

        with patch("metabolon.enzymes.thrombin.platform.system", return_value="Linux"):
            result = thrombin(
                action="launchagent",
                plist_path="/Library/LaunchAgents/com.test.plist",
                launchagent_action="unload",
            )

        assert result.success is False
        assert "launchctl is not available" in result.message
        assert "Linux" in result.message


class TestHandoffAction:
    """Tests for the 'handoff' action of thrombin."""

    def test_writes_handoff_note(self, tmp_path):
        from metabolon.enzymes import thrombin as mod

        handoff_dir = tmp_path / "Thrombin"
        with patch.object(mod, "_HANDOFF_DIR", handoff_dir):
            result = mod.thrombin(
                action="handoff",
                what_stopped="Rogue worker process",
                known_gaps="Redis still flaky",
                next_steps="Restart workers after Redis fix",
            )

        assert result.success is True
        assert "Handoff note written" in result.message

        # Verify file was created
        files = list(handoff_dir.glob("thrombin-*.md"))
        assert len(files) == 1

        content = files[0].read_text()
        assert "Rogue worker process" in content
        assert "Redis still flaky" in content
        assert "Restart workers after Redis fix" in content
        assert "thrombin-handoff" in content

    def test_handoff_creates_directory(self, tmp_path):
        from metabolon.enzymes import thrombin as mod

        handoff_dir = tmp_path / "nested" / "Thrombin"
        assert not handoff_dir.exists()

        with patch.object(mod, "_HANDOFF_DIR", handoff_dir):
            result = mod.thrombin(
                action="handoff",
                what_stopped="test",
                known_gaps="none",
                next_steps="none",
            )

        assert result.success is True
        assert handoff_dir.exists()


class TestUnknownAction:
    """Tests for unknown/invalid actions."""

    def test_unknown_action_returns_error(self):
        from metabolon.enzymes.thrombin import thrombin

        result = thrombin(action="foobar")

        assert result.success is False
        assert "Unknown action" in result.message

    def test_action_is_case_insensitive(self):
        from metabolon.enzymes.thrombin import thrombin

        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch(
            "metabolon.enzymes.thrombin.subprocess.run", return_value=mock_result
        ) as mock_run:
            result = thrombin(action="PS", pattern="test")

        assert result.count == 0
        mock_run.assert_called_once()
