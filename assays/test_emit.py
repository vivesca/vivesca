"""Tests for metabolon.enzymes.emit."""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.emit import (
    DAILY_DIR,
    INTERPHASE_DAILY_DIR,
    SPARKS_FILE,
    TELEMETRY_FILE,
    EmitResult,
    PraxisResult,
    _append_to_file,
    _today_iso,
    emit,
)
from metabolon.morphology import EffectorResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_emit(**overrides):
    """Build keyword arguments for emit(), filling sensible defaults."""
    defaults = dict(action="spark", label="test-label", content="test-content")
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# _today_iso
# ---------------------------------------------------------------------------

class TestTodayIso:
    def test_returns_date_string(self):
        result = _today_iso()
        assert len(result) == 10
        # Should parse as a valid date
        date.fromisoformat(result)

    def test_format_is_yyyy_mm_dd(self):
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2}$", _today_iso())


# ---------------------------------------------------------------------------
# _append_to_file
# ---------------------------------------------------------------------------

class TestAppendToFile:
    def test_creates_directory_and_appends(self, tmp_path):
        fpath = str(tmp_path / "sub" / "dir" / "file.md")
        _append_to_file(fpath, "hello\n")
        _append_to_file(fpath, "world\n")
        with open(fpath) as f:
            assert f.read() == "hello\nworld\n"


# ---------------------------------------------------------------------------
# spark action
# ---------------------------------------------------------------------------

class TestSpark:
    @patch("metabolon.enzymes.emit._append_to_file")
    def test_spark_success(self, mock_append):
        result = emit(action="spark", label="idea", content="big thought")
        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert "idea" in result.message
        mock_append.assert_called_once()

    @patch("metabolon.enzymes.emit._append_to_file")
    def test_spark_with_tags(self, mock_append):
        result = emit(action="spark", label="x", content="y", tags="ai,ml")
        assert result.success is True
        written = mock_append.call_args[0][1]
        assert "ai,ml" in written

    def test_spark_missing_label(self):
        result = emit(action="spark", label="", content="stuff")
        assert result.success is False
        assert "label" in result.message.lower() or "content" in result.message.lower()

    def test_spark_missing_content(self):
        result = emit(action="spark", label="lab", content="")
        assert result.success is False


# ---------------------------------------------------------------------------
# daily_note action
# ---------------------------------------------------------------------------

class TestDailyNote:
    @patch("metabolon.enzymes.emit._append_to_file")
    @patch("os.path.exists", return_value=True)
    def test_daily_note_appends_section(self, mock_exists, mock_append):
        result = emit(action="daily_note", section="Insights", content="Learned X")
        assert result.success is True
        assert "Insights" in result.message
        # Second call appends the section entry
        mock_append.assert_called_once()
        written = mock_append.call_args[0][1]
        assert "## Insights\n" in written
        assert "Learned X" in written

    @patch("metabolon.enzymes.emit._append_to_file")
    @patch("os.path.exists", return_value=False)
    def test_daily_note_creates_file_if_missing(self, mock_exists, mock_append):
        result = emit(action="daily_note", section="Log", content="entry")
        assert result.success is True
        # First call creates header, second appends section
        assert mock_append.call_count == 2

    def test_daily_note_missing_section(self):
        result = emit(action="daily_note", section="", content="stuff")
        assert result.success is False

    def test_daily_note_missing_content(self):
        result = emit(action="daily_note", section="sec", content="")
        assert result.success is False


# ---------------------------------------------------------------------------
# telemetry action
# ---------------------------------------------------------------------------

class TestTelemetry:
    @patch("metabolon.enzymes.emit._append_to_file")
    @patch("os.path.exists", return_value=True)
    def test_telemetry_success(self, mock_exists, mock_append):
        result = emit(
            action="telemetry", channel="blog", title="Post Title",
            source_skill="writing", tags="tech",
        )
        assert result.success is True
        assert "blog" in result.message
        mock_append.assert_called_once()
        row = mock_append.call_args[0][1]
        assert "| blog |" in row
        assert "| Post Title |" in row

    @patch("metabolon.enzymes.emit._append_to_file")
    @patch("os.path.exists", return_value=False)
    def test_telemetry_creates_header_if_missing(self, mock_exists, mock_append):
        result = emit(
            action="telemetry", channel="video", title="Vid",
            source_skill="editing",
        )
        assert result.success is True
        assert mock_append.call_count == 2  # header then row

    def test_telemetry_missing_channel(self):
        result = emit(action="telemetry", title="T", source_skill="s")
        assert result.success is False

    def test_telemetry_missing_source_skill(self):
        result = emit(action="telemetry", channel="c", title="T", source_skill="")
        assert result.success is False


# ---------------------------------------------------------------------------
# telegram_text action
# ---------------------------------------------------------------------------

class TestTelegramText:
    @patch("metabolon.enzymes.emit._sv")
    def test_telegram_text_sends_html(self, mock_sv):
        mock_sv.secrete_text.return_value = "sent"
        result = emit(action="telegram_text", text="**bold** and <b>hi</b>", format="html")
        assert result.success is True
        mock_sv.secrete_text.assert_called_once()
        assert mock_sv.secrete_text.call_args[1]["html"] is True

    @patch("metabolon.enzymes.emit._sv")
    def test_telegram_text_plain_format(self, mock_sv):
        mock_sv.secrete_text.return_value = "sent"
        result = emit(action="telegram_text", text="hello", format="plain")
        assert result.success is True
        assert mock_sv.secrete_text.call_args[1]["html"] is False

    def test_telegram_text_missing_text(self):
        result = emit(action="telegram_text", text="")
        assert result.success is False


# ---------------------------------------------------------------------------
# telegram_image action
# ---------------------------------------------------------------------------

class TestTelegramImage:
    @patch("metabolon.enzymes.emit._sv")
    @patch("os.path.isfile", return_value=True)
    def test_telegram_image_sends(self, mock_isfile, mock_sv):
        mock_sv.secrete_image.return_value = "sent"
        result = emit(action="telegram_image", path="/tmp/img.png", caption="cap")
        assert result.success is True
        mock_sv.secrete_image.assert_called_once_with("/tmp/img.png", caption="cap")

    def test_telegram_image_missing_path(self):
        result = emit(action="telegram_image", path="")
        assert result.success is False

    @patch("os.path.isfile", return_value=False)
    def test_telegram_image_file_not_found(self, mock_isfile):
        result = emit(action="telegram_image", path="/no/such/file.png")
        assert result.success is False
        assert "not found" in result.message.lower()


# ---------------------------------------------------------------------------
# reminder action
# ---------------------------------------------------------------------------

class TestReminder:
    @patch("metabolon.enzymes.emit._pacemaker")
    def test_reminder_success(self, mock_pm):
        mock_pm.add.return_value = "reminder set"
        result = emit(action="reminder", title="Call dentist")
        assert result.success is True
        mock_pm.add.assert_called_once()

    def test_reminder_missing_title(self):
        result = emit(action="reminder", title="")
        assert result.success is False

    @patch("metabolon.enzymes.emit._pacemaker")
    def test_reminder_exception_caught(self, mock_pm):
        mock_pm.add.side_effect = RuntimeError("boom")
        result = emit(action="reminder", title="test")
        assert result.success is False
        assert "boom" in result.message


# ---------------------------------------------------------------------------
# praxis action
# ---------------------------------------------------------------------------

class TestPraxis:
    @patch("metabolon.enzymes.emit._praxis")
    def test_praxis_today_json(self, mock_px):
        mock_px.today.return_value = [{"task": "write tests"}]
        result = emit(action="praxis", subcommand="today")
        assert isinstance(result, PraxisResult)
        parsed = json.loads(result.output)
        assert parsed[0]["task"] == "write tests"

    @patch("metabolon.enzymes.emit._praxis")
    def test_praxis_stats_str(self, mock_px):
        mock_px.stats.return_value = {"total": 42}
        result = emit(action="praxis", subcommand="stats", json_output=False)
        assert isinstance(result, PraxisResult)
        assert "42" in result.output

    def test_praxis_unknown_subcommand(self):
        result = emit(action="praxis", subcommand="nonexistent")
        assert isinstance(result, PraxisResult)
        assert "Unknown" in result.output


# ---------------------------------------------------------------------------
# knowledge_signal action
# ---------------------------------------------------------------------------

class TestKnowledgeSignal:
    @patch("metabolon.enzymes.emit.SensorySystem")
    def test_knowledge_signal_useful(self, mock_ss_cls):
        mock_collector = MagicMock()
        mock_ss_cls.return_value = mock_collector
        result = emit(action="knowledge_signal", artifact="doc-42", useful=True, context="helped debugging")
        assert result.success is True
        assert "useful" in result.message
        mock_collector.append.assert_called_once()

    @patch("metabolon.enzymes.emit.SensorySystem")
    def test_knowledge_signal_not_useful(self, mock_ss_cls):
        mock_collector = MagicMock()
        mock_ss_cls.return_value = mock_collector
        result = emit(action="knowledge_signal", artifact="card-7", useful=False)
        assert result.success is True
        assert "not useful" in result.message

    def test_knowledge_signal_missing_artifact(self):
        result = emit(action="knowledge_signal", artifact="")
        assert result.success is False


# ---------------------------------------------------------------------------
# interphase_close action
# ---------------------------------------------------------------------------

class TestInterphaseClose:
    def test_interphase_close_writes_file(self, tmp_path):
        daily_dir = tmp_path / "Daily"
        daily_dir.mkdir()
        target = daily_dir / "2026-04-02.md"
        with patch("metabolon.enzymes.emit.INTERPHASE_DAILY_DIR", daily_dir):
            result = emit(
                action="interphase_close",
                shipped="tests", tomorrow="more tests",
                open_threads="none", nudges="none",
                day_score=4, note_date="2026-04-02",
            )
        assert isinstance(result, EmitResult)
        assert "written" in result.output.lower() or "Interphase" in result.output
        content = target.read_text()
        assert "## Interphase" in content
        assert "**Shipped:** tests" in content
        assert "4/5" in content

    def test_interphase_close_invalid_date(self):
        result = emit(
            action="interphase_close",
            shipped="x", tomorrow="y", open_threads="z", nudges="w",
            day_score=3, note_date="not-a-date",
        )
        assert result.success is False
        assert "Invalid" in result.message

    def test_interphase_close_bad_day_score(self, tmp_path):
        daily_dir = tmp_path / "Daily"
        daily_dir.mkdir()
        with patch("metabolon.enzymes.emit.INTERPHASE_DAILY_DIR", daily_dir):
            result = emit(
                action="interphase_close",
                shipped="x", tomorrow="y", open_threads="z", nudges="w",
                day_score=0, note_date="2026-04-02",
            )
        assert result.success is False
        assert "day_score" in result.message

    def test_interphase_close_missing_required(self):
        result = emit(action="interphase_close")
        assert result.success is False

    def test_interphase_close_duplicate_block(self, tmp_path):
        daily_dir = tmp_path / "Daily"
        daily_dir.mkdir()
        target = daily_dir / "2026-04-02.md"
        target.write_text("# 2026-04-02\n\n## Interphase\n\nold content\n")
        with patch("metabolon.enzymes.emit.INTERPHASE_DAILY_DIR", daily_dir):
            result = emit(
                action="interphase_close",
                shipped="x", tomorrow="y", open_threads="z", nudges="w",
                day_score=3, note_date="2026-04-02",
            )
        assert isinstance(result, EmitResult)
        assert "already present" in result.output


# ---------------------------------------------------------------------------
# unknown action
# ---------------------------------------------------------------------------

class TestUnknownAction:
    def test_unknown_action_returns_error(self):
        result = emit(action="nonexistent_action")
        assert result.success is False
        assert "Unknown" in result.message
