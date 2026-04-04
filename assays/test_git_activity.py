#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/git-activity — git pulse across repos."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load():
    """Load git-activity module via exec."""
    source = Path(str(Path.home() / "germline/effectors/git-activity")).read_text()
    ns: dict = {"__name__": "git_activity"}
    exec(source, ns)
    return ns


_mod = _load()
classify_author = _mod["classify_author"]
classify_message = _mod["classify_message"]
gather_commits = _mod["gather_commits"]
gather_file_stats = _mod["gather_file_stats"]
gather_diff_summary = _mod["gather_diff_summary"]
build_report = _mod["build_report"]
REPOS = _mod["REPOS"]


# ── classify_author ──────────────────────────────────────────────────────────


class TestClassifyAuthor:
    def test_human(self):
        assert classify_author("Terry Li", "terry@terryli.dev") == "human"

    def test_golem_in_name(self):
        assert classify_author("golem-bot", "bot@example.com") == "golem"

    def test_golem_in_email(self):
        assert classify_author("CI", "golem@ci.dev") == "golem"

    def test_sortase(self):
        assert classify_author("sortase-worker", "noreply@sortase.dev") == "golem"

    def test_bot_keyword(self):
        assert classify_author("deploy-bot", "deploy@corp.com") == "golem"

    def test_regular_name(self):
        assert classify_author("Alice Smith", "alice@company.com") == "human"


# ── classify_message ─────────────────────────────────────────────────────────


class TestClassifyMessage:
    def test_golem_prefix(self):
        assert classify_message("golem: daemon auto-commit") == "golem"

    def test_golem_reviewer_prefix(self):
        assert classify_message("golem-reviewer: cycle output") == "golem"

    def test_sortase_prefix(self):
        assert classify_message("sortase: fix tests") == "golem"

    def test_auto_commit_prefix(self):
        assert classify_message("auto-commit: daily sync") == "golem"

    def test_human_message(self):
        assert classify_message("feat: add new feature") == "human"

    def test_fix_message(self):
        assert classify_message("fix: correct off-by-one") == "human"

    def test_golem_in_middle(self):
        """golem keyword in middle of message is still human."""
        assert classify_message("feat: golem integration") == "human"


# ── gather_commits ───────────────────────────────────────────────────────────


class TestGatherCommits:
    def test_empty_log(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="")
            commits = gather_commits(Path("/fake"), "2026-03-31")
        assert commits == []

    def test_parses_log_lines(self):
        log_output = (
            "abc123456789|Terry Li|terry@terryli.dev|2026-03-31T10:00:00+00:00|feat: add X\n"
            "def123456789|Terry Li|terry@terryli.dev|2026-03-31T09:00:00+00:00|golem: daemon auto-commit\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=log_output)
            commits = gather_commits(Path("/fake"), "2026-03-31")

        assert len(commits) == 2
        assert commits[0]["hash"] == "abc123456789"
        assert commits[0]["author_kind"] == "human"
        assert commits[0]["message_kind"] == "human"
        assert commits[1]["hash"] == "def123456789"
        assert commits[1]["message_kind"] == "golem"

    def test_malformed_line_skipped(self):
        log_output = (
            "bad-line-without-pipes\nabc123456789|Terry|t@t.dev|2026-03-31T10:00:00+00:00|ok\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=log_output)
            commits = gather_commits(Path("/fake"), "2026-03-31")
        assert len(commits) == 1


# ── gather_file_stats ────────────────────────────────────────────────────────


class TestGatherFileStats:
    def test_empty_log(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="")
            stats = gather_file_stats(Path("/fake"), "2026-03-31")
        assert stats == {}

    def test_counts_files(self):
        log_output = "effectors/git-activity\neffectors/git-activity\nassays/test_git.py\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=log_output)
            stats = gather_file_stats(Path("/fake"), "2026-03-31")

        assert stats["effectors/git-activity"] == 2
        assert stats["assays/test_git.py"] == 1

    def test_top_20(self):
        log_output = "\n".join([f"file_{i}" for i in range(30)])
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=log_output)
            stats = gather_file_stats(Path("/fake"), "2026-03-31")
        assert len(stats) == 20


# ── gather_diff_summary ──────────────────────────────────────────────────────


class TestGatherDiffSummary:
    def test_empty(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="")
            result = gather_diff_summary(Path("/fake"), "2026-03-31")
        assert result == {"commits": 0, "files_changed": 0, "insertions": 0, "deletions": 0}

    def test_parses_shortstat(self):
        stat_output = (
            "abc1234 feat: add thing\n"
            " 3 files changed, 45 insertions(+), 12 deletions(-)\n"
            "def5678 fix: bug\n"
            " 1 file changed, 5 insertions(+)\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=stat_output)
            result = gather_diff_summary(Path("/fake"), "2026-03-31")
        assert result["commits"] == 2
        assert result["files_changed"] == 4
        assert result["insertions"] == 50
        assert result["deletions"] == 12


# ── build_report ─────────────────────────────────────────────────────────────


class TestBuildReport:
    def setup_method(self):
        self._orig_repos = _mod["REPOS"].copy()

    def teardown_method(self):
        _mod["REPOS"].clear()
        _mod["REPOS"].update(self._orig_repos)

    def test_json_output(self):
        _mod["REPOS"].clear()
        result = build_report("2026-03-31", as_json=True)
        data = json.loads(result)
        assert "repos" in data
        assert "summary" in data
        assert data["summary"]["since"] == "2026-03-31"

    def test_text_output(self):
        _mod["REPOS"].clear()
        result = build_report("2026-03-31", as_json=False)
        assert "GIT ACTIVITY PULSE" in result
        assert "Since: 2026-03-31" in result

    def test_with_mock_repo(self):
        _mod["REPOS"].clear()
        _mod["REPOS"]["test-repo"] = Path("/fake")
        log_output = (
            "abc123456789|Terry Li|terry@terryli.dev|2026-03-31T10:00:00+00:00|feat: add X\n"
        )
        file_output = "effectors/git-activity\n"
        stat_output = "abc1234 feat: add X\n 2 files changed, 30 insertions(+)\n"

        with patch("pathlib.Path.exists", return_value=True), patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=log_output),
                MagicMock(stdout=file_output),
                MagicMock(stdout=stat_output),
            ]
            result = build_report("2026-03-31", as_json=False)

        assert "test-repo" in result
        assert "feat: add X" in result
        assert "👤" in result

    def test_golem_vs_human_counts(self):
        _mod["REPOS"].clear()
        _mod["REPOS"]["test-repo"] = Path("/fake")
        log_output = (
            "abc123456789|Terry Li|t@t.dev|2026-03-31T10:00:00+00:00|golem: auto-commit\n"
            "def123456789|Terry Li|t@t.dev|2026-03-31T09:00:00+00:00|feat: real work\n"
        )

        with patch("pathlib.Path.exists", return_value=True), patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=log_output),
                MagicMock(stdout=""),
                MagicMock(stdout=""),
            ]
            result = build_report("2026-03-31", as_json=True)

        data = json.loads(result)
        assert data["summary"]["golem_commits"] == 1
        assert data["summary"]["human_commits"] == 1
        assert data["summary"]["total_commits"] == 2

    def test_inactive_repo_skipped(self):
        _mod["REPOS"].clear()
        _mod["REPOS"]["dead-repo"] = Path("/nonexistent")
        with patch("pathlib.Path.exists", return_value=False):
            result = build_report("2026-03-31", as_json=True)
        data = json.loads(result)
        assert data["summary"]["repos_active"] == 0
        assert "dead-repo" not in data["repos"]
