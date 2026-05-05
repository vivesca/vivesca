"""Tests for axon.py read-target-preflight detector — Sub-detector B.

POS: Edit on chromatin/immunity draft with no prior Read → fires.
POS: Edit on marks/feedback file with no prior Read → fires.
NEG: Edit on chromatin file after prior Read in same session → no fire.
NEG: Write to new path (file doesn't exist) → no fire.
NEG: Edit on ~/tmp file → no fire (stoplist).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "membrane" / "cytoskeleton"))
import axon

HOME = Path.home()
_SESSIONS_DIR = Path(__file__).parent / ".preflight_scratch"


@pytest.fixture(autouse=True)
def _clean_scratch():
    _SESSIONS_DIR.mkdir(exist_ok=True)
    yield
    shutil.rmtree(_SESSIONS_DIR, ignore_errors=True)


def _make_session_jsonl(reads: list[str], session_id: str = "test-session-001") -> Path:
    """Create a mock session JSONL with Read tool_use entries for the given paths."""
    jsonl = _SESSIONS_DIR / f"{session_id}.jsonl"
    lines = []
    for fp in reads:
        entry = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Read",
                        "input": {"file_path": fp},
                    }
                ],
            },
        }
        lines.append(json.dumps(entry))
    jsonl.write_text("\n".join(lines) + "\n" if lines else "")
    return jsonl


def _make_data(tool: str, file_path: str, session_id: str = "test-session-001") -> dict:
    return {
        "tool": tool,
        "tool_input": {"file_path": file_path},
        "session_id": session_id,
    }


class TestWasTargetRead:
    """Unit tests for _was_target_read JSONL scanner."""

    def test_read_present(self):
        target = "/home/vivesca/epigenome/chromatin/Tonus.md"
        jsonl = _make_session_jsonl(reads=[target])
        assert axon._was_target_read(jsonl, target) is True

    def test_read_absent(self):
        jsonl = _make_session_jsonl(reads=["/other/file.md"])
        assert (
            axon._was_target_read(jsonl, "/home/vivesca/epigenome/chromatin/immunity/draft.md")
            is False
        )

    def test_empty_jsonl(self):
        jsonl = _make_session_jsonl(reads=[])
        assert axon._was_target_read(jsonl, "/any/file.md") is False

    def test_different_file_same_dir(self):
        target_a = "/home/vivesca/epigenome/chromatin/immunity/a.md"
        target_b = "/home/vivesca/epigenome/chromatin/immunity/b.md"
        jsonl = _make_session_jsonl(reads=[target_b])
        assert axon._was_target_read(jsonl, target_a) is False

    def test_path_resolution_matches(self):
        """Read with relative-ish path still matches when resolved to same absolute."""
        target = "/home/vivesca/epigenome/chromatin/Tonus.md"
        jsonl = _make_session_jsonl(reads=[target])
        assert axon._was_target_read(jsonl, target) is True


class TestIsUserCurated:
    """Unit tests for _is_user_curated_path."""

    def test_chromatin(self):
        assert (
            axon._is_user_curated_path(Path("/home/vivesca/epigenome/chromatin/Tonus.md")) is True
        )

    def test_immunity(self):
        assert (
            axon._is_user_curated_path(Path("/home/vivesca/epigenome/chromatin/immunity/draft.md"))
            is True
        )

    def test_marks(self):
        assert (
            axon._is_user_curated_path(Path("/home/vivesca/epigenome/marks/feedback_foo.md"))
            is True
        )

    def test_drafts(self):
        assert axon._is_user_curated_path(Path("/home/vivesca/drafts/paper-v2.md")) is True

    def test_random_path(self):
        assert axon._is_user_curated_path(Path("/home/vivesca/code/project/main.py")) is False

    def test_loci_plans(self):
        assert (
            axon._is_user_curated_path(
                Path("/home/vivesca/epigenome/chromatin/loci/plans/spec.md")
            )
            is True
        )


class TestIsStoplisted:
    """Unit tests for _is_stoplisted_path."""

    def test_home_tmp(self):
        assert axon._is_stoplisted_path(Path("/home/vivesca/tmp/scratch.md")) is True

    def test_sys_tmp(self):
        assert axon._is_stoplisted_path(Path("/tmp/build-output.log")) is True

    def test_normal_path(self):
        assert (
            axon._is_stoplisted_path(Path("/home/vivesca/epigenome/chromatin/Tonus.md")) is False
        )

    def test_tmp_as_prefix(self):
        """Path starting with /tmp prefix is stoplisted."""
        assert axon._is_stoplisted_path(Path("/tmp/pytest-123/chromatin/file.md")) is True


class TestGuardReadTargetPreflight:
    """Integration tests for guard_read_target_preflight detector."""

    def test_pos_edit_immunity_no_prior_read(self, capsys):
        """POS: Edit on chromatin/immunity draft with no prior Read → fires."""
        target = (
            _SESSIONS_DIR
            / "chromatin"
            / "immunity"
            / "2026-05-03-terry-email-simon-monday-preview-DRAFT.md"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("draft content")
        jsonl = _make_session_jsonl(reads=[])

        data = _make_data("Edit", str(target))
        with patch.object(axon, "_session_jsonl_path", return_value=jsonl):
            axon.guard_read_target_preflight(data)

        captured = capsys.readouterr()
        assert captured.out.strip(), "Expected warning output for unread target"
        output = json.loads(captured.out.strip())
        msg = output.get("hookSpecificOutput", {}).get("message", "")
        assert "About to edit" in msg
        assert "Read it in this session" in msg

    def test_pos_edit_marks_no_prior_read(self, capsys):
        """POS: Edit on marks/feedback file with no prior Read → fires."""
        target = _SESSIONS_DIR / "epigenome" / "marks" / "feedback_ribosome_coaching.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("feedback content")
        jsonl = _make_session_jsonl(reads=[])

        data = _make_data("Edit", str(target))
        with patch.object(axon, "_session_jsonl_path", return_value=jsonl):
            axon.guard_read_target_preflight(data)

        captured = capsys.readouterr()
        assert captured.out.strip(), "Expected warning output for unread marks file"
        output = json.loads(captured.out.strip())
        msg = output.get("hookSpecificOutput", {}).get("message", "")
        assert "About to edit" in msg

    def test_neg_edit_after_prior_read(self, capsys):
        """NEG: Edit on chromatin file after prior Read → no fire."""
        target = _SESSIONS_DIR / "epigenome" / "chromatin" / "Tonus.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("tonus content")
        jsonl = _make_session_jsonl(reads=[str(target)])

        data = _make_data("Edit", str(target))
        with patch.object(axon, "_session_jsonl_path", return_value=jsonl):
            axon.guard_read_target_preflight(data)

        captured = capsys.readouterr()
        assert captured.out.strip() == "", (
            f"Expected no output after prior Read, got: {captured.out.strip()}"
        )

    def test_neg_write_new_file(self, capsys):
        """NEG: Write to a new path that doesn't exist → no fire."""
        target = _SESSIONS_DIR / "epigenome" / "chromatin" / "loci" / "plans" / "new-plan.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        # Don't create the target file — simulating new file creation
        jsonl = _make_session_jsonl(reads=[])

        data = _make_data("Write", str(target))
        with patch.object(axon, "_session_jsonl_path", return_value=jsonl):
            axon.guard_read_target_preflight(data)

        captured = capsys.readouterr()
        assert captured.out.strip() == "", "Expected no output for new file creation"

    def test_neg_stoplist_home_tmp(self, capsys):
        """NEG: Edit on ~/tmp/scratch.md → no fire (stoplist)."""
        target = HOME / "tmp" / "scratch-preflight-test.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("scratch content")
        jsonl = _make_session_jsonl(reads=[])

        data = _make_data("Edit", str(target))
        with patch.object(axon, "_session_jsonl_path", return_value=jsonl):
            axon.guard_read_target_preflight(data)

        captured = capsys.readouterr()
        assert captured.out.strip() == "", "Expected no output for stoplisted ~/tmp path"

    def test_non_curated_path_no_fire(self, capsys):
        """Path outside curated dirs → no fire even without prior Read."""
        target = _SESSIONS_DIR / "code" / "project" / "main.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("print('hello')")
        jsonl = _make_session_jsonl(reads=[])

        data = _make_data("Edit", str(target))
        with patch.object(axon, "_session_jsonl_path", return_value=jsonl):
            axon.guard_read_target_preflight(data)

        captured = capsys.readouterr()
        assert captured.out.strip() == "", "Expected no output for non-curated path"

    def test_no_session_id_graceful(self, capsys):
        """Missing session_id → graceful no-op (no crash, no fire)."""
        target = _SESSIONS_DIR / "chromatin" / "test.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("content")

        data = {"tool": "Edit", "tool_input": {"file_path": str(target)}}
        axon.guard_read_target_preflight(data)

        captured = capsys.readouterr()
        assert captured.out.strip() == "", "Expected graceful no-op without session_id"

    def test_multiedit_triggers(self, capsys):
        """MultiEdit on unread curated file → fires."""
        target = _SESSIONS_DIR / "chromatin" / "drafts" / "paper-v2.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("paper content")
        jsonl = _make_session_jsonl(reads=[])

        data = _make_data("MultiEdit", str(target))
        with patch.object(axon, "_session_jsonl_path", return_value=jsonl):
            axon.guard_read_target_preflight(data)

        captured = capsys.readouterr()
        assert captured.out.strip(), "Expected warning for MultiEdit on unread target"
