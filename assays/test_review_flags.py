"""Tests for review flag fixes: commit-count awareness, incomplete verdict, full-diff preservation."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Path setup — add polysome to sys.path so imports work
# ---------------------------------------------------------------------------
_POLYSOME_DIR = Path(__file__).resolve().parent.parent / "effectors" / "polysome"
sys.path.insert(0, str(_POLYSOME_DIR))


# ============================================================================
# Fix 1: no_commit_on_success should be commit-count-aware
# ============================================================================


class TestNoCommitFlag:
    """no_commit_on_success must not fire when commits exist on the branch."""

    def test_not_flagged_with_commits(self):
        """exit_code=0, empty stat, but commit_count>0 → no false flag."""
        import translocase as worker

        result = asyncio.run(
            worker.chaperone(
                {
                    "task": "Build foo at x.py",
                    "provider": "zhipu",
                    "exit_code": 0,
                    "stdout": "Done!",
                    "stderr": "",
                    "pre_diff": {"stat": "", "numstat": ""},
                    "post_diff": {
                        "stat": "",
                        "numstat": "",
                        "commits": ["abc123 partial fix"],
                        "commit_count": 1,
                        "patch": "",
                    },
                    "branch_name": "ribosome-abc123",
                    "merged": False,
                }
            )
        )
        assert "no_commit_on_success" not in result["flags"]

    def test_flagged_with_no_commits(self):
        """exit_code=0, empty stat, commit_count=0 → flag still fires."""
        import translocase as worker

        result = asyncio.run(
            worker.chaperone(
                {
                    "task": "Build foo at x.py",
                    "provider": "zhipu",
                    "exit_code": 0,
                    "stdout": "Done!",
                    "stderr": "",
                    "pre_diff": {"stat": "", "numstat": ""},
                    "post_diff": {
                        "stat": "",
                        "numstat": "",
                        "commits": [],
                        "commit_count": 0,
                        "patch": "",
                    },
                }
            )
        )
        assert "no_commit_on_success" in result["flags"]


# ============================================================================
# Fix 2: incomplete verdict
# ============================================================================


class TestIncompleteVerdict:
    """exit!=0 with commits>0 should produce 'incomplete' verdict."""

    def test_incomplete_fires(self):
        """exit_code=1 + commit_count>0 → verdict='incomplete'."""
        import translocase as worker

        result = asyncio.run(
            worker.chaperone(
                {
                    "task": "Build foo at x.py",
                    "provider": "zhipu",
                    "exit_code": 1,
                    "stdout": "partial work",
                    "stderr": "some error",
                    "pre_diff": {"stat": "", "numstat": ""},
                    "post_diff": {
                        "stat": " x.py | 5 +\n",
                        "numstat": "5\t0\tx.py",
                        "commits": ["abc123 partial"],
                        "commit_count": 1,
                        "patch": "diff content",
                    },
                    "branch_name": "ribosome-abc123",
                    "merged": False,
                }
            )
        )
        assert result["verdict"] == "incomplete"
        assert result["approved"] is False

    def test_not_incomplete_when_no_commits(self):
        """exit_code=1 + commit_count=0 → verdict='rejected', not incomplete."""
        import translocase as worker

        result = asyncio.run(
            worker.chaperone(
                {
                    "task": "Build foo at x.py",
                    "provider": "zhipu",
                    "exit_code": 1,
                    "stdout": "Error",
                    "stderr": "fatal error",
                    "pre_diff": {"stat": "", "numstat": ""},
                    "post_diff": {
                        "stat": "",
                        "numstat": "",
                        "commits": [],
                        "commit_count": 0,
                        "patch": "",
                    },
                }
            )
        )
        assert result["verdict"] != "incomplete"
        assert result["verdict"] == "rejected"


# ============================================================================
# Fix 3: approved verdict with merged
# ============================================================================


class TestApprovedVerdict:
    """exit==0 and merged==True should produce approved verdict."""

    def test_approved_when_merged(self):
        """exit_code=0 + merged=True with valid diff → approved."""
        import translocase as worker

        result = asyncio.run(
            worker.chaperone(
                {
                    "task": "Build foo at x.py",
                    "provider": "zhipu",
                    "exit_code": 0,
                    "stdout": "All tests pass!",
                    "stderr": "",
                    "pre_diff": {"stat": "", "numstat": ""},
                    "post_diff": {
                        "stat": " x.py | 10 +\n",
                        "numstat": "10\t0\tx.py",
                        "commits": ["abc123 add feature"],
                        "commit_count": 1,
                        "patch": "",
                    },
                    "branch_name": "ribosome-abc123",
                    "merged": True,
                }
            )
        )
        assert result["approved"] is True
        assert result["verdict"] in ("approved", "approved_with_flags")

    def test_approved_clean(self):
        """exit_code=0, no flags, merged → clean 'approved' verdict."""
        import translocase as worker

        result = asyncio.run(
            worker.chaperone(
                {
                    "task": "Build foo at x.py",
                    "provider": "zhipu",
                    "exit_code": 0,
                    "stdout": "All good! Tests pass. Changes made.",
                    "stderr": "",
                    "pre_diff": {"stat": "", "numstat": ""},
                    "post_diff": {
                        "stat": " x.py | 10 +\n",
                        "numstat": "10\t0\tx.py",
                        "commits": ["abc123"],
                        "commit_count": 1,
                        "patch": "",
                    },
                    "branch_name": "ribosome-abc123",
                    "merged": True,
                }
            )
        )
        assert result["verdict"] == "approved"


# ============================================================================
# Full patch preservation
# ============================================================================


async def _run_translate_incomplete():
    """Helper: run translate with exit=1 + commit_count=1 (incomplete)."""
    import translocase as worker

    mock_proc = AsyncMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(return_value=(b"partial work", b"some error"))
    mock_proc.kill = MagicMock()

    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_proc),
        patch("translocase._git_snapshot") as mock_snap,
        patch("translocase._create_worktree", return_value="/tmp/worktree"),
        patch("translocase._git_pull_ff_only"),
        patch("translocase._merge_worktree") as mock_merge,
        patch.object(
            sys.modules.get("temporalio.activity", MagicMock()), "heartbeat", MagicMock()
        ),
    ):
        mock_snap.side_effect = [
            {"stat": "", "numstat": "", "commits": [], "commit_count": 0, "patch": ""},
            {
                "stat": " x.py | 5 +\n",
                "numstat": "5\t0\tx.py",
                "commits": ["abc partial"],
                "commit_count": 1,
                "patch": "--- a/x.py\n+++ b/x.py\n+new line\n",
            },
        ]
        return (
            await worker.translate("[t-patch001] Fix the thing", "zhipu", 10),
            mock_merge,
        )


async def _run_translate_rejected():
    """Helper: run translate with exit=1 + commit_count=0 (rejected)."""
    import translocase as worker

    mock_proc = AsyncMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(return_value=(b"error output", b"fatal error"))
    mock_proc.kill = MagicMock()

    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_proc),
        patch("translocase._git_snapshot") as mock_snap,
        patch("translocase._create_worktree", return_value="/tmp/worktree"),
        patch("translocase._git_pull_ff_only"),
        patch("translocase._merge_worktree", return_value=True) as mock_merge,
        patch.object(
            sys.modules.get("temporalio.activity", MagicMock()), "heartbeat", MagicMock()
        ),
    ):
        mock_snap.side_effect = [
            {"stat": "", "numstat": "", "commits": [], "commit_count": 0, "patch": ""},
            {
                "stat": " x.py | 3 +\n",
                "numstat": "3\t0\tx.py",
                "commits": [],
                "commit_count": 0,
                "patch": "--- a/x.py\n+++ b/x.py\n+some change\n",
            },
        ]
        return (
            await worker.translate("[t-rej001] Fix the thing", "zhipu", 10),
            mock_merge,
        )


async def _run_translate_success():
    """Helper: run translate with exit=0 + commit_count=1 (success)."""
    import translocase as worker

    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"all done", b""))
    mock_proc.kill = MagicMock()

    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_proc),
        patch("translocase._git_snapshot") as mock_snap,
        patch("translocase._create_worktree", return_value="/tmp/worktree"),
        patch("translocase._git_pull_ff_only"),
        patch("translocase._merge_worktree", return_value=True) as mock_merge,
        patch.object(
            sys.modules.get("temporalio.activity", MagicMock()), "heartbeat", MagicMock()
        ),
    ):
        mock_snap.side_effect = [
            {"stat": "", "numstat": "", "commits": [], "commit_count": 0, "patch": ""},
            {
                "stat": " x.py | 10 +\n",
                "numstat": "10\t0\tx.py",
                "commits": ["abc done"],
                "commit_count": 1,
                "patch": "",
            },
        ]
        return (
            await worker.translate("[t-suc001] Build feature", "zhipu", 10),
            mock_merge,
        )


class TestFullPatchPreservation:
    """Full patch should appear in output for rejected/incomplete results."""

    def test_full_patch_on_incomplete(self):
        """Incomplete run writes full patch + branch name to output file."""
        result, _ = asyncio.run(_run_translate_incomplete())

        assert result["output_path"], "output_path should be populated"
        content = Path(result["output_path"]).read_text()
        assert "--- full patch (recoverable) ---" in content
        assert "Branch preserved for re-dispatch" in content
        # Cleanup
        Path(result["output_path"]).unlink(missing_ok=True)

    def test_full_patch_on_rejected(self):
        """Rejected run (exit!=0, no commits) still writes full patch."""
        result, _ = asyncio.run(_run_translate_rejected())

        assert result["output_path"], "output_path should be populated"
        content = Path(result["output_path"]).read_text()
        assert "--- full patch (recoverable) ---" in content
        # Cleanup
        Path(result["output_path"]).unlink(missing_ok=True)


# ============================================================================
# Branch preservation for incomplete
# ============================================================================


class TestBranchPreserved:
    """For incomplete verdict, branch must be preserved (not deleted)."""

    def test_merge_not_called_on_incomplete(self):
        """_merge_worktree should NOT be called when exit!=0 and commits>0."""
        result, mock_merge = asyncio.run(_run_translate_incomplete())

        # _merge_worktree must NOT have been called
        mock_merge.assert_not_called()
        # Branch name should be in result, merged=False
        assert result["branch_name"] != ""
        assert result["merged"] is False

    def test_merge_called_on_success(self):
        """_merge_worktree IS called when exit==0 (normal success path)."""
        result, mock_merge = asyncio.run(_run_translate_success())

        mock_merge.assert_called_once()
        assert result["merged"] is True
