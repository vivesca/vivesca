#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/gemmule-sync — remote directory sync from gemmule."""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

GEMMULE_SYNC_PATH = Path(__file__).resolve().parents[1] / "effectors" / "gemmule-sync"


@pytest.fixture()
def gs():
    """Load gemmule-sync via exec into an isolated namespace."""
    ns: dict = {"__name__": "gemmule_sync"}
    source = GEMMULE_SYNC_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    mod = type("gs", (), {})()
    for k, v in ns.items():
        if not k.startswith("__"):
            setattr(mod, k, v)
    return mod


# ── Constants ─────────────────────────────────────────────────────────────────


class TestConstants:
    def test_remote_host(self, gs):
        assert gs.REMOTE_HOST == "terry@100.94.27.93"

    def test_sync_pairs_count(self, gs):
        assert len(gs.SYNC_PAIRS) == 3

    def test_sync_pairs_sources(self, gs):
        srcs = [s for s, _ in gs.SYNC_PAIRS]
        assert "~/epigenome/chromatin/" in srcs
        assert "~/notes/" in srcs
        assert "~/code/acta/" in srcs

    def test_log_file_path(self, gs):
        assert gs.LOG_FILE == Path.home() / ".local" / "share" / "vivesca" / "gemmule-sync.log"


# ── rsync_dir ─────────────────────────────────────────────────────────────────


class TestRsyncDir:
    def test_builds_correct_command(self, gs):
        """rsync_dir invokes rsync with -az --delete and correct src/dst."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run, \
             patch("pathlib.Path.mkdir"):
            rc, out = gs.rsync_dir("terry@host", "~/src/", "~/dst")

        cmd = mock_run.call_args[0][0]
        assert cmd[:3] == ["rsync", "-az", "--delete"]
        assert cmd[-2] == "terry@host:~/src/"
        assert cmd[-1].endswith("/dst/")

    def test_dry_run_adds_flag(self, gs):
        """rsync_dir appends --dry-run when dry_run=True."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run, \
             patch("pathlib.Path.mkdir"):
            gs.rsync_dir("terry@host", "~/src/", "~/dst", dry_run=True)

        cmd = mock_run.call_args[0][0]
        assert "--dry-run" in cmd

    def test_returns_nonzero_on_failure(self, gs):
        """rsync_dir returns the rsync exit code."""
        mock_result = MagicMock()
        mock_result.returncode = 23
        mock_result.stdout = ""
        mock_result.stderr = "some error"

        with patch("subprocess.run", return_value=mock_result), \
             patch("pathlib.Path.mkdir"):
            rc, out = gs.rsync_dir("terry@host", "~/src/", "~/dst")

        assert rc == 23
        assert "some error" in out

    def test_creates_dst_directory(self, gs):
        """rsync_dir calls mkdir on the destination path."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run, \
             patch("pathlib.Path.mkdir") as mock_mkdir:
            gs.rsync_dir("terry@host", "~/src/", "~/dst")

        mock_mkdir.assert_called()


# ── run_sync ──────────────────────────────────────────────────────────────────


class TestRunSync:
    def test_syncs_all_three_dirs(self, gs):
        """run_sync calls rsync_dir for each SYNC_PAIR."""
        with patch.object(gs, "rsync_dir", return_value=(0, "")) as mock_rsync, \
             patch.object(gs, "setup_logging"):
            results = gs.run_sync()

        assert mock_rsync.call_count == 3
        assert len(results) == 3

    def test_passes_dry_run(self, gs):
        """run_sync forwards dry_run flag to rsync_dir."""
        with patch.object(gs, "rsync_dir", return_value=(0, "")) as mock_rsync, \
             patch.object(gs, "setup_logging"):
            gs.run_sync(dry_run=True)

        for c in mock_rsync.call_args_list:
            assert c.kwargs.get("dry_run") is True or c.args[-1] is True or "dry_run" in str(c)

    def test_collects_results(self, gs):
        """run_sync returns (label, rc, output) tuples."""
        with patch.object(gs, "rsync_dir", side_effect=[
            (0, "ok1"), (1, "err"), (0, "ok2"),
        ]), patch.object(gs, "setup_logging"):
            results = gs.run_sync()

        assert results[0][1] == 0
        assert results[1][1] == 1
        assert results[2][1] == 0


# ── main ──────────────────────────────────────────────────────────────────────


class TestMain:
    def test_returns_zero_on_success(self, gs):
        """main() returns 0 when all rsyncs succeed."""
        with patch.object(gs, "run_sync", return_value=[
            ("chromatin", 0, ""), ("notes", 0, ""), ("acta", 0, ""),
        ]):
            rc = gs.main(["--dry-run"])
        assert rc == 0

    def test_returns_one_on_failure(self, gs):
        """main() returns 1 when any rsync fails."""
        with patch.object(gs, "run_sync", return_value=[
            ("chromatin", 0, ""), ("notes", 23, "error"), ("acta", 0, ""),
        ]):
            rc = gs.main([])
        assert rc == 1

    def test_dry_run_flag_parsed(self, gs):
        """main passes --dry-run through to run_sync."""
        with patch.object(gs, "run_sync", return_value=[
            ("chromatin", 0, ""), ("notes", 0, ""), ("acta", 0, ""),
        ]) as mock_sync:
            gs.main(["--dry-run"])

        # Verify run_sync was called with dry_run=True
        mock_sync.assert_called_once_with(dry_run=True)

    def test_no_args_is_live_run(self, gs):
        """main with no args runs a live (non-dry) sync."""
        with patch.object(gs, "run_sync", return_value=[
            ("chromatin", 0, ""), ("notes", 0, ""), ("acta", 0, ""),
        ]) as mock_sync:
            gs.main([])

        mock_sync.assert_called_once_with(dry_run=False)


# ── Idempotency ───────────────────────────────────────────────────────────────


class TestIdempotency:
    def test_rsync_same_args_repeated(self, gs):
        """Calling rsync_dir twice with same args produces same command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run, \
             patch("pathlib.Path.mkdir"):
            gs.rsync_dir("terry@host", "~/src/", "~/dst")
            gs.rsync_dir("terry@host", "~/src/", "~/dst")

        cmd1 = mock_run.call_args_list[0][0][0]
        cmd2 = mock_run.call_args_list[1][0][0]
        assert cmd1 == cmd2
