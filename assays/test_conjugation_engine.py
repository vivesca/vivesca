from __future__ import annotations

"""Tests for conjugation_engine — CC→Gemini config replication."""

import json
from pathlib import Path

import pytest


class TestEventMapping:
    def test_all_cc_events_mapped(self):
        from metabolon.organelles.conjugation_engine import CC_TO_GEMINI_EVENT
        assert "UserPromptSubmit" in CC_TO_GEMINI_EVENT
        assert "PreToolUse" in CC_TO_GEMINI_EVENT
        assert "PostToolUse" in CC_TO_GEMINI_EVENT
        assert "Stop" in CC_TO_GEMINI_EVENT


class TestReadSettings:
    def test_read_missing_file(self, tmp_path):
        from metabolon.organelles.conjugation_engine import read_cc_settings
        assert read_cc_settings(tmp_path / "nope.json") == {}

    def test_read_valid_file(self, tmp_path):
        from metabolon.organelles.conjugation_engine import read_cc_settings
        f = tmp_path / "settings.json"
        f.write_text(json.dumps({"hooks": {}}))
        result = read_cc_settings(f)
        assert result == {"hooks": {}}


class TestTransformHooks:
    def test_maps_event_names(self):
        from metabolon.organelles.conjugation_engine import transform_hooks
        cc_hooks = {
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": "echo test"}]}
            ]
        }
        gemini_hooks, dropped, count = transform_hooks(cc_hooks)
        assert "BeforeModel" in gemini_hooks
        assert count == 1

    def test_drops_unknown_events(self):
        from metabolon.organelles.conjugation_engine import transform_hooks
        cc_hooks = {
            "SomeNewEvent": [
                {"hooks": [{"type": "command", "command": "echo"}]}
            ]
        }
        _, dropped, _ = transform_hooks(cc_hooks)
        assert "SomeNewEvent" in dropped

    def test_preserves_matcher(self):
        from metabolon.organelles.conjugation_engine import transform_hooks
        cc_hooks = {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo"}]}
            ]
        }
        gemini_hooks, _, _ = transform_hooks(cc_hooks)
        assert gemini_hooks["BeforeTool"][0]["matcher"] == "Bash"

    def test_filters_prompt_type_hooks(self):
        from metabolon.organelles.conjugation_engine import transform_hooks
        cc_hooks = {
            "PreToolUse": [
                {"hooks": [{"type": "prompt", "prompt": "Be careful"}]}
            ]
        }
        gemini_hooks, _, count = transform_hooks(cc_hooks)
        assert count == 0

    def test_silently_drops_notification(self):
        from metabolon.organelles.conjugation_engine import transform_hooks
        cc_hooks = {
            "Notification": [
                {"hooks": [{"type": "command", "command": "echo"}]}
            ]
        }
        _, dropped, _ = transform_hooks(cc_hooks)
        assert "Notification" not in dropped  # silently dropped, not in dropped list


class TestTransformMcpServers:
    def test_copies_servers(self):
        from metabolon.organelles.conjugation_engine import transform_mcp_servers
        cc_servers = {
            "vivesca": {"command": "uv", "args": ["run", "server.py"]}
        }
        result = transform_mcp_servers(cc_servers)
        assert "vivesca" in result
        assert result["vivesca"]["command"] == "uv"

    def test_empty_input(self):
        from metabolon.organelles.conjugation_engine import transform_mcp_servers
        assert transform_mcp_servers({}) == {}


class TestConjugationResult:
    def test_summary(self):
        from metabolon.organelles.conjugation_engine import ConjugationResult
        r = ConjugationResult(
            hooks_replicated=3,
            mcp_servers_replicated=2,
            hooks_dropped=["SomeEvent"],
            dry_run=False,
        )
        assert "3 hook" in r.summary
        assert "2 MCP" in r.summary
        assert "SomeEvent" in r.summary

    def test_dry_run_label(self):
        from metabolon.organelles.conjugation_engine import ConjugationResult
        r = ConjugationResult(
            hooks_replicated=1,
            mcp_servers_replicated=0,
            hooks_dropped=[],
            dry_run=True,
        )
        assert "dry-run" in r.summary
