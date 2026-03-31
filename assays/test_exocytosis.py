#!/usr/bin/env python3
"""Tests for effectors/exocytosis.py — garden post pipeline."""
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR = Path.home() / "germline" / "effectors" / "exocytosis.py"
CONF = Path.home() / "germline" / "effectors" / "exocytosis.conf"


@pytest.fixture
def ns(tmp_path, monkeypatch):
    """Load the effector into a namespace with mocks for lazy imports."""
    # Create fake metabolon submodules for lazy imports
    fake_sv = types.ModuleType("metabolon.organelles.secretory_vesicle")
    fake_sv.secrete_text = MagicMock()
    fake_symbiont = types.ModuleType("metabolon.symbiont")
    fake_symbiont.transduce = MagicMock(return_value="PASS Great post.")
    fake_golgi = types.ModuleType("metabolon.organelles.golgi")
    fake_golgi.new = MagicMock(return_value=("test-slug", tmp_path / "test-post.md"))
    fake_golgi.publish = MagicMock()

    # Ensure parent packages exist
    for pkg in ("metabolon", "metabolon.organelles"):
        if pkg not in sys.modules:
            sys.modules[pkg] = types.ModuleType(pkg)

    monkeypatch.setitem(sys.modules, "metabolon.organelles.secretory_vesicle", fake_sv)
    monkeypatch.setitem(sys.modules, "metabolon.symbiont", fake_symbiont)
    monkeypatch.setitem(sys.modules, "metabolon.organelles.golgi", fake_golgi)

    # Provide a fake queue file
    queue = tmp_path / "Queue.md"
    queue.write_text("- [ ] My test topic\n")
    # Provide a fake style guide
    style = tmp_path / "CLAUDE.md"
    style.write_text("Write clearly. Be concise.\n")

    namespace: dict = {"__name__": "test_exocytosis", "__file__": str(EFFECTOR)}
    exec(open(EFFECTOR).read(), namespace)

    # Patch module-level constants to use tmp_path
    namespace["QUEUE"] = queue
    namespace["STYLE_GUIDE"] = style

    return namespace


# ---------------------------------------------------------------------------
# get_next_topic
# ---------------------------------------------------------------------------
class TestGetNextTopic:
    def test_returns_first_unchecked(self, ns):
        result = ns["get_next_topic"]()
        assert result is not None
        line_num, topic = result
        assert line_num == 0
        assert topic == "My test topic"

    def test_returns_none_when_all_done(self, ns):
        queue: Path = ns["QUEUE"]
        queue.write_text("- [x] Done thing\n- [x] Also done\n")
        assert ns["get_next_topic"]() is None

    def test_returns_none_on_empty(self, ns):
        ns["QUEUE"].write_text("")
        assert ns["get_next_topic"]() is None

    def test_skips_checked_returns_second(self, ns):
        ns["QUEUE"].write_text("- [x] Done\n- [ ] Pending topic\n")
        line_num, topic = ns["get_next_topic"]()
        assert line_num == 1
        assert topic == "Pending topic"

    def test_strips_whitespace(self, ns):
        ns["QUEUE"].write_text("- [ ]   Spaced topic   \n")
        _, topic = ns["get_next_topic"]()
        assert topic == "Spaced topic"


# ---------------------------------------------------------------------------
# mark_done
# ---------------------------------------------------------------------------
class TestMarkDone:
    def test_marks_line_done(self, ns):
        ns["mark_done"](0)
        content = ns["QUEUE"].read_text()
        assert "- [x] My test topic" in content
        assert "- [ ] " not in content

    def test_only_touches_target_line(self, ns):
        ns["QUEUE"].write_text("- [ ] First\n- [ ] Second\n")
        ns["mark_done"](0)
        lines = ns["QUEUE"].read_text().splitlines()
        assert lines[0].startswith("- [x]")
        assert lines[1].startswith("- [ ]")

    def test_preserves_other_content(self, ns):
        ns["QUEUE"].write_text("# Title\n- [ ] Task\n## Notes\n")
        ns["mark_done"](1)
        content = ns["QUEUE"].read_text()
        assert "# Title" in content
        assert "## Notes" in content


# ---------------------------------------------------------------------------
# notify
# ---------------------------------------------------------------------------
class TestNotify:
    def test_calls_secrete_text(self, ns):
        ns["notify"]("hello world")
        sv = sys.modules["metabolon.organelles.secretory_vesicle"]
        sv.secrete_text.assert_called_once_with("hello world", html=False, label="garden")


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------
class TestGenerate:
    def test_calls_transduce(self, ns):
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "Generated post body."
        result = ns["generate"]("my topic", "style rules")
        assert result == "Generated post body."
        fake_transduce.assert_called_once()
        call_args = fake_transduce.call_args
        assert call_args[0][0] == "goose"
        assert "my topic" in call_args[0][1]
        assert "style rules" in call_args[0][1]

    def test_appends_extra_when_provided(self, ns):
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "Better post."
        ns["generate"]("topic", "style", extra="\nPrevious failed.")
        prompt = fake_transduce.call_args[0][1]
        assert "Previous failed." in prompt


# ---------------------------------------------------------------------------
# judge
# ---------------------------------------------------------------------------
class TestJudge:
    def test_pass_verdict(self, ns):
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "PASS — clear thesis and good evidence."
        passed, verdict = ns["judge"]("A great post about testing.")
        assert passed is True
        assert "PASS" in verdict

    def test_fail_verdict(self, ns):
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "FAIL — no thesis."
        passed, verdict = ns["judge"]("Weak post.")
        assert passed is False
        assert "FAIL" in verdict

    def test_case_insensitive_pass(self, ns):
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "pass — decent post."
        passed, _ = ns["judge"]("ok post")
        assert passed is True

    def test_includes_post_in_prompt(self, ns):
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "PASS"
        ns["judge"]("Unique post content XYZ")
        prompt = fake_transduce.call_args[0][1]
        assert "Unique post content XYZ" in prompt

    def test_uses_glm_provider(self, ns):
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "PASS"
        ns["judge"]("post")
        assert fake_transduce.call_args[0][0] == "glm"


# ---------------------------------------------------------------------------
# publish
# ---------------------------------------------------------------------------
class TestPublish:
    def test_creates_and_publishes(self, ns, tmp_path):
        fake_golgi = sys.modules["metabolon.organelles.golgi"]
        post_file = tmp_path / "test-post.md"
        post_file.write_text("---\ntitle: Test\n---\n")
        fake_golgi.new.return_value = ("my-slug", post_file)

        slug = ns["publish"]("Test Title", "Body content here.")
        assert slug == "my-slug"
        fake_golgi.publish.assert_called_once_with("my-slug", force=True)

    def test_appends_body_to_post(self, ns, tmp_path):
        fake_golgi = sys.modules["metabolon.organelles.golgi"]
        post_file = tmp_path / "test-post.md"
        post_file.write_text("existing content")
        fake_golgi.new.return_value = ("slug2", post_file)

        ns["publish"]("Title", "New body text.")
        written = post_file.read_text()
        assert "existing content" in written
        assert "New body text." in written


# ---------------------------------------------------------------------------
# main — integration
# ---------------------------------------------------------------------------
class TestMainIntegration:
    def test_empty_queue_notifies(self, ns, capsys):
        ns["QUEUE"].write_text("")
        ns["main"]()
        sv = sys.modules["metabolon.organelles.secretory_vesicle"]
        sv.secrete_text.assert_called()
        msg = sv.secrete_text.call_args[0][0]
        assert "empty" in msg.lower() or "nothing" in msg.lower()

    def test_happy_path_publishes(self, ns):
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "PASS — excellent."
        fake_golgi = sys.modules["metabolon.organelles.golgi"]
        post_file = ns["QUEUE"].parent / "post.md"
        post_file.write_text("---\n---\n")
        fake_golgi.new.return_value = ("slug", post_file)

        ns["main"]()
        fake_golgi.publish.assert_called_once()
        sv = sys.modules["metabolon.organelles.secretory_vesicle"]
        notify_msg = sv.secrete_text.call_args[0][0]
        assert "Published" in notify_msg

    def test_judge_fail_skips_publish(self, ns):
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "FAIL — no thesis."
        fake_golgi = sys.modules["metabolon.organelles.golgi"]

        ns["main"]()
        fake_golgi.publish.assert_not_called()
        sv = sys.modules["metabolon.organelles.secretory_vesicle"]
        notify_msg = sv.secrete_text.call_args[0][0]
        assert "skipped" in notify_msg.lower()

    def test_marks_done_even_on_fail(self, ns):
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "FAIL — bad."

        ns["main"]()
        content = ns["QUEUE"].read_text()
        assert "- [x]" in content

    def test_publish_exception_notifies(self, ns):
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "PASS — great."
        fake_golgi = sys.modules["metabolon.organelles.golgi"]
        fake_golgi.new.side_effect = RuntimeError("disk full")

        ns["main"]()
        sv = sys.modules["metabolon.organelles.secretory_vesicle"]
        notify_msg = sv.secrete_text.call_args[0][0]
        assert "failed" in notify_msg.lower()

    def test_title_truncation(self, ns):
        long_topic = "A very long topic that goes on and on and should be truncated"
        ns["QUEUE"].write_text(f"- [ ] {long_topic}\n")
        fake_transduce = sys.modules["metabolon.symbiont"].transduce
        fake_transduce.return_value = "PASS"
        fake_golgi = sys.modules["metabolon.organelles.golgi"]
        post_file = ns["QUEUE"].parent / "post.md"
        post_file.write_text("---\n---\n")
        fake_golgi.new.return_value = ("slug", post_file)

        ns["main"]()
        title_arg = fake_golgi.new.call_args[0][0]
        assert len(title_arg) <= 60
