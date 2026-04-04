from __future__ import annotations

"""Tests for metabolon.sortase.diff_viewer — commit lookup and diff formatting."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from metabolon.sortase.diff_viewer import find_task_commit, format_diff_summary, get_task_diff

# ---------------------------------------------------------------------------
# find_task_commit
# ---------------------------------------------------------------------------


class TestFindTaskCommit:
    """Tests for find_task_commit()."""

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_returns_hash_when_sortase_prefix_matches(self, mock_run):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = "abc1234 sortase: add widget parser\n"
        mock_run.return_value = completed

        result = find_task_commit("widget parser", Path("/proj"))
        assert result == "abc1234"

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_returns_hash_when_translocon_prefix_matches(self, mock_run):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = "def5678 translocon: refactor endpoints\n"
        mock_run.return_value = completed

        result = find_task_commit("refactor endpoints", Path("/proj"))
        assert result == "def5678"

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_returns_hash_for_non_prefixed_match(self, mock_run):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = "aaa1111 chore: update widget parser config\n"
        mock_run.return_value = completed

        result = find_task_commit("widget parser", Path("/proj"))
        assert result == "aaa1111"

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_returns_first_match_when_multiple(self, mock_run):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = "bbb2222 sortase: widget parser v1\nccc3333 sortase: widget parser v2\n"
        mock_run.return_value = completed

        result = find_task_commit("widget parser", Path("/proj"))
        assert result == "bbb2222"

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_returns_none_when_no_match(self, mock_run):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = "abc1234 chore: unrelated commit\n"
        mock_run.return_value = completed

        result = find_task_commit("widget parser", Path("/proj"))
        assert result is None

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_returns_none_on_git_failure(self, mock_run):
        completed = MagicMock()
        completed.returncode = 128
        completed.stdout = ""
        mock_run.return_value = completed

        result = find_task_commit("anything", Path("/proj"))
        assert result is None

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_returns_none_on_empty_output(self, mock_run):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = ""
        mock_run.return_value = completed

        result = find_task_commit("anything", Path("/proj"))
        assert result is None

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_skips_blank_lines(self, mock_run):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = "\n\nabc1234 sortase: my task\n\n"
        mock_run.return_value = completed

        result = find_task_commit("my task", Path("/proj"))
        assert result == "abc1234"

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_skips_lines_with_only_hash(self, mock_run):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = "abc1234\n"
        mock_run.return_value = completed

        result = find_task_commit("anything", Path("/proj"))
        assert result is None

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_case_insensitive_match(self, mock_run):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = "abc1234 sortase: Widget Parser\n"
        mock_run.return_value = completed

        result = find_task_commit("widget parser", Path("/proj"))
        assert result == "abc1234"

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_passes_project_dir_as_cwd(self, mock_run):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = ""
        mock_run.return_value = completed

        proj = Path("/some/project")
        find_task_commit("anything", proj)
        mock_run.assert_called_once()
        assert (
            mock_run.call_args.kwargs.get("cwd") == proj
            or mock_run.call_args[1].get("cwd") == proj
        )


# ---------------------------------------------------------------------------
# get_task_diff
# ---------------------------------------------------------------------------


class TestGetTaskDiff:
    """Tests for get_task_diff()."""

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_returns_diff_stdout(self, mock_run):
        completed = MagicMock()
        completed.stdout = "diff --git a/file.py b/file.py\n+new line\n"
        mock_run.return_value = completed

        result = get_task_diff("abc1234", Path("/proj"))
        assert "diff --git" in result
        assert "+new line" in result

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_returns_empty_string_on_no_diff(self, mock_run):
        completed = MagicMock()
        completed.stdout = ""
        mock_run.return_value = completed

        result = get_task_diff("abc1234", Path("/proj"))
        assert result == ""

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_uses_correct_git_args(self, mock_run):
        completed = MagicMock()
        completed.stdout = ""
        mock_run.return_value = completed

        get_task_diff("deadbeef", Path("/proj"))
        args = mock_run.call_args[0][0]
        assert args[:3] == ["git", "show", "--format="]
        assert "--patch" in args
        assert "deadbeef" in args

    @patch("metabolon.sortase.diff_viewer.subprocess.run")
    def test_passes_cwd(self, mock_run):
        completed = MagicMock()
        completed.stdout = ""
        mock_run.return_value = completed

        proj = Path("/my/project")
        get_task_diff("abc", proj)
        call_kwargs = mock_run.call_args[1] if mock_run.call_args[1] else mock_run.call_args.kwargs
        assert call_kwargs.get("cwd") == proj


# ---------------------------------------------------------------------------
# format_diff_summary
# ---------------------------------------------------------------------------


class TestFormatDiffSummary:
    """Tests for format_diff_summary()."""

    def test_empty_string_returns_no_changes(self):
        assert format_diff_summary("") == "No changes."

    def test_whitespace_only_returns_no_changes(self):
        assert format_diff_summary("   \n  \n") == "No changes."

    def test_no_diff_headers_returns_no_changes(self):
        diff = "+some line\n-another line\n"
        assert format_diff_summary(diff) == "No changes."

    def test_single_file_summary(self):
        diff = (
            "diff --git a/foo.py b/foo.py\n"
            "--- a/foo.py\n"
            "+++ b/foo.py\n"
            "+added line 1\n"
            "+added line 2\n"
            "-removed line\n"
        )
        result = format_diff_summary(diff)
        assert "Files changed: 1" in result
        assert "Lines: +2 / -1" in result
        assert "foo.py" in result
        assert "+2 / -1" in result

    def test_multiple_files_summary(self):
        diff = (
            "diff --git a/alpha.py b/alpha.py\n"
            "--- a/alpha.py\n"
            "+++ b/alpha.py\n"
            "+a1\n"
            "diff --git b/beta.py b/beta.py\n"
            "--- b/beta.py\n"
            "+++ b/beta.py\n"
            "-b1\n"
            "-b2\n"
        )
        result = format_diff_summary(diff)
        assert "Files changed: 2" in result
        assert "Lines: +1 / -2" in result
        assert "alpha.py" in result
        assert "beta.py" in result

    def test_files_sorted_alphabetically(self):
        diff = "diff --git b/zebra.py b/zebra.py\n+z\ndiff --git a/apple.py b/apple.py\n+a\n"
        result = format_diff_summary(diff)
        lines = result.splitlines()
        file_lines = [
            l for l in lines if l.strip() and not l.strip().startswith(("Files", "Lines"))
        ]
        assert file_lines[0].strip().startswith("apple.py")
        assert file_lines[1].strip().startswith("zebra.py")

    def test_plus_plus_plus_and_minus_minus_minus_not_counted(self):
        diff = (
            "diff --git a/file.py b/file.py\n"
            "--- a/file.py\n"
            "+++ b/file.py\n"
            "+real addition\n"
            "-real removal\n"
        )
        result = format_diff_summary(diff)
        assert "Lines: +1 / -1" in result

    def test_zero_changes_shows_zeros(self):
        diff = "diff --git a/empty.py b/empty.py\n"
        result = format_diff_summary(diff)
        assert "Files changed: 1" in result
        assert "Lines: +0 / -0" in result

    def test_path_with_subdirectories(self):
        diff = "diff --git a/src/deep/file.py b/src/deep/file.py\n+x\n"
        result = format_diff_summary(diff)
        assert "src/deep/file.py" in result
        assert "Lines: +1 / -0" in result
