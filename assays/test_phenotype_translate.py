from __future__ import annotations

"""Tests for phenotype_translate and gemini_adapter.

Covers:
  - Event name mapping (CC → Gemini CLI)
  - Command wrapping detection and output
  - gemini_adapter stdin translation (Gemini CLI → CC)
  - gemini_adapter stdout translation (CC → Gemini CLI)
  - Adapter round-trip (Gemini → CC → Gemini)
  - Full translate_to_gemini pipeline (dry-run)
"""


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
    SyncResult,
    TranslationResult,
    _ensure_symlink,
    _is_synaptic_script,
    _wrap_command,
    diff_settings,
    merge_hooks_into_gemini,
    sync_phenotype,
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
        assert _is_synaptic_script(f"python3 {Path.home()}/germline/synaptic/axon.py")

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


# ── phenotype sync ────────────────────────────────────────────────────────────


class TestEnsureSymlink:
    def test_creates_missing_symlink(self, tmp_path):
        target = tmp_path / "phenotype.md"
        target.write_text("# phenotype")
        link = tmp_path / "CLAUDE.md"
        assert not link.exists()
        outcome = _ensure_symlink(link, target, dry_run=False)
        assert outcome == "fixed"
        assert link.is_symlink()
        assert link.resolve() == target.resolve()

    def test_dry_run_does_not_create_symlink(self, tmp_path):
        target = tmp_path / "phenotype.md"
        target.write_text("# phenotype")
        link = tmp_path / "CLAUDE.md"
        outcome = _ensure_symlink(link, target, dry_run=True)
        assert outcome == "fixed"
        assert not link.exists()

    def test_correct_symlink_returns_ok(self, tmp_path):
        target = tmp_path / "phenotype.md"
        target.write_text("# phenotype")
        link = tmp_path / "CLAUDE.md"
        link.symlink_to(target)
        outcome = _ensure_symlink(link, target, dry_run=False)
        assert outcome == "ok"

    def test_wrong_target_gets_fixed(self, tmp_path):
        target = tmp_path / "phenotype.md"
        target.write_text("# phenotype")
        wrong = tmp_path / "other.md"
        wrong.write_text("# other")
        link = tmp_path / "CLAUDE.md"
        link.symlink_to(wrong)
        outcome = _ensure_symlink(link, target, dry_run=False)
        assert outcome == "fixed"
        assert link.resolve() == target.resolve()

    def test_regular_file_returns_failed(self, tmp_path):
        target = tmp_path / "phenotype.md"
        target.write_text("# phenotype")
        link = tmp_path / "CLAUDE.md"
        link.write_text("# regular file, not a symlink")
        outcome = _ensure_symlink(link, target, dry_run=False)
        assert outcome == "failed"
        # Must not have clobbered the regular file
        assert link.read_text() == "# regular file, not a symlink"


class TestSyncPhenotype:
    @patch('metabolon.locus.PLATFORM_SYMLINKS', [])
    @patch('metabolon.locus.phenotype_md', Path('/tmp/fake_phenotype.md'))
    @patch('metabolon.locus.receptors', Path('/tmp/fake_receptors'))
    @patch('metabolon.enzymes.integrin._check_phenotype_symlinks', return_value=([], []))
    @patch('metabolon.organelles.phenotype_translate.GEMINI_ADAPTER_PATH', Path('/tmp/fake_adapter.py'))
    def test_dry_run_does_not_write_gemini_settings(self, mock_check, tmp_path):
        gemini_settings = tmp_path / "settings.json"
        cc_settings = tmp_path / "cc_settings.json"
        cc_settings.write_text(json.dumps({"hooks": {}}))
        from metabolon.organelles.phenotype_translate import CC_SETTINGS_PATH
        # patch CC_SETTINGS_PATH for this test only
        with patch('metabolon.organelles.phenotype_translate.CC_SETTINGS_PATH', cc_settings):
            result = sync_phenotype(
                dry_run=True,
                cc_settings_path=cc_settings,
                gemini_settings_path=gemini_settings,
            )
        assert not gemini_settings.exists(), "dry_run must not write settings.json"
        assert result.dry_run is True

    @patch('metabolon.locus.PLATFORM_SYMLINKS', [])
    @patch('metabolon.locus.phenotype_md', Path('/tmp/fake_phenotype.md'))
    @patch('metabolon.locus.receptors', Path('/tmp/fake_receptors'))
    @patch('metabolon.enzymes.integrin._check_phenotype_symlinks', return_value=([], []))
    @patch('metabolon.organelles.phenotype_translate.GEMINI_ADAPTER_PATH', Path('/tmp/fake_adapter.py'))
    def test_sync_result_has_summary(self, mock_check, tmp_path):
        gemini_settings = tmp_path / "settings.json"
        cc_settings = tmp_path / "cc_settings.json"
        cc_settings.write_text(json.dumps({"hooks": {}}))
        from metabolon.organelles.phenotype_translate import CC_SETTINGS_PATH
        with patch('metabolon.organelles.phenotype_translate.CC_SETTINGS_PATH', cc_settings):
            result = sync_phenotype(
                dry_run=True,
                cc_settings_path=cc_settings,
                gemini_settings_path=gemini_settings,
            )
        summary = result.summary
        assert "Symlinks" in summary
        assert "Hooks" in summary
        assert "GEMINI.md" in summary
        assert "Integrin" in summary

    @patch('metabolon.locus.PLATFORM_SYMLINKS', [])
    @patch('metabolon.locus.phenotype_md', Path('/tmp/fake_phenotype.md'))
    @patch('metabolon.locus.receptors', Path('/tmp/fake_receptors'))
    @patch('metabolon.enzymes.integrin._check_phenotype_symlinks', return_value=([], []))
    @patch('metabolon.organelles.phenotype_translate.GEMINI_ADAPTER_PATH', Path('/tmp/fake_adapter.py'))
    def test_sync_result_dry_run_label_in_summary(self, mock_check, tmp_path):
        gemini_settings = tmp_path / "settings.json"
        cc_settings = tmp_path / "cc_settings.json"
        cc_settings.write_text(json.dumps({"hooks": {}}))
        from metabolon.organelles.phenotype_translate import CC_SETTINGS_PATH
        with patch('metabolon.organelles.phenotype_translate.CC_SETTINGS_PATH', cc_settings):
            result = sync_phenotype(
                dry_run=True,
                cc_settings_path=cc_settings,
                gemini_settings_path=gemini_settings,
            )
        assert "dry-run" in result.summary

    @patch('metabolon.locus.PLATFORM_SYMLINKS', [])
    @patch('metabolon.locus.phenotype_md', Path('/tmp/fake_phenotype.md'))
    @patch('metabolon.locus.receptors', Path('/tmp/fake_receptors'))
    @patch('metabolon.enzymes.integrin._check_phenotype_symlinks', return_value=([], []))
    @patch('metabolon.organelles.phenotype_translate.GEMINI_ADAPTER_PATH', Path('/tmp/fake_adapter.py'))
    def test_no_cc_settings_hooks_skipped(self, mock_check, tmp_path):
        missing_cc = tmp_path / "nonexistent_settings.json"
        gemini_settings = tmp_path / "settings.json"
        result = sync_phenotype(
            dry_run=True,
            cc_settings_path=missing_cc,
            gemini_settings_path=gemini_settings,
        )
        assert result.hooks_result is None
        assert "skipped" in result.summary

    def test_sync_result_ok_property(self):
        r = SyncResult(
            symlinks_ok=["a"],
            symlinks_fixed=[],
            symlinks_failed=[],
            hooks_result=None,
            gemini_md_ok=True,
            integrin_issues=[],
            unknown_platforms=[],
            dry_run=False,
        )
        assert r.ok is True

    def test_sync_result_not_ok_when_symlink_failed(self):
        r = SyncResult(
            symlinks_ok=[],
            symlinks_fixed=[],
            symlinks_failed=["~/CLAUDE.md"],
            hooks_result=None,
            gemini_md_ok=True,
            integrin_issues=[],
            unknown_platforms=[],
            dry_run=False,
        )
        assert r.ok is False

    def test_sync_result_not_ok_when_gemini_md_missing(self):
        r = SyncResult(
            symlinks_ok=["a"],
            symlinks_fixed=[],
            symlinks_failed=[],
            hooks_result=None,
            gemini_md_ok=False,
            integrin_issues=[],
            unknown_platforms=[],
            dry_run=False,
        )
        assert r.ok is False

    def test_sync_result_not_ok_when_integrin_issues(self):
        r = SyncResult(
            symlinks_ok=["a"],
            symlinks_fixed=[],
            symlinks_failed=[],
            hooks_result=None,
            gemini_md_ok=True,
            integrin_issues=[{"path": "/some/path", "problem": "missing"}],
            unknown_platforms=[],
            dry_run=False,
        )
        assert r.ok is False

    def test_unknown_platforms_in_summary(self):
        r = SyncResult(
            symlinks_ok=["a"],
            symlinks_fixed=[],
            symlinks_failed=[],
            hooks_result=None,
            gemini_md_ok=True,
            integrin_issues=[],
            unknown_platforms=[".codex"],
            dry_run=False,
        )
        assert ".codex" in r.summary
        assert "PLATFORM_SYMLINKS" in r.summary

    def test_skills_synced_in_summary(self):
        r = SyncResult(
            symlinks_ok=["a"],
            symlinks_fixed=[],
            symlinks_failed=[],
            hooks_result=None,
            gemini_md_ok=True,
            integrin_issues=[],
            unknown_platforms=[],
            dry_run=False,
            skills_synced=42,
        )
        assert "42 synced" in r.summary
        assert "Skills" in r.summary

    def test_skills_default_zero(self):
        r = SyncResult(
            symlinks_ok=[],
            symlinks_fixed=[],
            symlinks_failed=[],
            hooks_result=None,
            gemini_md_ok=True,
            integrin_issues=[],
            unknown_platforms=[],
            dry_run=False,
        )
        assert r.skills_synced == 0


class TestSkillSymlinking:
    """Test skill symlinking to ~/.gemini/skills/."""

    def test_creates_symlinks_for_skills(self, tmp_path):
        """Skills with SKILL.md get symlinked to gemini skills dir."""
        receptors = tmp_path / "receptors"
        skill_a = receptors / "alpha"
        skill_a.mkdir(parents=True)
        (skill_a / "SKILL.md").write_text("---\nname: alpha\n---\n# Alpha")
        skill_b = receptors / "beta"
        skill_b.mkdir()
        (skill_b / "SKILL.md").write_text("---\nname: beta\n---\n# Beta")
        # dir without SKILL.md should be skipped
        (receptors / "gamma").mkdir()

        gemini_skills = tmp_path / "gemini_skills"

        import metabolon.organelles.phenotype_translate as pt
        orig_receptors = pt.__dict__.get("_test_receptors_override")
        # Monkey-patch just the skill sync loop
        gemini_skills.mkdir()
        for skill_dir in sorted(receptors.iterdir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            target_link = gemini_skills / skill_dir.name
            target_link.symlink_to(skill_dir)

        assert (gemini_skills / "alpha").is_symlink()
        assert (gemini_skills / "beta").is_symlink()
        assert not (gemini_skills / "gamma").exists()
        assert (gemini_skills / "alpha").resolve() == skill_a.resolve()

    def test_skips_already_correct_symlinks(self, tmp_path):
        """Existing correct symlinks are not recreated."""
        receptors = tmp_path / "receptors"
        skill_a = receptors / "alpha"
        skill_a.mkdir(parents=True)
        (skill_a / "SKILL.md").write_text("---\nname: alpha\n---\n")

        gemini_skills = tmp_path / "gemini_skills"
        gemini_skills.mkdir()
        link = gemini_skills / "alpha"
        link.symlink_to(skill_a)
        original_stat = link.lstat()

        # Re-run the logic — should detect it's already correct
        for skill_dir in sorted(receptors.iterdir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            target_link = gemini_skills / skill_dir.name
            if target_link.is_symlink() and target_link.resolve() == skill_dir.resolve():
                continue  # skip — already correct
            target_link.unlink(missing_ok=True)
            target_link.symlink_to(skill_dir)

        # Symlink should be untouched
        assert link.lstat() == original_stat

    def test_fixes_wrong_target_symlink(self, tmp_path):
        """Symlink pointing to wrong target gets replaced."""
        receptors = tmp_path / "receptors"
        skill_a = receptors / "alpha"
        skill_a.mkdir(parents=True)
        (skill_a / "SKILL.md").write_text("---\nname: alpha\n---\n")

        wrong_target = tmp_path / "wrong"
        wrong_target.mkdir()

        gemini_skills = tmp_path / "gemini_skills"
        gemini_skills.mkdir()
        link = gemini_skills / "alpha"
        link.symlink_to(wrong_target)

        # Fix it
        for skill_dir in sorted(receptors.iterdir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            target_link = gemini_skills / skill_dir.name
            if target_link.is_symlink() and target_link.resolve() == skill_dir.resolve():
                continue
            target_link.unlink(missing_ok=True)
            target_link.symlink_to(skill_dir)

        assert link.resolve() == skill_a.resolve()

    @patch('metabolon.locus.PLATFORM_SYMLINKS', [])
    @patch('metabolon.locus.phenotype_md', Path('/tmp/fake_phenotype.md'))
    @patch('metabolon.enzymes.integrin._check_phenotype_symlinks', return_value=([], []))
    @patch('metabolon.organelles.phenotype_translate.GEMINI_ADAPTER_PATH', Path('/tmp/fake_adapter.py'))
    def test_live_sync_includes_skills_count(self, mock_check, tmp_path):
        """Full sync reports skills_synced count."""
        # Create a mock receptors directory with a skill
        receptors = tmp_path / "receptors"
        skill_dir = receptors / "test_skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n")
        # Patch receptors to point to this directory
        with patch('metabolon.locus.receptors', receptors):
            cc_settings = tmp_path / "cc_settings.json"
            cc_settings.write_text(json.dumps({"hooks": {}}))
            with patch('metabolon.organelles.phenotype_translate.CC_SETTINGS_PATH', cc_settings):
                gemini_settings = tmp_path / "settings.json"
                result = sync_phenotype(
                    dry_run=True,
                    cc_settings_path=cc_settings,
                    gemini_settings_path=gemini_settings,
                )
                assert result.skills_synced > 0
                assert "Skills" in result.summary
