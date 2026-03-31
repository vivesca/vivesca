"""Tests for gemmule-clean — temp/cache cleaner."""
from __future__ import annotations

import os
import time
from pathlib import Path

import pytest


def _load_module():
    """Load gemmule-clean by exec-ing its source."""
    source = Path("/home/terry/germline/effectors/gemmule-clean").read_text()
    ns: dict = {"__name__": "gemmule_clean_test"}
    exec(source, ns)
    return ns


_mod = _load_module()
clean_tmp_claude = _mod["clean_tmp_claude"]
clean_uv_archive = _mod["clean_uv_archive"]
clean_pycache = _mod["clean_pycache"]
_fmt_bytes = _mod["_fmt_bytes"]
_dir_size = _mod["_dir_size"]
_safe_path = _mod["_safe_path"]
TMP_CUTOFF = _mod["TMP_CUTOFF"]
UV_CACHE_CUTOFF = _mod["UV_CACHE_CUTOFF"]


# ── _fmt_bytes ─────────────────────────────────────────────────────────

def test_fmt_bytes_units():
    assert _fmt_bytes(0) == "0.0 B"
    assert _fmt_bytes(512) == "512.0 B"
    assert _fmt_bytes(1024) == "1.0 KB"
    assert _fmt_bytes(1024 * 1024) == "1.0 MB"
    assert _fmt_bytes(1024 ** 3) == "1.0 GB"


def test_fmt_bytes_fractional():
    assert _fmt_bytes(1536) == "1.5 KB"


# ── _dir_size ──────────────────────────────────────────────────────────

def test_dir_size_empty(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    assert _dir_size(d) == 0


def test_dir_size_with_files(tmp_path):
    d = tmp_path / "dir"
    d.mkdir()
    (d / "a.txt").write_bytes(b"hello")        # 5 bytes
    sub = d / "sub"
    sub.mkdir()
    (sub / "b.bin").write_bytes(b"x" * 100)    # 100 bytes
    assert _dir_size(d) == 105


def test_dir_size_missing_dir():
    assert _dir_size(Path("/no/such/path")) == 0


# ── _safe_path ─────────────────────────────────────────────────────────

def test_safe_path_allows_tmp(tmp_path):
    assert _safe_path(tmp_path / "claude-xyz", germline=tmp_path / "g", epigenome=tmp_path / "e")


def test_safe_path_blocks_germline_source(tmp_path):
    germline = tmp_path / "germline"
    src = germline / "effectors" / "foo.py"
    assert not _safe_path(src, germline=germline, epigenome=tmp_path / "e")


def test_safe_path_allows_pycache_in_germline(tmp_path):
    germline = tmp_path / "germline"
    pyc = germline / "effectors" / "__pycache__"
    assert _safe_path(pyc, germline=germline, epigenome=tmp_path / "e")


def test_safe_path_blocks_epigenome(tmp_path):
    epigenome = tmp_path / "epigenome"
    assert not _safe_path(epigenome / "some" / "file", germline=tmp_path / "g", epigenome=epigenome)


# ── clean_tmp_claude ──────────────────────────────────────────────────

def test_clean_tmp_claude_removes_old(tmp_path):
    """Entries older than 24h are removed."""
    now = time.time()
    old_dir = tmp_path / "claude-old"
    old_dir.mkdir()
    (old_dir / "file.txt").write_bytes(b"x" * 200)
    old_mtime = now - TMP_CUTOFF - 3600
    os.utime(old_dir, (old_mtime, old_mtime))

    freed = clean_tmp_claude(now, tmp_root=tmp_path)
    assert freed >= 200
    assert not old_dir.exists()


def test_clean_tmp_claude_keeps_recent(tmp_path):
    """Entries younger than 24h are kept."""
    now = time.time()
    recent_dir = tmp_path / "claude-recent"
    recent_dir.mkdir()
    (recent_dir / "file.txt").write_bytes(b"y" * 300)
    os.utime(recent_dir, (now - 3600, now - 3600))

    freed = clean_tmp_claude(now, tmp_root=tmp_path)
    assert freed == 0
    assert recent_dir.exists()


def test_clean_tmp_claude_ignores_non_claude(tmp_path):
    """Non claude-* entries are ignored."""
    now = time.time()
    other = tmp_path / "other-dir"
    other.mkdir()
    (other / "f").write_bytes(b"z" * 500)
    os.utime(other, (now - TMP_CUTOFF - 3600, now - TMP_CUTOFF - 3600))

    freed = clean_tmp_claude(now, tmp_root=tmp_path)
    assert freed == 0
    assert other.exists()


# ── clean_uv_archive ─────────────────────────────────────────────────

def test_clean_uv_archive_removes_old(tmp_path):
    now = time.time()
    uv_dir = tmp_path / ".cache" / "uv" / "archive-v0"
    uv_dir.mkdir(parents=True)
    old = uv_dir / "old-pkg"
    old.mkdir()
    (old / "data").write_bytes(b"a" * 1000)
    old_mtime = now - UV_CACHE_CUTOFF - 3600
    os.utime(old, (old_mtime, old_mtime))

    freed = clean_uv_archive(now, home=tmp_path)
    assert freed >= 1000
    assert not old.exists()


def test_clean_uv_archive_keeps_recent(tmp_path):
    now = time.time()
    uv_dir = tmp_path / ".cache" / "uv" / "archive-v0"
    uv_dir.mkdir(parents=True)
    recent = uv_dir / "new-pkg"
    recent.mkdir()
    (recent / "data").write_bytes(b"b" * 500)
    os.utime(recent, (now - 3600, now - 3600))

    freed = clean_uv_archive(now, home=tmp_path)
    assert freed == 0
    assert recent.exists()


def test_clean_uv_archive_no_dir(tmp_path):
    """Gracefully handles missing archive-v0."""
    freed = clean_uv_archive(time.time(), home=tmp_path)
    assert freed == 0


# ── clean_pycache ────────────────────────────────────────────────────

def test_clean_pycache_removes_dirs(tmp_path):
    germline = tmp_path / "germline"
    pc = germline / "effectors" / "__pycache__"
    pc.mkdir(parents=True)
    (pc / "foo.cpython-312.pyc").write_bytes(b"c" * 100)

    freed = clean_pycache(germline=germline, epigenome=tmp_path / "epi")
    assert freed >= 100
    assert not pc.exists()


def test_clean_pycache_skips_epigenome(tmp_path):
    """Does not touch __pycache__ under epigenome."""
    germline = tmp_path / "germline"
    epi = tmp_path / "epigenome"
    pc_germ = germline / "__pycache__"
    pc_germ.mkdir(parents=True)
    (pc_germ / "a.pyc").write_bytes(b"d" * 50)

    pc_epi = epi / "__pycache__"
    pc_epi.mkdir(parents=True)
    (pc_epi / "b.pyc").write_bytes(b"e" * 50)

    freed = clean_pycache(germline=germline, epigenome=epi)
    assert freed >= 50
    assert not pc_germ.exists()
    assert pc_epi.exists()


def test_clean_pycache_no_germline(tmp_path):
    """Gracefully handles missing germline dir."""
    freed = clean_pycache(germline=tmp_path / "nonexistent")
    assert freed == 0


# ── dry-run mode ──────────────────────────────────────────────────────

def test_dry_run_does_not_delete(tmp_path):
    """dry_run=True reports size but does not remove."""
    now = time.time()
    old_dir = tmp_path / "claude-old"
    old_dir.mkdir()
    (old_dir / "f.txt").write_bytes(b"x" * 200)
    old_mtime = now - TMP_CUTOFF - 3600
    os.utime(old_dir, (old_mtime, old_mtime))

    freed = clean_tmp_claude(now, dry_run=True, tmp_root=tmp_path)
    assert freed >= 200
    assert old_dir.exists()


# ── integration: main() ──────────────────────────────────────────────

def test_main_runs_without_error(capsys):
    """main() completes and prints summary."""
    _main = _mod["main"]
    _main(dry_run=True)
    captured = capsys.readouterr()
    assert "Total freed:" in captured.out
