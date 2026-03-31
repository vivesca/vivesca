"""Tests for orphan-scan — find .py files in metabolon/ not imported anywhere."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest


def _load_effector():
    """Load orphan-scan by exec-ing its source."""
    source = open(Path.home() / "germline" / "effectors" / "orphan-scan").read()
    ns: dict = {"__name__": "orphan_scan"}
    exec(source, ns)
    return ns


_mod = _load_effector()
module_path = _mod["module_path"]
collect_metabolon_modules = _mod["collect_metabolon_modules"]
extract_imports_from_file = _mod["extract_imports_from_file"]
find_orphans = _mod["find_orphans"]
format_report = _mod["format_report"]
main = _mod["main"]


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture()
def fake_root(tmp_path: Path) -> Path:
    """Create a minimal fake germline tree for testing."""
    meta = tmp_path / "metabolon"
    meta.mkdir()
    (meta / "__init__.py").write_text("")
    return tmp_path


def _write_file(path: Path, content: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# ── module_path ───────────────────────────────────────────────────────


class TestModulePath:
    def test_simple_module(self, fake_root: Path):
        p = fake_root / "metabolon" / "alpha.py"
        assert module_path(p, fake_root) == "metabolon.alpha"

    def test_nested_module(self, fake_root: Path):
        p = fake_root / "metabolon" / "organelles" / "nucleus.py"
        assert module_path(p, fake_root) == "metabolon.organelles.nucleus"

    def test_deeply_nested(self, fake_root: Path):
        p = fake_root / "metabolon" / "a" / "b" / "c.py"
        assert module_path(p, fake_root) == "metabolon.a.b.c"


# ── collect_metabolon_modules ────────────────────────────────────────


class TestCollectMetabolonModules:
    def test_finds_py_files(self, fake_root: Path):
        _write_file(fake_root / "metabolon" / "alpha.py")
        _write_file(fake_root / "metabolon" / "beta.py")
        modules = collect_metabolon_modules(fake_root / "metabolon")
        assert "metabolon.alpha" in modules
        assert "metabolon.beta" in modules

    def test_excludes_init(self, fake_root: Path):
        _write_file(fake_root / "metabolon" / "__init__.py", "# init")
        _write_file(fake_root / "metabolon" / "real.py")
        modules = collect_metabolon_modules(fake_root / "metabolon")
        assert "metabolon" not in modules  # __init__ -> "metabolon"
        assert "metabolon.real" in modules

    def test_excludes_test_files(self, fake_root: Path):
        _write_file(fake_root / "metabolon" / "test_foo.py")
        _write_file(fake_root / "metabolon" / "real.py")
        modules = collect_metabolon_modules(fake_root / "metabolon")
        assert "metabolon.test_foo" not in modules
        assert "metabolon.real" in modules

    def test_nested_subdirs(self, fake_root: Path):
        _write_file(fake_root / "metabolon" / "organelles" / "nucleus.py")
        _write_file(fake_root / "metabolon" / "organelles" / "__init__.py")
        modules = collect_metabolon_modules(fake_root / "metabolon")
        assert "metabolon.organelles.nucleus" in modules

    def test_empty_dir(self, fake_root: Path):
        modules = collect_metabolon_modules(fake_root / "metabolon")
        assert modules == set()


# ── extract_imports_from_file ────────────────────────────────────────


class TestExtractImports:
    def test_captures_from_import(self, fake_root: Path):
        p = _write_file(
            fake_root / "consumer.py",
            "from metabolon.alpha import something\n",
        )
        idx = extract_imports_from_file(p)
        assert "metabolon.alpha" in idx
        assert "something" in idx
        assert "metabolon.alpha.something" in idx

    def test_captures_plain_import(self, fake_root: Path):
        p = _write_file(
            fake_root / "consumer.py",
            "import metabolon.organelles.nucleus\n",
        )
        idx = extract_imports_from_file(p)
        assert "metabolon.organelles.nucleus" in idx

    def test_ignores_comments(self, fake_root: Path):
        p = _write_file(
            fake_root / "consumer.py",
            "# from metabolon.alpha import something\n",
        )
        idx = extract_imports_from_file(p)
        assert "metabolon.alpha" not in idx

    def test_handles_multiple_imports(self, fake_root: Path):
        p = _write_file(
            fake_root / "consumer.py",
            textwrap.dedent("""\
                from metabolon.alpha import foo
                from metabolon.beta import bar
                import os
            """),
        )
        idx = extract_imports_from_file(p)
        assert "metabolon.alpha" in idx
        assert "metabolon.beta" in idx
        assert "os" in idx

    def test_syntax_error_returns_empty(self, fake_root: Path):
        p = _write_file(fake_root / "bad.py", "def broken(:\n")
        idx = extract_imports_from_file(p)
        assert idx == set()


# ── find_orphans ─────────────────────────────────────────────────────


class TestFindOrphans:
    def test_no_orphans_when_imported(self, fake_root: Path):
        _write_file(fake_root / "metabolon" / "alpha.py")
        _write_file(
            fake_root / "main.py",
            "from metabolon.alpha import run\n",
        )
        orphans = find_orphans(fake_root)
        assert orphans == []

    def test_detects_orphan(self, fake_root: Path):
        _write_file(fake_root / "metabolon" / "alpha.py")
        _write_file(fake_root / "metabolon" / "orphan.py")
        _write_file(
            fake_root / "main.py",
            "from metabolon.alpha import run\n",
        )
        orphans = find_orphans(fake_root)
        modules = [o["module"] for o in orphans]
        assert "metabolon.orphan" in modules
        assert "metabolon.alpha" not in modules

    def test_entry_point_flagged(self, fake_root: Path):
        """__main__.py IS reported but marked as an entry point."""
        _write_file(fake_root / "metabolon" / "sortase" / "__main__.py")
        orphans = find_orphans(fake_root)
        modules = [o["module"] for o in orphans]
        assert "metabolon.sortase.__main__" in modules
        ep = [o for o in orphans if o["module"] == "metabolon.sortase.__main__"]
        assert ep[0]["is_entry_point"] is True

    def test_from_pkg_import_name(self, fake_root: Path):
        """``from metabolon.organelles import nucleus`` should count."""
        _write_file(fake_root / "metabolon" / "organelles" / "__init__.py")
        _write_file(fake_root / "metabolon" / "organelles" / "nucleus.py")
        _write_file(
            fake_root / "main.py",
            "from metabolon.organelles import nucleus\n",
        )
        orphans = find_orphans(fake_root)
        modules = [o["module"] for o in orphans]
        assert "metabolon.organelles.nucleus" not in modules

    def test_missing_metabolon_dir(self, tmp_path: Path):
        orphans = find_orphans(tmp_path)
        assert orphans == []

    def test_all_orphans(self, fake_root: Path):
        """Everything is an orphan when nothing is imported."""
        _write_file(fake_root / "metabolon" / "alpha.py")
        _write_file(fake_root / "metabolon" / "beta.py")
        orphans = find_orphans(fake_root)
        assert len(orphans) == 2

    def test_self_import_counts(self, fake_root: Path):
        """A file importing itself counts as referenced."""
        _write_file(
            fake_root / "metabolon" / "lonely.py",
            "from metabolon.lonely import self_ref\n",
        )
        orphans = find_orphans(fake_root)
        modules = [o["module"] for o in orphans]
        assert "metabolon.lonely" not in modules


# ── format_report ────────────────────────────────────────────────────


class TestFormatReport:
    def test_human_no_orphans(self):
        report = format_report([], use_json=False)
        assert "No orphan modules found" in report

    def test_human_with_orphans(self):
        orphans = [
            {"path": "metabolon/alpha.py", "module": "metabolon.alpha",
             "is_entry_point": False},
        ]
        report = format_report(orphans, use_json=False)
        assert "metabolon/alpha.py" in report
        assert "Orphans" in report

    def test_human_entry_points_section(self):
        orphans = [
            {"path": "metabolon/foo/__main__.py",
             "module": "metabolon.foo.__main__",
             "is_entry_point": True},
        ]
        report = format_report(orphans, use_json=False)
        assert "Entry points" in report

    def test_json_structure(self):
        orphans = [
            {"path": "metabolon/alpha.py", "module": "metabolon.alpha",
             "is_entry_point": False},
        ]
        out = format_report(orphans, use_json=True)
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["module"] == "metabolon.alpha"

    def test_json_empty(self):
        out = format_report([], use_json=True)
        data = json.loads(out)
        assert data == []


# ── main() integration ───────────────────────────────────────────────


class TestMain:
    def test_main_returns_zero(self, fake_root: Path, capsys):
        rc = main(["--path", str(fake_root)])
        assert rc == 0

    def test_main_json_flag(self, fake_root: Path, capsys):
        _write_file(fake_root / "metabolon" / "alpha.py")
        rc = main(["--path", str(fake_root), "--json"])
        assert rc == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert isinstance(data, list)

    def test_main_human_readable(self, fake_root: Path, capsys):
        _write_file(fake_root / "metabolon" / "alpha.py")
        rc = main(["--path", str(fake_root)])
        assert rc == 0
        output = capsys.readouterr().out
        assert "metabolon" in output
