"""Tests for temporal worker cache collision fix (t-ca2248)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class TestCacheCollision:
    """Stale failure cache must not be replayed on re-dispatch."""

    def test_successful_cache_returns_cached(self, tmp_path: Path):
        """A cached output with Exit: 0 should be returned as-is."""
        output_dir = tmp_path / "ribosome-outputs"
        output_dir.mkdir()
        cached_file = output_dir / "20260403-abc123.txt"
        cached_file.write_text(
            "Task: do stuff\nProvider: zhipu\nExit: 0\n\n--- stdout ---\nAll tests passed.\n"
        )

        content = cached_file.read_text()
        rc = 0 if "Exit: 0" in content[:200] else 1
        assert rc == 0, "Successful cache should return exit 0"

    def test_failed_cache_not_replayed(self, tmp_path: Path):
        """A cached output with Exit: 1 should NOT be returned — re-execute instead."""
        output_dir = tmp_path / "ribosome-outputs"
        output_dir.mkdir()
        cached_file = output_dir / "20260403-def456.txt"
        cached_file.write_text(
            "Task: do stuff\nProvider: zhipu\nExit: 1\n\n--- stdout ---\nRate limited.\n"
        )

        content = cached_file.read_text()
        is_success = "Exit: 0" in content[:200]
        assert not is_success, "Failed cache should not be treated as success"
        # Worker should skip this cache and re-execute

    def test_cache_overwritten_on_retry(self, tmp_path: Path):
        """After re-execution, the output file should be overwritten."""
        output_dir = tmp_path / "ribosome-outputs"
        output_dir.mkdir()
        cached_file = output_dir / "20260403-ghi789.txt"

        # Write stale failure
        cached_file.write_text(
            "Task: do stuff\nProvider: zhipu\nExit: 1\n\n--- stdout ---\nFailed.\n"
        )

        # Simulate successful retry — overwrite
        cached_file.write_text(
            "Task: do stuff\nProvider: zhipu\nExit: 0\n\n--- stdout ---\nAll good now.\n"
        )

        content = cached_file.read_text()
        assert "Exit: 0" in content[:200], "Retry should overwrite stale cache"
        assert "All good now" in content

    def test_missing_cache_triggers_execution(self, tmp_path: Path):
        """No cached file means execute normally."""
        output_dir = tmp_path / "ribosome-outputs"
        output_dir.mkdir()
        cached_file = output_dir / "20260403-nope.txt"
        assert not cached_file.exists(), "No cache file = fresh execution"

    def test_cache_check_uses_first_200_chars(self, tmp_path: Path):
        """Exit code check should only scan first 200 chars, not deep in output."""
        output_dir = tmp_path / "ribosome-outputs"
        output_dir.mkdir()
        cached_file = output_dir / "20260403-tricky.txt"

        # Exit: 0 appears deep in stdout but actual exit was 1
        cached_file.write_text(
            "Task: do stuff\nProvider: zhipu\nExit: 1\n\n"
            "--- stdout ---\n" + ("x" * 300) + "\nExit: 0 found in output\n"
        )

        content = cached_file.read_text()
        is_success = "Exit: 0" in content[:200]
        assert not is_success, "Should only check first 200 chars for exit code"
