from __future__ import annotations

"""Tests for conjugation_engine — CC→Gemini config replication."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.organelles.conjugation_engine import (
    CC_TO_GEMINI_EVENT,
    ConjugationResult,
    diff_settings,
    merge_into_gemini_settings,
    read_cc_settings,
    read_gemini_settings,
    replicate_to_gemini,
    transform_hooks,
    transform_mcp_servers,
    transform_skills,
)


# ── Event mapping ────────────────────────────────────────────────────────────


class TestEventMapping:
    def test_all_four_cc_events_mapped(self):
        assert CC_TO_GEMINI_EVENT == {
            "UserPromptSubmit": "BeforeModel",
            "PreToolUse": "BeforeTool",
            "PostToolUse": "AfterTool",
            "Stop": "AfterModel",
        }


class TestUnmappedEvents:
    def test_notification_silently_dropped(self):
        from metabolon.organelles.conjugation_engine import _CC_UNMAPPED_EVENTS

        _, dropped, _ = transform_hooks(
            {"Notification": [{"hooks": [{"type": "command", "command": "echo"}]}]}
        )
        assert "Notification" not in dropped
        assert "Notification" in _CC_UNMAPPED_EVENTS

    def test_pre_compact_silently_dropped(self):
        from metabolon.organelles.conjugation_engine import _CC_UNMAPPED_EVENTS

        _, dropped, _ = transform_hooks(
            {"PreCompact": [{"hooks": [{"type": "command", "command": "echo"}]}]}
        )
        assert "PreCompact" not in dropped

    def test_instructions_loaded_silently_dropped(self):
        _, dropped, _ = transform_hooks(
            {"InstructionsLoaded": [{"hooks": [{"type": "command", "command": "echo"}]}]}
        )
        assert "InstructionsLoaded" not in dropped


# ── read_cc_settings / read_gemini_settings ──────────────────────────────────


class TestReadCcSettings:
    def test_missing_file_returns_empty(self, tmp_path):
        assert read_cc_settings(tmp_path / "nope.json") == {}

    def test_valid_json(self, tmp_path):
        f = tmp_path / "settings.json"
        f.write_text(json.dumps({"hooks": {}}))
        assert read_cc_settings(f) == {"hooks": {}}

    def test_invalid_json_returns_empty(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("NOT JSON {{{")
        assert read_cc_settings(f) == {}

    def test_unreadable_file_returns_empty(self, tmp_path):
        f = tmp_path / "secret.json"
        f.write_text("{}")
        f.chmod(0o000)
        try:
            assert read_cc_settings(f) == {}
        finally:
            f.chmod(0o644)

    def test_uses_default_path(self):
        """read_cc_settings() with no args uses CC_SETTINGS_PATH."""
        with patch("metabolon.organelles.conjugation_engine.CC_SETTINGS_PATH") as mock_path:
            mock_path.exists.return_value = False
            assert read_cc_settings() == {}


class TestReadGeminiSettings:
    def test_missing_file_returns_empty(self, tmp_path):
        assert read_gemini_settings(tmp_path / "nope.json") == {}

    def test_valid_json(self, tmp_path):
        f = tmp_path / "gemini.json"
        f.write_text(json.dumps({"hooks": {"BeforeModel": []}}))
        assert read_gemini_settings(f) == {"hooks": {"BeforeModel": []}}

    def test_invalid_json_returns_empty(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("BROKEN")
        assert read_gemini_settings(f) == {}

    def test_uses_default_path(self):
        with patch("metabolon.organelles.conjugation_engine.GEMINI_SETTINGS_PATH") as mock_path:
            mock_path.exists.return_value = False
            assert read_gemini_settings() == {}


# ── transform_hooks ──────────────────────────────────────────────────────────


class TestTransformHooks:
    def test_single_command_hook(self):
        gemini_hooks, dropped, count = transform_hooks(
            {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "echo test"}]}]}
        )
        assert "BeforeModel" in gemini_hooks
        assert count == 1
        assert dropped == []

    def test_maps_all_four_events(self):
        cc_hooks = {
            event: [{"hooks": [{"type": "command", "command": f"cmd_{event}"}]}]
            for event in CC_TO_GEMINI_EVENT
        }
        gemini_hooks, dropped, count = transform_hooks(cc_hooks)
        assert set(gemini_hooks.keys()) == set(CC_TO_GEMINI_EVENT.values())
        assert count == 4
        assert dropped == []

    def test_unknown_event_reported_as_dropped(self):
        _, dropped, _ = transform_hooks(
            {"SomeNewEvent": [{"hooks": [{"type": "command", "command": "echo"}]}]}
        )
        assert dropped == ["SomeNewEvent"]

    def test_multiple_dropped_events(self):
        _, dropped, _ = transform_hooks(
            {
                "Foo": [{"hooks": [{"type": "command", "command": "a"}]}],
                "Bar": [{"hooks": [{"type": "command", "command": "b"}]}],
            }
        )
        assert set(dropped) == {"Foo", "Bar"}

    def test_preserves_matcher(self):
        gemini_hooks, _, _ = transform_hooks(
            {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo"}]}]}
        )
        assert gemini_hooks["BeforeTool"][0]["matcher"] == "Bash"

    def test_omits_matcher_when_absent(self):
        gemini_hooks, _, _ = transform_hooks(
            {"PreToolUse": [{"hooks": [{"type": "command", "command": "echo"}]}]}
        )
        assert "matcher" not in gemini_hooks["BeforeTool"][0]

    def test_filters_prompt_type_hooks(self):
        gemini_hooks, _, count = transform_hooks(
            {"PreToolUse": [{"hooks": [{"type": "prompt", "prompt": "Be careful"}]}]}
        )
        assert count == 0
        assert gemini_hooks == {}

    def test_mixed_command_and_prompt_in_same_definition(self):
        gemini_hooks, _, count = transform_hooks(
            {
                "PreToolUse": [
                    {
                        "hooks": [
                            {"type": "prompt", "prompt": "Be careful"},
                            {"type": "command", "command": "check.sh"},
                        ]
                    }
                ]
            }
        )
        assert count == 1
        assert gemini_hooks["BeforeTool"][0]["hooks"] == [
            {"type": "command", "command": "check.sh"}
        ]

    def test_multiple_definitions_per_event(self):
        cc_hooks = {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "a.sh"}]},
                {"matcher": "Edit", "hooks": [{"type": "command", "command": "b.sh"}]},
            ]
        }
        gemini_hooks, _, count = transform_hooks(cc_hooks)
        assert len(gemini_hooks["BeforeTool"]) == 2
        assert count == 2

    def test_empty_definitions_list_skips_event(self):
        gemini_hooks, _, _ = transform_hooks(
            {"PreToolUse": [{"hooks": [{"type": "prompt", "prompt": "x"}]}]}
        )
        assert "BeforeTool" not in gemini_hooks

    def test_empty_hooks_input(self):
        gemini_hooks, dropped, count = transform_hooks({})
        assert gemini_hooks == {}
        assert dropped == []
        assert count == 0

    def test_multiple_hooks_in_single_definition(self):
        gemini_hooks, _, count = transform_hooks(
            {
                "Stop": [
                    {
                        "hooks": [
                            {"type": "command", "command": "cleanup.sh"},
                            {"type": "command", "command": "log.sh"},
                        ]
                    }
                ]
            }
        )
        assert count == 2
        assert len(gemini_hooks["AfterModel"][0]["hooks"]) == 2


# ── transform_mcp_servers ────────────────────────────────────────────────────


class TestTransformMcpServers:
    def test_copies_servers(self):
        cc_servers = {"vivesca": {"command": "uv", "args": ["run", "server.py"]}}
        result = transform_mcp_servers(cc_servers)
        assert result["vivesca"]["command"] == "uv"

    def test_empty_input(self):
        assert transform_mcp_servers({}) == {}

    def test_shallow_copy_independence(self):
        cc_servers = {"s": {"command": "uv"}}
        result = transform_mcp_servers(cc_servers)
        result["s"]["command"] = "changed"
        assert cc_servers["s"]["command"] == "uv"

    def test_multiple_servers(self):
        cc_servers = {
            "a": {"command": "a_cmd"},
            "b": {"command": "b_cmd", "args": ["--flag"]},
        }
        result = transform_mcp_servers(cc_servers)
        assert len(result) == 2
        assert result["b"]["args"] == ["--flag"]


# ── transform_skills ─────────────────────────────────────────────────────────


class TestTransformSkills:
    def test_stub_returns_none(self):
        assert transform_skills({"anything": True}) is None


# ── merge_into_gemini_settings ───────────────────────────────────────────────


class TestMergeIntoGeminiSettings:
    def test_merge_hooks_and_mcp(self):
        current = {"existingField": True}
        hooks = {"BeforeModel": [{"hooks": [{"type": "command", "command": "echo"}]}]}
        mcp = {"server1": {"command": "uv"}}
        result = merge_into_gemini_settings(current, hooks, mcp)
        assert result["hooks"] == hooks
        assert result["mcpServers"] == {"server1": {"command": "uv"}}
        assert result["existingField"] is True

    def test_preserves_existing_mcp_servers(self):
        current = {"mcpServers": {"old_server": {"command": "old"}}}
        mcp = {"new_server": {"command": "new"}}
        result = merge_into_gemini_settings(current, {}, mcp)
        assert "old_server" in result["mcpServers"]
        assert "new_server" in result["mcpServers"]

    def test_hooks_only_skips_mcp(self):
        hooks = {"BeforeModel": []}
        mcp = {"server1": {"command": "uv"}}
        result = merge_into_gemini_settings({}, hooks, mcp, hooks_only=True)
        assert "hooks" in result
        assert "mcpServers" not in result

    def test_mcp_only_skips_hooks(self):
        hooks = {"BeforeModel": []}
        mcp = {"server1": {"command": "uv"}}
        result = merge_into_gemini_settings({}, hooks, mcp, mcp_only=True)
        assert "hooks" not in result
        assert "mcpServers" in result

    def test_empty_hooks_not_written(self):
        result = merge_into_gemini_settings({}, {}, {"s": {"command": "c"}})
        assert "hooks" not in result

    def test_empty_mcp_not_written(self):
        result = merge_into_gemini_settings(
            {}, {"BeforeModel": [{"hooks": []}]}, {}
        )
        assert "mcpServers" not in result

    def test_does_not_mutate_current(self):
        current = {"keep": 1}
        result = merge_into_gemini_settings(
            current, {"BeforeModel": []}, {"s": {"command": "c"}}
        )
        assert "keep" not in result or result["keep"] == 1
        assert "hooks" not in current
        assert "mcpServers" not in current

    def test_mcp_overwrites_existing_key(self):
        current = {"mcpServers": {"s": {"command": "old"}}}
        mcp = {"s": {"command": "new"}}
        result = merge_into_gemini_settings(current, {}, mcp)
        assert result["mcpServers"]["s"]["command"] == "new"


# ── diff_settings ────────────────────────────────────────────────────────────


class TestDiffSettings:
    def test_no_changes(self):
        assert diff_settings({"a": 1}, {"a": 1}) == "(no changes)"

    def test_shows_diff(self):
        current = {"a": 1}
        proposed = {"a": 2}
        result = diff_settings(current, proposed)
        assert "-  \"a\": 1" in result
        assert "+  \"a\": 2" in result

    def test_shows_file_labels(self):
        result = diff_settings({}, {"a": 1})
        assert "current ~/.gemini/settings.json" in result
        assert "proposed ~/.gemini/settings.json" in result


# ── ConjugationResult ────────────────────────────────────────────────────────


class TestConjugationResult:
    def test_summary_with_drops(self):
        r = ConjugationResult(3, 2, ["SomeEvent"], False)
        assert "3 hook" in r.summary
        assert "2 MCP" in r.summary
        assert "SomeEvent" in r.summary

    def test_summary_no_drops(self):
        r = ConjugationResult(1, 0, [], False)
        assert "Dropped" not in r.summary

    def test_dry_run_label(self):
        r = ConjugationResult(1, 0, [], True)
        assert "(dry-run)" in r.summary

    def test_no_dry_run_no_label(self):
        r = ConjugationResult(1, 0, [], False)
        assert "dry-run" not in r.summary


# ── replicate_to_gemini (integration) ───────────────────────────────────────


class TestReplicateToGemini:
    @staticmethod
    def _cc_settings(tmp_path):
        """Create a CC settings file with hooks + MCP."""
        p = tmp_path / "cc_settings.json"
        p.write_text(
            json.dumps(
                {
                    "hooks": {
                        "UserPromptSubmit": [
                            {"hooks": [{"type": "command", "command": "run.sh"}]}
                        ]
                    },
                    "mcpServers": {
                        "myserver": {"command": "uv", "args": ["run", "s.py"]}
                    },
                }
            )
        )
        return p

    def test_dry_run_does_not_write(self, tmp_path):
        cc_path = self._cc_settings(tmp_path)
        gemini_path = tmp_path / "gemini_settings.json"
        result, diff_text = replicate_to_gemini(
            dry_run=True,
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert result.dry_run is True
        assert not gemini_path.exists()
        assert result.hooks_replicated == 1
        assert result.mcp_servers_replicated == 1

    def test_writes_file_when_not_dry_run(self, tmp_path):
        cc_path = self._cc_settings(tmp_path)
        gemini_path = tmp_path / "gemini_settings.json"
        result, _ = replicate_to_gemini(
            dry_run=False,
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert gemini_path.exists()
        written = json.loads(gemini_path.read_text())
        assert "BeforeModel" in written["hooks"]
        assert "myserver" in written["mcpServers"]

    def test_creates_parent_directory(self, tmp_path):
        cc_path = self._cc_settings(tmp_path)
        gemini_path = tmp_path / "subdir" / "nested" / "settings.json"
        replicate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert gemini_path.exists()

    def test_merges_with_existing_gemini_settings(self, tmp_path):
        cc_path = self._cc_settings(tmp_path)
        gemini_path = tmp_path / "gemini_settings.json"
        gemini_path.write_text(json.dumps({"customField": "kept"}))
        replicate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        written = json.loads(gemini_path.read_text())
        assert written["customField"] == "kept"
        assert "BeforeModel" in written["hooks"]

    def test_hooks_only_mode(self, tmp_path):
        cc_path = self._cc_settings(tmp_path)
        gemini_path = tmp_path / "gemini_settings.json"
        result, _ = replicate_to_gemini(
            hooks_only=True,
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert result.hooks_replicated == 1
        assert result.mcp_servers_replicated == 0
        written = json.loads(gemini_path.read_text())
        assert "mcpServers" not in written

    def test_mcp_only_mode(self, tmp_path):
        cc_path = self._cc_settings(tmp_path)
        gemini_path = tmp_path / "gemini_settings.json"
        result, _ = replicate_to_gemini(
            mcp_only=True,
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert result.hooks_replicated == 0
        assert result.mcp_servers_replicated == 1
        written = json.loads(gemini_path.read_text())
        assert "hooks" not in written

    def test_empty_cc_settings(self, tmp_path):
        cc_path = tmp_path / "cc_empty.json"
        cc_path.write_text("{}")
        gemini_path = tmp_path / "gemini_settings.json"
        result, diff_text = replicate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert result.hooks_replicated == 0
        assert result.mcp_servers_replicated == 0
        assert diff_text == "(no changes)"

    def test_missing_cc_file(self, tmp_path):
        gemini_path = tmp_path / "gemini_settings.json"
        result, diff_text = replicate_to_gemini(
            cc_settings_path=tmp_path / "nonexistent.json",
            gemini_settings_path=gemini_path,
        )
        assert result.hooks_replicated == 0

    def test_diff_returned(self, tmp_path):
        cc_path = self._cc_settings(tmp_path)
        gemini_path = tmp_path / "gemini_settings.json"
        _, diff_text = replicate_to_gemini(
            dry_run=True,
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert diff_text != "(no changes)"
        assert "BeforeModel" in diff_text

    def test_output_file_ends_with_newline(self, tmp_path):
        cc_path = self._cc_settings(tmp_path)
        gemini_path = tmp_path / "gemini_settings.json"
        replicate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert gemini_path.read_text().endswith("\n")
