from __future__ import annotations

"""Tests for metabolon.resources.vitals."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from metabolon.resources.vitals import express_vitals


class TestExpressVitals:
    """Test cases for express_vitals function."""

    def test_no_files_exist_returns_default_report(self):
        """When no files exist, should return basic report with placeholders."""
        with patch.object(Path, 'exists', return_value=False):
            result = express_vitals()
            
        assert "Claude Code Health" in result
        assert "_(no nightly health report)_" in result
        assert "## Plugins" not in result
        assert "## Recent Activity" not in result

    def test_nightly_report_exists_included(self, tmp_path: Path):
        """When nightly health file exists, should include its content."""
        health_file = tmp_path / "nightly-health.md"
        health_file.write_text("## All systems clear\n\nLast check: 2026-03-30")
        
        result = express_vitals(health_path=health_file, settings_path=Path("/nonexistent/settings.json"), stats_path=Path("/nonexistent/stats.json"))
        
        assert "## Nightly Report" in result
        assert "All systems clear" in result
        assert "Last check: 2026-03-30" in result

    def test_nightly_report_unreadable_handles_gracefully(self, tmp_path: Path):
        """When OSError reading health file, should show placeholder."""
        health_file = tmp_path / "nightly-health.md"
        health_file.touch()
        
        with patch.object(Path, 'read_text', side_effect=OSError("Permission denied")):
            result = express_vitals(health_path=health_file)
        
        assert "_(nightly health report unreadable)_" in result

    def test_plugins_are_parsed_and_displayed(self, tmp_path: Path):
        """When settings.json has enabledPlugins, should display enabled/disabled lists."""
        settings_file = tmp_path / "settings.json"
        settings_data = {
            "enabledPlugins": {
                "anthropic://claude-code": True,
                "anthropic://audit": True,
                "third-party://legacy": False,
                "experimental://debug": False
            }
        }
        settings_file.write_text(json.dumps(settings_data))
        
        result = express_vitals(health_path=Path("/nonexistent"), settings_path=settings_file, stats_path=Path("/nonexistent"))
        
        assert "## Plugins" in result
        assert "**Enabled (2):** `anthropic://claude-code`, `anthropic://audit`" in result
        assert "**Disabled (2):** `third-party://legacy`, `experimental://debug`" in result

    def test_only_enabled_plugins_shown_when_all_enabled(self, tmp_path: Path):
        """When all plugins are enabled, should only show enabled section."""
        settings_file = tmp_path / "settings.json"
        settings_data = {
            "enabledPlugins": {
                "plugin1": True,
                "plugin2": True
            }
        }
        settings_file.write_text(json.dumps(settings_data))
        
        result = express_vitals(settings_path=settings_file)
        
        assert "**Enabled (2):**" in result
        assert "**Disabled" not in result

    def test_only_disabled_plugins_shown_when_all_disabled(self, tmp_path: Path):
        """When all plugins are disabled, should only show disabled section."""
        settings_file = tmp_path / "settings.json"
        settings_data = {
            "enabledPlugins": {
                "plugin1": False,
                "plugin2": False
            }
        }
        settings_file.write_text(json.dumps(settings_data))
        
        result = express_vitals(settings_path=settings_file)
        
        assert "**Disabled (2):**" in result
        assert "**Enabled" not in result

    def test_empty_plugins_object_skips_section(self, tmp_path: Path):
        """When enabledPlugins is empty, should skip the section entirely."""
        settings_file = tmp_path / "settings.json"
        settings_data = {"enabledPlugins": {}}
        settings_file.write_text(json.dumps(settings_data))
        
        result = express_vitals(settings_path=settings_file)
        
        assert "## Plugins" not in result

    def test_invalid_json_settings_skips_section_gracefully(self, tmp_path: Path):
        """When settings.json is invalid JSON, should skip plugin section silently."""
        settings_file = tmp_path / "settings.json"
        settings_file.write_text("{ not valid json ")
        
        result = express_vitals(settings_path=settings_file)
        
        assert "## Plugins" not in result

    def test_oserror_reading_settings_skips_section(self, tmp_path: Path):
        """When OSError reading settings, should skip plugin section silently."""
        settings_file = tmp_path / "settings.json"
        settings_file.touch()
        
        with patch.object(Path, 'read_text', side_effect=OSError("Permission denied")):
            result = express_vitals(settings_path=settings_file)
        
        assert "## Plugins" not in result

    def test_activity_with_daily_activity_key_displays_table(self, tmp_path: Path):
        """When stats cache has {dailyActivity: [...]}, should display activity table."""
        stats_file = tmp_path / "stats-cache.json"
        stats_data = {
            "dailyActivity": [
                {"date": "2026-03-30", "messageCount": 42, "sessionCount": 5, "toolCallCount": 12},
                {"date": "2026-03-29", "messageCount": 28, "sessionCount": 3, "toolCallCount": 8},
            ]
        }
        stats_file.write_text(json.dumps(stats_data))
        
        result = express_vitals(stats_path=stats_file)
        
        assert "## Recent Activity" in result
        assert "| Date | Messages | Sessions | Tool Calls |" in result
        assert "| 2026-03-30 | 42 | 5 | 12 |" in result
        assert "| 2026-03-29 | 28 | 3 | 8 |" in result

    def test_activity_as_list_displays_table(self, tmp_path: Path):
        """When stats cache is already a list, should display activity table."""
        stats_file = tmp_path / "stats-cache.json"
        stats_data = [
            {"date": "2026-03-30", "messageCount": 42, "sessionCount": 5, "toolCallCount": 12},
        ]
        stats_file.write_text(json.dumps(stats_data))
        
        result = express_vitals(stats_path=stats_file)
        
        assert "## Recent Activity" in result
        assert "| 2026-03-30 | 42 | 5 | 12 |" in result

    def test_activity_as_flat_dict_displays_table(self, tmp_path: Path):
        """When stats cache is a flat dict {date: stats}, should display activity table."""
        stats_file = tmp_path / "stats-cache.json"
        stats_data = {
            "2026-03-30": {"messages": 42, "sessions": 5, "tool_calls": 12},
            "2026-03-29": {"messages": 28, "sessions": 3, "tool_calls": 8},
        }
        stats_file.write_text(json.dumps(stats_data))
        
        result = express_vitals(stats_path=stats_file)
        
        assert "## Recent Activity" in result
        assert "2026-03-30" in result
        assert "42" in result
        assert "12" in result

    def test_alternate_stat_key_names_handled(self, tmp_path: Path):
        """When stats use alternate key names (messages vs messageCount), should handle them."""
        stats_file = tmp_path / "stats-cache.json"
        stats_data = [
            {
                "date": "2026-03-30", 
                "messages": 100,
                "sessions": 10,
                "tool_calls": 25
            }
        ]
        stats_file.write_text(json.dumps(stats_data))
        
        result = express_vitals(stats_path=stats_file)
        
        assert "| 2026-03-30 | 100 | 10 | 25 |" in result

    def test_missing_date_uses_question_mark(self, tmp_path: Path):
        """When date is missing from activity entry, should display '?'."""
        stats_file = tmp_path / "stats-cache.json"
        stats_data = [{"messageCount": 42, "sessionCount": 5, "toolCallCount": 12}]
        stats_file.write_text(json.dumps(stats_data))
        
        result = express_vitals(stats_path=stats_file)
        
        assert "| ? | 42 | 5 | 12 |" in result

    def test_missing_stat_values_default_to_zero(self, tmp_path: Path):
        """When stat values are missing, should default to 0."""
        stats_file = tmp_path / "stats-cache.json"
        stats_data = [{"date": "2026-03-30"}]
        stats_file.write_text(json.dumps(stats_data))
        
        result = express_vitals(stats_path=stats_file)
        
        assert "| 2026-03-30 | 0 | 0 | 0 |" in result

    def test_sorts_by_date_descending_and_takes_last_five(self, tmp_path: Path):
        """Should sort activity by date descending and only show most recent 5 days."""
        stats_file = tmp_path / "stats-cache.json"
        # Create 8 days of activity out of order
        stats_data = [{"date": f"2026-03-{i:02d}", "messageCount": i} for i in range(23, 31)]
        stats_file.write_text(json.dumps(stats_data))
        
        result = express_vitals(stats_path=stats_file)
        
        # Should have the last 5 dates: 26, 27, 28, 29, 30
        assert "2026-03-30" in result
        assert "2026-03-29" in result
        assert "2026-03-28" in result
        assert "2026-03-27" in result
        assert "2026-03-26" in result
        # Earlier dates should not be present
        assert "2026-03-25" not in result
        assert "2026-03-24" not in result
        assert "2026-03-23" not in result

    def test_empty_activity_skips_section(self, tmp_path: Path):
        """When activity is empty, should skip the recent activity section."""
        stats_file = tmp_path / "stats-cache.json"
        stats_data = {"dailyActivity": []}
        stats_file.write_text(json.dumps(stats_data))
        
        result = express_vitals(stats_path=stats_file)
        
        assert "## Recent Activity" not in result

    def test_unexpected_activity_type_skips_section(self, tmp_path: Path):
        """When stats file has unexpected type for activity, should skip section."""
        stats_file = tmp_path / "stats-cache.json"
        stats_data = "not a dict or list"
        stats_file.write_text(json.dumps(stats_data))
        
        result = express_vitals(stats_path=stats_file)
        
        assert "## Recent Activity" not in result

    def test_invalid_json_stats_skips_section_gracefully(self, tmp_path: Path):
        """When stats cache has invalid JSON, should skip section silently."""
        stats_file = tmp_path / "stats-cache.json"
        stats_file.write_text("{ invalid json ")
        
        result = express_vitals(stats_path=stats_file)
        
        assert "## Recent Activity" not in result

    def test_oserror_reading_stats_skips_section(self, tmp_path: Path):
        """When OSError reading stats cache, should skip section silently."""
        stats_file = tmp_path / "stats-cache.json"
        stats_file.touch()
        
        with patch.object(Path, 'read_text', side_effect=OSError("Permission denied")):
            result = express_vitals(stats_path=stats_file)
        
        assert "## Recent Activity" not in result

    def test_all_files_present_full_report_generated(self, tmp_path: Path):
        """When all files are present and valid, should generate complete report."""
        # Create all three files
        health_file = tmp_path / "nightly-health.md"
        health_file.write_text("All systems green. No issues detected.")
        
        settings_file = tmp_path / "settings.json"
        settings_data = {
            "enabledPlugins": {
                "audit": True,
                "metrics": True,
                "legacy": False
            }
        }
        settings_file.write_text(json.dumps(settings_data))
        
        stats_file = tmp_path / "stats-cache.json"
        stats_data = {
            "dailyActivity": [
                {"date": "2026-03-30", "messageCount": 50, "sessionCount": 6, "toolCallCount": 20},
                {"date": "2026-03-29", "messageCount": 35, "sessionCount": 4, "toolCallCount": 15},
            ]
        }
        stats_file.write_text(json.dumps(stats_data))
        
        result = express_vitals(
            health_path=health_file,
            settings_path=settings_file,
            stats_path=stats_file
        )
        
        # All sections should be present
        assert "Claude Code Health" in result
        assert "## Nightly Report" in result
        assert "All systems green" in result
        assert "## Plugins" in result
        assert "**Enabled (2):**" in result
        assert "`audit`" in result
        assert "**Disabled (1):**" in result
        assert "`legacy`" in result
        assert "## Recent Activity" in result
        assert "| 2026-03-30 | 50 | 6 | 20 |" in result
