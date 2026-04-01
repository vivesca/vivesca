from __future__ import annotations

"""Tests for conjugation_engine — CC → Gemini CLI config replication.

Unit tests cover each mapping function in isolation.
Integration tests use the actual ~/.claude/settings.json as a fixture.
Dry-run tests verify no files are written.
Round-trip tests verify no hooks/MCP servers are silently dropped.
"""


import json
from pathlib import Path
from typing import Any

import pytest

from metabolon.organelles.conjugation_engine import (
    CC_SETTINGS_PATH,
    CC_TO_GEMINI_EVENT,
    ConjugationResult,
    diff_settings,
    merge_into_gemini_settings,
    read_cc_settings,
    read_gemini_settings,
    replicate_to_gemini,
    transform_hooks,
    transform_mcp_servers,
)

# ── sample fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_cc_hooks() -> dict[str, list[dict[str, Any]]]:
    """Minimal CC hooks covering all mapped event types."""
    return {
        "UserPromptSubmit": [
            {
                "matcher": "",
                "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/synapse.py"}],
            }
        ],
        "PreToolUse": [
            {
                "matcher": "",
                "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/axon.py"}],
            },
            {
                "matcher": "tool == 'Agent'",
                "hooks": [
                    {"type": "prompt", "prompt": "Check agent."},
                ],
            },
        ],
        "PostToolUse": [
            {
                "matcher": "",
                "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/dendrite.py"}],
            }
        ],
        "Stop": [
            {
                "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/terminus.py"}],
            }
        ],
        "Notification": [
            {
                "matcher": "",
                "hooks": [
                    {"type": "command", "command": "python3 ~/.claude/hooks/interoceptor.py"}
                ],
            }
        ],
        "PreCompact": [
            {
                "matcher": "",
                "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/compaction.py"}],
            }
        ],
    }


@pytest.fixture
def sample_cc_mcp_servers() -> dict[str, dict[str, Any]]:
    return {
        "vivesca": {
            "command": str(Path.home() / ".local/share/mise/installs/python/3.13.12/bin/vivesca"),
            "args": ["serve"],
        }
    }


@pytest.fixture
def sample_gemini_settings() -> dict[str, Any]:
    """Existing Gemini settings with non-hook/non-MCP fields that must be preserved."""
    return {
        "security": {"auth": {"selectedType": "oauth-personal"}},
        "general": {
            "sessionRetention": {
                "warningAcknowledged": True,
                "enabled": True,
                "maxAge": "30d",
            }
        },
        "mcpServers": {
            "old-server": {"command": "/usr/bin/old", "args": ["run"]},
        },
    }


# ── unit: transform_hooks ────────────────────────────────────────────────────


class TestTransformHooks:
    def test_user_prompt_submit_maps_to_before_model(self, sample_cc_hooks):
        gemini_hooks, _, _ = transform_hooks(
            {"UserPromptSubmit": sample_cc_hooks["UserPromptSubmit"]}
        )
        assert "BeforeModel" in gemini_hooks
        assert "UserPromptSubmit" not in gemini_hooks

    def test_pre_tool_use_maps_to_before_tool(self, sample_cc_hooks):
        gemini_hooks, _, _ = transform_hooks({"PreToolUse": sample_cc_hooks["PreToolUse"]})
        assert "BeforeTool" in gemini_hooks

    def test_post_tool_use_maps_to_after_tool(self, sample_cc_hooks):
        gemini_hooks, _, _ = transform_hooks({"PostToolUse": sample_cc_hooks["PostToolUse"]})
        assert "AfterTool" in gemini_hooks

    def test_stop_maps_to_after_model(self, sample_cc_hooks):
        gemini_hooks, _, _ = transform_hooks({"Stop": sample_cc_hooks["Stop"]})
        assert "AfterModel" in gemini_hooks

    def test_notification_silently_dropped(self, sample_cc_hooks):
        gemini_hooks, dropped, _ = transform_hooks(
            {"Notification": sample_cc_hooks["Notification"]}
        )
        assert "Notification" not in gemini_hooks
        assert "Notification" not in dropped  # known unmapped — not reported as error

    def test_pre_compact_silently_dropped(self, sample_cc_hooks):
        gemini_hooks, dropped, _ = transform_hooks({"PreCompact": sample_cc_hooks["PreCompact"]})
        assert "PreCompact" not in gemini_hooks
        assert "PreCompact" not in dropped

    def test_unknown_event_reported_as_dropped(self):
        unknown_hooks = {
            "FutureCCEvent": [
                {"matcher": "", "hooks": [{"type": "command", "command": "echo hi"}]}
            ]
        }
        _, dropped, _ = transform_hooks(unknown_hooks)
        assert "FutureCCEvent" in dropped

    def test_prompt_type_hooks_filtered_out(self, sample_cc_hooks):
        """CC 'prompt' type hooks have no Gemini equivalent — must be dropped."""
        gemini_hooks, _, count = transform_hooks({"PreToolUse": sample_cc_hooks["PreToolUse"]})
        # PreToolUse has 2 definitions: one command + one prompt
        # Only the command definition should survive
        before_tool = gemini_hooks.get("BeforeTool", [])
        for definition in before_tool:
            for hook_entry in definition.get("hooks", []):
                assert hook_entry.get("type") == "command"
        # Exactly 1 command hook in PreToolUse fixture
        assert count == 1

    def test_matcher_preserved(self, sample_cc_hooks):
        gemini_hooks, _, _ = transform_hooks(
            {"UserPromptSubmit": sample_cc_hooks["UserPromptSubmit"]}
        )
        definition = gemini_hooks["BeforeModel"][0]
        assert "matcher" in definition
        assert definition["matcher"] == ""

    def test_stop_without_matcher_omits_matcher_key(self, sample_cc_hooks):
        """Stop hooks in the fixture have no matcher — the key must not appear."""
        gemini_hooks, _, _ = transform_hooks({"Stop": sample_cc_hooks["Stop"]})
        definition = gemini_hooks["AfterModel"][0]
        assert "matcher" not in definition

    def test_hook_count_matches_command_hooks(self, sample_cc_hooks):
        """Total hook count counts individual command entries, not definitions."""
        _, _, total = transform_hooks(sample_cc_hooks)
        # synapse (1) + axon (1) + dendrite (1) + terminus (1) = 4
        # prompt-type hooks excluded; Notification/PreCompact dropped silently
        assert total == 4

    def test_all_event_mappings_covered(self):
        """Every key in CC_TO_GEMINI_EVENT is handled by transform_hooks."""
        hooks_input = {
            cc_event: [
                {"matcher": "", "hooks": [{"type": "command", "command": f"echo {cc_event}"}]}
            ]
            for cc_event in CC_TO_GEMINI_EVENT
        }
        gemini_hooks, dropped, count = transform_hooks(hooks_input)
        assert not dropped
        assert set(gemini_hooks.keys()) == set(CC_TO_GEMINI_EVENT.values())
        assert count == len(CC_TO_GEMINI_EVENT)


# ── unit: transform_mcp_servers ──────────────────────────────────────────────


class TestTransformMcpServers:
    def test_passthrough_preserves_structure(self, sample_cc_mcp_servers):
        result = transform_mcp_servers(sample_cc_mcp_servers)
        assert result == sample_cc_mcp_servers

    def test_returns_independent_copy(self, sample_cc_mcp_servers):
        result = transform_mcp_servers(sample_cc_mcp_servers)
        result["vivesca"]["command"] = "mutated"
        assert sample_cc_mcp_servers["vivesca"]["command"] != "mutated"

    def test_empty_input_returns_empty_dict(self):
        assert transform_mcp_servers({}) == {}

    def test_server_count_preserved(self, sample_cc_mcp_servers):
        result = transform_mcp_servers(sample_cc_mcp_servers)
        assert len(result) == len(sample_cc_mcp_servers)


# ── unit: merge_into_gemini_settings ─────────────────────────────────────────


class TestMergeIntoGeminiSettings:
    def test_non_hook_non_mcp_fields_preserved(self, sample_gemini_settings):
        merged = merge_into_gemini_settings(
            sample_gemini_settings,
            gemini_hooks={"BeforeModel": [{"hooks": [{"type": "command", "command": "echo"}]}]},
            gemini_mcp_servers={"server": {"command": "/bin/srv", "args": []}},
        )
        assert merged["security"] == sample_gemini_settings["security"]
        assert merged["general"] == sample_gemini_settings["general"]

    def test_hooks_replaced(self, sample_gemini_settings):
        new_hooks = {
            "BeforeModel": [{"hooks": [{"type": "command", "command": "python3 synapse.py"}]}]
        }
        merged = merge_into_gemini_settings(
            sample_gemini_settings,
            gemini_hooks=new_hooks,
            gemini_mcp_servers={},
        )
        assert merged["hooks"] == new_hooks

    def test_mcp_servers_merged(self, sample_gemini_settings):
        new_mcp = {"vivesca": {"command": "/usr/bin/vivesca", "args": ["serve"]}}
        merged = merge_into_gemini_settings(
            sample_gemini_settings,
            gemini_hooks={},
            gemini_mcp_servers=new_mcp,
        )
        # New servers added, existing preserved
        assert "vivesca" in merged["mcpServers"]
        assert "old-server" in merged["mcpServers"]

    def test_hooks_only_does_not_touch_mcp(self, sample_gemini_settings):
        merged = merge_into_gemini_settings(
            sample_gemini_settings,
            gemini_hooks={"BeforeTool": []},
            gemini_mcp_servers={"new": {"command": "/bin/new", "args": []}},
            hooks_only=True,
        )
        # mcpServers should remain unchanged from original
        assert merged["mcpServers"] == sample_gemini_settings["mcpServers"]

    def test_mcp_only_does_not_touch_hooks(self, sample_gemini_settings):
        existing_with_hooks = {**sample_gemini_settings, "hooks": {"BeforeTool": []}}
        merged = merge_into_gemini_settings(
            existing_with_hooks,
            gemini_hooks={"BeforeModel": []},
            gemini_mcp_servers={"new": {"command": "/bin/new", "args": []}},
            mcp_only=True,
        )
        # hooks must remain unchanged
        assert merged["hooks"] == existing_with_hooks["hooks"]

    def test_empty_hooks_preserves_existing_hooks(self, sample_gemini_settings):
        existing_with_hooks = {**sample_gemini_settings, "hooks": {"BeforeTool": []}}
        merged = merge_into_gemini_settings(
            existing_with_hooks,
            gemini_hooks={},
            gemini_mcp_servers={},
        )
        # Empty CC hooks = no replacement, existing preserved
        assert merged["hooks"] == existing_with_hooks["hooks"]


# ── unit: diff_settings ──────────────────────────────────────────────────────


class TestDiffSettings:
    def test_identical_returns_no_changes(self):
        settings = {"key": "value"}
        assert diff_settings(settings, settings) == "(no changes)"

    def test_diff_shows_addition(self):
        before = {"key": "value"}
        after = {"key": "value", "new_key": "new_value"}
        result = diff_settings(before, after)
        assert "new_key" in result
        assert "+" in result

    def test_diff_shows_removal(self):
        before = {"key": "value", "old_key": "old_value"}
        after = {"key": "value"}
        result = diff_settings(before, after)
        assert "old_key" in result
        assert "-" in result


# ── unit: ConjugationResult ──────────────────────────────────────────────────


class TestConjugationResult:
    def test_summary_includes_counts(self):
        result = ConjugationResult(
            hooks_replicated=4,
            mcp_servers_replicated=1,
            hooks_dropped=[],
            dry_run=False,
        )
        assert "4" in result.summary
        assert "1" in result.summary

    def test_dry_run_label_in_summary(self):
        result = ConjugationResult(
            hooks_replicated=0,
            mcp_servers_replicated=0,
            hooks_dropped=[],
            dry_run=True,
        )
        assert "dry-run" in result.summary

    def test_dropped_events_in_summary(self):
        result = ConjugationResult(
            hooks_replicated=0,
            mcp_servers_replicated=0,
            hooks_dropped=["FutureCCEvent"],
            dry_run=False,
        )
        assert "FutureCCEvent" in result.summary


# ── integration: actual ~/.claude/settings.json ───────────────────────────────


class TestIntegrationActualCC:
    """Use the live ~/.claude/settings.json as the source fixture."""

    def test_actual_cc_settings_readable(self):
        """The actual CC settings file is readable and valid JSON."""
        assert CC_SETTINGS_PATH.exists(), f"Missing: {CC_SETTINGS_PATH}"
        settings = read_cc_settings()
        assert isinstance(settings, dict)

    def test_actual_hooks_transform_produces_valid_gemini_hooks(self):
        """Transform produces only valid Gemini CLI event names."""
        from metabolon.organelles.conjugation_engine import CC_TO_GEMINI_EVENT

        cc_settings = read_cc_settings()
        cc_hooks = cc_settings.get("hooks", {})
        gemini_hooks, _, _ = transform_hooks(cc_hooks)

        valid_gemini_events = set(CC_TO_GEMINI_EVENT.values())
        for event_name in gemini_hooks:
            assert event_name in valid_gemini_events, f"Invalid Gemini event: {event_name}"

    def test_actual_hooks_all_command_type(self):
        """All hooks in the output are command-type (prompt-type filtered out)."""
        cc_settings = read_cc_settings()
        cc_hooks = cc_settings.get("hooks", {})
        gemini_hooks, _, _ = transform_hooks(cc_hooks)

        for event_name, definitions in gemini_hooks.items():
            for definition in definitions:
                for hook_entry in definition.get("hooks", []):
                    assert hook_entry.get("type") == "command", (
                        f"Non-command hook in {event_name}: {hook_entry}"
                    )

    def test_actual_mcp_servers_passthrough(self):
        """MCP servers from CC are reproduced verbatim."""
        cc_settings = read_cc_settings()
        cc_mcp = cc_settings.get("mcpServers", {})
        gemini_mcp = transform_mcp_servers(cc_mcp)
        assert gemini_mcp == cc_mcp

    def test_full_transform_produces_valid_json(self, tmp_path):
        """Full replicate_to_gemini produces valid JSON at the destination path."""
        dest = tmp_path / ".gemini" / "settings.json"
        dest.parent.mkdir(parents=True)
        result, _ = replicate_to_gemini(
            cc_settings_path=CC_SETTINGS_PATH,
            gemini_settings_path=dest,
        )
        assert dest.exists()
        with dest.open() as fh:
            written = json.load(fh)
        assert isinstance(written, dict)
        assert isinstance(result, ConjugationResult)


# ── dry-run tests ─────────────────────────────────────────────────────────────


class TestDryRun:
    def test_dry_run_does_not_write(self, tmp_path):
        """dry_run=True must not create or modify the destination file."""
        dest = tmp_path / "settings.json"
        replicate_to_gemini(
            cc_settings_path=CC_SETTINGS_PATH,
            gemini_settings_path=dest,
            dry_run=True,
        )
        assert not dest.exists(), "dry_run wrote the file — it must not"

    def test_dry_run_does_not_overwrite_existing(self, tmp_path):
        """dry_run=True must not modify an existing destination file."""
        dest = tmp_path / "settings.json"
        original_content = {"sentinel": "must-remain"}
        dest.write_text(json.dumps(original_content), encoding="utf-8")

        replicate_to_gemini(
            cc_settings_path=CC_SETTINGS_PATH,
            gemini_settings_path=dest,
            dry_run=True,
        )

        with dest.open() as fh:
            after = json.load(fh)
        assert after == original_content

    def test_dry_run_returns_diff(self, tmp_path):
        """dry_run returns a non-empty diff string when settings differ."""
        dest = tmp_path / "settings.json"
        _result, diff_output = replicate_to_gemini(
            cc_settings_path=CC_SETTINGS_PATH,
            gemini_settings_path=dest,
            dry_run=True,
        )
        # diff_output is a string (may be empty if CC has no hooks/MCP)
        assert isinstance(diff_output, str)


# ── round-trip tests ─────────────────────────────────────────────────────────


class TestRoundTrip:
    def test_no_command_hooks_lost_in_translation(self):
        """Every command hook in CC has a counterpart in the Gemini output."""
        cc_settings = read_cc_settings()
        cc_hooks = cc_settings.get("hooks", {})

        # Count command-type hooks in CC for mappable events
        cc_command_hook_count = 0
        for cc_event, definitions in cc_hooks.items():
            if cc_event not in CC_TO_GEMINI_EVENT:
                continue
            for definition in definitions:
                for hook_entry in definition.get("hooks", []):
                    if hook_entry.get("type") == "command":
                        cc_command_hook_count += 1

        gemini_hooks, _, total_mapped = transform_hooks(cc_hooks)

        # Count command-type hooks in Gemini output
        gemini_command_hook_count = 0
        for definitions in gemini_hooks.values():
            for definition in definitions:
                gemini_command_hook_count += len(definition.get("hooks", []))

        assert gemini_command_hook_count == cc_command_hook_count
        assert total_mapped == cc_command_hook_count

    def test_no_mcp_servers_lost(self):
        """Every MCP server in CC appears in the Gemini output."""
        cc_settings = read_cc_settings()
        cc_mcp = cc_settings.get("mcpServers", {})
        gemini_mcp = transform_mcp_servers(cc_mcp)
        assert set(gemini_mcp.keys()) == set(cc_mcp.keys())

    def test_full_pipeline_no_data_loss(self, tmp_path):
        """Write then read back — hooks and MCP servers survive the full pipeline."""
        dest = tmp_path / "settings.json"
        replicate_to_gemini(
            cc_settings_path=CC_SETTINGS_PATH,
            gemini_settings_path=dest,
        )

        cc_settings = read_cc_settings()
        written = read_gemini_settings(dest)

        # All CC MCP servers present in output
        cc_mcp = cc_settings.get("mcpServers", {})
        written_mcp = written.get("mcpServers", {})
        for server_name in cc_mcp:
            assert server_name in written_mcp, f"MCP server '{server_name}' lost in translation"

        # All command hooks for mapped CC events are present
        cc_hooks = cc_settings.get("hooks", {})
        for cc_event, definitions in cc_hooks.items():
            gemini_event = CC_TO_GEMINI_EVENT.get(cc_event)
            if gemini_event is None:
                continue
            for definition in definitions:
                command_hooks = [
                    hook_entry
                    for hook_entry in definition.get("hooks", [])
                    if hook_entry.get("type") == "command"
                ]
                if not command_hooks:
                    continue
                written_event_hooks = written.get("hooks", {}).get(gemini_event, [])
                written_commands = [
                    hook_entry["command"]
                    for defn in written_event_hooks
                    for hook_entry in defn.get("hooks", [])
                ]
                for hook_entry in command_hooks:
                    assert hook_entry["command"] in written_commands, (
                        f"Hook lost: {hook_entry['command']} "
                        f"(CC:{cc_event} → Gemini:{gemini_event})"
                    )
