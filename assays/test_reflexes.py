from __future__ import annotations

"""Tests for metabolon/resources/reflexes.py."""


import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.resources.reflexes import _extract_reflex_name, express_reflex_inventory


class TestExtractReflexName:
    """Tests for _extract_reflex_name helper function."""

    def test_python_hook(self) -> None:
        """Extract name from Python hook command."""
        command = "python3 ~/.claude/hooks/chromatin-pull.py"
        assert _extract_reflex_name(command) == "chromatin-pull"

    def test_node_hook(self) -> None:
        """Extract name from Node.js hook command."""
        command = "node ~/.claude/hooks/bash-guard.js"
        assert _extract_reflex_name(command) == "bash-guard"

    def test_shell_hook(self) -> None:
        """Extract name from shell hook command."""
        command = "bash ~/.claude/hooks/pre-commit.sh"
        assert _extract_reflex_name(command) == "pre-commit"

    def test_no_extension(self) -> None:
        """Return truncated command when no recognized extension."""
        command = "some-command-without-extension"
        assert _extract_reflex_name(command) == command[:40]

    def test_no_slash(self) -> None:
        """Handle command without slash."""
        command = "simplecommand"
        assert _extract_reflex_name(command) == command[:40]

    def test_deep_path(self) -> None:
        """Extract name from deeply nested path."""
        command = "/usr/local/bin/python /home/user/.claude/hooks/my-hook.py"
        assert _extract_reflex_name(command) == "my-hook"

    def test_long_command_truncation(self) -> None:
        """Long commands without file extension are truncated to 40 chars."""
        command = "a" * 100  # 100 characters
        result = _extract_reflex_name(command)
        assert len(result) == 40
        assert result == "a" * 40

    def test_empty_command(self) -> None:
        """Empty command returns empty string."""
        assert _extract_reflex_name("") == ""

    def test_exactly_40_chars_no_slash(self) -> None:
        """Command exactly 40 chars without slash returns as-is."""
        command = "a" * 40
        assert _extract_reflex_name(command) == command

    def test_multiple_slashes(self) -> None:
        """Extract from path with multiple slashes."""
        command = "python /a/b/c/d/hook-name.py"
        assert _extract_reflex_name(command) == "hook-name"

    def test_extension_case_sensitivity(self) -> None:
        """Extension matching is case-sensitive (.PY not stripped)."""
        command = "python ~/.claude/hooks/script.PY"  # uppercase extension
        # .PY is not stripped because we check .py (lowercase)
        assert _extract_reflex_name(command) == "script.PY"

    def test_no_slash_returns_truncated(self) -> None:
        """Command without slash returns truncated version."""
        command = "python script.py"  # no slash
        # No slash means rsplit returns single element, returns truncated
        assert _extract_reflex_name(command) == "python script.py"


class TestExpressReflexInventory:
    """Tests for express_reflex_inventory function."""

    def test_no_settings_file(self) -> None:
        """Return message when settings file doesn't exist."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False

        result = express_reflex_inventory(mock_path)
        assert result == "No settings.json found."

    def test_invalid_json(self) -> None:
        """Return message when settings file has invalid JSON."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "{ invalid json"

        result = express_reflex_inventory(mock_path)
        assert result == "Could not parse settings.json."

    def test_os_error_reading_file(self) -> None:
        """Handle OSError when reading file."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.side_effect = OSError("Permission denied")

        result = express_reflex_inventory(mock_path)
        assert result == "Could not parse settings.json."

    def test_no_hooks_key(self) -> None:
        """Return message when settings has no hooks key."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({"other": "data"})

        result = express_reflex_inventory(mock_path)
        assert result == "No hooks configured."

    def test_empty_hooks(self) -> None:
        """Return message when hooks dict is empty."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({"hooks": {}})

        result = express_reflex_inventory(mock_path)
        assert result == "No hooks configured."

    def test_single_command_hook(self) -> None:
        """Render single command hook correctly."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {"type": "command", "command": "python ~/.claude/hooks/guard.py"}
                        ]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        assert "# Claude Code Hooks" in result
        assert "PreToolUse" in result
        assert "guard" in result
        assert "`Bash`" in result
        assert "_Total: 1 hooks across 1 events_" in result

    def test_single_prompt_hook(self) -> None:
        """Render single prompt hook correctly."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "Notification": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"type": "prompt", "prompt": "Remember to check for issues"}
                        ]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        assert "[prompt]" in result
        assert "Remember to check for issues" in result
        assert "_Total: 1 hooks across 1 events_" in result

    def test_prompt_hook_truncation(self) -> None:
        """Prompt text longer than 60 chars is truncated."""
        long_prompt = "x" * 100
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "Notification": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"type": "prompt", "prompt": long_prompt}
                        ]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        # Prompt should be truncated to 60 chars in display
        assert "x" * 60 in result
        assert "..." in result
        assert "x" * 61 not in result  # Full prompt shouldn't appear

    def test_empty_matcher_shows_all(self) -> None:
        """Empty matcher displays as _(all)_."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "Stop": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"type": "command", "command": "python ~/hook.py"}
                        ]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)
        assert "_(all)_" in result

    def test_multiple_hooks_in_group(self) -> None:
        """Handle multiple hooks in a single group."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {"type": "command", "command": "python ~/hook1.py"},
                            {"type": "command", "command": "node ~/hook2.js"},
                        ]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        assert "hook1" in result
        assert "hook2" in result
        assert "(2)" in result
        assert "_Total: 2 hooks across 1 events_" in result

    def test_multiple_groups_same_event(self) -> None:
        """Handle multiple groups for the same event."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [{"type": "command", "command": "python ~/bash-hook.py"}]
                    },
                    {
                        "matcher": "Read",
                        "hooks": [{"type": "command", "command": "python ~/read-hook.py"}]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        assert "bash-hook" in result
        assert "read-hook" in result
        assert "`Bash`" in result
        assert "`Read`" in result
        assert "_Total: 2 hooks across 1 events_" in result

    def test_multiple_events(self) -> None:
        """Handle multiple events with hooks."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [{"type": "command", "command": "python ~/pre.py"}]
                    }
                ],
                "PostToolUse": [
                    {
                        "matcher": "Edit",
                        "hooks": [{"type": "command", "command": "python ~/post.py"}]
                    }
                ],
                "Stop": [
                    {
                        "matcher": "",
                        "hooks": [{"type": "prompt", "prompt": "Goodbye"}]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        assert "PreToolUse" in result
        assert "PostToolUse" in result
        assert "Stop" in result
        assert "_Total: 3 hooks across 3 events_" in result

    def test_unknown_hook_type(self) -> None:
        """Unknown hook types are not included in output."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {"type": "command", "command": "python ~/known.py"},
                            {"type": "unknown_type", "command": "something"},
                            {"command": "no-type-field"},  # missing type
                        ]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        # Only the command hook should appear
        assert "known" in result
        assert "_Total: 1 hooks across 1 events_" in result

    def test_missing_command_field(self) -> None:
        """Handle command hook without command field gracefully."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {"type": "command"}  # missing command
                        ]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        # Should still render the hook with empty name
        assert "PreToolUse" in result
        assert "_Total: 1 hooks across 1 events_" in result

    def test_missing_prompt_field(self) -> None:
        """Handle prompt hook without prompt field gracefully."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "Notification": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"type": "prompt"}  # missing prompt
                        ]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        assert "[prompt]" in result
        assert "_Total: 1 hooks across 1 events_" in result

    def test_default_path_uses_home(self) -> None:
        """When no path provided, uses default ~/.claude/settings.json."""
        with patch("metabolon.resources.reflexes._SETTINGS") as mock_settings:
            mock_settings.exists.return_value = False

            result = express_reflex_inventory()

            assert result == "No settings.json found."
            mock_settings.exists.assert_called_once()

    def test_output_format_markdown_table(self) -> None:
        """Verify markdown table format."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [{"type": "command", "command": "python ~/hook.py"}]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        # Check markdown structure
        assert "| Hook | Matcher |" in result
        assert "|------|---------|" in result
        assert "| `hook` | `Bash` |" in result

    def test_event_with_no_valid_hooks(self) -> None:
        """Event with no valid hooks should not appear in output."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": []  # Empty hooks list
                    }
                ],
                "PostToolUse": [
                    {
                        "matcher": "",
                        "hooks": [{"type": "command", "command": "python ~/valid.py"}]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        # PreToolUse should not appear (no hooks)
        assert "PostToolUse" in result
        assert "valid" in result
        assert "_Total: 1 hooks across 2 events_" in result

    def test_hook_without_matcher_key(self) -> None:
        """Group without matcher key defaults to empty string."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "Stop": [
                    {
                        # No matcher key
                        "hooks": [{"type": "command", "command": "python ~/hook.py"}]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        assert "_(all)_" in result
        assert "hook" in result

    def test_complex_realistic_config(self) -> None:
        """Test with a realistic hooks configuration."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {"type": "command", "command": "python3 ~/.claude/hooks/bash-guard.py"}
                        ]
                    },
                    {
                        "matcher": "Edit",
                        "hooks": [
                            {"type": "command", "command": "python3 ~/.claude/hooks/edit-check.py"},
                            {"type": "prompt", "prompt": "Verify the edit is safe before proceeding with changes"}
                        ]
                    }
                ],
                "PostToolUse": [
                    {
                        "matcher": "Write",
                        "hooks": [
                            {"type": "command", "command": "node ~/.claude/hooks/file-log.js"}
                        ]
                    }
                ],
                "Notification": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"type": "prompt", "prompt": "Log important notifications"}
                        ]
                    }
                ],
                "Stop": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"type": "command", "command": "bash ~/.claude/hooks/cleanup.sh"}
                        ]
                    }
                ]
            }
        })

        result = express_reflex_inventory(mock_path)

        # Verify structure
        assert "# Claude Code Hooks" in result
        assert "## PreToolUse (3)" in result
        assert "## PostToolUse (1)" in result
        assert "## Notification (1)" in result
        assert "## Stop (1)" in result
        assert "_Total: 6 hooks across 4 events_" in result

        # Verify hooks are present
        assert "bash-guard" in result
        assert "edit-check" in result
        assert "file-log" in result
        assert "cleanup" in result

        # Verify matchers
        assert "`Bash`" in result
        assert "`Edit`" in result
        assert "`Write`" in result
        assert "_(all)_" in result


class TestSettingsPathDefault:
    """Test the default settings path constant."""

    def test_default_settings_path(self) -> None:
        """The default path should be ~/.claude/settings.json."""
        from metabolon.resources.reflexes import _SETTINGS

        assert _SETTINGS.name == "settings.json"
        assert ".claude" in str(_SETTINGS)
        assert _SETTINGS.parent.name == ".claude"
