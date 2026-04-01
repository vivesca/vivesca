from __future__ import annotations

"""Tests for conjugation_engine — additional edge cases and mock-heavy coverage.

Complements assays/test_conjugation_engine.py with:
  - Edge cases for transform_hooks (missing keys, empty structures)
  - Full mock-based read_* tests that work regardless of real files
  - merge_into_gemini_settings edge cases (both flags, empty inputs)
  - diff_settings with structured diffs
  - replicate_to_gemini integration with synthetic fixtures
  - ConjugationResult summary formatting edge cases
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

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


# ── transform_hooks edge cases ─────────────────────────────────────────────


class TestTransformHooksEdgeCases:
    def test_definition_missing_hooks_key(self):
        """A definition dict with no 'hooks' key should be skipped."""
        gemini_hooks, dropped, count = transform_hooks(
            {"UserPromptSubmit": [{"matcher": "Bash"}]}
        )
        assert gemini_hooks == {}
        assert count == 0
        assert dropped == []

    def test_definition_with_empty_hooks_list(self):
        """A definition whose 'hooks' list is empty should be skipped."""
        gemini_hooks, _, count = transform_hooks(
            {"PreToolUse": [{"hooks": []}]}
        )
        assert gemini_hooks == {}
        assert count == 0

    def test_definition_hooks_key_is_none_raises(self):
        """If hooks value is explicitly None, iteration fails — known limitation."""
        with pytest.raises(TypeError):
            transform_hooks({"PostToolUse": [{"hooks": None}]})

    def test_mixed_event_partial_mapping(self):
        """Mixture of mappable, unmapped-known, and unknown events."""
        cc_hooks = {
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": "a.sh"}]}
            ],
            "Notification": [
                {"hooks": [{"type": "command", "command": "b.sh"}]}
            ],
            "UnknownEvent": [
                {"hooks": [{"type": "command", "command": "c.sh"}]}
            ],
        }
        gemini_hooks, dropped, count = transform_hooks(cc_hooks)
        assert "BeforeModel" in gemini_hooks
        assert "Notification" not in gemini_hooks
        assert dropped == ["UnknownEvent"]
        assert count == 1

    def test_definition_with_only_prompt_hooks_produces_empty_event(self):
        """If all hooks for a mappable event are prompt-type, event is absent."""
        gemini_hooks, _, count = transform_hooks(
            {
                "Stop": [
                    {"hooks": [{"type": "prompt", "prompt": "Be good"}]},
                ]
            }
        )
        assert "AfterModel" not in gemini_hooks
        assert count == 0

    def test_multiple_hooks_across_events(self):
        """Multiple command hooks across several events."""
        cc_hooks = {
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": "a"}]},
            ],
            "Stop": [
                {
                    "hooks": [
                        {"type": "command", "command": "b"},
                        {"type": "command", "command": "c"},
                    ]
                },
            ],
        }
        _, _, count = transform_hooks(cc_hooks)
        assert count == 3

    def test_hook_entry_without_type_key(self):
        """A hook entry missing 'type' should not match 'command' and be filtered."""
        gemini_hooks, _, count = transform_hooks(
            {"UserPromptSubmit": [{"hooks": [{"command": "echo"}]}]}
        )
        assert count == 0
        assert gemini_hooks == {}

    def test_same_cc_event_mapped_multiple_times_does_not_duplicate(self):
        """Two definitions for the same CC event both appear under one Gemini event."""
        cc_hooks = {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "x"}]},
                {"matcher": "Edit", "hooks": [{"type": "command", "command": "y"}]},
            ]
        }
        gemini_hooks, _, count = transform_hooks(cc_hooks)
        assert len(gemini_hooks["BeforeTool"]) == 2
        assert count == 2


# ── transform_mcp_servers edge cases ───────────────────────────────────────


class TestTransformMcpServersEdgeCases:
    def test_server_with_nested_config(self):
        cc = {"s": {"command": "uv", "args": ["run"], "env": {"KEY": "val"}}}
        result = transform_mcp_servers(cc)
        # Shallow copy: inner dict values are same references
        assert result["s"]["env"] == {"KEY": "val"}

    def test_many_servers(self):
        cc = {f"server_{i}": {"command": f"cmd_{i}"} for i in range(20)}
        result = transform_mcp_servers(cc)
        assert len(result) == 20


# ── read_cc_settings / read_gemini_settings with proper mocking ─────────────


class TestReadCcSettingsMocked:
    def test_calls_open_with_path(self, tmp_path):
        f = tmp_path / "cc.json"
        f.write_text(json.dumps({"hooks": {}}))
        result = read_cc_settings(f)
        assert result == {"hooks": {}}

    def test_oserror_returns_empty(self, tmp_path):
        f = tmp_path / "denied.json"
        f.write_text("{}")
        f.chmod(0o000)
        try:
            assert read_cc_settings(f) == {}
        finally:
            f.chmod(0o644)

    def test_default_path_is_home_claude(self):
        from metabolon.organelles.conjugation_engine import CC_SETTINGS_PATH

        assert CC_SETTINGS_PATH == Path.home() / ".claude" / "settings.json"


class TestReadGeminiSettingsMocked:
    def test_oserror_returns_empty(self, tmp_path):
        f = tmp_path / "denied.json"
        f.write_text("{}")
        f.chmod(0o000)
        try:
            assert read_gemini_settings(f) == {}
        finally:
            f.chmod(0o644)

    def test_default_path_is_home_gemini(self):
        from metabolon.organelles.conjugation_engine import GEMINI_SETTINGS_PATH

        assert GEMINI_SETTINGS_PATH == Path.home() / ".gemini" / "settings.json"

    def test_valid_gemini_json(self, tmp_path):
        f = tmp_path / "gemini.json"
        f.write_text(json.dumps({"hooks": {"BeforeModel": []}}))
        result = read_gemini_settings(f)
        assert "BeforeModel" in result["hooks"]


# ── merge_into_gemini_settings edge cases ───────────────────────────────────


class TestMergeIntoGeminiSettingsEdgeCases:
    def test_both_hooks_only_and_mcp_only_blocks_both(self):
        """Setting both flags means neither section is written."""
        result = merge_into_gemini_settings(
            {},
            gemini_hooks={"BeforeModel": [{"hooks": []}]},
            gemini_mcp_servers={"s": {"command": "c"}},
            hooks_only=True,
            mcp_only=True,
        )
        assert "hooks" not in result
        assert "mcpServers" not in result

    def test_merge_mutates_nested_mcpServers_in_input(self):
        """merge_into_gemini_settings does a shallow copy — nested mcpServers dict
        is shared, so .update() mutates the original. Document this behavior."""
        original = {"keep": 1, "mcpServers": {"old": {"command": "old"}}}
        merge_into_gemini_settings(
            original,
            gemini_hooks={"BeforeModel": []},
            gemini_mcp_servers={"new": {"command": "new"}},
        )
        # The shallow copy means original["mcpServers"] is the same dict object
        # that got .update() called on it — so it now contains "new" too.
        assert "new" in original["mcpServers"]

    def test_empty_everything_returns_copy_of_current(self):
        current = {"onlyField": True}
        result = merge_into_gemini_settings(current, {}, {})
        assert result == {"onlyField": True}
        assert result is not current

    def test_mcp_update_overwrites_matching_server(self):
        current = {"mcpServers": {"shared": {"command": "v1"}}}
        new_mcp = {"shared": {"command": "v2"}}
        result = merge_into_gemini_settings(current, {}, new_mcp)
        assert result["mcpServers"]["shared"]["command"] == "v2"


# ── diff_settings edge cases ────────────────────────────────────────────────


class TestDiffSettingsEdgeCases:
    def test_both_empty(self):
        assert diff_settings({}, {}) == "(no changes)"

    def test_nested_change_visible(self):
        before = {"hooks": {"BeforeModel": []}}
        after = {"hooks": {"BeforeModel": [{"hooks": [{"type": "command", "command": "x"}]}]}}
        result = diff_settings(before, after)
        assert "-  \"hooks\":" in result or "+" in result

    def test_sorted_keys_in_output(self):
        """json.dumps with sort_keys means keys are alphabetized in diff."""
        before = {}
        after = {"z_key": 1, "a_key": 2}
        result = diff_settings(before, after)
        a_pos = result.index("a_key")
        z_pos = result.index("z_key")
        assert a_pos < z_pos


# ── ConjugationResult edge cases ────────────────────────────────────────────


class TestConjugationResultEdgeCases:
    def test_zero_counts(self):
        r = ConjugationResult(0, 0, [], False)
        assert "0 hook" in r.summary
        assert "0 MCP" in r.summary

    def test_multiple_dropped_events_formatted(self):
        r = ConjugationResult(1, 1, ["Foo", "Bar", "Baz"], False)
        s = r.summary
        assert "Foo" in s
        assert "Bar" in s
        assert "Baz" in s

    def test_summary_is_string(self):
        r = ConjugationResult(0, 0, [], True)
        assert isinstance(r.summary, str)

    def test_dry_run_attribute(self):
        r = ConjugationResult(1, 0, [], True)
        assert r.dry_run is True
        r2 = ConjugationResult(1, 0, [], False)
        assert r2.dry_run is False


# ── replicate_to_gemini integration with synthetic fixtures ─────────────────


class TestReplicateIntegration:
    @staticmethod
    def _write_cc_settings(path: Path, data: dict) -> Path:
        p = path / "cc.json"
        p.write_text(json.dumps(data))
        return p

    def test_no_hooks_no_mcp_no_write(self, tmp_path):
        cc_path = self._write_cc_settings(tmp_path, {"hooks": {}, "mcpServers": {}})
        gemini_path = tmp_path / "gemini.json"
        result, diff = replicate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert result.hooks_replicated == 0
        assert result.mcp_servers_replicated == 0

    def test_hooks_only_excludes_mcp_from_result(self, tmp_path):
        cc_path = self._write_cc_settings(
            tmp_path,
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {"hooks": [{"type": "command", "command": "a.sh"}]}
                    ]
                },
                "mcpServers": {"s": {"command": "c"}},
            },
        )
        gemini_path = tmp_path / "gemini.json"
        result, _ = replicate_to_gemini(
            hooks_only=True,
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert result.hooks_replicated == 1
        assert result.mcp_servers_replicated == 0
        written = json.loads(gemini_path.read_text())
        assert "mcpServers" not in written

    def test_mcp_only_excludes_hooks_from_result(self, tmp_path):
        cc_path = self._write_cc_settings(
            tmp_path,
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {"hooks": [{"type": "command", "command": "a.sh"}]}
                    ]
                },
                "mcpServers": {"s": {"command": "c"}},
            },
        )
        gemini_path = tmp_path / "gemini.json"
        result, _ = replicate_to_gemini(
            mcp_only=True,
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert result.hooks_replicated == 0
        assert result.mcp_servers_replicated == 1
        written = json.loads(gemini_path.read_text())
        assert "hooks" not in written

    def test_preserves_existing_gemini_fields(self, tmp_path):
        cc_path = self._write_cc_settings(
            tmp_path,
            {
                "hooks": {
                    "Stop": [
                        {"hooks": [{"type": "command", "command": "log.sh"}]}
                    ]
                },
            },
        )
        gemini_path = tmp_path / "gemini.json"
        gemini_path.write_text(
            json.dumps({"myCustomField": [1, 2, 3], "theme": "dark"})
        )
        replicate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        written = json.loads(gemini_path.read_text())
        assert written["myCustomField"] == [1, 2, 3]
        assert written["theme"] == "dark"
        assert "AfterModel" in written["hooks"]

    def test_creates_nested_parent_dirs(self, tmp_path):
        cc_path = self._write_cc_settings(
            tmp_path,
            {
                "mcpServers": {"s": {"command": "c"}},
            },
        )
        deep = tmp_path / "a" / "b" / "c" / "settings.json"
        replicate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=deep,
        )
        assert deep.exists()
        written = json.loads(deep.read_text())
        assert "s" in written["mcpServers"]

    def test_dry_run_returns_diff_even_when_no_existing_gemini(self, tmp_path):
        cc_path = self._write_cc_settings(
            tmp_path,
            {
                "hooks": {
                    "PreToolUse": [
                        {"hooks": [{"type": "command", "command": "x.sh"}]}
                    ]
                },
            },
        )
        gemini_path = tmp_path / "new_gemini.json"
        result, diff = replicate_to_gemini(
            dry_run=True,
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert not gemini_path.exists()
        assert "BeforeTool" in diff
        assert result.dry_run is True

    def test_json_output_ends_with_newline(self, tmp_path):
        cc_path = self._write_cc_settings(
            tmp_path,
            {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "s"}]}]}},
        )
        gemini_path = tmp_path / "out.json"
        replicate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        raw = gemini_path.read_text()
        assert raw.endswith("\n")

    def test_missing_cc_settings_produces_zero_result(self, tmp_path):
        gemini_path = tmp_path / "out.json"
        result, diff = replicate_to_gemini(
            cc_settings_path=tmp_path / "no_such_file.json",
            gemini_settings_path=gemini_path,
        )
        assert result.hooks_replicated == 0
        assert result.mcp_servers_replicated == 0

    def test_mcp_servers_merge_not_replace(self, tmp_path):
        """Existing Gemini MCP servers must be preserved when new ones are added."""
        cc_path = self._write_cc_settings(
            tmp_path,
            {"mcpServers": {"new_srv": {"command": "new"}}},
        )
        gemini_path = tmp_path / "gemini.json"
        gemini_path.write_text(
            json.dumps({"mcpServers": {"old_srv": {"command": "old"}}})
        )
        replicate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        written = json.loads(gemini_path.read_text())
        assert "old_srv" in written["mcpServers"]
        assert "new_srv" in written["mcpServers"]


# ── transform_skills ────────────────────────────────────────────────────────


class TestTransformSkills:
    def test_returns_none_for_any_input(self):
        assert transform_skills({}) is None
        assert transform_skills({"hooks": {}}) is None

    def test_returns_none_for_none_input(self):
        assert transform_skills(None) is None


# ── CC_TO_GEMINI_EVENT constant verification ────────────────────────────────


class TestConstants:
    def test_mapping_has_exactly_four_entries(self):
        assert len(CC_TO_GEMINI_EVENT) == 4

    def test_all_values_are_unique(self):
        assert len(set(CC_TO_GEMINI_EVENT.values())) == len(CC_TO_GEMINI_EVENT)

    def test_expected_event_names(self):
        expected = {
            "UserPromptSubmit": "BeforeModel",
            "PreToolUse": "BeforeTool",
            "PostToolUse": "AfterTool",
            "Stop": "AfterModel",
        }
        assert CC_TO_GEMINI_EVENT == expected
