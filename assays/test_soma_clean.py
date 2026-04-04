from __future__ import annotations

"""Tests for soma-clean — temp/cache cleaner effector."""

import os
import time
from pathlib import Path


def _load_module() -> dict:
    source = Path(str(Path.home() / "germline/effectors/soma-clean")).read_text()
    ns: dict = {"__name__": "soma_clean"}
    exec(source, ns)
    return ns


_mod = _load_module()
clean_tmp_claude = _mod["clean_tmp_claude"]
clean_uv_archive = _mod["clean_uv_archive"]
clean_pycache = _mod["clean_pycache"]
_fmt_bytes = _mod["_fmt_bytes"]
_dir_size = _mod["_dir_size"]
TMP_CUTOFF = _mod["TMP_CUTOFF"]
UV_CACHE_CUTOFF = _mod["UV_CACHE_CUTOFF"]


# ── helpers ──────────────────────────────────────────────


def _make_old_file(path: Path, age_seconds: float, size: int = 100) -> Path:
    """Create a file with given size and mtime set age_seconds in the past."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x00" * size)
    old_time = time.time() - age_seconds
    os.utime(path, (old_time, old_time))
    return path


def _make_old_dir(path: Path, age_seconds: float) -> Path:
    """Create a dir with mtime age_seconds ago and a 200-byte file inside."""
    path.mkdir(parents=True, exist_ok=True)
    (path / "data.bin").write_bytes(b"\x00" * 200)
    old_time = time.time() - age_seconds
    os.utime(path, (old_time, old_time))
    os.utime(path / "data.bin", (old_time, old_time))
    return path


NOW = time.time()


# ── _fmt_bytes ───────────────────────────────────────────


class TestFmtBytes:
    def test_bytes(self):
        assert _fmt_bytes(500) == "500.0 B"

    def test_kilobytes(self):
        assert _fmt_bytes(2048) == "2.0 KB"

    def test_megabytes(self):
        assert _fmt_bytes(2 * 1024 * 1024) == "2.0 MB"


# ── _dir_size ────────────────────────────────────────────


class TestDirSize:
    def test_empty_dir(self, tmp_path: Path):
        d = tmp_path / "empty"
        d.mkdir()
        assert _dir_size(d) == 0

    def test_dir_with_files(self, tmp_path: Path):
        d = tmp_path / "full"
        d.mkdir()
        (d / "a.bin").write_bytes(b"\x00" * 100)
        (d / "b.bin").write_bytes(b"\x00" * 50)
        assert _dir_size(d) == 150

    def test_nested(self, tmp_path: Path):
        d = tmp_path / "outer"
        inner = d / "inner"
        inner.mkdir(parents=True)
        (inner / "c.bin").write_bytes(b"\x00" * 200)
        assert _dir_size(d) == 200

    def test_nonexistent(self, tmp_path: Path):
        assert _dir_size(tmp_path / "nope") == 0


# ── clean_tmp_claude ─────────────────────────────────────


class TestCleanTmpClaude:
    def test_removes_old_claude_dir(self, tmp_path: Path):
        old = _make_old_dir(tmp_path / "claude-abc", age_seconds=TMP_CUTOFF + 3600)
        freed = clean_tmp_claude(NOW, tmp_root=tmp_path)
        assert freed >= 200
        assert not old.exists()

    def test_keeps_recent_claude_dir(self, tmp_path: Path):
        recent = _make_old_dir(tmp_path / "claude-new", age_seconds=TMP_CUTOFF - 3600)
        freed = clean_tmp_claude(NOW, tmp_root=tmp_path)
        assert freed == 0
        assert recent.exists()

    def test_ignores_non_claude_dirs(self, tmp_path: Path):
        _make_old_dir(tmp_path / "other-xyz", age_seconds=TMP_CUTOFF + 3600)
        freed = clean_tmp_claude(NOW, tmp_root=tmp_path)
        assert freed == 0
        assert (tmp_path / "other-xyz").exists()

    def test_nonexistent_root(self, tmp_path: Path):
        freed = clean_tmp_claude(NOW, tmp_root=tmp_path / "nope")
        assert freed == 0

    def test_dry_run_does_not_delete(self, tmp_path: Path):
        old = _make_old_dir(tmp_path / "claude-old", age_seconds=TMP_CUTOFF + 3600)
        freed = clean_tmp_claude(NOW, tmp_root=tmp_path, dry_run=True)
        assert freed >= 200
        assert old.exists()


# ── clean_uv_archive ─────────────────────────────────────


class TestCleanUvArchive:
    def _make_cache(self, tmp_path: Path) -> Path:
        """Return a fake home whose .cache/uv/archive-v0/ is usable."""
        return tmp_path

    def test_removes_old_dir_entry(self, tmp_path: Path):
        home = self._make_cache(tmp_path)
        archive = home / ".cache" / "uv" / "archive-v0"
        old = _make_old_dir(archive / "old-pkg", age_seconds=UV_CACHE_CUTOFF + 3600)
        freed = clean_uv_archive(NOW, home=home)
        assert freed >= 200
        assert not old.exists()

    def test_removes_old_file_entry(self, tmp_path: Path):
        home = self._make_cache(tmp_path)
        archive = home / ".cache" / "uv" / "archive-v0"
        _make_old_file(archive / "old-file.tar", age_seconds=UV_CACHE_CUTOFF + 3600, size=300)
        freed = clean_uv_archive(NOW, home=home)
        assert freed >= 300
        assert not (archive / "old-file.tar").exists()

    def test_keeps_recent_entry(self, tmp_path: Path):
        home = self._make_cache(tmp_path)
        archive = home / ".cache" / "uv" / "archive-v0"
        recent = _make_old_dir(archive / "new-pkg", age_seconds=UV_CACHE_CUTOFF - 3600)
        freed = clean_uv_archive(NOW, home=home)
        assert freed == 0
        assert recent.exists()

    def test_no_archive_dir(self, tmp_path: Path):
        freed = clean_uv_archive(NOW, home=tmp_path)
        assert freed == 0

    def test_dry_run_does_not_delete(self, tmp_path: Path):
        home = self._make_cache(tmp_path)
        archive = home / ".cache" / "uv" / "archive-v0"
        old = _make_old_dir(archive / "old-pkg", age_seconds=UV_CACHE_CUTOFF + 3600)
        freed = clean_uv_archive(NOW, home=home, dry_run=True)
        assert freed >= 200
        assert old.exists()


# ── clean_pycache ────────────────────────────────────────


class TestCleanPycache:
    def test_removes_pycache_dirs(self, tmp_path: Path):
        pyc = tmp_path / "sub" / "__pycache__"
        _make_old_dir(pyc, age_seconds=0)
        freed = clean_pycache(germline=tmp_path)
        assert freed >= 200
        assert not pyc.exists()

    def test_nested_pycache(self, tmp_path: Path):
        pyc1 = tmp_path / "a" / "__pycache__"
        pyc2 = tmp_path / "a" / "b" / "__pycache__"
        _make_old_dir(pyc1, age_seconds=0)
        _make_old_dir(pyc2, age_seconds=0)
        freed = clean_pycache(germline=tmp_path)
        assert freed >= 400
        assert not pyc1.exists()
        assert not pyc2.exists()

    def test_no_pycache(self, tmp_path: Path):
        freed = clean_pycache(germline=tmp_path)
        assert freed == 0

    def test_dry_run_does_not_delete(self, tmp_path: Path):
        pyc = tmp_path / "__pycache__"
        _make_old_dir(pyc, age_seconds=0)
        freed = clean_pycache(germline=tmp_path, dry_run=True)
        assert freed >= 200
        assert pyc.exists()

    def test_nonexistent_root(self, tmp_path: Path):
        freed = clean_pycache(germline=tmp_path / "nope")
        assert freed == 0
