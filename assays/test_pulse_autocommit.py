from __future__ import annotations

"""Tests for pulse provenance frontmatter and auto-commit on report write."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_paths(tmp_path, monkeypatch):
    """Redirect pulse paths to tmp_path."""
    import metabolon.pulse as pulse

    monkeypatch.setattr(pulse, "CARDIAC_LOG", tmp_path / "pulse-manifest.md")
    monkeypatch.setattr(pulse, "CARDIAC_LOCK", tmp_path / "pulse.lock")
    monkeypatch.setattr(pulse, "TOPIC_LOCK", tmp_path / "pulse-topics-done.txt")
    monkeypatch.setattr(pulse, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(pulse, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(pulse, "VITAL_SIGNS_FILE", tmp_path / "pulse-status.json")
    monkeypatch.setattr(pulse, "FOCUS_DIRECTIVE_FILE", tmp_path / "pulse-focus-directive.txt")
    monkeypatch.setattr(pulse, "PRAXIS_FILE", tmp_path / "Praxis.md")

    return {
        "report_dir": tmp_path / "reports",
    }


class TestProvenanceFrontmatter:
    """Frontmatter must contain author and agent tag."""

    def test_frontmatter_contains_author(self, mock_paths, monkeypatch):
        import metabolon.pulse as pulse

        monkeypatch.setattr(pulse, "log", MagicMock())
        monkeypatch.setattr(pulse, "record_event", MagicMock())

        with patch.object(subprocess, "run", return_value=MagicMock(returncode=1)):
            pulse.record_vital_signs(total_systoles=3, stop_reason="test_done")

        report_dir = mock_paths["report_dir"]
        report_files = list(report_dir.glob("*-pulse.md"))
        assert len(report_files) == 1

        content = report_files[0].read_text()
        assert "author: vivesca-pulse" in content

    def test_frontmatter_contains_agent_tag(self, mock_paths, monkeypatch):
        import metabolon.pulse as pulse

        monkeypatch.setattr(pulse, "log", MagicMock())
        monkeypatch.setattr(pulse, "record_event", MagicMock())

        with patch.object(subprocess, "run", return_value=MagicMock(returncode=1)):
            pulse.record_vital_signs(total_systoles=1, stop_reason="test_done")

        report_dir = mock_paths["report_dir"]
        content = next(iter(report_dir.glob("*-pulse.md"))).read_text()
        assert "vivesca-pulse" in content
        assert "tags: [pulse, report, vivesca-pulse]" in content


class TestAutoCommit:
    """Report write must trigger git add + git commit in epigenome."""

    def test_subprocess_called_with_git_add_and_commit(self, mock_paths, monkeypatch):
        import metabolon.pulse as pulse

        monkeypatch.setattr(pulse, "log", MagicMock())
        monkeypatch.setattr(pulse, "record_event", MagicMock())

        mock_run = MagicMock(return_value=MagicMock(returncode=1))
        with patch.object(subprocess, "run", mock_run):
            pulse.record_vital_signs(total_systoles=2, stop_reason="done")

        calls = mock_run.call_args_list
        add_calls = [c for c in calls if c[0][0][:2] == ["git", "add"]]
        commit_calls = [c for c in calls if c[0][0][:2] == ["git", "commit"]]

        assert len(add_calls) >= 1, f"Expected git add call, got calls: {calls}"
        assert len(commit_calls) >= 1, f"Expected git commit call, got calls: {calls}"

        commit_args = commit_calls[0][0][0]
        assert commit_args[2] == "-m"
        assert commit_args[3].startswith("auto: pulse report ")

        cwd_kw = commit_calls[0][1].get("cwd")
        assert cwd_kw is not None
        assert "epigenome" in str(cwd_kw)

    def test_noop_when_nothing_staged(self, mock_paths, monkeypatch):
        """If git diff --cached --quiet exits 0, no commit should be attempted."""
        import metabolon.pulse as pulse

        monkeypatch.setattr(pulse, "log", MagicMock())
        monkeypatch.setattr(pulse, "record_event", MagicMock())

        def fake_run(args, **kwargs):
            if "diff" in args and "--cached" in args:
                return MagicMock(returncode=0)  # nothing staged
            if args[0] == "git" and args[1] == "add":
                return MagicMock(returncode=0)
            return MagicMock(returncode=0)

        mock_run = MagicMock(side_effect=fake_run)
        with patch.object(subprocess, "run", mock_run):
            pulse.record_vital_signs(total_systoles=1, stop_reason="noop_test")

        calls = mock_run.call_args_list
        commit_calls = [c for c in calls if c[0][0][:2] == ["git", "commit"]]
        assert len(commit_calls) == 0, (
            f"Commit should be skipped when nothing staged, but got: {commit_calls}"
        )

    def test_git_failure_does_not_crash(self, mock_paths, monkeypatch):
        """If git raises an exception, pulse must log a warning, not crash."""
        import metabolon.pulse as pulse

        mock_log = MagicMock()
        monkeypatch.setattr(pulse, "log", mock_log)
        monkeypatch.setattr(pulse, "record_event", MagicMock())

        def fake_run(args, **kwargs):
            if args[0] == "git" and args[1] == "add":
                raise FileNotFoundError("git not found")
            return MagicMock(returncode=0)

        mock_run = MagicMock(side_effect=fake_run)
        with patch.object(subprocess, "run", mock_run):
            pulse.record_vital_signs(total_systoles=1, stop_reason="resilient")

        report_dir = mock_paths["report_dir"]
        assert len(list(report_dir.glob("*-pulse.md"))) == 1, "Report should still be written"
