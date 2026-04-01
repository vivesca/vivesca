from __future__ import annotations

"""Tests for metabolon.resources.vitals — isolated, tmp_path-based, no global Path patching."""

import json
from pathlib import Path
from unittest.mock import patch

from metabolon.resources.vitals import express_vitals


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _no_file() -> Path:
    """Return a path guaranteed not to exist."""
    return Path("/nonexistent/vitals-test-placeholder-xyz")


# ---------------------------------------------------------------------------
# Nightly health report section
# ---------------------------------------------------------------------------


class TestNightlyReport:
    """Tests for the nightly health file handling."""

    def test_missing_health_file_shows_placeholder(self):
        result = express_vitals(
            health_path=_no_file(),
            settings_path=_no_file(),
            stats_path=_no_file(),
        )
        assert "# Claude Code Health" in result
        assert "_(no nightly health report)_" in result

    def test_health_file_content_included(self, tmp_path: Path):
        hp = tmp_path / "health.md"
        hp.write_text("Disk OK\nMemory OK")
        result = express_vitals(health_path=hp, settings_path=_no_file(), stats_path=_no_file())
        assert "## Nightly Report" in result
        assert "Disk OK" in result
        assert "Memory OK" in result

    def test_empty_health_file_still_shows_section(self, tmp_path: Path):
        hp = tmp_path / "health.md"
        hp.write_text("")
        result = express_vitals(health_path=hp, settings_path=_no_file(), stats_path=_no_file())
        assert "## Nightly Report" in result

    def test_health_file_with_whitespace_only(self, tmp_path: Path):
        hp = tmp_path / "health.md"
        hp.write_text("   \n  \n")
        result = express_vitals(health_path=hp, settings_path=_no_file(), stats_path=_no_file())
        assert "## Nightly Report" in result

    def test_health_file_multiline_markdown(self, tmp_path: Path):
        hp = tmp_path / "health.md"
        hp.write_text("### CPU\n- load: 1.2\n### RAM\n- used: 4GB")
        result = express_vitals(health_path=hp, settings_path=_no_file(), stats_path=_no_file())
        assert "### CPU" in result
        assert "### RAM" in result


# ---------------------------------------------------------------------------
# Plugin section
# ---------------------------------------------------------------------------


class TestPlugins:
    """Tests for the settings.json / plugin parsing."""

    def test_no_enabled_plugins_key_skips_section(self, tmp_path: Path):
        sp = tmp_path / "settings.json"
        sp.write_text(json.dumps({"someOtherKey": 42}))
        result = express_vitals(
            health_path=_no_file(), settings_path=sp, stats_path=_no_file()
        )
        assert "## Plugins" not in result

    def test_enabled_plugins_true_only(self, tmp_path: Path):
        sp = tmp_path / "settings.json"
        sp.write_text(json.dumps({"enabledPlugins": {"alpha": True, "beta": True}}))
        result = express_vitals(
            health_path=_no_file(), settings_path=sp, stats_path=_no_file()
        )
        assert "**Enabled (2):**" in result
        assert "`alpha`" in result
        assert "`beta`" in result
        assert "Disabled" not in result

    def test_disabled_plugins_only(self, tmp_path: Path):
        sp = tmp_path / "settings.json"
        sp.write_text(json.dumps({"enabledPlugins": {"x": False, "y": False}}))
        result = express_vitals(
            health_path=_no_file(), settings_path=sp, stats_path=_no_file()
        )
        assert "**Disabled (2):**" in result
        assert "Enabled" not in result

    def test_mixed_enabled_disabled(self, tmp_path: Path):
        sp = tmp_path / "settings.json"
        sp.write_text(
            json.dumps({"enabledPlugins": {"a": True, "b": False, "c": True, "d": False}})
        )
        result = express_vitals(
            health_path=_no_file(), settings_path=sp, stats_path=_no_file()
        )
        assert "**Enabled (2):**" in result
        assert "**Disabled (2):**" in result

    def test_settings_file_missing(self):
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=_no_file()
        )
        assert "## Plugins" not in result

    def test_settings_invalid_json(self, tmp_path: Path):
        sp = tmp_path / "settings.json"
        sp.write_text("{{broken")
        result = express_vitals(
            health_path=_no_file(), settings_path=sp, stats_path=_no_file()
        )
        assert "## Plugins" not in result


# ---------------------------------------------------------------------------
# Activity / stats section
# ---------------------------------------------------------------------------


class TestActivityStats:
    """Tests for the stats-cache.json activity parsing."""

    def test_daily_activity_key_format(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps({
            "dailyActivity": [
                {"date": "2026-01-01", "messageCount": 10, "sessionCount": 2, "toolCallCount": 3},
            ]
        }))
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "| 2026-01-01 | 10 | 2 | 3 |" in result

    def test_list_format(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps([
            {"date": "2026-02-15", "messageCount": 5, "sessionCount": 1, "toolCallCount": 1},
        ]))
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "| 2026-02-15 | 5 | 1 | 1 |" in result

    def test_flat_dict_format(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps({
            "2026-03-10": {"messages": 99, "sessions": 7, "tool_calls": 44},
        }))
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "| 2026-03-10 | 99 | 7 | 44 |" in result

    def test_flat_dict_ignores_non_dict_values(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps({
            "2026-03-10": {"messages": 5, "sessions": 1, "tool_calls": 1},
            "meta": "string_value",
            "version": 3,
        }))
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "2026-03-10" in result
        # "meta" and "version" are non-dict values and should not appear as rows
        lines = [l for l in result.splitlines() if l.startswith("|") and "Date" not in l and "---" not in l]
        assert len(lines) == 1

    def test_alternate_key_names_messages_sessions_tool_calls(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps([
            {"date": "2026-04-01", "messages": 200, "sessions": 15, "tool_calls": 50},
        ]))
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "| 2026-04-01 | 200 | 15 | 50 |" in result

    def test_missing_values_default_to_zero(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps([{"date": "2026-01-01"}]))
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "| 2026-01-01 | 0 | 0 | 0 |" in result

    def test_missing_date_shows_question_mark(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps([{"messageCount": 1, "sessionCount": 1, "toolCallCount": 1}]))
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "| ? | 1 | 1 | 1 |" in result

    def test_sorted_descending_limited_to_five(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        entries = [{"date": f"2026-03-{d:02d}", "messageCount": d} for d in range(1, 11)]
        stp.write_text(json.dumps(entries))
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        # Last 5 dates by desc: 10, 09, 08, 07, 06
        for d in [10, 9, 8, 7, 6]:
            assert f"2026-03-{d:02d}" in result
        # Earlier dates should be excluded
        for d in [5, 4, 3, 2, 1]:
            assert f"2026-03-0{d}" not in result

    def test_empty_daily_activity_skips_section(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps({"dailyActivity": []}))
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "## Recent Activity" not in result

    def test_empty_list_skips_section(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text("[]")
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "## Recent Activity" not in result

    def test_stats_string_json_skips_section(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps("just a string"))
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "## Recent Activity" not in result

    def test_stats_number_json_skips_section(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text("42")
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "## Recent Activity" not in result

    def test_stats_invalid_json_skips_section(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text("{bad json!!")
        result = express_vitals(
            health_path=_no_file(), settings_path=_no_file(), stats_path=stp
        )
        assert "## Recent Activity" not in result


# ---------------------------------------------------------------------------
# Integration: full report
# ---------------------------------------------------------------------------


class TestFullReport:
    """Tests for the full report with all sections present."""

    def test_all_sections_present(self, tmp_path: Path):
        hp = tmp_path / "health.md"
        hp.write_text("All clear.")

        sp = tmp_path / "settings.json"
        sp.write_text(json.dumps({"enabledPlugins": {"audit": True, "debug": False}}))

        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps({
            "dailyActivity": [
                {"date": "2026-03-30", "messageCount": 50, "sessionCount": 6, "toolCallCount": 20},
            ]
        }))

        result = express_vitals(health_path=hp, settings_path=sp, stats_path=stp)

        assert "# Claude Code Health" in result
        assert "## Nightly Report" in result
        assert "All clear." in result
        assert "## Plugins" in result
        assert "`audit`" in result
        assert "`debug`" in result
        assert "## Recent Activity" in result
        assert "| 2026-03-30 | 50 | 6 | 20 |" in result

    def test_report_ordering_health_then_plugins_then_activity(self, tmp_path: Path):
        hp = tmp_path / "health.md"
        hp.write_text("report body")

        sp = tmp_path / "settings.json"
        sp.write_text(json.dumps({"enabledPlugins": {"p": True}}))

        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps([{"date": "2026-01-01", "messageCount": 1, "sessionCount": 1, "toolCallCount": 1}]))

        result = express_vitals(health_path=hp, settings_path=sp, stats_path=stp)

        idx_health = result.index("## Nightly Report")
        idx_plugins = result.index("## Plugins")
        idx_activity = result.index("## Recent Activity")
        assert idx_health < idx_plugins < idx_activity

    def test_default_paths_are_module_constants(self):
        """Verify module-level defaults exist and are Path objects."""
        from metabolon.resources import vitals as mod
        assert isinstance(mod._HEALTH_FILE, Path)
        assert isinstance(mod._SETTINGS, Path)
        assert isinstance(mod._STATS_CACHE, Path)


# ---------------------------------------------------------------------------
# Error handling (OSError branches)
# ---------------------------------------------------------------------------


class TestOSErrorHandling:
    """Tests for OSError handling across all three file reads."""

    def test_health_file_unreadable_shows_unreadable_message(self, tmp_path: Path):
        hp = tmp_path / "health.md"
        hp.write_text("should not appear")
        with patch.object(Path, "read_text", side_effect=OSError("permission denied")):
            result = express_vitals(health_path=hp, settings_path=_no_file(), stats_path=_no_file())
        assert "_(nightly health report unreadable)_" in result
        assert "should not appear" not in result

    def test_settings_file_unreadable_skips_plugins(self, tmp_path: Path):
        sp = tmp_path / "settings.json"
        sp.write_text(json.dumps({"enabledPlugins": {"p": True}}))
        with patch.object(Path, "read_text", side_effect=OSError("permission denied")):
            result = express_vitals(health_path=_no_file(), settings_path=sp, stats_path=_no_file())
        assert "## Plugins" not in result

    def test_stats_file_unreadable_skips_activity(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps({"dailyActivity": [{"date": "2026-01-01", "messageCount": 1, "sessionCount": 1, "toolCallCount": 1}]}))
        with patch.object(Path, "read_text", side_effect=OSError("permission denied")):
            result = express_vitals(health_path=_no_file(), settings_path=_no_file(), stats_path=stp)
        assert "## Recent Activity" not in result


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_settings_with_null_enabled_plugins_skips_section(self, tmp_path: Path):
        sp = tmp_path / "settings.json"
        sp.write_text(json.dumps({"enabledPlugins": None}))
        result = express_vitals(health_path=_no_file(), settings_path=sp, stats_path=_no_file())
        assert "## Plugins" not in result

    def test_settings_with_list_enabled_plugins_skips_section(self, tmp_path: Path):
        sp = tmp_path / "settings.json"
        sp.write_text(json.dumps({"enabledPlugins": ["a", "b"]}))
        result = express_vitals(health_path=_no_file(), settings_path=sp, stats_path=_no_file())
        assert "## Plugins" not in result

    def test_settings_with_truthy_falsy_plugin_values(self, tmp_path: Path):
        """Non-boolean truthy/falsy values should be handled correctly."""
        sp = tmp_path / "settings.json"
        sp.write_text(json.dumps({"enabledPlugins": {"present": 1, "absent": 0}}))
        result = express_vitals(health_path=_no_file(), settings_path=sp, stats_path=_no_file())
        assert "**Enabled (1):**" in result
        assert "**Disabled (1):**" in result

    def test_plugin_names_with_special_characters(self, tmp_path: Path):
        """Plugin names containing colons and slashes should render in backticks."""
        sp = tmp_path / "settings.json"
        sp.write_text(json.dumps({"enabledPlugins": {"anthropic://claude-code": True}}))
        result = express_vitals(health_path=_no_file(), settings_path=sp, stats_path=_no_file())
        assert "`anthropic://claude-code`" in result

    def test_empty_flat_dict_stats_skips_section(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps({}))
        result = express_vitals(health_path=_no_file(), settings_path=_no_file(), stats_path=stp)
        assert "## Recent Activity" not in result

    def test_single_plugin_enabled(self, tmp_path: Path):
        sp = tmp_path / "settings.json"
        sp.write_text(json.dumps({"enabledPlugins": {"solo": True}}))
        result = express_vitals(health_path=_no_file(), settings_path=sp, stats_path=_no_file())
        assert "**Enabled (1):**" in result
        assert "Disabled" not in result

    def test_health_file_with_unicode_content(self, tmp_path: Path):
        hp = tmp_path / "health.md"
        hp.write_text("Systèmes: ✓ OK\nMémoire: stable")
        result = express_vitals(health_path=hp, settings_path=_no_file(), stats_path=_no_file())
        assert "Systèmes: ✓ OK" in result

    def test_activity_table_header_format(self, tmp_path: Path):
        stp = tmp_path / "stats.json"
        stp.write_text(json.dumps([{"date": "2026-01-01", "messageCount": 1, "sessionCount": 1, "toolCallCount": 1}]))
        result = express_vitals(health_path=_no_file(), settings_path=_no_file(), stats_path=stp)
        assert "| Date | Messages | Sessions | Tool Calls |" in result
        assert "|------|----------|----------|------------|" in result

    def test_return_type_is_string(self):
        result = express_vitals(
            health_path=_no_file(),
            settings_path=_no_file(),
            stats_path=_no_file(),
        )
        assert isinstance(result, str)
