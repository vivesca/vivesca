"""Tests for mitosis — DR sync organelle.

Unit tests that don't require network access. Integration tests
(actual fly ssh) are skipped unless MITOSIS_INTEGRATION=1.
"""

from __future__ import annotations

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.mitosis import (
    LUCERNA_APP,
    LUCERNA_HOME,
    SYNC_TARGETS,
    FidelityReport,
    ReplicationResult,
    _git_push,
    _is_gemmule_reachable,
    setup,
    status,
    sync,
)

# ── Unit tests (no network) ──────────────────────────────────


class TestReplicationResult:
    def test_basic(self):
        r = ReplicationResult("test", True, 1.5, "ok")
        assert r.success
        assert r.elapsed_s == 1.5

    def test_failure(self):
        r = ReplicationResult("test", False, 0.5, "boom")
        assert not r.success
        assert r.message == "boom"


class TestFidelityReport:
    def test_summary(self):
        report = FidelityReport(
            results=[
                ReplicationResult("a", True, 1.0),
                ReplicationResult("b", False, 2.0, "fail"),
            ],
            started=0,
            finished=5.0,
        )
        assert "1/2" in report.summary
        assert "5.0s" in report.summary

    def test_ok_ignores_non_critical(self):
        """Non-critical failures don't make the report fail."""
        # scripts is not critical
        report = FidelityReport(
            results=[
                ReplicationResult("germline", True, 1.0),
                ReplicationResult("epigenome", True, 1.0),
                ReplicationResult("scripts", False, 1.0, "fail"),
            ],
        )
        assert report.ok

    def test_ok_fails_on_critical(self):
        """Critical target failure makes report fail."""
        report = FidelityReport(
            results=[
                ReplicationResult("germline", False, 1.0, "fail"),
                ReplicationResult("epigenome", True, 1.0),
            ],
        )
        assert not report.ok


class TestSyncTargets:
    def test_all_targets_have_required_fields(self):
        for t in SYNC_TARGETS:
            assert "name" in t
            assert "local" in t
            assert "remote" in t
            assert "repo" in t
            assert "critical" in t

    def test_critical_targets(self):
        critical = {t["name"] for t in SYNC_TARGETS if t["critical"]}
        assert "germline" in critical
        assert "epigenome" in critical

    def test_remote_paths_use_lucerna_home(self):
        for t in SYNC_TARGETS:
            assert t["remote"].startswith(LUCERNA_HOME)


class TestGitPush:
    def test_not_a_repo(self, tmp_path):
        ok, msg = _git_push(str(tmp_path))
        assert not ok
        assert "not a git repo" in msg

    def test_clean_repo(self, tmp_path):
        """A repo with no changes should push (or be up-to-date)."""
        subprocess.run(["git", "init", str(tmp_path)], capture_output=True)
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "--allow-empty", "-m", "init"],
            capture_output=True,
        )
        # No remote, so push will fail — but that's expected
        ok, msg = _git_push(str(tmp_path))
        # Push fails because no remote configured — that's fine for this test
        assert not ok or "up-to-date" in msg


class TestReachability:
    @patch("metabolon.organelles.mitosis.subprocess.run")
    def test_reachable(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="started")
        assert _is_gemmule_reachable()

    @patch("metabolon.organelles.mitosis.subprocess.run")
    def test_unreachable(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert not _is_gemmule_reachable()

    @patch("metabolon.organelles.mitosis.subprocess.run")
    def test_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="fly", timeout=15)
        assert not _is_gemmule_reachable()


class TestSyncUnreachable:
    @patch("metabolon.organelles.mitosis._is_gemmule_reachable", return_value=False)
    def test_sync_when_unreachable(self, _):
        report = sync()
        assert len(report.results) == 1
        assert not report.results[0].success
        assert "not running" in report.results[0].message

    @patch("metabolon.organelles.mitosis._is_gemmule_reachable", return_value=False)
    def test_status_when_unreachable(self, _):
        info = status()
        assert not info["reachable"]
        assert info["machine_state"] == "unknown"

    @patch("metabolon.organelles.mitosis._is_gemmule_reachable", return_value=False)
    def test_setup_when_unreachable(self, _):
        result = setup()
        assert not result["success"]
        assert "not running" in result["error"]


class TestAppName:
    def test_app_is_gemmule(self):
        assert LUCERNA_APP == "gemmule"


# ── Integration tests (require fly CLI + running gemmule) ────


INTEGRATION = os.environ.get("MITOSIS_INTEGRATION") == "1"


@pytest.mark.skipif(not INTEGRATION, reason="MITOSIS_INTEGRATION not set")
class TestIntegration:
    def test_status(self):
        info = status()
        assert info["reachable"]
        assert info["machine_state"] == "started"

    def test_sync(self):
        report = sync(["germline"])
        assert report.ok
        assert len(report.results) >= 1

    def test_setup_idempotent(self):
        result = setup()
        assert result["success"]
        for step in result["steps"]:
            assert step["success"], f"{step['name']}: {step.get('message')}"
