"""Tests for effectors/disk-audit — disk usage and cleanup reporter."""
from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def _load_disk_audit():
    """Load the disk-audit effector by exec-ing its Python body."""
    import types
    import sys
    source = open(Path.home() / "germline" / "effectors" / "disk-audit").read()
    # Create a proper module for dataclasses to find
    mod = types.ModuleType("disk_audit_effector")
    mod.__file__ = str(Path.home() / "germline" / "effectors" / "disk-audit")
    # Register in sys.modules so dataclasses can find it
    sys.modules["disk_audit_effector"] = mod
    exec(source, mod.__dict__)
    return mod.__dict__


# Load the module and extract functions/classes
_mod = _load_disk_audit()
DiskUsage = _mod["DiskUsage"]
DirInfo = _mod["DirInfo"]
TmpCandidate = _mod["TmpCandidate"]
_fmt_bytes = _mod["_fmt_bytes"]
_fmt_age = _mod["_fmt_age"]
get_root_usage = _mod["get_root_usage"]
_dir_size = _mod["_dir_size"]
get_largest_dirs = _mod["get_largest_dirs"]
get_tmp_candidates = _mod["get_tmp_candidates"]
print_report = _mod["print_report"]
main = _mod["main"]


# ── DiskUsage dataclass tests ────────────────────────────────────────────────


def test_disk_usage_percent_used():
    """DiskUsage.percent_used calculates correctly."""
    du = DiskUsage(total=1000, used=500, free=500)
    assert du.percent_used == 50.0


def test_disk_usage_percent_used_zero_total():
    """DiskUsage.percent_used returns 0 when total is 0."""
    du = DiskUsage(total=0, used=0, free=0)
    assert du.percent_used == 0.0


def test_disk_usage_percent_used_full():
    """DiskUsage.percent_used returns 100 when full."""
    du = DiskUsage(total=1000, used=1000, free=0)
    assert du.percent_used == 100.0


# ── DirInfo dataclass tests ──────────────────────────────────────────────────


def test_dir_info_comparison():
    """DirInfo supports comparison by size."""
    small = DirInfo(path=Path("/small"), size=100)
    large = DirInfo(path=Path("/large"), size=1000)
    assert small < large
    assert large > small


def test_dir_info_sorting():
    """DirInfo can be sorted by size."""
    dirs = [
        DirInfo(path=Path("/mid"), size=500),
        DirInfo(path=Path("/small"), size=100),
        DirInfo(path=Path("/large"), size=1000),
    ]
    dirs.sort(reverse=True)
    assert dirs[0].path == Path("/large")
    assert dirs[1].path == Path("/mid")
    assert dirs[2].path == Path("/small")


# ── TmpCandidate dataclass tests ─────────────────────────────────────────────


def test_tmp_candidate_fields():
    """TmpCandidate stores all expected fields."""
    now = time.time()
    tc = TmpCandidate(path=Path("/tmp/oldfile"), size=1000, mtime=now, reason="old")
    assert tc.path == Path("/tmp/oldfile")
    assert tc.size == 1000
    assert tc.mtime == now
    assert tc.reason == "old"


# ── _fmt_bytes tests ──────────────────────────────────────────────────────────


def test_fmt_bytes_bytes():
    """_fmt_bytes formats bytes correctly."""
    assert _fmt_bytes(500) == "500.0 B"


def test_fmt_bytes_kilobytes():
    """_fmt_bytes formats kilobytes correctly."""
    assert _fmt_bytes(1024) == "1.0 KB"


def test_fmt_bytes_megabytes():
    """_fmt_bytes formats megabytes correctly."""
    assert _fmt_bytes(1024 * 1024) == "1.0 MB"


def test_fmt_bytes_gigabytes():
    """_fmt_bytes formats gigabytes correctly."""
    assert _fmt_bytes(1024 * 1024 * 1024) == "1.0 GB"


def test_fmt_bytes_terabytes():
    """_fmt_bytes formats terabytes correctly."""
    assert _fmt_bytes(1024 * 1024 * 1024 * 1024) == "1.0 TB"


def test_fmt_bytes_petabytes():
    """_fmt_bytes formats petabytes correctly."""
    assert _fmt_bytes(1024 ** 5) == "1.0 PB"


# ── _fmt_age tests ────────────────────────────────────────────────────────────


def test_fmt_age_minutes():
    """_fmt_age formats minutes correctly."""
    now = time.time()
    mtime = now - 1800  # 30 minutes ago
    assert _fmt_age(mtime, now) == "30m"


def test_fmt_age_hours():
    """_fmt_age formats hours correctly."""
    now = time.time()
    mtime = now - 7200  # 2 hours ago
    assert _fmt_age(mtime, now) == "2h"


def test_fmt_age_days():
    """_fmt_age formats days correctly."""
    now = time.time()
    mtime = now - 86400 * 3  # 3 days ago
    assert _fmt_age(mtime, now) == "3d"


# ── get_root_usage tests ──────────────────────────────────────────────────────


def test_get_root_usage_returns_disk_usage():
    """get_root_usage returns a DiskUsage instance."""
    result = get_root_usage()
    assert isinstance(result, DiskUsage)
    assert result.total > 0
    assert result.used >= 0
    assert result.free >= 0


def test_get_root_usage_values_consistent():
    """get_root_usage returns consistent values (total = used + free)."""
    result = get_root_usage()
    # Allow small rounding differences
    assert abs(result.total - result.used - result.free) < 1024


# ── _dir_size tests ───────────────────────────────────────────────────────────


def test_dir_size_empty(tmp_path):
    """_dir_size returns 0 for empty directory."""
    assert _dir_size(tmp_path) == 0


def test_dir_size_with_files(tmp_path):
    """_dir_size calculates total size of files."""
    (tmp_path / "file1.txt").write_bytes(b"x" * 100)
    (tmp_path / "file2.txt").write_bytes(b"x" * 200)
    assert _dir_size(tmp_path) == 300


def test_dir_size_with_subdirs(tmp_path):
    """_dir_size includes files in subdirectories."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (tmp_path / "file1.txt").write_bytes(b"x" * 100)
    (subdir / "file2.txt").write_bytes(b"x" * 200)
    assert _dir_size(tmp_path) == 300


def test_dir_size_skips_symlinks(tmp_path):
    """_dir_size does not follow symlinks."""
    (tmp_path / "real.txt").write_bytes(b"x" * 100)
    (tmp_path / "link.txt").symlink_to(tmp_path / "real.txt")
    # Should only count the real file once
    assert _dir_size(tmp_path) == 100


def test_dir_size_handles_permission_error(tmp_path):
    """_dir_size handles permission errors gracefully."""
    # Create a file that we can read
    (tmp_path / "readable.txt").write_bytes(b"x" * 100)
    # Patch os.scandir to raise PermissionError for one entry
    with patch("os.scandir") as mock_scandir:
        mock_scandir.side_effect = PermissionError("access denied")
        result = _dir_size(tmp_path)
    assert result == 0  # Should return 0, not raise


# ── get_largest_dirs tests ────────────────────────────────────────────────────


def test_get_largest_dirs_empty(tmp_path):
    """get_largest_dirs returns empty list for non-existent directory."""
    result = get_largest_dirs(Path("/nonexistent/path"))
    assert result == []


def test_get_largest_dirs_no_subdirs(tmp_path):
    """get_largest_dirs returns empty list when no subdirectories."""
    (tmp_path / "file.txt").write_bytes(b"x" * 100)
    result = get_largest_dirs(tmp_path)
    assert result == []


def test_get_largest_dirs_returns_sorted(tmp_path):
    """get_largest_dirs returns directories sorted by size descending."""
    # Create subdirectories with different sizes
    small = tmp_path / "small"
    large = tmp_path / "large"
    small.mkdir()
    large.mkdir()
    (small / "file.txt").write_bytes(b"x" * 100)
    (large / "file.txt").write_bytes(b"x" * 1000)

    result = get_largest_dirs(tmp_path)
    assert len(result) == 2
    assert result[0].path.name == "large"
    assert result[1].path.name == "small"


def test_get_largest_dirs_limits_top_n(tmp_path):
    """get_largest_dirs limits results to top_n."""
    for i in range(20):
        d = tmp_path / f"dir{i}"
        d.mkdir()
        (d / "file.txt").write_bytes(b"x" * (i + 1) * 100)

    result = get_largest_dirs(tmp_path, top_n=5)
    assert len(result) == 5


def test_get_largest_dirs_skips_hidden(tmp_path):
    """get_largest_dirs skips hidden directories."""
    visible = tmp_path / "visible"
    hidden = tmp_path / ".hidden"
    visible.mkdir()
    hidden.mkdir()
    (visible / "file.txt").write_bytes(b"x" * 100)
    (hidden / "file.txt").write_bytes(b"x" * 1000)

    result = get_largest_dirs(tmp_path)
    assert len(result) == 1
    assert result[0].path.name == "visible"


# ── get_tmp_candidates tests ──────────────────────────────────────────────────


def test_get_tmp_candidates_empty(tmp_path):
    """get_tmp_candidates returns empty list for empty directory."""
    result = get_tmp_candidates(tmp_path)
    assert result == []


def test_get_tmp_candidates_finds_old_files(tmp_path):
    """get_tmp_candidates identifies old files."""
    old_file = tmp_path / "old.txt"
    old_file.write_bytes(b"x" * 100)
    # Set mtime to 10 days ago
    old_time = time.time() - (10 * 86400)
    os.utime(old_file, (old_time, old_time))

    result = get_tmp_candidates(tmp_path, old_days=7, large_mb=1000)
    assert len(result) == 1
    assert result[0].reason == "old"


def test_get_tmp_candidates_finds_large_files(tmp_path):
    """get_tmp_candidates identifies large files."""
    large_file = tmp_path / "large.txt"
    large_file.write_bytes(b"x" * (150 * 1024 * 1024))  # 150 MB

    result = get_tmp_candidates(tmp_path, old_days=365, large_mb=100)
    assert len(result) == 1
    assert result[0].reason == "large"


def test_get_tmp_candidates_finds_old_and_large(tmp_path):
    """get_tmp_candidates identifies files that are both old and large."""
    file = tmp_path / "old_large.txt"
    file.write_bytes(b"x" * (150 * 1024 * 1024))  # 150 MB
    old_time = time.time() - (10 * 86400)
    os.utime(file, (old_time, old_time))

    result = get_tmp_candidates(tmp_path, old_days=7, large_mb=100)
    assert len(result) == 1
    assert result[0].reason == "old+large"


def test_get_tmp_candidates_sorts_by_size(tmp_path):
    """get_tmp_candidates sorts results by size descending."""
    # Create files of different sizes
    for i, (name, size_mb, days_old) in enumerate([
        ("small_old", 10, 10),
        ("large_new", 200, 1),
        ("medium_old", 50, 10),
    ]):
        f = tmp_path / f"{name}.txt"
        f.write_bytes(b"x" * (size_mb * 1024 * 1024))
        old_time = time.time() - (days_old * 86400)
        os.utime(f, (old_time, old_time))

    result = get_tmp_candidates(tmp_path, old_days=7, large_mb=100)
    assert len(result) == 3
    # Should be sorted by size descending
    assert result[0].path.name == "large_new.txt"
    assert result[1].path.name == "medium_old.txt"
    assert result[2].path.name == "small_old.txt"


def test_get_tmp_candidates_limits_to_20(tmp_path):
    """get_tmp_candidates limits results to 20 entries."""
    for i in range(30):
        f = tmp_path / f"file{i}.txt"
        f.write_bytes(b"x" * (200 * 1024 * 1024))  # Large enough

    result = get_tmp_candidates(tmp_path, old_days=365, large_mb=100)
    assert len(result) == 20


# ── main function tests ───────────────────────────────────────────────────────


def test_main_help_flag():
    """main with --help returns 0 and prints docstring."""
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = main(["--help"])
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    assert result == 0
    assert "disk-audit" in output


def test_main_h_flag():
    """main with -h returns 0 and prints docstring."""
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = main(["-h"])
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    assert result == 0
    assert "disk-audit" in output


def test_main_no_args_runs_report():
    """main with no args runs print_report and returns 0."""
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = main([])
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    assert result == 0
    assert "ROOT FILESYSTEM" in output


# ── print_report tests ─────────────────────────────────────────────────────────


def test_print_report_includes_root_filesystem():
    """print_report includes root filesystem info."""
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        print_report()
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    assert "ROOT FILESYSTEM (/)" in output
    assert "Total:" in output
    assert "Used:" in output
    assert "Free:" in output


def test_print_report_includes_germline_dirs():
    """print_report includes germline directory info."""
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        print_report()
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    assert "LARGEST DIRS UNDER" in output
    assert "germline" in output


def test_print_report_includes_tmp_candidates():
    """print_report includes tmp cleanup candidates."""
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        print_report()
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    assert "TMP CLEANUP CANDIDATES" in output
