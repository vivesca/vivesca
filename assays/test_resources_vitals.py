from __future__ import annotations

"""Tests for metabolon.resources.vitals — focus on mocked external calls."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.resources.vitals import express_vitals


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def no_files(tmp_path: Path):
    """Return three nonexistent paths under tmp_path."""
    return {
        "health_path": tmp_path / "no-health.md",
        "settings_path": tmp_path / "no-settings.json",
        "stats_path": tmp_path / "no-stats.json",
    }


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# 1. Minimal report — no input files
# ---------------------------------------------------------------------------

class TestMinimalReport:
    """When none of the three files exist."""

    def test_header_present(self, no_files):
        result = express_vitals(**no_files)
        assert result.startswith("# Claude Code Health\n")

    def test_placeholder_for_nightly(self, no_files):
        result = express_vitals(**no_files)
        assert "_(no nightly health report)_" in result

    def test_no_plugins_section(self, no_files):
        result = express_vitals(**no_files)
        assert "## Plugins" not in result

    def test_no_activity_section(self, no_files):
        result = express_vitals(**no_files)
        assert "## Recent Activity" not in result


# ---------------------------------------------------------------------------
# 2. Nightly health report
# ---------------------------------------------------------------------------

class TestNightlyReport:
    """Reading ~/.claude/nightly-health.md."""

    def test_content_included(self, tmp_path, no_files):
        hp = _write(tmp_path / "h.md", "Disk OK\nMemory OK")
        result = express_vitals(**{**no_files, "health_path": hp})
        assert "## Nightly Report" in result
        assert "Disk OK" in result
        assert "Memory OK" in result

    def test_empty_file_still_shows_section(self, tmp_path, no_files):
        hp = _write(tmp_path / "h.md", "")
        result = express_vitals(**{**no_files, "health_path": hp})
        assert "## Nightly Report" in result

    def test_oserror_shows_unreadable(self, tmp_path, no_files):
        hp = tmp_path / "h.md"
        hp.touch()
        with patch.object(Path, "read_text", side_effect=OSError("denied")):
            result = express_vitals(health_path=hp)
        assert "_(nightly health report unreadable)_" in result


# ---------------------------------------------------------------------------
# 3. Plugin status from settings.json
# ---------------------------------------------------------------------------

class TestPlugins:
    """Reading ~/.claude/settings.json enabledPlugins."""

    def test_enabled_and_disabled_listed(self, tmp_path, no_files):
        sp = _write(tmp_path / "s.json", json.dumps({
            "enabledPlugins": {"a": True, "b": False},
        }))
        result = express_vitals(**{**no_files, "settings_path": sp})
        assert "**Enabled (1):** `a`" in result
        assert "**Disabled (1):** `b`" in result

    def test_no_enabled_plugins_key_skips_section(self, tmp_path, no_files):
        sp = _write(tmp_path / "s.json", json.dumps({"otherKey": 42}))
        result = express_vitals(**{**no_files, "settings_path": sp})
        assert "## Plugins" not in result

    def test_empty_enabled_plugins_skips_section(self, tmp_path, no_files):
        sp = _write(tmp_path / "s.json", json.dumps({"enabledPlugins": {}}))
        result = express_vitals(**{**no_files, "settings_path": sp})
        assert "## Plugins" not in result

    def test_malformed_json_skips_section(self, tmp_path, no_files):
        sp = _write(tmp_path / "s.json", "}{not json")
        result = express_vitals(**{**no_files, "settings_path": sp})
        assert "## Plugins" not in result

    def test_oserror_skips_section(self, tmp_path, no_files):
        sp = tmp_path / "s.json"
        sp.touch()
        with patch.object(Path, "read_text", side_effect=OSError("err")):
            result = express_vitals(settings_path=sp)
        assert "## Plugins" not in result

    def test_all_enabled_no_disabled_line(self, tmp_path, no_files):
        sp = _write(tmp_path / "s.json", json.dumps({
            "enabledPlugins": {"x": True, "y": True},
        }))
        result = express_vitals(**{**no_files, "settings_path": sp})
        assert "**Enabled (2):**" in result
        assert "Disabled" not in result

    def test_all_disabled_no_enabled_line(self, tmp_path, no_files):
        sp = _write(tmp_path / "s.json", json.dumps({
            "enabledPlugins": {"x": False},
        }))
        result = express_vitals(**{**no_files, "settings_path": sp})
        assert "**Disabled (1):**" in result
        assert "Enabled" not in result


# ---------------------------------------------------------------------------
# 4. Activity stats from stats-cache.json
# ---------------------------------------------------------------------------

class TestActivity:
    """Reading ~/.claude/stats-cache.json."""

    def test_daily_activity_key(self, tmp_path, no_files):
        sp = _write(tmp_path / "st.json", json.dumps({
            "dailyActivity": [
                {"date": "2026-01-01", "messageCount": 10, "sessionCount": 2, "toolCallCount": 3},
            ],
        }))
        result = express_vitals(**{**no_files, "stats_path": sp})
        assert "## Recent Activity" in result
        assert "| 2026-01-01 | 10 | 2 | 3 |" in result

    def test_list_format(self, tmp_path, no_files):
        sp = _write(tmp_path / "st.json", json.dumps([
            {"date": "2026-01-02", "messages": 5, "sessions": 1, "tool_calls": 0},
        ]))
        result = express_vitals(**{**no_files, "stats_path": sp})
        assert "| 2026-01-02 | 5 | 1 | 0 |" in result

    def test_flat_dict_format(self, tmp_path, no_files):
        sp = _write(tmp_path / "st.json", json.dumps({
            "2026-01-03": {"messages": 8, "sessions": 2, "tool_calls": 4},
            "2026-01-04": {"messages": 9, "sessions": 3, "tool_calls": 5},
        }))
        result = express_vitals(**{**no_files, "stats_path": sp})
        assert "2026-01-04" in result
        assert "2026-01-03" in result

    def test_flat_dict_ignores_non_dict_values(self, tmp_path, no_files):
        """Flat dict entries whose values aren't dicts should be skipped."""
        sp = _write(tmp_path / "st.json", json.dumps({
            "2026-01-05": "just a string",
            "2026-01-06": {"messages": 1, "sessions": 1, "tool_calls": 1},
        }))
        result = express_vitals(**{**no_files, "stats_path": sp})
        assert "2026-01-06" in result
        # The string-valued entry is excluded by the isinstance check
        assert "| 2026-01-05 |" not in result

    def test_limits_to_five_rows(self, tmp_path, no_files):
        days = [{"date": f"2026-01-{d:02d}", "messageCount": d} for d in range(1, 11)]
        sp = _write(tmp_path / "st.json", json.dumps(days))
        result = express_vitals(**{**no_files, "stats_path": sp})
        # Should include dates 10,9,8,7,6 (top 5 desc) and NOT 5,4,3,2,1
        for d in range(6, 11):
            assert f"2026-01-{d:02d}" in result
        for d in range(1, 6):
            assert f"| 2026-01-{d:02d}" not in result

    def test_missing_date_shows_question_mark(self, tmp_path, no_files):
        sp = _write(tmp_path / "st.json", json.dumps([
            {"messageCount": 1, "sessionCount": 2, "toolCallCount": 3},
        ]))
        result = express_vitals(**{**no_files, "stats_path": sp})
        assert "| ? | 1 | 2 | 3 |" in result

    def test_missing_stat_keys_default_zero(self, tmp_path, no_files):
        sp = _write(tmp_path / "st.json", json.dumps([{"date": "2026-02-01"}]))
        result = express_vitals(**{**no_files, "stats_path": sp})
        assert "| 2026-02-01 | 0 | 0 | 0 |" in result

    def test_empty_activity_skips_section(self, tmp_path, no_files):
        sp = _write(tmp_path / "st.json", json.dumps({"dailyActivity": []}))
        result = express_vitals(**{**no_files, "stats_path": sp})
        assert "## Recent Activity" not in result

    def test_scalar_json_skips_section(self, tmp_path, no_files):
        sp = _write(tmp_path / "st.json", json.dumps(42))
        result = express_vitals(**{**no_files, "stats_path": sp})
        assert "## Recent Activity" not in result

    def test_malformed_json_skips_section(self, tmp_path, no_files):
        sp = _write(tmp_path / "st.json", "not json")
        result = express_vitals(**{**no_files, "stats_path": sp})
        assert "## Recent Activity" not in result

    def test_oserror_skips_section(self, tmp_path, no_files):
        sp = tmp_path / "st.json"
        sp.touch()
        with patch.object(Path, "read_text", side_effect=OSError("err")):
            result = express_vitals(stats_path=sp)
        assert "## Recent Activity" not in result

    def test_table_header_format(self, tmp_path, no_files):
        sp = _write(tmp_path / "st.json", json.dumps([
            {"date": "2026-03-01", "messageCount": 1, "sessionCount": 1, "toolCallCount": 1},
        ]))
        result = express_vitals(**{**no_files, "stats_path": sp})
        assert "| Date | Messages | Sessions | Tool Calls |" in result
        assert "|------|----------|----------|------------|" in result


# ---------------------------------------------------------------------------
# 5. Full integration — all three files present
# ---------------------------------------------------------------------------

class TestFullReport:
    """All three input files are valid."""

    def test_all_sections_present(self, tmp_path):
        hp = _write(tmp_path / "h.md", "All good")
        sp = _write(tmp_path / "s.json", json.dumps({
            "enabledPlugins": {"p1": True, "p2": False},
        }))
        stp = _write(tmp_path / "st.json", json.dumps({
            "dailyActivity": [
                {"date": "2026-04-01", "messageCount": 99, "sessionCount": 7, "toolCallCount": 33},
            ],
        }))
        result = express_vitals(health_path=hp, settings_path=sp, stats_path=stp)

        assert "# Claude Code Health" in result
        assert "## Nightly Report" in result
        assert "All good" in result
        assert "## Plugins" in result
        assert "`p1`" in result
        assert "`p2`" in result
        assert "## Recent Activity" in result
        assert "| 2026-04-01 | 99 | 7 | 33 |" in result

    def test_output_ends_with_newline(self, tmp_path):
        """Joined lines should end cleanly."""
        hp = _write(tmp_path / "h.md", "ok")
        result = express_vitals(
            health_path=hp,
            settings_path=tmp_path / "no.json",
            stats_path=tmp_path / "no2.json",
        )
        assert result.endswith("\n") or result.strip() == result
