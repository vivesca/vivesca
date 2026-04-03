"""Tests for automatic git sync in temporal worker (t-gitsync).

Worker should git pull before golem runs and git push after successful runs.
Both operations must be non-fatal — sync failure should not block golem work.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

WORKER_PY = Path.home() / "germline" / "effectors" / "temporal-golem" / "worker.py"


class TestGitPullBeforeGolem:
    """Worker should pull latest before running golem."""

    def test_git_pull_present(self):
        """run_golem_task should include a git pull step before execution."""
        source = WORKER_PY.read_text()
        # Look for git pull in the run_golem_task function
        fn_match = re.search(
            r'async def run_golem_task.*?(?=\n@activity\.defn|\nclass |\Z)',
            source,
            re.DOTALL,
        )
        assert fn_match, "Could not find run_golem_task function"
        fn_body = fn_match.group()
        assert "git" in fn_body and "pull" in fn_body, (
            "run_golem_task should include git pull before golem execution"
        )

    def test_pull_has_timeout(self):
        """Git pull must have a timeout to prevent hanging."""
        source = WORKER_PY.read_text()
        # Should have a timeout on the pull subprocess (15-30s range)
        assert "timeout" in source.lower(), "Git pull must have a timeout"


class TestGitPushAfterGolem:
    """Worker should push after successful golem runs."""

    def test_git_push_present(self):
        """run_golem_task should include a git push step after successful execution."""
        source = WORKER_PY.read_text()
        fn_match = re.search(
            r'async def run_golem_task.*?(?=\n@activity\.defn|\nclass |\Z)',
            source,
            re.DOTALL,
        )
        assert fn_match, "Could not find run_golem_task function"
        fn_body = fn_match.group()
        assert "git" in fn_body and "push" in fn_body, (
            "run_golem_task should include git push after successful golem execution"
        )

    def test_push_only_on_success(self):
        """Git push should only run when rc == 0."""
        source = WORKER_PY.read_text()
        fn_match = re.search(
            r'async def run_golem_task.*?(?=\n@activity\.defn|\nclass |\Z)',
            source,
            re.DOTALL,
        )
        assert fn_match, "Could not find run_golem_task function"
        fn_body = fn_match.group()
        # Push should be gated on success — look for rc == 0 or success check near push
        push_idx = fn_body.find("push")
        assert push_idx > 0, "git push not found in run_golem_task"
        # Check that there's an rc/success check within 200 chars before push
        context_before = fn_body[max(0, push_idx - 300):push_idx]
        assert "rc == 0" in context_before or "rc ==" in context_before or "success" in context_before.lower(), (
            "git push should be gated on successful golem exit (rc == 0)"
        )


class TestSyncNonFatal:
    """Sync failures must not block golem execution."""

    def test_pull_failure_non_fatal(self):
        """A failed git pull should log a warning, not raise."""
        source = WORKER_PY.read_text()
        # Should have try/except or error handling around pull
        fn_match = re.search(
            r'async def run_golem_task.*?(?=\n@activity\.defn|\nclass |\Z)',
            source,
            re.DOTALL,
        )
        assert fn_match
        fn_body = fn_match.group()
        # Should have exception handling (try/except) near git operations
        assert "except" in fn_body, "Git operations should be wrapped in try/except"


class TestSyntaxValid:
    """worker.py must parse without errors after modification."""

    def test_ast_parse(self):
        source = WORKER_PY.read_text()
        ast.parse(source)
