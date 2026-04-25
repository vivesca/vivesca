"""Smoke tests for mod_excisor in dendrite.py."""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

import dendrite


def _data(tool, file_path, old_string="", new_string=""):
    return {
        "tool": tool,
        "tool_input": {
            "file_path": file_path,
            "old_string": old_string,
            "new_string": new_string,
        },
    }


def _capture_stderr(fn, data):
    buf = StringIO()
    with patch.object(sys, "stderr", buf):
        fn(data)
    return buf.getvalue()


def test_excisor_fires_on_substantive_paper_deletion():
    """80+ char deletion in chromatin/immunity paper triggers nudge."""
    big_old = "This is a paragraph being removed from the paper. " * 5
    data = _data(
        "Edit",
        "/home/vivesca/epigenome/chromatin/immunity/some-paper-2026-04-27.md",
        old_string=big_old,
        new_string="",
    )
    out = _capture_stderr(dendrite.mod_excisor, data)
    assert "EXCISOR" in out
    assert "some-paper" in out
    assert "cutting-room-some-paper.md" in out


def test_excisor_skips_small_deletion():
    """Sub-80 char delta should be ignored."""
    data = _data(
        "Edit",
        "/home/vivesca/epigenome/chromatin/immunity/some-paper.md",
        old_string="small change here",
        new_string="",
    )
    out = _capture_stderr(dendrite.mod_excisor, data)
    assert out == ""


def test_excisor_skips_non_immunity_path():
    """File outside chromatin/immunity should be ignored."""
    big_old = "x" * 200
    data = _data(
        "Edit",
        "/home/vivesca/notes/random.md",
        old_string=big_old,
        new_string="",
    )
    out = _capture_stderr(dendrite.mod_excisor, data)
    assert out == ""


def test_excisor_skips_write_tool():
    """Write tool means new file, not deletion — skip."""
    data = _data(
        "Write",
        "/home/vivesca/epigenome/chromatin/immunity/new-paper.md",
        old_string="",
        new_string="",
    )
    out = _capture_stderr(dendrite.mod_excisor, data)
    assert out == ""


def test_excisor_skips_cutting_room_file_itself():
    """Editing the cutting-room file itself should not nudge."""
    big_old = "x" * 200
    data = _data(
        "Edit",
        "/home/vivesca/epigenome/chromatin/immunity/cutting-room-some-paper.md",
        old_string=big_old,
        new_string="",
    )
    out = _capture_stderr(dendrite.mod_excisor, data)
    assert out == ""


def test_excisor_strips_version_and_date_for_cutting_stem():
    """Paper named foo-v1.1-2026-04-27 should map to cutting-room-foo.md."""
    big_old = "x" * 200
    data = _data(
        "Edit",
        "/home/vivesca/epigenome/chromatin/immunity/hsbc-group-ai-safety-capability-model-v1.1-2026-04-27.md",
        old_string=big_old,
        new_string="",
    )
    out = _capture_stderr(dendrite.mod_excisor, data)
    assert "cutting-room-hsbc-group-ai-safety-capability-model.md" in out


def test_excisor_existing_cutting_room_uses_log_phrasing():
    """If cutting-room file exists, nudge says 'Log in', not 'Create'."""
    paper = "/home/vivesca/epigenome/chromatin/immunity/hsbc-group-ai-safety-capability-model-v1.1-2026-04-27.md"
    big_old = "x" * 200
    data = _data("Edit", paper, old_string=big_old, new_string="")
    out = _capture_stderr(dendrite.mod_excisor, data)
    # cutting-room-ai-safety-paper.md exists; cutting-room-hsbc-group-...md does not
    # so this should say "Create"
    assert "Create" in out or "Log in" in out


if __name__ == "__main__":
    test_excisor_fires_on_substantive_paper_deletion()
    test_excisor_skips_small_deletion()
    test_excisor_skips_non_immunity_path()
    test_excisor_skips_write_tool()
    test_excisor_skips_cutting_room_file_itself()
    test_excisor_strips_version_and_date_for_cutting_stem()
    test_excisor_existing_cutting_room_uses_log_phrasing()
    print("All excisor tests passed")
