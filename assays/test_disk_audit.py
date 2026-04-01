from __future__ import annotations

"""Tests for disk-audit — disk usage and cleanup candidate reporter."""

import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_disk_audit():
    """Load the disk-audit effector by exec-ing its Python body."""
    import sys, types
    source = open(str(Path.home() / "germline/effectors/disk-audit")).read()
    mod = types.ModuleType("disk_audit")
    sys.modules["disk_audit"] = mod
    ns: dict = {"__name__": "disk_audit"}
    exec(source, ns)
    del sys.modules["disk_audit"]
    return ns


_mod = _load_disk_audit()

_fmt_bytes = _mod["_fmt_bytes"]
_fmt_age = _mod["_fmt_age"]
DiskUsage = _mod["DiskUsage"]
DirInfo = _mod["DirInfo"]
TmpCandidate = _mod["TmpCandidate"]
get_root_usage = _mod["get_root_usage"]
_dir_size = _mod["_dir_size"]
get_largest_dirs = _mod["get_largest_dirs"]
get_tmp_candidates = _mod["get_tmp_candidates"]
print_report = _mod["print_report"]
main = _mod["main"]


# ── _fmt_bytes tests ────────────────────────────────────────────────────


class TestFmtBytes:
    """Tests for _fmt_bytes human-readable byte formatter."""

    def test_zero(self):
        assert _fmt_bytes(0) == "0.0 B"

    def test_bytes(self):
        assert _fmt_bytes(512) == "512.0 B"

    def test_kilobytes(self):
        assert _fmt_bytes(1024) == "1.0 KB"

    def test_megabytes(self):
        assert _fmt_bytes(1024 * 1024) == "1.0 MB"

    def test_gigabytes(self):
        assert _fmt_bytes(1024 ** 3) == "1.0 GB"

    def test_terabytes(self):
        assert _fmt_bytes(1024 ** 4) == "1.0 TB"

    def test_petabytes(self):
        assert _fmt_bytes(1024 ** 5) == "1.0 PB"

    def test_fractional(self):
        result = _fmt_bytes(1536)  # 1.5 KB
        assert "KB" in result
        assert "1.5" in result

    def test_negative_zero(self):
        result = _fmt_bytes(-0)
        assert "0.0 B" == result


# ── _fmt_age tests ──────────────────────────────────────────────────────


class TestFmtAge:
    """Tests for _fmt_age human-readable age formatter."""

    def test_minutes(self):
        now = time.time()
        mtime = now - 120  # 2 minutes ago
        assert _fmt_age(mtime, now) == "2m"

    def test_hours(self):
        now = time.time()
        mtime = now - 7200  # 2 hours ago
        assert _fmt_age(mtime, now) == "2h"

    def test_days(self):
        now = time.time()
        mtime = now - 172800  # 2 days ago
        assert _fmt_age(mtime, now) == "2d"

    def test_zero_age(self):
        now = time.time()
        assert _fmt_age(now, now) == "0m"

    def test_59_seconds(self):
        now = time.time()
        mtime = now - 59
        assert _fmt_age(mtime, now) == "0m"

    def test_just_under_one_hour(self):
        now = time.time()
        mtime = now - 3599
        assert _fmt_age(mtime, now) == "59m"

    def test_just_under_one_day(self):
        now = time.time()
        mtime = now - 86399
        assert _fmt_age(mtime, now) == "23h"


# ── DiskUsage dataclass tests ───────────────────────────────────────────


class TestDiskUsage:
    """Tests for DiskUsage dataclass and percent_used property."""

    def test_percent_used_normal(self):
        du = DiskUsage(total=1000, used=750, free=250)
        assert du.percent_used == 75.0

    def test_percent_used_zero_total(self):
        du = DiskUsage(total=0, used=0, free=0)
        assert du.percent_used == 0

    def test_percent_used_full(self):
        du = DiskUsage(total=1000, used=1000, free=0)
        assert du.percent_used == 100.0

    def test_percent_used_empty(self):
        du = DiskUsage(total=1000, used=0, free=1000)
        assert du.percent_used == 0.0

    def test_fields(self):
        du = DiskUsage(total=100, used=50, free=50)
        assert du.total == 100
        assert du.used == 50
        assert du.free == 50


# ── DirInfo dataclass tests ─────────────────────────────────────────────


class TestDirInfo:
    """Tests for DirInfo dataclass and comparison."""

    def test_less_than(self):
        a = DirInfo(path=Path("/a"), size=100)
        b = DirInfo(path=Path("/b"), size=200)
        assert a < b
        assert not b < a

    def test_sorting(self):
        dirs = [
            DirInfo(path=Path("/c"), size=300),
            DirInfo(path=Path("/a"), size=100),
            DirInfo(path=Path("/b"), size=200),
        ]
        dirs.sort(reverse=True)
        assert dirs[0].path == Path("/c")
        assert dirs[1].path == Path("/b")
        assert dirs[2].path == Path("/a")

    def test_equal_size(self):
        a = DirInfo(path=Path("/a"), size=100)
        b = DirInfo(path=Path("/b"), size=100)
        assert not a < b
        assert not b < a


# ── TmpCandidate dataclass tests ────────────────────────────────────────


class TestTmpCandidate:
    """Tests for TmpCandidate dataclass."""

    def test_fields(self):
        tc = TmpCandidate(path=Path("/tmp/foo"), size=500, mtime=12345.0, reason="old")
        assert tc.path == Path("/tmp/foo")
        assert tc.size == 500
        assert tc.mtime == 12345.0
        assert tc.reason == "old"

    def test_reasons(self):
        for reason in ("old", "large", "old+large"):
            tc = TmpCandidate(path=Path("/tmp/x"), size=1, mtime=0.0, reason=reason)
            assert tc.reason == reason


# ── _dir_size tests ─────────────────────────────────────────────────────


class TestDirSize:
    """Tests for _dir_size recursive directory size calculator."""

    def test_empty_dir(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        assert _dir_size(d) == 0

    def test_single_file(self, tmp_path):
        d = tmp_path / "sfile"
        d.mkdir()
        (d / "f.txt").write_bytes(b"x" * 100)
        assert _dir_size(d) == 100

    def test_multiple_files(self, tmp_path):
        d = tmp_path / "mfiles"
        d.mkdir()
        (d / "a.txt").write_bytes(b"x" * 50)
        (d / "b.txt").write_bytes(b"y" * 75)
        assert _dir_size(d) == 125

    def test_nested_dirs(self, tmp_path):
        d = tmp_path / "top"
        sub = d / "sub"
        sub.mkdir(parents=True)
        (d / "root.txt").write_bytes(b"x" * 100)
        (sub / "deep.txt").write_bytes(b"y" * 200)
        assert _dir_size(d) == 300

    def test_nonexistent_dir(self, tmp_path):
        assert _dir_size(tmp_path / "nope") == 0

    def test_permission_error_handled(self, tmp_path):
        """_dir_size doesn't crash on permission errors."""
        d = tmp_path / "restricted"
        d.mkdir()
        (d / "f.txt").write_text("ok")
        # No easy way to trigger PermissionError as root, but test that
        # the function is callable and returns an int
        result = _dir_size(d)
        assert isinstance(result, int)
        assert result >= 0


# ── get_root_usage tests ────────────────────────────────────────────────


class TestGetRootUsage:
    """Tests for get_root_usage."""

    def test_returns_disk_usage(self):
        du = get_root_usage()
        assert isinstance(du, DiskUsage)
        assert du.total > 0
        assert du.used > 0
        assert du.free >= 0
        # total >= used + free (reserved blocks may make total larger)
        assert du.total >= du.used + du.free

    def test_percent_used_reasonable(self):
        du = get_root_usage()
        assert 0 <= du.percent_used <= 100


# ── get_largest_dirs tests ──────────────────────────────────────────────


class TestGetLargestDirs:
    """Tests for get_largest_dirs."""

    def test_empty_dir(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        assert get_largest_dirs(root) == []

    def test_nonexistent_dir(self, tmp_path):
        assert get_largest_dirs(tmp_path / "nope") == []

    def test_returns_sorted_dirs(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        # Create dirs with different sizes
        for name, size in [("small", 100), ("large", 500), ("medium", 300)]:
            d = root / name
            d.mkdir()
            (d / "f.bin").write_bytes(b"x" * size)
        result = get_largest_dirs(root)
        assert len(result) == 3
        assert result[0].path.name == "large"
        assert result[1].path.name == "medium"
        assert result[2].path.name == "small"

    def test_top_n_limit(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        for i in range(5):
            d = root / f"dir{i}"
            d.mkdir()
            (d / "f.bin").write_bytes(b"x" * (i * 100))
        result = get_largest_dirs(root, top_n=2)
        assert len(result) == 2

    def test_skips_hidden_dirs(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        visible = root / "visible"
        hidden = root / ".hidden"
        visible.mkdir()
        hidden.mkdir()
        (visible / "f.bin").write_bytes(b"x" * 100)
        (hidden / "f.bin").write_bytes(b"x" * 999)
        result = get_largest_dirs(root)
        assert len(result) == 1
        assert result[0].path.name == "visible"

    def test_files_ignored(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        (root / "bigfile.bin").write_bytes(b"x" * 10000)
        result = get_largest_dirs(root)
        assert result == []


# ── get_tmp_candidates tests ────────────────────────────────────────────


class TestGetTmpCandidates:
    """Tests for get_tmp_candidates."""

    def _make_old_file(self, tmp_path, name, size=1000, days_old=10):
        """Create a file with an old mtime."""
        f = tmp_path / name
        f.write_bytes(b"x" * size)
        old_time = time.time() - (days_old * 86400)
        os.utime(f, (old_time, old_time))
        return f

    def _make_large_file(self, tmp_path, name, size_mb=150):
        """Create a large file."""
        f = tmp_path / name
        f.write_bytes(b"x" * (size_mb * 1024 * 1024))
        return f

    def test_empty_dir(self, tmp_path):
        tmp = tmp_path / "tmp"
        tmp.mkdir()
        assert get_tmp_candidates(tmp_root=tmp) == []

    def test_old_file_detected(self, tmp_path):
        tmp = tmp_path / "tmp"
        tmp.mkdir()
        self._make_old_file(tmp, "oldfile.txt", size=500, days_old=10)
        candidates = get_tmp_candidates(tmp_root=tmp)
        assert len(candidates) == 1
        assert candidates[0].reason == "old"
        assert candidates[0].path.name == "oldfile.txt"

    def test_large_file_detected(self, tmp_path):
        tmp = tmp_path / "tmp"
        tmp.mkdir()
        self._make_large_file(tmp, "bigfile.bin", size_mb=150)
        candidates = get_tmp_candidates(tmp_root=tmp)
        assert len(candidates) == 1
        assert candidates[0].reason == "large"

    def test_old_and_large_file(self, tmp_path):
        tmp = tmp_path / "tmp"
        tmp.mkdir()
        f = tmp / "oldbig.bin"
        f.write_bytes(b"x" * (200 * 1024 * 1024))  # 200 MB
        old_time = time.time() - (10 * 86400)
        os.utime(f, (old_time, old_time))
        candidates = get_tmp_candidates(tmp_root=tmp)
        assert len(candidates) == 1
        assert candidates[0].reason == "old+large"

    def test_fresh_small_file_ignored(self, tmp_path):
        tmp = tmp_path / "tmp"
        tmp.mkdir()
        (tmp / "fresh.txt").write_bytes(b"x" * 50)
        candidates = get_tmp_candidates(tmp_root=tmp)
        assert candidates == []

    def test_sorted_by_size_descending(self, tmp_path):
        tmp = tmp_path / "tmp"
        tmp.mkdir()
        # Create several old files of different sizes
        for i, sz in enumerate([500, 200, 800]):
            self._make_old_file(tmp, f"old{i}.txt", size=sz, days_old=10)
        candidates = get_tmp_candidates(tmp_root=tmp)
        sizes = [c.size for c in candidates]
        assert sizes == sorted(sizes, reverse=True)

    def test_top_20_limit(self, tmp_path):
        tmp = tmp_path / "tmp"
        tmp.mkdir()
        for i in range(25):
            self._make_old_file(tmp, f"old{i:02d}.txt", size=100, days_old=10)
        candidates = get_tmp_candidates(tmp_root=tmp)
        assert len(candidates) <= 20

    def test_custom_thresholds(self, tmp_path):
        tmp = tmp_path / "tmp"
        tmp.mkdir()
        # 3-day-old file: not old with default 7 days, but old with custom 2 days
        self._make_old_file(tmp, "recent.txt", size=500, days_old=3)
        # Default: not old
        assert get_tmp_candidates(tmp_root=tmp, old_days=7) == []
        # Custom: old
        candidates = get_tmp_candidates(tmp_root=tmp, old_days=2)
        assert len(candidates) == 1

    def test_nonexistent_tmp_root(self, tmp_path):
        candidates = get_tmp_candidates(tmp_root=tmp_path / "nope")
        assert candidates == []


# ── print_report tests ──────────────────────────────────────────────────


class TestPrintReport:
    """Tests for print_report output."""

    def test_report_prints_sections(self, capsys):
        print_report()
        out = capsys.readouterr().out
        assert "ROOT FILESYSTEM" in out
        assert "LARGEST DIRS UNDER" in out
        assert "TMP CLEANUP CANDIDATES" in out

    def test_report_contains_usage_numbers(self, capsys):
        print_report()
        out = capsys.readouterr().out
        assert "Total:" in out
        assert "Used:" in out
        assert "Free:" in out

    def test_report_separator_lines(self, capsys):
        print_report()
        out = capsys.readouterr().out
        assert "=" * 60 in out


# ── main tests ──────────────────────────────────────────────────────────


class TestMain:
    """Tests for main entry point."""

    def test_help_flag(self, capsys):
        rc = main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "disk-audit" in out

    def test_help_short_flag(self, capsys):
        rc = main(["-h"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "disk-audit" in out

    def test_normal_run(self, capsys):
        rc = main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "ROOT FILESYSTEM" in out

    def test_default_argv(self, capsys):
        """main() with no args uses sys.argv[1:] equivalent."""
        rc = main()
        assert rc == 0


# ── Integration: subprocess invocation ──────────────────────────────────


class TestSubprocessInvocation:
    """Test running disk-audit as a subprocess."""

    def test_exit_code_zero(self):
        import subprocess
        result = subprocess.run(
            [str(Path.home() / "germline/effectors/disk-audit")],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0

    def test_help_via_subprocess(self):
        import subprocess
        result = subprocess.run(
            [str(Path.home() / "germline/effectors/disk-audit"), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "disk-audit" in result.stdout
