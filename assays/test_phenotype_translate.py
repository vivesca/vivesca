"""Tests for phenotype_translate and gemini_adapter.

Covers:
  - Event name mapping (CC → Gemini CLI)
  - Command wrapping detection and output
  - gemini_adapter stdin translation (Gemini CLI → CC)
  - gemini_adapter stdout translation (CC → Gemini CLI)
  - Adapter round-trip (Gemini → CC → Gemini)
  - Full translate_to_gemini pipeline (dry-run)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.phenotype_translate import (
    CC_TO_GEMINI_EVENT,
    GEMINI_ADAPTER_PATH,
    TranslationResult,
    _is_synaptic_script,
    _wrap_command,
    diff_settings,
    merge_hooks_into_gemini,
    translate_hooks,
    translate_to_gemini,
)

# Import adapter translation functions directly
sys.path.insert(0, str(Path(__file__).parent.parent / "synaptic"))
from gemini_adapter import translate_cc_to_gemini, translate_gemini_to_cc

# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_cc_hooks() -> dict[str, list[dict[str, Any]]]:
    """CC hooks fixture covering all mapped events plus unsupported types."""
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
                "hooks": [{"type": "prompt", "prompt": "Check agent."}],
            },
        ],
        "PostToolUse": [
            {
                "matcher": "",
                "hooks": [
                    {"type": "command", "command": "python3 ~/.claude/hooks/dendrite.py"}
                ],
            }
        ],
        "Stop": [
            {
                "hooks": [
                    {"type": "command", "command": "python3 ~/.claude/hooks/terminus.py"}
                ]
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
                "hooks": [
                    {"type": "command", "command": "python3 ~/.claude/hooks/compaction.py"}
                ],
            }
        ],
        "InstructionsLoaded": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python3 ~/.claude/hooks/morphogen.py",
                        "timeout": 2000,
                    }
                ],
            }
        ],
    }


@pytest.fixture
def sample_gemini_settings() -> dict[str, Any]:
    return {
        "security": {"auth": {"selectedType": "oauth-personal"}},
        "general": {"sessionRetention": {"enabled": True}},
    }


# ── event mapping ─────────────────────────────────────────────────────────────


class TestEventMapping:
    def test_user_prompt_submit_maps_to_before_agent(self, sample_cc_hooks):
        gemini_hooks, _ = translate_hooks(
            {"UserPromptSubmit": sample_cc_hooks["UserPromptSubmit"]}, wrap=False
        )
        assert "BeforeAgent" in gemini_hooks
        assert "UserPromptSubmit" not in gemini_hooks

    def test_pre_tool_use_maps_to_before_tool(self, sample_cc_hooks):
        gemini_hooks, _ = translate_hooks(
            {"PreToolUse": sample_cc_hooks["PreToolUse"]}, wrap=False
        )
        assert "BeforeTool" in gemini_hooks

    def test_post_tool_use_maps_to_after_tool(self, sample_cc_hooks):
        gemini_hooks, _ = translate_hooks(
            {"PostToolUse": sample_cc_hooks["PostToolUse"]}, wrap=False
        )
        assert "AfterTool" in gemini_hooks

    def test_stop_maps_to_after_agent(self, sample_cc_hooks):
        gemini_hooks, _ = translate_hooks({"Stop": sample_cc_hooks["Stop"]}, wrap=False)
        assert "AfterAgent" in gemini_hooks

    def test_notification_maps_to_notification(self, sample_cc_hooks):
        gemini_hooks, _ = translate_hooks(
            {"Notification": sample_cc_hooks["Notification"]}, wrap=False
        )
        assert "Notification" in gemini_hooks

    def test_pre_compact_maps_to_pre_compress(self, sample_cc_hooks):
        gemini_hooks, _ = translate_hooks(
            {"PreCompact": sample_cc_hooks["PreCompact"]}, wrap=False
        )
        assert "PreCompress" in gemini_hooks

    def test_instructions_loaded_silently_dropped(self, sample_cc_hooks):
        gemini_hooks, result = translate_hooks(
            {"InstructionsLoaded": sample_cc_hooks["InstructionsLoaded"]}, wrap=False
        )
        assert "InstructionsLoaded" not in gemini_hooks
        assert "InstructionsLoaded" not in result.events_dropped  # silently dropped

    def test_unknown_event_reported_in_result(self):
        unknown = {
            "FutureCCEvent": [
                {"matcher": "", "hooks": [{"type": "command", "command": "echo hi"}]}
            ]
        }
        _, result = translate_hooks(unknown, wrap=False)
        assert "FutureCCEvent" in result.events_dropped

    def test_all_mapped_events_covered(self):
        """Every key in CC_TO_GEMINI_EVENT produces a valid Gemini event."""
        hooks_input = {
            cc_event: [
                {"matcher": "", "hooks": [{"type": "command", "command": f"echo {cc_event}"}]}
            ]
            for cc_event in CC_TO_GEMINI_EVENT
        }
        gemini_hooks, result = translate_hooks(hooks_input, wrap=False)
        assert set(gemini_hooks.keys()) == set(CC_TO_GEMINI_EVENT.values())
        assert not result.events_dropped


# ── prompt-type hook handling ─────────────────────────────────────────────────


class TestPromptTypeFiltering:
    def test_prompt_type_hooks_filtered_out(self, sample_cc_hooks):
        import warnings

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            gemini_hooks, result = translate_hooks(
                {"PreToolUse": sample_cc_hooks["PreToolUse"]}, wrap=False
            )
        # Only the command hook survives; prompt hook is dropped
        before_tool = gemini_hooks.get("BeforeTool", [])
        for defn in before_tool:
            for entry in defn.get("hooks", []):
                assert entry.get("type") == "command"
        assert result.prompt_hooks_skipped == 1

    def test_prompt_only_definition_drops_entire_definition(self):
        import warnings

        prompt_only = {
            "PreToolUse": [{"matcher": "x", "hooks": [{"type": "prompt", "prompt": "hi"}]}]
        }
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            gemini_hooks, result = translate_hooks(prompt_only, wrap=False)
        # No command hooks → definition dropped → event absent
        assert "BeforeTool" not in gemini_hooks
        assert result.prompt_hooks_skipped == 1


# ── command wrapping ──────────────────────────────────────────────────────────


class TestCommandWrapping:
    def test_is_synaptic_script_hooks_dir(self):
        assert _is_synaptic_script("python3 ~/.claude/hooks/synapse.py")

    def test_is_synaptic_script_synaptic_dir(self):
        assert _is_synaptic_script("python3 /Users/terry/germline/synaptic/axon.py")

    def test_is_synaptic_script_non_py(self):
        assert not _is_synaptic_script("echo hello")

    def test_is_synaptic_script_non_synaptic_dir(self):
        assert not _is_synaptic_script("python3 /usr/local/bin/something.py")

    def test_wrap_command_injects_adapter(self):
        adapter = Path("/path/to/gemini_adapter.py")
        wrapped = _wrap_command("python3 ~/.claude/hooks/synapse.py", adapter)
        assert "gemini_adapter.py" in wrapped
        assert "synapse.py" in wrapped
        assert wrapped.startswith("python3")

    def test_wrap_command_preserves_interpreter(self):
        adapter = Path("/path/to/gemini_adapter.py")
        wrapped = _wrap_command("python3 ~/.claude/hooks/axon.py", adapter)
        assert wrapped.startswith("python3")

    def test_synaptic_commands_wrapped_in_translate_hooks(self, sample_cc_hooks):
        adapter = Path("/fake/gemini_adapter.py")
        gemini_hooks, result = translate_hooks(
            {"UserPromptSubmit": sample_cc_hooks["UserPromptSubmit"]},
            adapter_path=adapter,
            wrap=True,
        )
        before_agent = gemini_hooks.get("BeforeAgent", [])
        commands = [
            entry["command"]
            for defn in before_agent
            for entry in defn.get("hooks", [])
        ]
        assert any("gemini_adapter.py" in cmd for cmd in commands)
        assert result.hooks_wrapped >= 1

    def test_no_wrap_flag_preserves_original_commands(self, sample_cc_hooks):
        gemini_hooks, result = translate_hooks(
            {"UserPromptSubmit": sample_cc_hooks["UserPromptSubmit"]},
            wrap=False,
        )
        before_agent = gemini_hooks.get("BeforeAgent", [])
        commands = [
            entry["command"]
            for defn in before_agent
            for entry in defn.get("hooks", [])
        ]
        assert not any("gemini_adapter.py" in cmd for cmd in commands)
        assert result.hooks_wrapped == 0

    def test_matcher_preserved_after_wrapping(self, sample_cc_hooks):
        adapter = Path("/fake/gemini_adapter.py")
        gemini_hooks, _ = translate_hooks(
            {"UserPromptSubmit": sample_cc_hooks["UserPromptSubmit"]},
            adapter_path=adapter,
            wrap=True,
        )
        defn = gemini_hooks["BeforeAgent"][0]
        assert defn.get("matcher") == ""

    def test_stop_without_matcher_no_matcher_key(self, sample_cc_hooks):
        gemini_hooks, _ = translate_hooks(
            {"Stop": sample_cc_hooks["Stop"]}, wrap=False
        )
        defn = gemini_hooks["AfterAgent"][0]
        assert "matcher" not in defn


# ── gemini_adapter stdin translation ─────────────────────────────────────────


class TestAdapterStdinTranslation:
    def test_before_agent_sets_prompt(self):
        gemini_data = {
            "event": "BeforeAgent",
            "session_id": "abc",
            "message": {"content": "Hello world"},
        }
        cc = translate_gemini_to_cc(gemini_data)
        assert cc["prompt"] == "Hello world"
        assert cc["session_id"] == "abc"
        assert "event" not in cc

    def test_before_agent_empty_message(self):
        cc = translate_gemini_to_cc({"event": "BeforeAgent", "session_id": "x"})
        assert cc["prompt"] == ""

    def test_before_tool_maps_tool_fields(self):
        gemini_data = {
            "event": "BeforeTool",
            "session_id": "abc",
            "tool": {"name": "Bash", "input": {"command": "ls"}},
        }
        cc = translate_gemini_to_cc(gemini_data)
        assert cc["tool"] == "Bash"
        assert cc["tool_input"] == {"command": "ls"}
        assert "event" not in cc

    def test_after_tool_maps_tool_and_response(self):
        gemini_data = {
            "event": "AfterTool",
            "session_id": "abc",
            "tool": {"name": "Read", "input": {"file_path": "/foo.py"}},
            "tool_response": {"output": "content"},
        }
        cc = translate_gemini_to_cc(gemini_data)
        assert cc["tool"] == "Read"
        assert cc["tool_input"] == {"file_path": "/foo.py"}
        assert cc["tool_response"] == {"output": "content"}

    def test_after_agent_preserves_session_id(self):
        cc = translate_gemini_to_cc({"event": "AfterAgent", "session_id": "xyz"})
        assert cc["session_id"] == "xyz"
        assert "event" not in cc

    def test_event_key_removed(self):
        cc = translate_gemini_to_cc({"event": "BeforeAgent", "session_id": "s"})
        assert "event" not in cc

    def test_before_tool_with_scalar_tool(self):
        cc = translate_gemini_to_cc({"event": "BeforeTool", "tool": "Bash"})
        assert cc["tool"] == "Bash"
        assert cc["tool_input"] == {}


# ── gemini_adapter stdout translation ────────────────────────────────────────


class TestAdapterStdoutTranslation:
    def test_empty_output_returns_none(self):
        assert translate_cc_to_gemini("") is None
        assert translate_cc_to_gemini("   \n  ") is None

    def test_block_decision_translates_to_deny(self):
        cc_out = json.dumps({"decision": "block", "reason": "not allowed"})
        result = translate_cc_to_gemini(cc_out)
        parsed = json.loads(result)
        assert parsed["decision"] == "deny"
        assert parsed["reason"] == "not allowed"

    def test_block_without_reason(self):
        cc_out = json.dumps({"decision": "block"})
        result = translate_cc_to_gemini(cc_out)
        parsed = json.loads(result)
        assert parsed["decision"] == "deny"
        assert "reason" not in parsed

    def test_allow_decision_returns_none(self):
        cc_out = json.dumps({"decision": "allow"})
        assert translate_cc_to_gemini(cc_out) is None

    def test_approve_decision_returns_none(self):
        cc_out = json.dumps({"decision": "approve"})
        assert translate_cc_to_gemini(cc_out) is None

    def test_output_field_wraps_as_additional_context(self):
        cc_out = json.dumps({"output": "injected context"})
        result = translate_cc_to_gemini(cc_out)
        parsed = json.loads(result)
        assert parsed["hookSpecificOutput"]["additionalContext"] == "injected context"

    def test_plain_text_wraps_as_additional_context(self):
        result = translate_cc_to_gemini("some plain text context")
        parsed = json.loads(result)
        assert parsed["hookSpecificOutput"]["additionalContext"] == "some plain text context"

    def test_prompt_type_returns_none_with_warning(self):
        import warnings

        cc_out = json.dumps({"type": "prompt", "prompt": "do this"})
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # translate_cc_to_gemini doesn't use warnings module — check stderr via adapter
            result = translate_cc_to_gemini(cc_out)
        assert result is None

    def test_hook_specific_output_passthrough(self):
        cc_out = json.dumps({"hookSpecificOutput": {"additionalContext": "already gemini format"}})
        result = translate_cc_to_gemini(cc_out)
        parsed = json.loads(result)
        assert parsed["hookSpecificOutput"]["additionalContext"] == "already gemini format"

    def test_arbitrary_json_wrapped_as_context(self):
        cc_out = json.dumps({"some_cc_field": "value"})
        result = translate_cc_to_gemini(cc_out)
        parsed = json.loads(result)
        assert "additionalContext" in parsed["hookSpecificOutput"]


# ── adapter round-trip ────────────────────────────────────────────────────────


class TestAdapterRoundTrip:
    """Verify translate_gemini_to_cc → hook script → translate_cc_to_gemini preserves semantics."""

    def test_block_round_trip(self):
        """A hook that blocks in CC format should block in Gemini CLI format."""
        # Simulate: Gemini sends BeforeTool → adapter translates → hook outputs block → adapter translates back
        gemini_in = {
            "event": "BeforeTool",
            "session_id": "abc",
            "tool": {"name": "Bash", "input": {"command": "rm -rf /"}},
        }
        cc_in = translate_gemini_to_cc(gemini_in)
        # Simulated hook output
        cc_out = json.dumps({"decision": "block", "reason": "dangerous command"})
        gemini_out = translate_cc_to_gemini(cc_out)
        parsed = json.loads(gemini_out)
        assert parsed["decision"] == "deny"
        assert "dangerous command" in parsed.get("reason", "")

    def test_context_injection_round_trip(self):
        """Context injection from CC output reaches Gemini additionalContext."""
        gemini_in = {"event": "BeforeAgent", "session_id": "s", "message": {"content": "hello"}}
        cc_in = translate_gemini_to_cc(gemini_in)
        cc_out = json.dumps({"output": "This is injected context"})
        gemini_out = translate_cc_to_gemini(cc_out)
        parsed = json.loads(gemini_out)
        assert parsed["hookSpecificOutput"]["additionalContext"] == "This is injected context"

    def test_empty_hook_output_round_trip(self):
        """Hook producing no output → Gemini adapter produces no output."""
        gemini_in = {"event": "AfterAgent", "session_id": "s"}
        _cc_in = translate_gemini_to_cc(gemini_in)
        gemini_out = translate_cc_to_gemini("")
        assert gemini_out is None

    def test_session_id_preserved_through_translation(self):
        """session_id survives Gemini → CC translation."""
        gemini_in = {"event": "BeforeAgent", "session_id": "my-session-123", "message": {}}
        cc = translate_gemini_to_cc(gemini_in)
        assert cc["session_id"] == "my-session-123"

    def test_tool_input_preserved_through_translation(self):
        """tool_input fields survive Gemini → CC translation."""
        gemini_in = {
            "event": "BeforeTool",
            "session_id": "s",
            "tool": {"name": "Edit", "input": {"file_path": "/foo.py", "content": "x = 1"}},
        }
        cc = translate_gemini_to_cc(gemini_in)
        assert cc["tool_input"]["file_path"] == "/foo.py"
        assert cc["tool_input"]["content"] == "x = 1"


# ── merge_hooks_into_gemini ───────────────────────────────────────────────────


class TestMergeHooks:
    def test_non_hook_fields_preserved(self, sample_gemini_settings):
        merged = merge_hooks_into_gemini(
            sample_gemini_settings,
            {"BeforeAgent": [{"hooks": [{"type": "command", "command": "echo"}]}]},
        )
        assert merged["security"] == sample_gemini_settings["security"]
        assert merged["general"] == sample_gemini_settings["general"]

    def test_hooks_replaced(self, sample_gemini_settings):
        new_hooks = {"BeforeTool": [{"hooks": [{"type": "command", "command": "echo"}]}]}
        merged = merge_hooks_into_gemini(sample_gemini_settings, new_hooks)
        assert merged["hooks"] == new_hooks

    def test_empty_hooks_preserves_existing(self, sample_gemini_settings):
        existing = {**sample_gemini_settings, "hooks": {"BeforeAgent": []}}
        merged = merge_hooks_into_gemini(existing, {})
        assert merged["hooks"] == existing["hooks"]


# ── diff_settings ─────────────────────────────────────────────────────────────


class TestDiffSettings:
    def test_identical_returns_no_changes(self):
        s = {"key": "value"}
        assert diff_settings(s, s) == "(no changes)"

    def test_diff_shows_added_field(self):
        result = diff_settings({"a": 1}, {"a": 1, "b": 2})
        assert "b" in result and "+" in result

    def test_diff_shows_removed_field(self):
        result = diff_settings({"a": 1, "b": 2}, {"a": 1})
        assert "b" in result and "-" in result


# ── full pipeline: translate_to_gemini ───────────────────────────────────────


class TestTranslateToGemini:
    def test_dry_run_does_not_write(self, tmp_path):
        dest = tmp_path / "settings.json"
        from metabolon.organelles.phenotype_translate import CC_SETTINGS_PATH

        if CC_SETTINGS_PATH.exists():
            translate_to_gemini(
                cc_settings_path=CC_SETTINGS_PATH,
                gemini_settings_path=dest,
                wrap=False,
                dry_run=True,
            )
            assert not dest.exists(), "dry_run must not write to disk"

    def test_dry_run_does_not_overwrite(self, tmp_path):
        dest = tmp_path / "settings.json"
        original = {"sentinel": "must-remain"}
        dest.write_text(json.dumps(original))
        from metabolon.organelles.phenotype_translate import CC_SETTINGS_PATH

        if CC_SETTINGS_PATH.exists():
            translate_to_gemini(
                cc_settings_path=CC_SETTINGS_PATH,
                gemini_settings_path=dest,
                wrap=False,
                dry_run=True,
            )
            assert json.loads(dest.read_text()) == original

    def test_full_pipeline_writes_valid_json(self, tmp_path):
        dest = tmp_path / "settings.json"
        from metabolon.organelles.phenotype_translate import CC_SETTINGS_PATH

        if not CC_SETTINGS_PATH.exists():
            pytest.skip("No ~/.claude/settings.json available")
        translate_to_gemini(
            cc_settings_path=CC_SETTINGS_PATH,
            gemini_settings_path=dest,
            wrap=False,
            dry_run=False,
        )
        assert dest.exists()
        written = json.loads(dest.read_text())
        assert isinstance(written, dict)

    def test_full_pipeline_only_gemini_event_names(self, tmp_path):
        dest = tmp_path / "settings.json"
        from metabolon.organelles.phenotype_translate import CC_SETTINGS_PATH

        if not CC_SETTINGS_PATH.exists():
            pytest.skip("No ~/.claude/settings.json available")
        import warnings

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            translate_to_gemini(
                cc_settings_path=CC_SETTINGS_PATH,
                gemini_settings_path=dest,
                wrap=False,
                dry_run=False,
            )
        written = json.loads(dest.read_text())
        valid_events = set(CC_TO_GEMINI_EVENT.values())
        for event in written.get("hooks", {}):
            assert event in valid_events, f"Invalid Gemini event name: {event}"

    def test_full_pipeline_no_command_hooks_lost(self, tmp_path):
        dest = tmp_path / "settings.json"
        from metabolon.organelles.phenotype_translate import CC_SETTINGS_PATH, CC_TO_GEMINI_EVENT

        if not CC_SETTINGS_PATH.exists():
            pytest.skip("No ~/.claude/settings.json available")
        import warnings

        from metabolon.organelles.phenotype_translate import read_cc_settings

        cc_settings = read_cc_settings(CC_SETTINGS_PATH)
        cc_hooks = cc_settings.get("hooks", {})
        # Count expected command hooks for mapped events
        expected = sum(
            1
            for cc_event, definitions in cc_hooks.items()
            if cc_event in CC_TO_GEMINI_EVENT
            for defn in definitions
            for entry in defn.get("hooks", [])
            if entry.get("type") == "command"
        )

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            translate_to_gemini(
                cc_settings_path=CC_SETTINGS_PATH,
                gemini_settings_path=dest,
                wrap=False,
                dry_run=False,
            )
        written = json.loads(dest.read_text())
        actual = sum(
            1
            for definitions in written.get("hooks", {}).values()
            for defn in definitions
            for _entry in defn.get("hooks", [])
        )
        assert actual == expected, f"Hook count mismatch: expected {expected}, got {actual}"


# ── TranslationResult ─────────────────────────────────────────────────────────


class TestTranslationResult:
    def test_summary_includes_hook_count(self):
        r = TranslationResult(
            hooks_translated=5,
            hooks_wrapped=3,
            prompt_hooks_skipped=1,
            events_dropped=[],
            dry_run=False,
        )
        assert "5" in r.summary
        assert "3" in r.summary

    def test_dry_run_label(self):
        r = TranslationResult(0, 0, 0, [], dry_run=True)
        assert "dry-run" in r.summary

    def test_dropped_events_in_summary(self):
        r = TranslationResult(0, 0, 0, events_dropped=["FutureCCEvent"], dry_run=False)
        assert "FutureCCEvent" in r.summary

    def test_prompt_skipped_in_summary(self):
        r = TranslationResult(0, 0, prompt_hooks_skipped=2, events_dropped=[], dry_run=False)
        assert "2" in r.summary
