"""Tests for metabolon/enzymes/emit.py — all outbound secretion channels."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import the module under test.  We mock heavy deps at the module level so
# every test shares the same patches.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _tmp_notes(tmp_path, monkeypatch):
    """Redirect NOTES / file paths to a temp dir so tests never touch real FS."""
    notes = tmp_path / "notes"
    notes.mkdir()
    # Patch chromatin-based NOTES constant
    monkeypatch.setattr("metabolon.enzymes.emit.NOTES", str(notes))
    monkeypatch.setattr("metabolon.enzymes.emit.SPARKS_FILE", str(notes / "_sparks.md"))
    monkeypatch.setattr("metabolon.enzymes.emit.DAILY_DIR", str(notes / "Daily"))
    monkeypatch.setattr("metabolon.enzymes.emit.TELEMETRY_FILE", str(notes / "telemetry.md"))
    interphase_dir = tmp_path / "epigenome" / "chromatin" / "Daily"
    monkeypatch.setattr("metabolon.enzymes.emit.INTERPHASE_DAILY_DIR", interphase_dir)
    return notes


# Convenience: get the wrapped function (bypass @tool decorator)
def _fn():
    from metabolon.enzymes import emit as mod

    return mod.emit


# ===================================================================
# spark
# ===================================================================


class TestSpark:
    def test_spark_success(self):
        fn = _fn()
        result = fn(action="spark", label="idea", content="test content")
        assert result.success is True
        assert "idea" in result.message

    def test_spark_missing_label(self):
        fn = _fn()
        result = fn(action="spark", label="", content="stuff")
        assert result.success is False

    def test_spark_missing_content(self):
        fn = _fn()
        result = fn(action="spark", label="x", content="")
        assert result.success is False

    def test_spark_appends_file(self, tmp_path):
        notes = tmp_path / "notes"
        fn = _fn()
        fn(action="spark", label="L1", content="C1", tags="t1")
        fn(action="spark", label="L2", content="C2")
        text = (notes / "_sparks.md").read_text()
        assert "**L1**: C1" in text
        assert "t1 --" in text
        assert "**L2**: C2" in text


# ===================================================================
# tweet
# ===================================================================


class TestTweet:
    @patch("metabolon.enzymes.emit.invoke_organelle", return_value="ok-tweeted")
    @patch("metabolon.enzymes.emit._golgi")
    def test_tweet_direct_text(self, mock_golgi, mock_invoke):
        mock_golgi.chaperone_check.return_value = None  # no rejection
        fn = _fn()
        result = fn(action="tweet", text="Hello world")
        assert result.success is True
        mock_invoke.assert_called_once()
        mock_golgi.chaperone_check.assert_called_once_with("Hello world", "tweet")

    @patch("metabolon.enzymes.emit.invoke_organelle", return_value="ok")
    @patch("metabolon.enzymes.emit._golgi")
    def test_tweet_rejected_by_chaperone(self, mock_golgi, mock_invoke):
        mock_golgi.chaperone_check.return_value = "contains PII"
        fn = _fn()
        result = fn(action="tweet", text="secret stuff")
        assert result.success is False
        assert "PII" in result.message
        mock_invoke.assert_not_called()

    @patch("metabolon.enzymes.emit.synthesize", return_value="compressed tweet")
    @patch("metabolon.enzymes.emit.invoke_organelle", return_value="ok")
    @patch("metabolon.enzymes.emit._golgi")
    def test_tweet_from_insight(self, mock_golgi, mock_invoke, mock_synth):
        mock_golgi.chaperone_check.return_value = None
        fn = _fn()
        result = fn(action="tweet", insight="long insight text")
        assert result.success is True
        mock_synth.assert_called_once()

    def test_tweet_no_text_no_insight(self):
        fn = _fn()
        result = fn(action="tweet")
        assert result.success is False
        assert "requires" in result.message.lower()


# ===================================================================
# daily_note
# ===================================================================


class TestDailyNote:
    def test_daily_note_creates_file(self, tmp_path):
        fn = _fn()
        with patch("metabolon.enzymes.emit._today_iso", return_value="2026-03-31"):
            result = fn(action="daily_note", section="Journal", content="Wrote tests.")
        assert result.success is True
        daily_dir = tmp_path / "notes" / "Daily"
        content = (daily_dir / "2026-03-31.md").read_text()
        assert "## Journal" in content
        assert "Wrote tests." in content

    def test_daily_note_missing_section(self):
        fn = _fn()
        result = fn(action="daily_note", section="", content="stuff")
        assert result.success is False

    def test_daily_note_missing_content(self):
        fn = _fn()
        result = fn(action="daily_note", section="sec", content="")
        assert result.success is False

    def test_daily_note_appends_to_existing(self, tmp_path):
        fn = _fn()
        daily_dir = tmp_path / "notes" / "Daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        (daily_dir / "2026-03-31.md").write_text("# 2026-03-31\n")
        with patch("metabolon.enzymes.emit._today_iso", return_value="2026-03-31"):
            result = fn(action="daily_note", section="Evening", content="Wrap-up")
        text = (daily_dir / "2026-03-31.md").read_text()
        assert "## Evening" in text
        assert "Wrap-up" in text


# ===================================================================
# praxis
# ===================================================================


class TestPraxis:
    @patch("metabolon.enzymes.emit._praxis")
    def test_praxis_today(self, mock_prx):
        mock_prx.today.return_value = [{"task": "do stuff"}]
        fn = _fn()
        result = fn(action="praxis", subcommand="today")
        assert result.output is not None
        parsed = json.loads(result.output)
        assert parsed[0]["task"] == "do stuff"

    @patch("metabolon.enzymes.emit._praxis")
    def test_praxis_unknown_subcommand(self, mock_prx):
        fn = _fn()
        result = fn(action="praxis", subcommand="nonexistent")
        assert "Unknown subcommand" in result.output

    @patch("metabolon.enzymes.emit._praxis")
    def test_praxis_json_output_false(self, mock_prx):
        mock_prx.stats.return_value = {"total": 5}
        fn = _fn()
        result = fn(action="praxis", subcommand="stats", json_output=False)
        assert "total" in result.output  # str(dict), not json


# ===================================================================
# publish
# ===================================================================


class TestPublish:
    # publish does a local `from metabolon.organelles import golgi`,
    # so we must patch the real module, not the module-level _golgi alias.
    @patch("metabolon.organelles.golgi.push")
    @patch("metabolon.organelles.golgi.index")
    @patch("metabolon.organelles.golgi.publish")
    @patch("metabolon.organelles.golgi.list_posts")
    @patch("metabolon.organelles.golgi.new")
    def test_publish_new(self, mock_new, mock_list, mock_publish, mock_index, mock_push):
        mock_new.return_value = ("slug", "/path/to/draft.md")
        fn = _fn()
        result = fn(action="publish", subcommand="new", slug="my-post")
        assert result.success is True
        assert "draft" in result.message.lower()

    @patch("metabolon.organelles.golgi.push")
    @patch("metabolon.organelles.golgi.index")
    @patch("metabolon.organelles.golgi.publish")
    @patch("metabolon.organelles.golgi.list_posts")
    @patch("metabolon.organelles.golgi.new")
    def test_publish_list(self, mock_new, mock_list, mock_publish, mock_index, mock_push):
        mock_list.return_value = [
            {"slug": "post-a", "title": "Title A", "draft": True},
            {"slug": "post-b", "title": "Title B", "draft": False},
        ]
        fn = _fn()
        result = fn(action="publish", subcommand="list")
        assert result.success is True
        assert "post-a" in result.message
        assert "draft" in result.message

    @patch("metabolon.organelles.golgi.push")
    @patch("metabolon.organelles.golgi.index")
    @patch("metabolon.organelles.golgi.publish")
    @patch("metabolon.organelles.golgi.list_posts")
    @patch("metabolon.organelles.golgi.new")
    def test_publish_publish(self, mock_new, mock_list, mock_publish, mock_index, mock_push):
        mock_publish.return_value = "2026-03-31-my-post"
        fn = _fn()
        result = fn(action="publish", subcommand="publish", slug="my-post")
        assert result.success is True
        assert "Published" in result.message

    @patch("metabolon.organelles.golgi.push")
    @patch("metabolon.organelles.golgi.index")
    @patch("metabolon.organelles.golgi.publish")
    @patch("metabolon.organelles.golgi.list_posts")
    @patch("metabolon.organelles.golgi.new")
    def test_publish_push(self, mock_new, mock_list, mock_publish, mock_index, mock_push):
        mock_push.return_value = "pushed"
        fn = _fn()
        result = fn(action="publish", subcommand="push")
        assert result.success is True
        assert "pushed" in result.message

    @patch("metabolon.organelles.golgi.push")
    @patch("metabolon.organelles.golgi.index")
    @patch("metabolon.organelles.golgi.publish")
    @patch("metabolon.organelles.golgi.list_posts")
    @patch("metabolon.organelles.golgi.new")
    def test_publish_index(self, mock_new, mock_list, mock_publish, mock_index, mock_push):
        mock_index.return_value = 42
        fn = _fn()
        result = fn(action="publish", subcommand="index")
        assert result.success is True
        assert "42" in result.message

    @patch("metabolon.organelles.golgi.push")
    @patch("metabolon.organelles.golgi.index")
    @patch("metabolon.organelles.golgi.publish")
    @patch("metabolon.organelles.golgi.list_posts")
    @patch("metabolon.organelles.golgi.new")
    def test_publish_unknown_subcommand(self, mock_new, mock_list, mock_publish, mock_index, mock_push):
        fn = _fn()
        result = fn(action="publish", subcommand="bogus")
        assert result.success is False


# ===================================================================
# reminder
# ===================================================================


class TestReminder:
    @patch("metabolon.enzymes.emit._pacemaker")
    def test_reminder_success(self, mock_pm):
        mock_pm.add.return_value = "reminder set"
        fn = _fn()
        result = fn(action="reminder", title="Standup", date="2026-04-01")
        assert result.success is True
        mock_pm.add.assert_called_once_with("Standup", date="2026-04-01")

    def test_reminder_missing_title(self):
        fn = _fn()
        result = fn(action="reminder", title="")
        assert result.success is False

    @patch("metabolon.enzymes.emit._pacemaker")
    def test_reminder_exception(self, mock_pm):
        mock_pm.add.side_effect = RuntimeError("no Due.app")
        fn = _fn()
        result = fn(action="reminder", title="Test")
        assert result.success is False
        assert "no Due.app" in result.message


# ===================================================================
# telemetry
# ===================================================================


class TestTelemetry:
    def test_telemetry_creates_file(self, tmp_path):
        fn = _fn()
        result = fn(
            action="telemetry",
            channel="blog",
            title="My Post",
            source_skill="writing",
            slug="my-post",
            tags="tech,ai",
        )
        assert result.success is True
        tfile = tmp_path / "notes" / "telemetry.md"
        text = tfile.read_text()
        assert "Content Telemetry" in text  # header written
        assert "blog" in text
        assert "my-post" in text

    def test_telemetry_appends_to_existing(self, tmp_path):
        fn = _fn()
        # First entry creates file
        fn(action="telemetry", channel="x", title="T1", source_skill="s1")
        # Second entry appends
        fn(action="telemetry", channel="y", title="T2", source_skill="s2")
        tfile = tmp_path / "notes" / "telemetry.md"
        lines = tfile.read_text().splitlines()
        # header + separator + data rows => at least 2 data rows
        data_rows = [l for l in lines if l.startswith("|") and "blog" not in l and "channel" not in l and "---" not in l]
        assert len(data_rows) >= 2

    def test_telemetry_missing_channel(self):
        fn = _fn()
        result = fn(action="telemetry", channel="", title="X", source_skill="s")
        assert result.success is False

    def test_telemetry_uses_text_as_title_fallback(self, tmp_path):
        fn = _fn()
        result = fn(action="telemetry", channel="blog", text="Fallback Title", source_skill="s")
        assert result.success is True
        assert "Fallback Title" in result.message


# ===================================================================
# telegram_text
# ===================================================================


class TestTelegramText:
    @patch("metabolon.enzymes.emit._sv")
    def test_telegram_text_plain(self, mock_sv):
        mock_sv.secrete_text.return_value = "sent"
        fn = _fn()
        result = fn(action="telegram_text", text="hello", format="plain")
        assert result.success is True
        mock_sv.secrete_text.assert_called_once_with("hello", html=False)

    @patch("metabolon.enzymes.emit._sv")
    def test_telegram_text_html(self, mock_sv):
        mock_sv.secrete_text.return_value = "sent"
        fn = _fn()
        result = fn(action="telegram_text", text="## Heading\n**bold**\n[link](http://x.com)")
        assert result.success is True
        call_args = mock_sv.secrete_text.call_args
        msg = call_args[0][0]
        assert "<b>Heading</b>" in msg
        assert "<b>bold</b>" in msg
        assert "link (http://x.com)" in msg

    def test_telegram_text_missing_text(self):
        fn = _fn()
        result = fn(action="telegram_text", text="")
        assert result.success is False


# ===================================================================
# telegram_image
# ===================================================================


class TestTelegramImage:
    @patch("metabolon.enzymes.emit._sv")
    def test_telegram_image_success(self, mock_sv, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"\xff\xd8\xff")
        mock_sv.secrete_image.return_value = "sent"
        fn = _fn()
        result = fn(action="telegram_image", path=str(img), caption="test")
        assert result.success is True
        mock_sv.secrete_image.assert_called_once_with(str(img), caption="test")

    def test_telegram_image_missing_path(self):
        fn = _fn()
        result = fn(action="telegram_image", path="")
        assert result.success is False

    def test_telegram_image_file_not_found(self):
        fn = _fn()
        result = fn(action="telegram_image", path="/no/such/file.jpg")
        assert result.success is False
        assert "not found" in result.message.lower()


# ===================================================================
# linkedin
# ===================================================================


class TestLinkedin:
    @patch("metabolon.enzymes.emit.synthesize", return_value="Professional post body here.")
    def test_linkedin_returns_post_in_data(self, mock_synth):
        fn = _fn()
        result = fn(action="linkedin", tweet="short tweet")
        assert result.success is False  # posting unavailable
        assert "post" in result.data
        assert "Professional post body" in result.data["post"]
        mock_synth.assert_called_once()

    def test_linkedin_missing_tweet(self):
        fn = _fn()
        result = fn(action="linkedin", tweet="")
        assert result.success is False
        assert "requires" in result.message.lower()


# ===================================================================
# knowledge_signal
# ===================================================================


class TestKnowledgeSignal:
    @patch("metabolon.enzymes.emit.SensorySystem")
    def test_knowledge_signal_useful(self, mock_ss_cls):
        mock_instance = MagicMock()
        mock_ss_cls.return_value = mock_instance
        fn = _fn()
        result = fn(action="knowledge_signal", artifact="card-42", useful=True, context="review")
        assert result.success is True
        assert "useful" in result.message
        mock_instance.append.assert_called_once()

    @patch("metabolon.enzymes.emit.SensorySystem")
    def test_knowledge_signal_not_useful(self, mock_ss_cls):
        mock_instance = MagicMock()
        mock_ss_cls.return_value = mock_instance
        fn = _fn()
        result = fn(action="knowledge_signal", artifact="card-99", useful=False)
        assert result.success is True
        assert "not useful" in result.message

    def test_knowledge_signal_missing_artifact(self):
        fn = _fn()
        result = fn(action="knowledge_signal", artifact="")
        assert result.success is False


# ===================================================================
# interphase_close
# ===================================================================


class TestInterphaseClose:
    def test_interphase_close_creates_note(self, tmp_path):
        fn = _fn()
        result = fn(
            action="interphase_close",
            shipped="feature A",
            tomorrow="feature B",
            open_threads="none",
            nudges="none",
            day_score=4,
            note_date="2026-03-31",
        )
        assert "written" in result.output.lower()
        ip_dir = tmp_path / "epigenome" / "chromatin" / "Daily"
        note = ip_dir / "2026-03-31.md"
        assert note.exists()
        text = note.read_text()
        assert "## Interphase" in text
        assert "feature A" in text
        assert "4/5" in text

    def test_interphase_close_appends_to_existing(self, tmp_path):
        ip_dir = tmp_path / "epigenome" / "chromatin" / "Daily"
        ip_dir.mkdir(parents=True)
        (ip_dir / "2026-03-31.md").write_text("# 2026-03-31\n\nSome existing content.\n")
        fn = _fn()
        result = fn(
            action="interphase_close",
            shipped="X",
            tomorrow="Y",
            open_threads="Z",
            nudges="N",
            day_score=3,
            note_date="2026-03-31",
        )
        text = (ip_dir / "2026-03-31.md").read_text()
        assert "Some existing content" in text
        assert "## Interphase" in text

    def test_interphase_close_duplicate_block(self, tmp_path):
        ip_dir = tmp_path / "epigenome" / "chromatin" / "Daily"
        ip_dir.mkdir(parents=True)
        (ip_dir / "2026-03-31.md").write_text("# 2026-03-31\n\n## Interphase\n\nold stuff\n")
        fn = _fn()
        result = fn(
            action="interphase_close",
            shipped="X",
            tomorrow="Y",
            open_threads="Z",
            nudges="N",
            day_score=3,
            note_date="2026-03-31",
        )
        assert "already present" in result.output

    def test_interphase_close_invalid_date(self):
        fn = _fn()
        result = fn(
            action="interphase_close",
            shipped="X", tomorrow="Y", open_threads="Z", nudges="N",
            day_score=3, note_date="not-a-date",
        )
        assert result.success is False
        assert "Invalid date" in result.message

    def test_interphase_close_bad_score(self):
        fn = _fn()
        result = fn(
            action="interphase_close",
            shipped="X", tomorrow="Y", open_threads="Z", nudges="N",
            day_score=0,
        )
        assert result.success is False
        assert "day_score" in result.message

    def test_interphase_close_score_too_high(self):
        fn = _fn()
        result = fn(
            action="interphase_close",
            shipped="X", tomorrow="Y", open_threads="Z", nudges="N",
            day_score=6,
        )
        assert result.success is False
        assert "day_score" in result.message

    def test_interphase_close_missing_fields(self):
        fn = _fn()
        result = fn(
            action="interphase_close",
            shipped="", tomorrow="Y", open_threads="Z", nudges="N", day_score=3,
        )
        assert result.success is False
        assert "requires" in result.message.lower()


# ===================================================================
# unknown action
# ===================================================================


class TestUnknownAction:
    def test_unknown_action(self):
        fn = _fn()
        result = fn(action="foobar")
        assert result.success is False
        assert "Unknown action" in result.message
