"""Tests for gemmule-clean -- removes stale temp/cache files."""
from __future__ import annotations

import os
import time

import pytest


def _load_gemmule_clean():
    """Load gemmule-clean by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/gemmule-clean").read()
    ns: dict = {"__name__": "gemmule_clean"}
    exec(source, ns)
    return ns


_mod = _load_gemmule_clean()
clean_tmp_claude = _mod["clean_tmp_claude"]
clean_uv_archive = _mod["clean_uv_archive"]
clean_pycache = _mod["clean_pycache"]
_format_bytes = _mod["_format_bytes"]
_dir_size = _mod["_dir_size"]
run = _mod["run"]


# -- _dir_size tests ---------------------------------------------------------


def test_dir_size_empty(tmp_path):
    """_dir_size returns 0 for empty directory."""
    assert _dir_size(tmp_path) == 0


def test_dir_size_with_files(tmp_path):
    """_dir_size sums file sizes."""
    (tmp_path / "a.txt").write_bytes(b"x" * 100)
    (tmp_path / "b.txt").write_bytes(b"y" * 50)
    assert _dir_size(tmp_path) == 150


def test_dir_size_nested(tmp_path):
    """_dir_size sums across nested directories."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "top.txt").write_bytes(b"x" * 10)
    (sub / "deep.txt").write_bytes(b"y" * 20)
    assert _dir_size(tmp_path) == 30


# -- _format_bytes tests -----------------------------------------------------


def test_format_bytes_units():
    """_format_bytes uses correct units."""
    assert _format_bytes(0) == "0 B"
    assert _format_bytes(512) == "512 B"
    assert _format_bytes(1024) == "1.0 KB"
    assert _format_bytes(1024 * 1024) == "1.0 MB"
    assert _format_bytes(1024 * 1024 * 1024) == "1.0 GB"


# -- clean_tmp_claude tests --------------------------------------------------


def test_clean_tmp_claude_removes_old(tmp_path):
    """clean_tmp_claude removes dirs older than 24h."""
    old_dir = tmp_path / "claude-old"
    old_dir.mkdir()
    (old_dir / "file.txt").write_bytes(b"x" * 100)
    old_time = time.time() - 90001
    os.utime(old_dir, (old_time, old_time))

    freed = clean_tmp_claude(tmp_dir=tmp_path, max_age=86400)

    assert not old_dir.exists()
    assert freed >= 100


def test_clean_tmp_claude_keeps_new(tmp_path):
    """clean_tmp_claude keeps dirs newer than 24h."""
    new_dir = tmp_path / "claude-new"
    new_dir.mkdir()
    (new_dir / "file.txt").write_bytes(b"x" * 100)

    freed = clean_tmp_claude(tmp_dir=tmp_path, max_age=86400)

    assert new_dir.exists()
    assert freed == 0


def test_clean_tmp_claude_ignores_non_claude(tmp_path):
    """clean_tmp_claude ignores non-claude-* dirs."""
    other_dir = tmp_path / "other-dir"
    other_dir.mkdir()
    old_time = time.time() - 100000
    os.utime(other_dir, (old_time, old_time))

    freed = clean_tmp_claude(tmp_dir=tmp_path, max_age=86400)

    assert other_dir.exists()
    assert freed == 0


def test_clean_tmp_claude_mixed(tmp_path):
    """clean_tmp_claude removes old, keeps new claude dirs."""
    old = tmp_path / "claude-old"
    old.mkdir()
    old_time = time.time() - 100000
    os.utime(old, (old_time, old_time))

    new = tmp_path / "claude-new"
    new.mkdir()

    freed = clean_tmp_claude(tmp_dir=tmp_path, max_age=86400)

    assert not old.exists()
    assert new.exists()


def test_clean_tmp_claude_skips_files(tmp_path):
    """clean_tmp_claude skips claude-* files (only removes dirs)."""
    old_file = tmp_path / "claude-file.txt"
    old_file.write_bytes(b"x" * 50)
    old_time = time.time() - 100000
    os.utime(old_file, (old_time, old_time))

    freed = clean_tmp_claude(tmp_dir=tmp_path, max_age=86400)

    assert old_file.exists()
    assert freed == 0


# -- clean_uv_archive tests --------------------------------------------------


def test_clean_uv_archive_removes_old_dir(tmp_path):
    """clean_uv_archive removes old directory entries."""
    old_entry = tmp_path / "old-pkg"
    old_entry.mkdir()
    (old_entry / "data").write_bytes(b"x" * 200)
    old_time = time.time() - 604801
    os.utime(old_entry, (old_time, old_time))

    freed = clean_uv_archive(archive_dir=tmp_path, max_age=604800)

    assert not old_entry.exists()
    assert freed >= 200


def test_clean_uv_archive_keeps_new(tmp_path):
    """clean_uv_archive keeps entries newer than 7d."""
    new_entry = tmp_path / "new-pkg"
    new_entry.mkdir()
    (new_entry / "data").write_bytes(b"x" * 200)

    freed = clean_uv_archive(archive_dir=tmp_path, max_age=604800)

    assert new_entry.exists()
    assert freed == 0


def test_clean_uv_archive_removes_old_files(tmp_path):
    """clean_uv_archive removes old regular files too."""
    old_file = tmp_path / "old-file.tar"
    old_file.write_bytes(b"x" * 300)
    old_time = time.time() - 700000
    os.utime(old_file, (old_time, old_time))

    freed = clean_uv_archive(archive_dir=tmp_path, max_age=604800)

    assert not old_file.exists()
    assert freed >= 300


def test_clean_uv_archive_nonexistent(tmp_path):
    """clean_uv_archive returns 0 for nonexistent directory."""
    missing = tmp_path / "no-such-dir"
    freed = clean_uv_archive(archive_dir=missing, max_age=604800)
    assert freed == 0


def test_clean_uv_archive_mixed(tmp_path):
    """clean_uv_archive removes old entries, keeps new ones."""
    old = tmp_path / "pkg-old"
    old.mkdir()
    old_time = time.time() - 700000
    os.utime(old, (old_time, old_time))

    new = tmp_path / "pkg-new"
    new.mkdir()

    freed = clean_uv_archive(archive_dir=tmp_path, max_age=604800)

    assert not old.exists()
    assert new.exists()


# -- clean_pycache tests -----------------------------------------------------


def test_clean_pycache_removes_dirs(tmp_path):
    """clean_pycache removes __pycache__ dirs."""
    pc = tmp_path / "__pycache__"
    pc.mkdir()
    (pc / "module.cpython-312.pyc").write_bytes(b"x" * 50)

    freed = clean_pycache(germline_dir=tmp_path)

    assert not pc.exists()
    assert freed >= 50


def test_clean_pycache_nested(tmp_path):
    """clean_pycache finds __pycache__ in subdirectories."""
    sub = tmp_path / "metabolon" / "organelles"
    sub.mkdir(parents=True)
    pc = sub / "__pycache__"
    pc.mkdir()
    (pc / "foo.pyc").write_bytes(b"x" * 30)

    freed = clean_pycache(germline_dir=tmp_path)

    assert not pc.exists()
    assert freed >= 30


def test_clean_pycache_no_cache_dirs(tmp_path):
    """clean_pycache returns 0 when no __pycache__ dirs exist."""
    (tmp_path / "assays").mkdir()
    (tmp_path / "effectors").mkdir()

    freed = clean_pycache(germline_dir=tmp_path)
    assert freed == 0


def test_clean_pycache_nonexistent(tmp_path):
    """clean_pycache returns 0 for nonexistent directory."""
    missing = tmp_path / "no-such-dir"
    freed = clean_pycache(germline_dir=missing)
    assert freed == 0


def test_clean_pycache_multiple(tmp_path):
    """clean_pycache removes multiple __pycache__ dirs at different depths."""
    pc1 = tmp_path / "__pycache__"
    pc1.mkdir()
    (pc1 / "a.pyc").write_bytes(b"x" * 10)

    sub = tmp_path / "assays"
    sub.mkdir()
    pc2 = sub / "__pycache__"
    pc2.mkdir()
    (pc2 / "b.pyc").write_bytes(b"x" * 20)

    freed = clean_pycache(germline_dir=tmp_path)

    assert not pc1.exists()
    assert not pc2.exists()
    assert freed >= 30


# -- run (integration) tests -------------------------------------------------


def test_run_prints_report(tmp_path, capsys):
    """run() prints a cleanup report with total freed."""
    pc = tmp_path / "__pycache__"
    pc.mkdir()
    (pc / "x.pyc").write_bytes(b"x" * 40)

    orig_tmp = _mod["TMP_DIR"]
    orig_uv = _mod["UV_ARCHIVE_DIR"]
    orig_germ = _mod["GERMLINE_DIR"]
    try:
        _mod["TMP_DIR"] = tmp_path
        _mod["UV_ARCHIVE_DIR"] = tmp_path / "no-uv-cache"
        _mod["GERMLINE_DIR"] = tmp_path
        rc = run()
    finally:
        _mod["TMP_DIR"] = orig_tmp
        _mod["UV_ARCHIVE_DIR"] = orig_uv
        _mod["GERMLINE_DIR"] = orig_germ

    assert rc == 0
    out = capsys.readouterr().out
    assert "gemmule-clean report:" in out
    assert "Total freed:" in out
    assert "/tmp/claude-*/" in out
    assert "~/.cache/uv/archive-v0/" in out
    assert "~/germline/__pycache__" in out


def test_run_handles_empty_dirs(tmp_path, capsys):
    """run() works when all target directories are missing."""
    orig_tmp = _mod["TMP_DIR"]
    orig_uv = _mod["UV_ARCHIVE_DIR"]
    orig_germ = _mod["GERMLINE_DIR"]
    try:
        _mod["TMP_DIR"] = tmp_path / "no-tmp"
        _mod["UV_ARCHIVE_DIR"] = tmp_path / "no-uv"
        _mod["GERMLINE_DIR"] = tmp_path / "no-germ"
        rc = run()
    finally:
        _mod["TMP_DIR"] = orig_tmp
        _mod["UV_ARCHIVE_DIR"] = orig_uv
        _mod["GERMLINE_DIR"] = orig_germ

    assert rc == 0
    out = capsys.readouterr().out
    assert "Total freed: 0 B" in out
