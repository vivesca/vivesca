from __future__ import annotations

"""Tests for the new MCP resources: skills, tools, operons, cc/hooks, cc/health."""


import json
from typing import TYPE_CHECKING

from metabolon.resources.operons import express_operon_map
from metabolon.resources.proteome import express_effector_index
from metabolon.resources.receptome import express_operon_index
from metabolon.resources.reflexes import express_reflex_inventory
from metabolon.resources.vitals import express_vitals

if TYPE_CHECKING:
    from pathlib import Path


def _write_skill(skills_dir: Path, name: str, frontmatter: str) -> None:
    """Create a skill directory with SKILL.md."""
    d = skills_dir / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(frontmatter)


# ── Skills Resource ──────────────────────────────────────────


class TestSkillsIndex:
    def test_scans_skill_directories(self, tmp_path):
        _write_skill(
            tmp_path,
            "todo",
            "---\nname: todo\ndescription: Manage TODOs\nuser_invocable: true\n---\n# Todo\n",
        )
        _write_skill(
            tmp_path,
            "askesis",
            "---\nname: askesis\ndescription: Growth mode sessions\n---\n# Askesis\n",
        )
        result = express_operon_index(skills_root=tmp_path)
        assert "todo" in result
        assert "askesis" in result
        assert "Manage TODOs" in result
        assert "2 active" in result

    def test_scans_subdirectories(self, tmp_path):
        sub = tmp_path / "compound-engineering" / "ce-plan"
        sub.mkdir(parents=True)
        (sub / "SKILL.md").write_text(
            "---\nname: ce-plan\ndescription: Planning skill\n---\n# Plan\n"
        )
        result = express_operon_index(skills_root=tmp_path)
        assert "compound-engineering:ce-plan" in result

    def test_skips_archive(self, tmp_path):
        _write_skill(tmp_path, "active", "---\nname: active\ndescription: Active\n---\n")
        _write_skill(tmp_path / "archive", "old", "---\nname: old\ndescription: Old\n---\n")
        result = express_operon_index(skills_root=tmp_path)
        assert "active" in result
        assert "old" not in result

    def test_skips_hidden_dirs(self, tmp_path):
        _write_skill(tmp_path, ".hidden", "---\nname: hidden\ndescription: Hidden\n---\n")
        result = express_operon_index(skills_root=tmp_path)
        assert "hidden" not in result

    def test_missing_directory(self, tmp_path):
        result = express_operon_index(skills_root=tmp_path / "nonexistent")
        assert "No receptor directory" in result

    def test_missing_frontmatter(self, tmp_path):
        d = tmp_path / "bad"
        d.mkdir()
        (d / "SKILL.md").write_text("# No frontmatter here\n")
        result = express_operon_index(skills_root=tmp_path)
        assert "0 active" in result

    def test_includes_modified_date(self, tmp_path):
        _write_skill(tmp_path, "todo", "---\nname: todo\ndescription: Manage TODOs\n---\n")
        result = express_operon_index(skills_root=tmp_path)
        # Should contain a date in YYYY-MM-DD format
        assert "20" in result  # Year prefix


# ── Tool Index Resource ──────────────────────────────────────


class TestToolIndex:
    def test_scans_bin_dir(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        script = bin_dir / "my-tool"
        script.write_text("#!/bin/sh\necho hi\n")
        script.chmod(0o755)

        result = express_effector_index(bin_dir=bin_dir, tools_dir=tmp_path / "tools")
        assert "my-tool" in result
        assert "CLI Tools" in result

    def test_scans_vivesca_tools(self, tmp_path):
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        (tools_dir / "__init__.py").write_text("")
        (tools_dir / "fasti.py").write_text(
            "from fastmcp.tools import tool\n\n"
            '@tool(name="fasti_list_events", description="List events")\n'
            "def fasti_list_events(date: str) -> str:\n"
            '    """List calendar events."""\n'
            '    return ""\n'
        )
        result = express_effector_index(bin_dir=tmp_path / "bin", tools_dir=tools_dir)
        assert "fasti_list_events" in result
        assert "MCP Tools" in result

    def test_skips_non_executable(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        readme = bin_dir / "README.md"
        readme.write_text("Just a readme\n")
        readme.chmod(0o644)

        result = express_effector_index(bin_dir=bin_dir, tools_dir=tmp_path / "tools")
        assert "README" not in result

    def test_skips_hidden_files(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        hidden = bin_dir / ".hidden"
        hidden.write_text("#!/bin/sh\n")
        hidden.chmod(0o755)

        result = express_effector_index(bin_dir=bin_dir, tools_dir=tmp_path / "tools")
        assert ".hidden" not in result

    def test_shows_total_count(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        s = bin_dir / "tool1"
        s.write_text("#!/bin/sh\n")
        s.chmod(0o755)

        result = express_effector_index(bin_dir=bin_dir, tools_dir=tmp_path / "tools")
        assert "Total: 1 tools" in result

    def test_includes_routing_table(self, tmp_path):
        routing = tmp_path / "tool-index.md"
        routing.write_text(
            "### Communication\n| Trigger | Tool |\n|---|---|\n| Email | `stilus` |\n"
        )
        result = express_effector_index(
            bin_dir=tmp_path / "bin",
            tools_dir=tmp_path / "tools",
            routing_path=routing,
        )
        assert "Communication" in result
        assert "stilus" in result

    def test_works_without_routing_table(self, tmp_path):
        result = express_effector_index(
            bin_dir=tmp_path / "bin",
            tools_dir=tmp_path / "tools",
            routing_path=tmp_path / "nonexistent.md",
        )
        assert "Tool Index" in result


# ── Operon Map Resource ──────────────────────────────────────


class TestOperonMap:
    def test_returns_operon_data(self):
        result = express_operon_map()
        # Should have real operon data from metabolon.operons
        assert "Operon Map" in result
        assert "expressed" in result.lower()

    def test_contains_table_structure(self):
        result = express_operon_map()
        assert "| Operon |" in result
        assert "|--------|" in result


# ── CC Hooks Resource ──────────────────────────────────────


class TestCCHooks:
    def test_parses_settings(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text(
            json.dumps(
                {
                    "hooks": {
                        "UserPromptSubmit": [
                            {
                                "matcher": "",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "python3 ~/.claude/hooks/chromatin-pull.py",
                                    }
                                ],
                            }
                        ],
                        "Stop": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "node ~/.claude/hooks/dirty-repos.js",
                                    }
                                ],
                            }
                        ],
                    }
                }
            )
        )
        result = express_reflex_inventory(settings_path=settings)
        assert "chromatin-pull" in result
        assert "dirty-repos" in result
        assert "UserPromptSubmit" in result
        assert "Stop" in result
        assert "Total: 2 hooks" in result

    def test_handles_prompt_hooks(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PreToolUse": [
                            {
                                "matcher": "tool == 'Agent'",
                                "hooks": [
                                    {
                                        "type": "prompt",
                                        "prompt": "Check if this agent is necessary before proceeding",
                                    }
                                ],
                            }
                        ],
                    }
                }
            )
        )
        result = express_reflex_inventory(settings_path=settings)
        assert "[prompt]" in result
        assert "Agent" in result

    def test_shows_matchers(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PreToolUse": [
                            {
                                "matcher": "tool == 'Bash'",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "node ~/.claude/hooks/bash-guard.js",
                                    }
                                ],
                            }
                        ],
                    }
                }
            )
        )
        result = express_reflex_inventory(settings_path=settings)
        assert "tool == 'Bash'" in result

    def test_missing_settings(self, tmp_path):
        result = express_reflex_inventory(settings_path=tmp_path / "nonexistent.json")
        assert "No settings.json" in result

    def test_no_hooks(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({"env": {}}))
        result = express_reflex_inventory(settings_path=settings)
        assert "No hooks configured" in result


# ── CC Health Resource ──────────────────────────────────────


class TestCCHealth:
    def test_includes_nightly_report(self, tmp_path):
        health = tmp_path / "nightly-health.md"
        health.write_text("## System OK\nAll checks passed.")
        result = express_vitals(
            health_path=health,
            settings_path=tmp_path / "s.json",
            stats_path=tmp_path / "st.json",
        )
        assert "System OK" in result
        assert "All checks passed" in result

    def test_includes_plugin_status(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text(
            json.dumps(
                {
                    "enabledPlugins": {
                        "superpowers@official": True,
                        "swift-lsp@official": False,
                    }
                }
            )
        )
        result = express_vitals(
            health_path=tmp_path / "h.md",
            settings_path=settings,
            stats_path=tmp_path / "st.json",
        )
        assert "superpowers@official" in result
        assert "swift-lsp@official" in result
        assert "Enabled (1)" in result
        assert "Disabled (1)" in result

    def test_includes_recent_activity(self, tmp_path):
        stats = tmp_path / "stats.json"
        stats.write_text(
            json.dumps(
                {
                    "2026-03-22": {"messages": 50, "sessions": 3, "tool_calls": 120},
                    "2026-03-21": {"messages": 30, "sessions": 2, "tool_calls": 80},
                }
            )
        )
        result = express_vitals(
            health_path=tmp_path / "h.md",
            settings_path=tmp_path / "s.json",
            stats_path=stats,
        )
        assert "2026-03-22" in result
        assert "50" in result
        assert "Recent Activity" in result

    def test_missing_all_files(self, tmp_path):
        result = express_vitals(
            health_path=tmp_path / "h.md",
            settings_path=tmp_path / "s.json",
            stats_path=tmp_path / "st.json",
        )
        assert "Health" in result
        assert "no nightly health report" in result

    def test_vitals_via_generator(self):
        result = express_vitals()
        assert isinstance(result, str)
        assert "Health" in result


# ── Tool Registration ──────────────────────────────────


class TestIntrospectionTools:
    """Verify proprioception tools can be imported and called."""

    def test_skills_tool_callable(self):
        result = express_operon_index()
        assert isinstance(result, str)

    def test_tool_index_callable(self):
        result = express_effector_index()
        assert isinstance(result, str)

    def test_operon_map_callable(self):
        result = express_operon_map()
        assert isinstance(result, str)

    def test_cc_hooks_callable(self):
        result = express_reflex_inventory()
        assert isinstance(result, str)

    def test_cc_health_callable(self):
        result = express_vitals()
        assert isinstance(result, str)
