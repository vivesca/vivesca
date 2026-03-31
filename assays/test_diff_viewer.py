from __future__ import annotations

"""Tests for metabolon.sortase.diff_viewer module."""


import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from metabolon.sortase.diff_viewer import (
    find_task_commit,
    format_diff_summary,
    get_task_diff,
)


class TestFindTaskCommit:
    """Tests for find_task_commit function."""

    def test_finds_sortase_commit(self, tmp_path: Path) -> None:
        """Should find commit with sortase: prefix matching task name."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123 sortase: my-task-name\n"
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = find_task_commit("my-task-name", tmp_path)
        
        assert result == "abc123"

    def test_finds_translocon_commit(self, tmp_path: Path) -> None:
        """Should find commit with translocon: prefix matching task name."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "def456 translocon: another-task\n"
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = find_task_commit("another-task", tmp_path)
        
        assert result == "def456"

    def test_finds_commit_by_task_name_in_message(self, tmp_path: Path) -> None:
        """Should find commit when task name appears anywhere in message."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "ghi789 fix: update special-task implementation\n"
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = find_task_commit("special-task", tmp_path)
        
        assert result == "ghi789"

    def test_case_insensitive_matching(self, tmp_path: Path) -> None:
        """Should match task name case-insensitively."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "jkl012 sortase: MY-TASK-NAME\n"
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = find_task_commit("my-task-name", tmp_path)
        
        assert result == "jkl012"

    def test_returns_first_match(self, tmp_path: Path) -> None:
        """Should return first matching commit when multiple exist."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123 sortase: target-task\nmno345 sortase: target-task\n"
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = find_task_commit("target-task", tmp_path)
        
        assert result == "abc123"

    def test_returns_none_no_match(self, tmp_path: Path) -> None:
        """Should return None when no commits match task name."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123 sortase: other-task\ndef456 fix: something else\n"
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = find_task_commit("nonexistent-task", tmp_path)
        
        assert result is None

    def test_returns_none_git_failure(self, tmp_path: Path) -> None:
        """Should return None when git command fails."""
        mock_result = Mock()
        mock_result.returncode = 128
        mock_result.stdout = ""
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = find_task_commit("any-task", tmp_path)
        
        assert result is None

    def test_handles_empty_git_log(self, tmp_path: Path) -> None:
        """Should return None when git log is empty."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = find_task_commit("any-task", tmp_path)
        
        assert result is None

    def test_skips_empty_lines(self, tmp_path: Path) -> None:
        """Should skip empty lines in git log output."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "\n\nabc123 sortase: my-task\n\n"
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = find_task_commit("my-task", tmp_path)
        
        assert result == "abc123"

    def test_skips_lines_without_message(self, tmp_path: Path) -> None:
        """Should skip lines that only have a hash (no message)."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123\nxyz789 sortase: found-task\n"
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = find_task_commit("found-task", tmp_path)
        
        assert result == "xyz789"

    def test_git_command_called_with_correct_args(self, tmp_path: Path) -> None:
        """Should call git with correct arguments."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result) as mock_run:
            find_task_commit("test-task", tmp_path)
            
            mock_run.assert_called_once()
            args = mock_run.call_args
            assert args[0][0] == ["git", "log", "--all", "--format=%h %s", "--", "."]
            assert args[1]["cwd"] == tmp_path
            assert args[1]["capture_output"] is True
            assert args[1]["text"] is True
            assert args[1]["check"] is False


class TestGetTaskDiff:
    """Tests for get_task_diff function."""

    def test_returns_diff_output(self, tmp_path: Path) -> None:
        """Should return stdout from git show command."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "diff --git a/file.py b/file.py\n+new line\n"
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = get_task_diff("abc123", tmp_path)
        
        assert result == "diff --git a/file.py b/file.py\n+new line\n"

    def test_returns_empty_string_for_empty_diff(self, tmp_path: Path) -> None:
        """Should return empty string when diff is empty."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = get_task_diff("abc123", tmp_path)
        
        assert result == ""

    def test_git_command_args(self, tmp_path: Path) -> None:
        """Should call git show with correct arguments."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result) as mock_run:
            get_task_diff("def456", tmp_path)
            
            mock_run.assert_called_once()
            args = mock_run.call_args
            assert args[0][0] == ["git", "show", "--format=", "--patch", "def456"]
            assert args[1]["cwd"] == tmp_path
            assert args[1]["capture_output"] is True
            assert args[1]["text"] is True
            assert args[1]["check"] is False

    def test_handles_multiline_diff(self, tmp_path: Path) -> None:
        """Should correctly return multiline diff output."""
        diff_output = """diff --git a/src/module.py b/src/module.py
index 1234567..abcdefg 100644
--- a/src/module.py
+++ b/src/module.py
@@ -1,5 +1,6 @@
 def existing_function():
-    old_code = 1
+    new_code = 2
+    extra_line = 3
     return True
"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = diff_output
        
        with patch("metabolon.sortase.diff_viewer.subprocess.run", return_value=mock_result):
            result = get_task_diff("abc123", tmp_path)
        
        assert result == diff_output


class TestFormatDiffSummary:
    """Tests for format_diff_summary function."""

    def test_empty_diff(self) -> None:
        """Should return 'No changes.' for empty diff."""
        assert format_diff_summary("") == "No changes."

    def test_whitespace_only_diff(self) -> None:
        """Should return 'No changes.' for whitespace-only diff."""
        assert format_diff_summary("   \n  \n") == "No changes."

    def test_diff_without_files(self) -> None:
        """Should return 'No changes.' for diff with no file entries."""
        # Diff that doesn't start with 'diff --git'
        diff = "some random text\nnot a real diff\n"
        assert format_diff_summary(diff) == "No changes."

    def test_single_file_additions(self) -> None:
        """Should count additions correctly for single file."""
        diff = """diff --git a/new_file.py b/new_file.py
new file mode 100644
index 0000000..abc123
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,3 @@
+def new_function():
+    return 42
+
"""
        result = format_diff_summary(diff)
        
        assert "Files changed: 1" in result
        assert "Lines: +3 / -0" in result
        assert "new_file.py  +3 / -0" in result

    def test_single_file_removals(self) -> None:
        """Should count removals correctly for single file."""
        diff = """diff --git a/old_file.py b/old_file.py
deleted file mode 100644
--- a/old_file.py
+++ /dev/null
@@ -1,2 +0,0 @@
-def old_function():
-    pass
"""
        result = format_diff_summary(diff)
        
        assert "Files changed: 1" in result
        assert "Lines: +0 / -2" in result
        assert "old_file.py  +0 / -2" in result

    def test_single_file_mixed_changes(self) -> None:
        """Should count both additions and removals."""
        diff = """diff --git a/module.py b/module.py
--- a/module.py
+++ b/module.py
@@ -1,3 +1,3 @@
-def old_func():
-    pass
+def new_func():
+    return 42
+    # added comment
"""
        result = format_diff_summary(diff)
        
        assert "Files changed: 1" in result
        assert "Lines: +3 / -2" in result

    def test_multiple_files(self) -> None:
        """Should handle multiple files in diff."""
        diff = """diff --git a/alpha.py b/alpha.py
--- a/alpha.py
+++ b/alpha.py
@@ -1 +1 @@
-old alpha
+new alpha
diff --git b/beta.py b/beta.py
--- a/beta.py
+++ b/beta.py
@@ -1 +1 @@
-old beta
+new beta
+extra line
"""
        result = format_diff_summary(diff)
        
        assert "Files changed: 2" in result
        assert "Lines: +3 / -2" in result
        # Files should be sorted alphabetically
        lines = result.splitlines()
        file_lines = [l for l in lines if l.startswith("  ")]
        assert len(file_lines) == 2
        # alpha.py should come before beta.py
        assert file_lines[0].strip().startswith("alpha.py")
        assert file_lines[1].strip().startswith("beta.py")

    def test_ignores_diff_header_lines(self) -> None:
        """Should not count +++ and --- header lines as changes."""
        diff = """diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
@@ -1 +1 @@
-old
+new
"""
        result = format_diff_summary(diff)
        
        assert "Lines: +1 / -1" in result

    def test_extracts_filename_from_b_prefix(self) -> None:
        """Should correctly extract filename from b/ prefix."""
        diff = """diff --git a/path/to/deep/file.txt b/path/to/deep/file.txt
--- a/path/to/deep/file.txt
+++ b/path/to/deep/file.txt
@@ -1 +1 @@
-content
+modified
"""
        result = format_diff_summary(diff)
        
        assert "path/to/deep/file.txt" in result

    def test_handles_filename_with_spaces(self) -> None:
        """Should handle filenames containing spaces."""
        diff = """diff --git a/my file.txt b/my file.txt
--- a/my file.txt
+++ b/my file.txt
@@ -1 +1 @@
-old content
+new content
"""
        result = format_diff_summary(diff)
        
        assert "my file.txt" in result

    def test_summary_format(self) -> None:
        """Should format summary with proper structure."""
        diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -0,0 +1 @@
+line
"""
        result = format_diff_summary(diff)
        
        lines = result.splitlines()
        assert lines[0] == "Files changed: 1"
        assert lines[1] == "Lines: +1 / -0"
        assert lines[2] == ""
        assert lines[3].startswith("  ")

    def test_counts_lines_correctly_across_hunks(self) -> None:
        """Should count lines correctly when multiple hunks exist."""
        diff = """diff --git a/large_file.py b/large_file.py
--- a/large_file.py
+++ b/large_file.py
@@ -10,2 +10,3 @@
 context line
-old line 1
+new line 1
+new line 2
@@ -50,2 +51,2 @@
 context
-old line 3
+new line 3
"""
        result = format_diff_summary(diff)

        # 3 additions, 2 removals across both hunks
        assert "Lines: +3 / -2" in result
