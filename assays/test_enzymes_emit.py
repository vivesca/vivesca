"""Tests for metabolon.enzymes.emit — all outbound secretion channels."""

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
    TELEMETRY_HEADER,
    EmitResult,
    PraxisResult,
    emit,
)
from metabolon.morphology import EffectorResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _eff(action: str, **kw):
    """Call emit and assert we got an EffectorResult."""
    r = emit(action, **kw)
    assert isinstance(r, EffectorResult)
    return r


# =========================== spark =========================================

class TestSpark:
    def test_spark_ok(self, tmp_path):
        spark_file = str(tmp_path / "sparks.md")
        with patch("metabolon.enzymes.emit._today_iso", return_value="2026-01-01"), \
             patch("metabolon.enzymes.emit.SPARKS_FILE", spark_file), \
             patch("metabolon.enzymes.emit._append_to_file") as mock_append:
            r = _eff("spark", label="test-label", content="test-content")
            assert r.success is True
            assert "test-label" in r.message
            mock_append.assert_called_once()

    def test_spark_with_tags(self):
        with patch("metabolon.enzymes.emit._today_iso", return_value="2026-01-01"), \
             patch("metabolon.enzymes.emit.SPARKS_FILE", "/dev/null"), \
             patch("metabolon.enzymes.emit._append_to_file"):
            r = _eff("spark", label="L", content="C", tags="t1,t2")
            assert r.success is True

    def test_spark_missing_label(self):
        r = _eff("spark", content="C")
        assert r.success is False
        assert "label" in r.message

    def test_spark_missing_content(self):
        r = _eff("spark", label="L")
        assert r.success is False
        assert "content" in r.message


# =========================== tweet =========================================

class TestTweet:
    def test_tweet_direct_text(self):
        with patch("metabolon.enzymes.emit._golgi") as mock_golgi, \
             patch("metabolon.enzymes.emit.invoke_organelle", return_value="tweet-id-123"):
            mock_golgi.chaperone_check.return_value = None
            r = _eff("tweet", text="Hello world")
            assert r.success is True
            assert "tweet-id-123" in r.message

    def test_tweet_from_insight(self):
        with patch("metabolon.enzymes.emit._golgi") as mock_golgi, \
             patch("metabolon.enzymes.emit.invoke_organelle", return_value="ok"), \
             patch("metabolon.enzymes.emit.synthesize", return_value="Compressed tweet"):
            mock_golgi.chaperone_check.return_value = None
            r = _eff("tweet", insight="A very long insight paragraph")
            assert r.success is True

    def test_tweet_chaperone_rejection(self):
        with patch("metabolon.enzymes.emit._golgi") as mock_golgi:
            mock_golgi.chaperone_check.return_value = "Too spicy"
            r = _eff("tweet", text="Something spicy")
            assert r.success is False
            assert "Too spicy" in r.message

    def test_tweet_missing_text_and_insight(self):
        r = _eff("tweet")
        assert r.success is False
        assert "text or insight" in r.message


# =========================== daily_note ====================================

class TestDailyNote:
    def test_daily_note_new_file(self, tmp_path):
        daily_dir = str(tmp_path / "daily")
        with patch("metabolon.enzymes.emit._today_iso", return_value="2026-03-15"), \
             patch("metabolon.enzymes.emit.DAILY_DIR", daily_dir):
            r = _eff("daily_note", section="Reflections", content="Deep thoughts")
            assert r.success is True
            assert "Reflections" in r.message
            fpath = os.path.join(daily_dir, "2026-03-15.md")
            assert os.path.exists(fpath)
            with open(fpath) as f:
                txt = f.read()
            assert "# 2026-03-15" in txt
            assert "## Reflections" in txt
            assert "Deep thoughts" in txt

    def test_daily_note_append_existing(self, tmp_path):
        daily_dir = str(tmp_path / "daily")
        fpath = os.path.join(daily_dir, "2026-03-15.md")
        os.makedirs(daily_dir)
        with open(fpath, "w") as f:
            f.write("# 2026-03-15\n")
        with patch("metabolon.enzymes.emit._today_iso", return_value="2026-03-15"), \
             patch("metabolon.enzymes.emit.DAILY_DIR", daily_dir):
            r = _eff("daily_note", section="Evening", content="Good day")
            assert r.success is True
            with open(fpath) as f:
                txt = f.read()
            assert "## Evening" in txt

    def test_daily_note_missing_section(self):
        r = _eff("daily_note", content="stuff")
        assert r.success is False
        assert "section" in r.message

    def test_daily_note_missing_content(self):
        r = _eff("daily_note", section="S")
        assert r.success is False
        assert "content" in r.message


# =========================== praxis ========================================

class TestPraxis:
    @patch("metabolon.enzymes.emit._praxis")
    def test_praxis_today(self, mock_prx):
        mock_prx.today.return_value = [{"task": "write tests"}]
        r = emit("praxis", subcommand="today")
        assert isinstance(r, PraxisResult)
        data = json.loads(r.output)
        assert data[0]["task"] == "write tests"

    @patch("metabolon.enzymes.emit._praxis")
    def test_praxis_no_json(self, mock_prx):
        mock_prx.stats.return_value = {"total": 5}
        r = emit("praxis", subcommand="stats", json_output=False)
        assert isinstance(r, PraxisResult)
        assert "total" in r.output
        # Not JSON — plain str()
        assert r.output == str({"total": 5})

    @patch("metabolon.enzymes.emit._praxis")
    def test_praxis_unknown_subcommand(self, mock_prx):
        r = emit("praxis", subcommand="nonexistent")
        assert isinstance(r, PraxisResult)
        assert "Unknown subcommand" in r.output

    @patch("metabolon.enzymes.emit._praxis")
    def test_praxis_spare(self, mock_prx):
        mock_prx.spare.return_value = ["task-a", "task-b"]
        r = emit("praxis", subcommand="spare")
        assert isinstance(r, PraxisResult)


# =========================== publish =======================================

class TestPublish:
    @patch("metabolon.enzymes.emit._golgi")
    def test_publish_new(self, mock_golgi):
        mock_golgi.new.return_value = ("slug-x", "/path/to/slug-x.md")
        r = _eff("publish", subcommand="new", slug="slug-x")
        assert r.success is True
        assert "slug-x" in r.message

    @patch("metabolon.enzymes.emit._golgi")
    def test_publish_list(self, mock_golgi):
        mock_golgi.list_posts.return_value = [
            {"slug": "s1", "title": "Title One", "draft": True},
            {"slug": "s2", "title": "Title Two", "draft": False},
        ]
        r = _eff("publish", subcommand="list")
        assert r.success is True
        assert "s1" in r.message
        assert "(draft)" in r.message

    @patch("metabolon.enzymes.emit._golgi")
    def test_publish_publish(self, mock_golgi):
        mock_golgi.publish.return_value = "v1.2"
        r = _eff("publish", subcommand="publish", slug="s1")
        assert r.success is True
        assert "v1.2" in r.message

    @patch("metabolon.enzymes.emit._golgi")
    def test_publish_push(self, mock_golgi):
        mock_golgi.push.return_value = "pushed"
        r = _eff("publish", subcommand="push")
        assert r.success is True
        assert "pushed" in r.message

    @patch("metabolon.enzymes.emit._golgi")
    def test_publish_index(self, mock_golgi):
        mock_golgi.index.return_value = 42
        r = _eff("publish", subcommand="index")
        assert r.success is True
        assert "42" in r.message

    @patch("metabolon.enzymes.emit._golgi")
    def test_publish_unknown_subcommand(self, mock_golgi):
        r = _eff("publish", subcommand="bogus")
        assert r.success is False
        assert "Unknown subcommand" in r.message


# =========================== reminder ======================================

class TestReminder:
    @patch("metabolon.enzymes.emit._pacemaker")
    def test_reminder_ok(self, mock_pm):
        mock_pm.add.return_value = "Reminder set"
        r = _eff("reminder", title="Call dentist")
        assert r.success is True
        assert "Reminder set" in r.message

    @patch("metabolon.enzymes.emit._pacemaker")
    def test_reminder_with_date(self, mock_pm):
        mock_pm.add.return_value = "ok"
        r = _eff("reminder", title="X", date="2026-04-01")
        assert r.success is True
        mock_pm.add.assert_called_once_with("X", date="2026-04-01")

    @patch("metabolon.enzymes.emit._pacemaker")
    def test_reminder_error(self, mock_pm):
        mock_pm.add.side_effect = RuntimeError("boom")
        r = _eff("reminder", title="X")
        assert r.success is False
        assert "boom" in r.message

    def test_reminder_missing_title(self):
        r = _eff("reminder")
        assert r.success is False
        assert "title" in r.message


# =========================== telemetry =====================================

class TestTelemetry:
    def test_telemetry_new_file(self, tmp_path):
        telem = str(tmp_path / "telemetry.md")
        with patch("metabolon.enzymes.emit._today_iso", return_value="2026-01-01"), \
             patch("metabolon.enzymes.emit.TELEMETRY_FILE", telem):
            r = _eff("telemetry", channel="blog", title="My Post", source_skill="write")
            assert r.success is True
            with open(telem) as f:
                txt = f.read()
            assert "| 2026-01-01 | blog |" in txt
            assert TELEMETRY_HEADER[:30] in txt

    def test_telemetry_existing_file(self, tmp_path):
        telem = str(tmp_path / "telemetry.md")
        with open(telem, "w") as f:
            f.write(TELEMETRY_HEADER + "| old | data |\n")
        with patch("metabolon.enzymes.emit._today_iso", return_value="2026-02-01"), \
             patch("metabolon.enzymes.emit.TELEMETRY_FILE", telem):
            r = _eff("telemetry", channel="tweet", title="T", source_skill="s")
            assert r.success is True

    def test_telemetry_uses_text_as_title(self, tmp_path):
        telem = str(tmp_path / "telemetry.md")
        with patch("metabolon.enzymes.emit._today_iso", return_value="2026-01-01"), \
             patch("metabolon.enzymes.emit.TELEMETRY_FILE", telem):
            r = _eff("telemetry", channel="c", text="title-from-text", source_skill="s")
            assert r.success is True
            with open(telem) as f:
                txt = f.read()
            assert "title-from-text" in txt

    def test_telemetry_missing_channel(self):
        r = _eff("telemetry", title="T", source_skill="s")
        assert r.success is False

    def test_telemetry_missing_source_skill(self):
        r = _eff("telemetry", channel="c", title="T")
        assert r.success is False


# =========================== telegram_text =================================

class TestTelegramText:
    @patch("metabolon.enzymes.emit._sv")
    def test_html_format(self, mock_sv):
        mock_sv.secrete_text.return_value = "sent"
        r = _eff("telegram_text", text="# Header\n**bold** and [link](http://x)")
        assert r.success is True
        call_args = mock_sv.secrete_text.call_args
        msg = call_args[0][0]
        assert "<b>Header</b>" in msg
        assert "<b>bold</b>" in msg
        assert "link (http://x)" in msg
        assert call_args[1]["html"] is True

    @patch("metabolon.enzymes.emit._sv")
    def test_plain_format(self, mock_sv):
        mock_sv.secrete_text.return_value = "sent"
        r = _eff("telegram_text", text="Hello", format="plain")
        assert r.success is True
        mock_sv.secrete_text.assert_called_once_with("Hello", html=False)

    def test_missing_text(self):
        r = _eff("telegram_text")
        assert r.success is False


# =========================== telegram_image ================================

class TestTelegramImage:
    @patch("metabolon.enzymes.emit._sv")
    def test_image_ok(self, mock_sv, tmp_path):
        img = tmp_path / "photo.png"
        img.write_bytes(b"\x89PNG")
        mock_sv.secrete_image.return_value = "sent"
        r = _eff("telegram_image", path=str(img), caption="nice")
        assert r.success is True
        mock_sv.secrete_image.assert_called_once_with(str(img), caption="nice")

    def test_image_missing_path(self):
        r = _eff("telegram_image")
        assert r.success is False
        assert "path" in r.message

    def test_image_file_not_found(self):
        r = _eff("telegram_image", path="/nonexistent/file.png")
        assert r.success is False
        assert "File not found" in r.message


# =========================== linkedin ======================================

class TestLinkedin:
    @patch("metabolon.enzymes.emit.synthesize", return_value="Professional post body here.")
    def test_linkedin_generates_post(self, mock_syn):
        r = _eff("linkedin", tweet="Short tweet text")
        assert r.success is False  # always returns False (not implemented)
        assert r.data["post"] == "Professional post body here."
        assert "unavailable" in r.message

    def test_linkedin_missing_tweet(self):
        r = _eff("linkedin")
        assert r.success is False
        assert "tweet" in r.message


# =========================== knowledge_signal ==============================

class TestKnowledgeSignal:
    @patch("metabolon.enzymes.emit.SensorySystem")
    def test_useful(self, mock_cls):
        instance = MagicMock()
        mock_cls.return_value = instance
        r = _eff("knowledge_signal", artifact="card-42", useful=True)
        assert r.success is True
        assert "useful" in r.message

    @patch("metabolon.enzymes.emit.SensorySystem")
    def test_not_useful(self, mock_cls):
        instance = MagicMock()
        mock_cls.return_value = instance
        r = _eff("knowledge_signal", artifact="card-99", useful=False, context="not relevant")
        assert r.success is True
        assert "not useful" in r.message

    def test_missing_artifact(self):
        r = _eff("knowledge_signal")
        assert r.success is False
        assert "artifact" in r.message


# =========================== interphase_close ==============================

class TestInterphaseClose:
    def test_writes_block(self, tmp_path):
        with patch("metabolon.enzymes.emit.INTERPHASE_DAILY_DIR", tmp_path):
            r = emit("interphase_close", shipped="did X", tomorrow="do Y",
                     open_threads="none", nudges="nudge1", day_score=3, note_date="2026-03-31")
            assert isinstance(r, EmitResult)
            assert "written" in r.output
            fpath = tmp_path / "2026-03-31.md"
            txt = fpath.read_text()
            assert "## Interphase" in txt
            assert "did X" in txt
            assert "3/5" in txt

    def test_appends_to_existing(self, tmp_path):
        fpath = tmp_path / "2026-03-30.md"
        fpath.write_text("# 2026-03-30\n## Morning\nHello")
        with patch("metabolon.enzymes.emit.INTERPHASE_DAILY_DIR", tmp_path):
            r = emit("interphase_close", shipped="s", tomorrow="t",
                     open_threads="o", nudges="n", day_score=4, note_date="2026-03-30")
            assert isinstance(r, EmitResult)
            txt = fpath.read_text()
            assert "## Morning" in txt
            assert "## Interphase" in txt

    def test_duplicate_block_rejected(self, tmp_path):
        fpath = tmp_path / "2026-03-30.md"
        fpath.write_text("# 2026-03-30\n## Interphase\nold content")
        with patch("metabolon.enzymes.emit.INTERPHASE_DAILY_DIR", tmp_path):
            r = emit("interphase_close", shipped="s", tomorrow="t",
                     open_threads="o", nudges="n", day_score=5, note_date="2026-03-30")
            assert isinstance(r, EmitResult)
            assert "already present" in r.output

    def test_invalid_date(self, tmp_path):
        with patch("metabolon.enzymes.emit.INTERPHASE_DAILY_DIR", tmp_path):
            r = _eff("interphase_close", shipped="s", tomorrow="t",
                     open_threads="o", nudges="n", day_score=3, note_date="bad-date")
            assert r.success is False
            assert "Invalid date" in r.message

    def test_day_score_out_of_range(self, tmp_path):
        with patch("metabolon.enzymes.emit.INTERPHASE_DAILY_DIR", tmp_path):
            r = _eff("interphase_close", shipped="s", tomorrow="t",
                     open_threads="o", nudges="n", day_score=0)
            assert r.success is False
            assert "day_score must be 1-5" in r.message

    def test_day_score_too_high(self, tmp_path):
        with patch("metabolon.enzymes.emit.INTERPHASE_DAILY_DIR", tmp_path):
            r = _eff("interphase_close", shipped="s", tomorrow="t",
                     open_threads="o", nudges="n", day_score=6)
            assert r.success is False
            assert "day_score must be 1-5" in r.message

    def test_missing_required_fields(self):
        r = _eff("interphase_close", shipped="s", tomorrow="t",
                 open_threads="o", nudges="n")
        assert r.success is False
        assert "interphase_close requires" in r.message


# =========================== unknown action ================================

class TestUnknownAction:
    def test_unknown(self):
        r = _eff("nonexistent_action")
        assert r.success is False
        assert "Unknown action" in r.message
