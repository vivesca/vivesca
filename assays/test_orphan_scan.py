"""Tests for orphan-scan — find .py files in metabolon/ not imported anywhere.

orphan-scan is a script loaded via exec() into isolated namespaces.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ORPHAN_SCAN_PATH = Path(__file__).resolve().parents[1] / "effectors" / "orphan-scan"


@pytest.fixture()
def ns():
    """Load orphan-scan via exec into an isolated namespace dict."""
    ns_dict: dict = {"__name__": "test_orphan_scan", "__file__": str(ORPHAN_SCAN_PATH)}
    source = ORPHAN_SCAN_PATH.read_text(encoding="utf-8")
    exec(source, ns_dict)
    return ns_dict


@pytest.fixture()
def fake_root(tmp_path: Path) -> Path:
    """Create a minimal fake germline tree for testing."""
    meta = tmp_path / "metabolon"
    meta.mkdir()
    (meta / "__init__.py").write_text("")
    return tmp_path


def _write(path: Path, content: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# ── File structure tests ───────────────────────────────────────────────────


class TestOrphanScanBasics:
    def test_file_exists(self):
        assert ORPHAN_SCAN_PATH.exists()
        assert ORPHAN_SCAN_PATH.is_file()

    def test_is_python_script(self):
        first_line = ORPHAN_SCAN_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/")
        assert "python" in first_line.lower()

    def test_has_docstring(self):
        content = ORPHAN_SCAN_PATH.read_text()
        assert '"""' in content


# ── collect_modules() ──────────────────────────────────────────────────────


class TestCollectModules:
    def test_finds_py_files(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        _write(fake_root / "metabolon" / "beta.py")
        modules = ns["collect_modules"](fake_root / "metabolon")
        names = [p.name for p in modules]
        assert "alpha.py" in names
        assert "beta.py" in names

    def test_excludes_init(self, ns, fake_root):
        _write(fake_root / "metabolon" / "__init__.py", "# init")
        _write(fake_root / "metabolon" / "real.py")
        modules = ns["collect_modules"](fake_root / "metabolon")
        names = [p.name for p in modules]
        assert "__init__.py" not in names
        assert "real.py" in names

    def test_nested_subdirs(self, ns, fake_root):
        _write(fake_root / "metabolon" / "organelles" / "nucleus.py")
        _write(fake_root / "metabolon" / "organelles" / "__init__.py")
        modules = ns["collect_modules"](fake_root / "metabolon")
        names = [p.name for p in modules]
        assert "nucleus.py" in names
        assert "__init__.py" not in names

    def test_empty_dir(self, ns, fake_root):
        modules = ns["collect_modules"](fake_root / "metabolon")
        assert modules == []

    def test_returns_sorted(self, ns, fake_root):
        _write(fake_root / "metabolon" / "zeta.py")
        _write(fake_root / "metabolon" / "alpha.py")
        modules = ns["collect_modules"](fake_root / "metabolon")
        names = [p.name for p in modules]
        assert names == sorted(names)


# ── file_to_module() ───────────────────────────────────────────────────────


class TestFileToModule:
    def test_simple_module(self, ns, fake_root):
        p = fake_root / "metabolon" / "alpha.py"
        assert ns["file_to_module"](p, fake_root) == "metabolon.alpha"

    def test_nested_module(self, ns, fake_root):
        p = fake_root / "metabolon" / "organelles" / "nucleus.py"
        assert ns["file_to_module"](p, fake_root) == "metabolon.organelles.nucleus"

    def test_deeply_nested(self, ns, fake_root):
        p = fake_root / "metabolon" / "a" / "b" / "c.py"
        assert ns["file_to_module"](p, fake_root) == "metabolon.a.b.c"


# ── build_import_index() ───────────────────────────────────────────────────


class TestBuildImportIndex:
    def test_captures_from_import(self, ns, fake_root):
        _write(fake_root / "consumer.py", "from metabolon.alpha import something\n")
        idx = ns["build_import_index"](fake_root)
        assert "metabolon.alpha" in idx
        assert "something" in idx

    def test_captures_plain_import(self, ns, fake_root):
        _write(fake_root / "consumer.py", "import metabolon.organelles.nucleus\n")
        idx = ns["build_import_index"](fake_root)
        assert "metabolon.organelles.nucleus" in idx

    def test_captures_parent_packages(self, ns, fake_root):
        _write(fake_root / "consumer.py", "from metabolon.organelles import crispr\n")
        idx = ns["build_import_index"](fake_root)
        assert "metabolon.organelles" in idx
        assert "metabolon" in idx
        assert "crispr" in idx

    def test_ignores_comments(self, ns, fake_root):
        _write(fake_root / "consumer.py", "# from metabolon.alpha import something\n")
        idx = ns["build_import_index"](fake_root)
        assert "metabolon.alpha" not in idx

    def test_handles_syntax_error(self, ns, fake_root):
        _write(fake_root / "bad.py", "def foo(:\n")
        idx = ns["build_import_index"](fake_root)
        # Should not crash, returns empty or partial set
        assert isinstance(idx, set)

    def test_multiple_imports(self, ns, fake_root):
        _write(
            fake_root / "consumer.py",
            "from metabolon.alpha import foo\nimport os\nfrom metabolon.beta import bar\n",
        )
        idx = ns["build_import_index"](fake_root)
        assert "metabolon.alpha" in idx
        assert "metabolon.beta" in idx
        assert "os" in idx


# ── find_orphans() ─────────────────────────────────────────────────────────


class TestFindOrphans:
    def test_no_orphans_when_imported(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        _write(fake_root / "main.py", "from metabolon.alpha import run\n")
        orphans = ns["find_orphans"](fake_root)
        assert orphans == []

    def test_detects_orphan(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        _write(fake_root / "metabolon" / "orphan.py")
        _write(fake_root / "main.py", "from metabolon.alpha import run\n")
        orphans = ns["find_orphans"](fake_root)
        modules = [o["module"] for o in orphans]
        assert "metabolon.orphan" in modules
        assert "metabolon.alpha" not in modules

    def test_from_pkg_import_name(self, ns, fake_root):
        """`from metabolon.organelles import nucleus` should mark nucleus as referenced."""
        _write(fake_root / "metabolon" / "organelles" / "__init__.py")
        _write(fake_root / "metabolon" / "organelles" / "nucleus.py")
        _write(fake_root / "main.py", "from metabolon.organelles import nucleus\n")
        orphans = ns["find_orphans"](fake_root)
        modules = [o["module"] for o in orphans]
        assert "metabolon.organelles.nucleus" not in modules

    def test_missing_metabolon_dir(self, ns, tmp_path):
        orphans = ns["find_orphans"](tmp_path)
        assert orphans == []

    def test_all_orphans(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        _write(fake_root / "metabolon" / "beta.py")
        orphans = ns["find_orphans"](fake_root)
        assert len(orphans) == 2

    def test_orphan_dict_has_required_keys(self, ns, fake_root):
        _write(fake_root / "metabolon" / "lonely.py")
        orphans = ns["find_orphans"](fake_root)
        assert len(orphans) == 1
        o = orphans[0]
        assert "module" in o
        assert "path" in o

    def test_skips_main_entry_point(self, ns, fake_root):
        _write(fake_root / "metabolon" / "sortase" / "__main__.py")
        orphans = ns["find_orphans"](fake_root)
        modules = [o["module"] for o in orphans]
        assert "metabolon.sortase.__main__" not in modules


# ── format_human() / format_json() ─────────────────────────────────────────


class TestFormatting:
    def test_format_human_no_orphans(self, ns, fake_root):
        report = ns["format_human"]([], fake_root)
        assert "No orphan modules found" in report

    def test_format_human_with_orphans(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        orphans = [{"path": "metabolon/alpha.py", "module": "metabolon.alpha"}]
        report = ns["format_human"](orphans, fake_root)
        assert "metabolon/alpha.py" in report
        assert "1 found" in report

    def test_format_json_structure(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        orphans = [{"path": "metabolon/alpha.py", "module": "metabolon.alpha"}]
        out = ns["format_json"](orphans, fake_root)
        data = json.loads(out)
        assert data["orphan_count"] == 1
        assert data["orphans"][0]["module"] == "metabolon.alpha"
        assert "total_modules" in data
        assert "root" in data

    def test_format_json_empty(self, ns, fake_root):
        out = ns["format_json"]([], fake_root)
        data = json.loads(out)
        assert data["orphan_count"] == 0
        assert data["orphans"] == []


# ── main() ─────────────────────────────────────────────────────────────────


class TestMain:
    def test_returns_zero(self, ns, fake_root, capsys):
        rc = ns["main"](["--path", str(fake_root)])
        assert rc == 0

    def test_json_flag(self, ns, fake_root, capsys):
        _write(fake_root / "metabolon" / "alpha.py")
        rc = ns["main"](["--path", str(fake_root), "--json"])
        assert rc == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert "orphan_count" in data
        assert "orphans" in data

    def test_no_args(self, ns, capsys):
        rc = ns["main"]([])
        assert rc == 0


# ── CLI subprocess ─────────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_runs_without_error(self):
        r = subprocess.run(
            [sys.executable, str(ORPHAN_SCAN_PATH)],
            capture_output=True, text=True, timeout=60,
        )
        assert r.returncode == 0
        assert r.stdout.strip()

    def test_json_flag_produces_valid_json(self):
        r = subprocess.run(
            [sys.executable, str(ORPHAN_SCAN_PATH), "--json"],
            capture_output=True, text=True, timeout=60,
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "orphan_count" in data
        assert "orphans" in data
        assert isinstance(data["orphans"], list)

    def test_json_entries_have_required_fields(self):
        r = subprocess.run(
            [sys.executable, str(ORPHAN_SCAN_PATH), "--json"],
            capture_output=True, text=True, timeout=60,
        )
        data = json.loads(r.stdout)
        for entry in data["orphans"]:
            assert "path" in entry
            assert "module" in entry
            assert entry["path"].startswith("metabolon/")
