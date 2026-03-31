"""Tests for effectors/exocytosis.py — garden post pipeline."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR_PATH = Path(__file__).parent.parent / "effectors" / "exocytosis.py"


def _load_exocytosis():
    """Load exocytosis effector via exec, with a fake __name__ so main() doesn't fire."""
    source = EFFECTOR_PATH.read_text()
    ns: dict = {"__name__": "test_exocytosis_load"}
    exec(source, ns)
    return ns


_mod = _load_exocytosis()
get_next_topic = _mod["get_next_topic"]
mark_done = _mod["mark_done"]
generate = _mod["generate"]
judge = _mod["judge"]
notify = _mod["notify"]
publish = _mod["publish"]
main = _mod["main"]


# ── get_next_topic ────────────────────────────────────────────────────


class TestGetNextTopic:
    def test_returns_first_unchecked(self, tmp_path):
        queue = tmp_path / "Queue.md"
        queue.write_text("- [ ] Topic A\n- [ ] Topic B\n")
        with patch.object(_mod, "QUEUE", queue):
            result = get_next_topic()
        assert result == (0, "Topic A")

    def test_skips_checked(self, tmp_path):
        queue = tmp_path / "Queue.md"
        queue.write_text("- [x] Done\n- [ ] Next\n")
        with patch.object(_mod, "QUEUE", queue):
            result = get_next_topic()
        assert result == (1, "Next")

    def test_returns_none_when_empty(self, tmp_path):
        queue = tmp_path / "Queue.md"
        queue.write_text("- [x] All done\n")
        with patch.object(_mod, "QUEUE", queue):
            assert get_next_topic() is None

    def test_returns_none_on_blank_file(self, tmp_path):
        queue = tmp_path / "Queue.md"
        queue.write_text("")
        with patch.object(_mod, "QUEUE", queue):
            assert get_next_topic() is None

    def test_strips_whitespace_from_topic(self, tmp_path):
        queue = tmp_path / "Queue.md"
        queue.write_text("- [ ]   Spaced topic  \n")
        with patch.object(_mod, "QUEUE", queue):
            result = get_next_topic()
        assert result == (0, "Spaced topic")


# ── mark_done ─────────────────────────────────────────────────────────


class TestMarkDone:
    def test_marks_line_checked(self, tmp_path):
        queue = tmp_path / "Queue.md"
        queue.write_text("- [ ] Alpha\n- [ ] Beta\n")
        with patch.object(_mod, "QUEUE", queue):
            mark_done(0)
        assert queue.read_text().startswith("- [x] Alpha")

    def test_preserves_other_lines(self, tmp_path):
        queue = tmp_path / "Queue.md"
        queue.write_text("- [ ] Alpha\n- [ ] Beta\n")
        with patch.object(_mod, "QUEUE", queue):
            mark_done(0)
        lines = queue.read_text().splitlines()
        assert lines[1] == "- [ ] Beta"

    def test_marks_second_line(self, tmp_path):
        queue = tmp_path / "Queue.md"
        queue.write_text("- [ ] Alpha\n- [ ] Beta\n")
        with patch.object(_mod, "QUEUE", queue):
            mark_done(1)
        lines = queue.read_text().splitlines()
        assert lines[0] == "- [ ] Alpha"
        assert lines[1] == "- [x] Beta"


# ── generate ──────────────────────────────────────────────────────────


class TestGenerate:
    @patch("metabolon.symbiont.transduce", return_value="Generated post body.")
    def test_calls_transduce_with_formatted_prompt(self, mock_td):
        result = generate("My topic", "be concise")
        assert result == "Generated post body."
        mock_td.assert_called_once()
        call_args = mock_td.call_args
        assert call_args[0][0] == "goose"
        assert "My topic" in call_args[0][1]
        assert "be concise" in call_args[0][1]

    @patch("metabolon.symbiont.transduce", return_value="With extra context.")
    def test_appends_extra_context(self, mock_td):
        result = generate("Topic", "style", extra="\n\nFix this.")
        assert result == "With extra context."
        prompt = mock_td.call_args[0][1]
        assert "Fix this." in prompt

    @patch("metabolon.symbiont.transduce", return_value="Post text.")
    def test_uses_timeout(self, mock_td):
        generate("Topic", "style")
        assert mock_td.call_args[1]["timeout"] == 120


# ── judge ─────────────────────────────────────────────────────────────


class TestJudge:
    @patch("metabolon.symbiont.transduce", return_value="PASS — strong thesis.")
    def test_pass_verdict(self, mock_td):
        passed, verdict = judge("Some post text")
        assert passed is True
        assert "PASS" in verdict

    @patch("metabolon.symbiont.transduce", return_value="FAIL — no thesis.")
    def test_fail_verdict(self, mock_td):
        passed, verdict = judge("Bad post")
        assert passed is False
        assert "FAIL" in verdict

    @patch("metabolon.symbiont.transduce", return_value="pass — lowercase.")
    def test_case_insensitive_pass(self, mock_td):
        passed, verdict = judge("Post")
        assert passed is True

    @patch("metabolon.symbiont.transduce", return_value="Whatever")
    def test_unexpected_response_is_fail(self, mock_td):
        passed, verdict = judge("Post")
        assert passed is False

    @patch("metabolon.symbiont.transduce", return_value="PASS.")
    def test_passes_post_to_prompt(self, mock_td):
        judge("My specific post content")
        prompt = mock_td.call_args[0][1]
        assert "My specific post content" in prompt


# ── notify ────────────────────────────────────────────────────────────


class TestNotify:
    @patch("metabolon.organelles.secretory_vesicle.secrete_text")
    def test_sends_message(self, mock_sec):
        notify("Hello world")
        mock_sec.assert_called_once_with("Hello world", html=False, label="garden")


# ── publish ───────────────────────────────────────────────────────────


class TestPublish:
    @patch("metabolon.organelles.golgi.publish")
    @patch("metabolon.organelles.golgi.new")
    def test_creates_and_publishes(self, mock_new, mock_pub, tmp_path):
        post_path = tmp_path / "post.md"
        post_path.write_text("---\ntitle: Test\n---\n")
        mock_new.return_value = ("test-slug", post_path)
        result = publish("Test Title", "Body content here")
        assert result == "test-slug"
        mock_pub.assert_called_once_with("test-slug", force=True)
        written = post_path.read_text()
        assert "Body content here" in written

    @patch("metabolon.organelles.golgi.publish")
    @patch("metabolon.organelles.golgi.new")
    def test_appends_body_to_existing_content(self, mock_new, mock_pub, tmp_path):
        post_path = tmp_path / "post.md"
        post_path.write_text("---\ntitle: Test\n---\nExisting\n")
        mock_new.return_value = ("slug-2", post_path)
        publish("Title", "New body")
        written = post_path.read_text()
        assert "Existing" in written
        assert "New body" in written


# ── main integration ──────────────────────────────────────────────────


class TestMain:
    @patch.object(_mod, "STYLE_GUIDE")
    @patch.object(_mod, "QUEUE")
    @patch("metabolon.organelles.golgi.publish")
    @patch("metabolon.organelles.golgi.new")
    @patch("metabolon.symbiont.transduce")
    @patch("metabolon.organelles.secretory_vesicle.secrete_text")
    def test_full_pipeline_publish(
        self, mock_sec, mock_td, mock_new, mock_pub, mock_queue, mock_style, tmp_path,
    ):
        queue = tmp_path / "Queue.md"
        queue.write_text("- [ ] My Topic — a subtitle\n")
        style = tmp_path / "CLAUDE.md"
        style.write_text("Write clearly.")
        mock_queue.__class__ = type(queue)
        # Patch QUEUE and STYLE_GUIDE to tmp_path versions
        with patch.object(_mod, "QUEUE", queue), \
             patch.object(_mod, "STYLE_GUIDE", style):
            post_path = tmp_path / "post.md"
            post_path.write_text("---\n---\n")
            mock_new.return_value = ("my-topic", post_path)
            # First transduce call = generate, second = judge (PASS)
            mock_td.side_effect = ["A great post.", "PASS — solid."]
            main()

        mock_sec.assert_called()
        msg = mock_sec.call_args[0][0]
        assert "Published" in msg
        assert queue.read_text().startswith("- [x]")

    @patch.object(_mod, "QUEUE")
    @patch("metabolon.organelles.secretory_vesicle.secrete_text")
    def test_empty_queue_notifies(self, mock_sec, mock_queue, tmp_path):
        queue = tmp_path / "Queue.md"
        queue.write_text("")
        with patch.object(_mod, "QUEUE", queue):
            main()
        mock_sec.assert_called_once()
        assert "empty" in mock_sec.call_args[0][0].lower()

    @patch.object(_mod, "STYLE_GUIDE")
    @patch.object(_mod, "QUEUE")
    @patch("metabolon.symbiont.transduce")
    @patch("metabolon.organelles.secretory_vesicle.secrete_text")
    def test_judge_fail_notifies(
        self, mock_sec, mock_td, mock_queue, mock_style, tmp_path,
    ):
        queue = tmp_path / "Queue.md"
        queue.write_text("- [ ] Failing topic\n")
        style = tmp_path / "CLAUDE.md"
        style.write_text("Style.")
        with patch.object(_mod, "QUEUE", queue), \
             patch.object(_mod, "STYLE_GUIDE", style):
            # generate + judge = FAIL, then retry generate + judge = FAIL
            mock_td.side_effect = [
                "Bad post.",
                "FAIL — weak.",
                "Still bad post.",
                "FAIL — still weak.",
            ]
            main()
        msgs = [c[0][0] for c in mock_sec.call_args_list]
        assert any("skipped" in m.lower() for m in msgs)

    @patch.object(_mod, "STYLE_GUIDE")
    @patch.object(_mod, "QUEUE")
    @patch("metabolon.organelles.golgi.publish")
    @patch("metabolon.organelles.golgi.new")
    @patch("metabolon.symbiont.transduce")
    @patch("metabolon.organelles.secretory_vesicle.secrete_text")
    def test_publish_failure_notifies(
        self, mock_sec, mock_td, mock_new, mock_pub, mock_queue, mock_style, tmp_path,
    ):
        queue = tmp_path / "Queue.md"
        queue.write_text("- [ ] Publish fail topic\n")
        style = tmp_path / "CLAUDE.md"
        style.write_text("Style.")
        with patch.object(_mod, "QUEUE", queue), \
             patch.object(_mod, "STYLE_GUIDE", style):
            post_path = tmp_path / "post.md"
            post_path.write_text("---\n---\n")
            mock_new.return_value = ("slug", post_path)
            mock_pub.side_effect = RuntimeError("Connection lost")
            mock_td.side_effect = ["Post body.", "PASS — good."]
            main()
        msgs = [c[0][0] for c in mock_sec.call_args_list]
        assert any("failed" in m.lower() for m in msgs)
