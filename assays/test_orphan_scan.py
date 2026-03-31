"""Tests for orphan-scan effector — find unimported metabolon .py files."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest


def _load_orphan_scan():
    """Load orphan-scan by exec-ing its source (effector pattern)."""
    source = Path("/home/terry/germline/effectors/orphan-scan").read_text()
    ns: dict = {"__name__": "orphan_scan"}
    exec(source, ns)
    return ns


_mod = _load_orphan_scan()
module_path = _mod["module_path"]
collect_metabolon_modules = _mod["collect_metabolon_modules"]
extract_imports_from_file = _mod["extract_imports_from_file"]
find_orphans = _mod["find_orphans"]
format_report = _mod["format_report"]


# ── module_path tests ────────────────────────────────────────────────────


def test_module_path_simple():
    """module_path converts a simple .py file to dotted path."""
    p = Path("/fake/metabolon/locus.py")
    assert module_path(p, Path("/fake")) == "metabolon.locus"


def test_module_path_nested():
    """module_path handles nested package files."""
    p = Path("/fake/metabolon/organelles/chromatin.py")
    assert module_path(p, Path("/fake")) == "metabolon.organelles.chromatin"


def test_module_path_init():
    """module_path strips __init__ suffix."""
    p = Path("/fake/metabolon/organelles/__init__.py")
    assert module_path(p, Path("/fake")) == "metabolon.organelles"


# ── collect_metabolon_modules tests ──────────────────────────────────────


def test_collect_excludes_init(tmp_path):
    """collect_metabolon_modules excludes __init__.py."""
    met = tmp_path / "metabolon"
    met.mkdir()
    (met / "__init__.py").write_text("")
    (met / "locus.py").write_text("x = 1\n")
    modules = collect_metabolon_modules(met)
    assert "metabolon.locus" in modules
    assert "metabolon.__init__" not in modules


def test_collect_excludes_test_files(tmp_path):
    """collect_metabolon_modules excludes test_*.py files."""
    met = tmp_path / "metabolon"
    met.mkdir()
    (met / "foo.py").write_text("x = 1\n")
    (met / "test_foo.py").write_text("def test_foo(): pass\n")
    modules = collect_metabolon_modules(met)
    assert "metabolon.foo" in modules
    assert "metabolon.test_foo" not in modules


def test_collect_nested(tmp_path):
    """collect_metabolon_modules finds nested subpackages."""
    met = tmp_path / "metabolon"
    enzymes = met / "enzymes"
    enzymes.mkdir(parents=True)
    (enzymes / "assay.py").write_text("x = 1\n")
    modules = collect_metabolon_modules(met)
    assert "metabolon.enzymes.assay" in modules


# ── extract_imports_from_file tests ──────────────────────────────────────


def test_extract_imports_simple(tmp_path):
    """extract_imports_from_file finds plain imports."""
    f = tmp_path / "a.py"
    f.write_text("import os\nimport json\n")
    imports = extract_imports_from_file(f)
    assert "os" in imports
    assert "json" in imports


def test_extract_imports_from(tmp_path):
    """extract_imports_from_file finds from-imports and parent packages."""
    f = tmp_path / "b.py"
    f.write_text("from metabolon.locus import meal_plan\n")
    imports = extract_imports_from_file(f)
    assert "metabolon.locus" in imports
    assert "metabolon" in imports


def test_extract_imports_syntax_error(tmp_path):
    """extract_imports_from_file returns empty on syntax error."""
    f = tmp_path / "bad.py"
    f.write_text("def broken(\n")
    imports = extract_imports_from_file(f)
    assert imports == set()


# ── find_orphans tests ───────────────────────────────────────────────────


def _make_project(tmp_path: Path, *, imported: list[str] | None = None,
                   orphaned: list[str] | None = None) -> Path:
    """Create a fake project tree with metabolon/ modules and a consumer file."""
    met = tmp_path / "metabolon"
    met.mkdir()

    all_modules = (imported or []) + (orphaned or [])
    for mod in all_modules:
        parts = mod.split(".")
        # e.g. "metabolon.enzymes.assay" => ["metabolon", "enzymes", "assay"]
        # First parts are dirs, last is the .py file
        if len(parts) > 1:
            dirs = met / "/".join(parts[1:-1])
            dirs.mkdir(parents=True, exist_ok=True)
            (dirs / (parts[-1] + ".py")).write_text("x = 1\n")
        else:
            (met / (parts[0] + ".py")).write_text("x = 1\n")

    # Create a consumer file that imports the "imported" modules
    if imported:
        consumer = tmp_path / "consumer.py"
        lines = [f"import {mod}" for mod in imported]
        consumer.write_text("\n".join(lines) + "\n")

    return tmp_path


def test_find_orphans_detects_unused(tmp_path):
    """find_orphans reports modules not imported anywhere."""
    root = _make_project(tmp_path,
                         imported=["metabolon.locus"],
                         orphaned=["metabolon.ghost"])
    orphans = find_orphans(root)
    modules = [o["module"] for o in orphans]
    assert "metabolon.locus" not in modules
    assert "metabolon.ghost" in modules


def test_find_orphans_empty_metabolon(tmp_path):
    """find_orphans returns empty when metabolon/ has no .py files."""
    met = tmp_path / "metabolon"
    met.mkdir()
    assert find_orphans(tmp_path) == []


def test_find_orphans_all_imported(tmp_path):
    """find_orphans returns empty when everything is imported."""
    root = _make_project(tmp_path,
                         imported=["metabolon.alpha", "metabolon.beta"],
                         orphaned=[])
    orphans = find_orphans(root)
    assert orphans == []


def test_find_orphans_from_import(tmp_path):
    """find_orphans recognizes from-imports as usage."""
    met = tmp_path / "metabolon"
    met.mkdir()
    (met / "used.py").write_text("x = 1\n")
    consumer = tmp_path / "main.py"
    consumer.write_text("from metabolon.used import x\n")
    orphans = find_orphans(tmp_path)
    modules = [o["module"] for o in orphans]
    assert "metabolon.used" not in modules


def test_find_orphans_marks_entry_points(tmp_path):
    """find_orphans marks __main__.py as entry points."""
    met = tmp_path / "metabolon"
    met.mkdir()
    (met / "__main__.py").write_text("print('hello')\n")
    orphans = find_orphans(tmp_path)
    assert len(orphans) == 1
    assert orphans[0]["is_entry_point"] is True
    assert orphans[0]["module"] == "metabolon.__main__"


# ── format_report tests ──────────────────────────────────────────────────


def test_format_report_empty():
    """format_report shows success when no orphans."""
    out = format_report([])
    assert "No orphan modules found" in out


def test_format_report_json():
    """format_report --json produces valid JSON."""
    data = [{"module": "metabolon.ghost", "path": "metabolon/ghost.py",
             "is_entry_point": False}]
    out = format_report(data, use_json=True)
    parsed = json.loads(out)
    assert len(parsed) == 1
    assert parsed[0]["module"] == "metabolon.ghost"


def test_format_report_groups_entry_points():
    """format_report separates orphans from entry points."""
    data = [
        {"module": "metabolon.ghost", "path": "metabolon/ghost.py",
         "is_entry_point": False},
        {"module": "metabolon.__main__", "path": "metabolon/__main__.py",
         "is_entry_point": True},
    ]
    out = format_report(data)
    assert "Orphans (never imported)" in out
    assert "Entry points (not imported by design)" in out
    assert "1 orphans, 1 entry points" in out


# ── Integration: run against real metabolon ─────────────────────────────


def test_real_metabolon_scan():
    """Sanity check: orphan-scan runs against the real metabolon tree."""
    root = Path("/home/terry/germline")
    orphans = find_orphans(root)
    # Should return a list (may be empty, may have entries, but must not crash)
    assert isinstance(orphans, list)
    for o in orphans:
        assert "module" in o
        assert "path" in o
        assert "is_entry_point" in o
