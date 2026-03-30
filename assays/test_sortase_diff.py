"""Tests for metabolon.sortase.diff_viewer."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from metabolon.sortase.diff_viewer import (
    find_task_commit,
    format_diff_summary,
    get_task_diff,
)

SAMPLE_GIT_LOG = """\
abc1234 sortase: implement-login
def5678 sortase: add-user-model
ghi9012 unrelated commit
jkl3456 translocon: build-api-endpoints
"""

SAMPLE_DIFF = """\
diff --git a/hello.py b/hello.py
new file mode 100644
--- /dev/null
+++ b/hello.py
@@ -0,0 +1,3 @@
+def greet():
+    return "hello"
+
diff --git a/util.py b/util.py
--- a/util.py
+++ b/util.py
@@ -1,2 +1,2 @@
-OLD_LINE
+NEW_LINE
+EXTRA_LINE
"""


def test_find_task_commit_found() -> None:
    """find_task_commit returns a hash when the log contains a matching commit."""
    mock_result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=SAMPLE_GIT_LOG, stderr=""
    )
    with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
        commit = find_task_commit("implement-login", Path("/fake"))
    assert commit == "abc1234"


def test_find_task_commit_not_found() -> None:
    """find_task_commit returns None when no commit matches."""
    mock_result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=SAMPLE_GIT_LOG, stderr=""
    )
    with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
        commit = find_task_commit("nonexistent-task", Path("/fake"))
    assert commit is None


def test_format_diff_summary() -> None:
    """format_diff_summary returns correct file and line counts."""
    summary = format_diff_summary(SAMPLE_DIFF)
    assert "Files changed: 2" in summary
    # hello.py: 3 added lines; util.py: 1 removed, 2 added
    assert "+5" in summary
    assert "-1" in summary
    assert "hello.py" in summary
    assert "util.py" in summary
