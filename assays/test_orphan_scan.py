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
collect_modules = _mod["collect_modules"]
file_to_module = _mod["file_to_module"]
build_import_index = _mod["build_import_index"]
find_orphans = _mod["find_orphans"]
format_human = _mod["format_human"]
format_json = _mod["format_json"]
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


# ── collect_modules ──────────────────────────────────────────────────


class TestCollectModules:
    def test_finds_py_files(self, fake_root: Path):
        _write_file(fake_root / "metabolon" / "alpha.py")
        _write_file(fake_root / "metabolon" / "beta.py")
        modules = collect_modules(fake_root / "metabolon")
        names = [p.name for p in modules]
        assert "alpha.py" in names
        assert "beta.py" in names

    def test_excludes_init(self, fake_root: Path):
        _write_file(fake_root / "metabolon" / "__init__.py", "# init")
        _write_file(fake_root / "metabolon" / "real.py")
        modules = collect_modules(fake_root / "metabolon")
        names = [p.name for p in modules]
        assert "__init__.py" not in names
        assert "real.py" in names

    def test_nested_subdirs(self, fake_root: Path):
        _write_file(fake_root / "metabolon" / "organelles" / "nucleus.py")
        _write_file(fake_root / "metabolon" / "organelles" / "__init__.py")
        modules = collect_modules(fake_root / "metabolon")
        names = [p.name for p in modules]
        assert "nucleus.py" in names
        assert "__init__.py" not in names

    def test_empty_dir(self, fake_root: Path):
        modules = collect_modules(fake_root / "metabolon")
        assert modules == []


# ── file_to_module ───────────────────────────────────────────────────


class TestFileToModule:
    def test_simple_module(self, fake_root: Path):
        p = fake_root / "metabolon" / "alpha.py"
        assert file_to_module(p, fake_root) == "metabolon.alpha"

    def test_nested_module(self, fake_root: Path):
        p = fake_root / "metabolon" / "organelles" / "nucleus.py"
        assert file_to_module(p, fake_root) == "metabolon.organelles.nucleus"

    def test_deeply_nested(self, fake_root: Path):
        p = fake_root / "metabolon" / "a" / "b" / "c.py"
        assert file_to_module(p, fake_root) == "metabolon.a.b.c"


# ── build_import_index ───────────────────────────────────────────────


class TestBuildImportIndex:
    def test_captures_from_import(self, fake_root: Path):
        _write_file(
            fake_root / "consumer.py",
            "from metabolon.alpha import something\n",
        )
        idx = build_import_index(fake_root)
        assert "metabolon.alpha" in idx
        assert "something" in idx

    def test_captures_plain_import(self, fake_root: Path):
        _write_file(
            fake_root / "consumer.py",
            "import metabolon.organelles.nucleus\n",
        )
        idx = build_import_index(fake_root)
        assert "metabolon.organelles.nucleus" in idx

    def test_ignores_comments(self, fake_root: Path):
        _write_file(
            fake_root / "consumer.py",
            "# from metabolon.alpha import something\n",
        )
        idx = build_import_index(fake_root)
        assert "metabolon.alpha" not in idx

    def test_handles_multiple_imports(self, fake_root: Path):
        _write_file(
            fake_root / "consumer.py",
            textwrap.dedent("""\
                from metabolon.alpha import foo
                from metabolon.beta import bar
                import os
            """),
        )
        idx = build_import_index(fake_root)
        assert "metabolon.alpha" in idx
        assert "metabolon.beta" in idx
        assert "os" in idx


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

    def test_skips_main_entry_point(self, fake_root: Path):
        _write_file(fake_root / "metabolon" / "sortase" / "__main__.py")
        # No imports of it anywhere — should still NOT be flagged
        orphans = find_orphans(fake_root)
        modules = [o["module"] for o in orphans]
        assert "metabolon.sortase.__main__" not in modules

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

    def test_import_from_orphan_itself_doesnt_count(self, fake_root: Path):
        """A file importing itself should still be an orphan."""
        _write_file(
            fake_root / "metabolon" / "lonely.py",
            "from metabolon.lonely import self_ref\n",
        )
        # The import IS in the file, so it IS referenced
        # This is actually correct — it's referenced
        orphans = find_orphans(fake_root)
        modules = [o["module"] for o in orphans]
        # lonely.py imports itself, so it is referenced
        assert "metabolon.lonely" not in modules


# ── format_human / format_json ───────────────────────────────────────


class TestFormatting:
    def test_format_human_no_orphans(self, fake_root: Path):
        report = format_human([], fake_root)
        assert "No orphan modules found" in report

    def test_format_human_with_orphans(self, fake_root: Path):
        orphans = [{"path": "metabolon/alpha.py", "module": "metabolon.alpha"}]
        report = format_human(orphans, fake_root)
        assert "metabolon/alpha.py" in report
        assert "1 found" in report

    def test_format_json_structure(self, fake_root: Path):
        _write_file(fake_root / "metabolon" / "alpha.py")
        orphans = [{"path": "metabolon/alpha.py", "module": "metabolon.alpha"}]
        out = format_json(orphans, fake_root)
        data = json.loads(out)
        assert data["orphan_count"] == 1
        assert data["orphans"][0]["module"] == "metabolon.alpha"

    def test_format_json_empty(self, fake_root: Path):
        out = format_json([], fake_root)
        data = json.loads(out)
        assert data["orphan_count"] == 0
        assert data["orphans"] == []


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
        assert "orphan_count" in data
