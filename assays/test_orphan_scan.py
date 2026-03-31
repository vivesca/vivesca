"""Tests for orphan-scan — find .py files in metabolon/ not imported anywhere."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ORPHAN_SCAN_PATH = Path(__file__).resolve().parents[1] / "effectors" / "orphan-scan"


@pytest.fixture()
def ns():
    ns_dict: dict = {"__name__": "test_orphan_scan", "__file__": str(ORPHAN_SCAN_PATH)}
    source = ORPHAN_SCAN_PATH.read_text(encoding="utf-8")
    exec(source, ns_dict)
    return ns_dict


@pytest.fixture()
def fake_root(tmp_path: Path) -> Path:
    meta = tmp_path / "metabolon"
    meta.mkdir()
    (meta / "__init__.py").write_text("")
    return tmp_path


def _write(path: Path, content: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# ── Basics ─────────────────────────────────────────────────────────────────


class TestBasics:
    def test_file_exists(self):
        assert ORPHAN_SCAN_PATH.exists()

    def test_is_python(self):
        assert ORPHAN_SCAN_PATH.read_text().startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        assert '"""' in ORPHAN_SCAN_PATH.read_text()


# ── module_path ────────────────────────────────────────────────────────────


class TestModulePath:
    def test_simple(self, ns, fake_root):
        assert ns["module_path"](fake_root / "metabolon" / "alpha.py", fake_root) == "metabolon.alpha"

    def test_nested(self, ns, fake_root):
        assert ns["module_path"](fake_root / "metabolon" / "org" / "nuc.py", fake_root) == "metabolon.org.nuc"


# ── collect_metabolon_modules ──────────────────────────────────────────────


class TestCollectModules:
    def test_finds_py(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        _write(fake_root / "metabolon" / "beta.py")
        assert ns["collect_metabolon_modules"](fake_root / "metabolon") == {"metabolon.alpha", "metabolon.beta"}

    def test_excludes_init(self, ns, fake_root):
        _write(fake_root / "metabolon" / "__init__.py")
        _write(fake_root / "metabolon" / "real.py")
        mods = ns["collect_metabolon_modules"](fake_root / "metabolon")
        assert "metabolon" not in mods
        assert "metabolon.real" in mods

    def test_excludes_test_and_conftest(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        _write(fake_root / "metabolon" / "test_alpha.py")
        _write(fake_root / "metabolon" / "conftest.py")
        mods = ns["collect_metabolon_modules"](fake_root / "metabolon")
        assert mods == {"metabolon.alpha"}

    def test_nested(self, ns, fake_root):
        _write(fake_root / "metabolon" / "org" / "nuc.py")
        _write(fake_root / "metabolon" / "org" / "__init__.py")
        mods = ns["collect_metabolon_modules"](fake_root / "metabolon")
        assert "metabolon.org.nuc" in mods
        assert "metabolon.org" not in mods

    def test_empty(self, ns, fake_root):
        assert ns["collect_metabolon_modules"](fake_root / "metabolon") == set()


# ── extract_imports_from_file ──────────────────────────────────────────────


class TestExtractImports:
    def test_from_import(self, ns, fake_root):
        p = _write(fake_root / "c.py", "from metabolon.alpha import something\n")
        idx = ns["extract_imports_from_file"](p)
        assert "metabolon.alpha" in idx
        assert "something" in idx

    def test_plain_import(self, ns, fake_root):
        p = _write(fake_root / "c.py", "import metabolon.org.nuc\n")
        assert "metabolon.org.nuc" in ns["extract_imports_from_file"](p)

    def test_parent_packages(self, ns, fake_root):
        p = _write(fake_root / "c.py", "from metabolon.org import crispr\n")
        idx = ns["extract_imports_from_file"](p)
        assert "metabolon" in idx
        assert "metabolon.org" in idx
        assert "crispr" in idx

    def test_ignores_comments(self, ns, fake_root):
        p = _write(fake_root / "c.py", "# from metabolon.alpha import x\n")
        assert "metabolon.alpha" not in ns["extract_imports_from_file"](p)

    def test_syntax_error_returns_empty(self, ns, fake_root):
        p = _write(fake_root / "bad.py", "def foo(:\n")
        assert ns["extract_imports_from_file"](p) == set()

    def test_missing_file(self, ns, tmp_path):
        assert ns["extract_imports_from_file"](tmp_path / "nope.py") == set()

    def test_multiple(self, ns, fake_root):
        p = _write(fake_root / "c.py", "from a import x\nimport os\nfrom b import y\n")
        idx = ns["extract_imports_from_file"](p)
        assert "a" in idx and "b" in idx and "os" in idx


# ── find_orphans ───────────────────────────────────────────────────────────


class TestFindOrphans:
    def test_no_orphans_when_imported(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        _write(fake_root / "main.py", "from metabolon.alpha import run\n")
        assert ns["find_orphans"](fake_root) == []

    def test_detects_orphan(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        _write(fake_root / "metabolon" / "orphan.py")
        _write(fake_root / "main.py", "from metabolon.alpha import run\n")
        mods = [o["module"] for o in ns["find_orphans"](fake_root)]
        assert "metabolon.orphan" in mods
        assert "metabolon.alpha" not in mods

    def test_from_pkg_import_matches_leaf(self, ns, fake_root):
        _write(fake_root / "metabolon" / "org" / "__init__.py")
        _write(fake_root / "metabolon" / "org" / "nuc.py")
        _write(fake_root / "main.py", "from metabolon.org import nuc\n")
        mods = [o["module"] for o in ns["find_orphans"](fake_root)]
        assert "metabolon.org.nuc" not in mods

    def test_missing_dir(self, ns, tmp_path):
        assert ns["find_orphans"](tmp_path) == []

    def test_all_orphans(self, ns, fake_root):
        _write(fake_root / "metabolon" / "a.py")
        _write(fake_root / "metabolon" / "b.py")
        assert len(ns["find_orphans"](fake_root)) == 2

    def test_dict_keys(self, ns, fake_root):
        _write(fake_root / "metabolon" / "lonely.py")
        o = ns["find_orphans"](fake_root)[0]
        assert set(o.keys()) == {"module", "path", "is_entry_point"}

    def test_entry_point_flagged(self, ns, fake_root):
        _write(fake_root / "metabolon" / "pkg" / "__main__.py")
        orphans = ns["find_orphans"](fake_root)
        ep = [o for o in orphans if o["is_entry_point"]]
        assert len(ep) == 1
        assert ep[0]["module"] == "metabolon.pkg.__main__"


# ── format_report ──────────────────────────────────────────────────────────


class TestFormatReport:
    def test_human_no_orphans(self, ns):
        assert "No orphan modules found" in ns["format_report"]([], use_json=False)

    def test_human_with_orphans(self, ns):
        orphans = [{"module": "m.alpha", "path": "metabolon/alpha.py", "is_entry_point": False}]
        r = ns["format_report"](orphans, use_json=False)
        assert "metabolon/alpha.py" in r
        assert "1 orphans" in r

    def test_human_entry_points(self, ns):
        orphans = [
            {"module": "m.lonely", "path": "m/lonely.py", "is_entry_point": False},
            {"module": "m.__main__", "path": "m/__main__.py", "is_entry_point": True},
        ]
        r = ns["format_report"](orphans, use_json=False)
        assert "Entry points" in r
        assert "1 orphans, 1 entry points" in r

    def test_json_list(self, ns):
        orphans = [{"module": "m.a", "path": "m/a.py", "is_entry_point": False}]
        data = json.loads(ns["format_report"](orphans, use_json=True))
        assert isinstance(data, list)
        assert data[0]["module"] == "m.a"

    def test_json_empty(self, ns):
        data = json.loads(ns["format_report"]([], use_json=True))
        assert data == []


# ── main ───────────────────────────────────────────────────────────────────


class TestMain:
    def test_returns_zero(self, ns, fake_root, capsys):
        assert ns["main"](["--path", str(fake_root)]) == 0

    def test_json_flag(self, ns, fake_root, capsys):
        _write(fake_root / "metabolon" / "alpha.py")
        ns["main"](["--path", str(fake_root), "--json"])
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)

    def test_no_args(self, ns, capsys):
        assert ns["main"]([]) == 0


# ── CLI subprocess ─────────────────────────────────────────────────────────


class TestCLI:
    def test_runs(self):
        r = subprocess.run([sys.executable, str(ORPHAN_SCAN_PATH)], capture_output=True, text=True, timeout=60)
        assert r.returncode == 0
        assert r.stdout.strip()

    def test_json_valid(self):
        r = subprocess.run([sys.executable, str(ORPHAN_SCAN_PATH), "--json"], capture_output=True, text=True, timeout=60)
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert isinstance(data, list)
        for e in data:
            assert "module" in e and "path" in e and "is_entry_point" in e
