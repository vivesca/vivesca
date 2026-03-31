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


# ── module_path() ──────────────────────────────────────────────────────────


class TestModulePath:
    def test_simple_module(self, ns, fake_root):
        p = fake_root / "metabolon" / "alpha.py"
        assert ns["module_path"](p, fake_root) == "metabolon.alpha"

    def test_nested_module(self, ns, fake_root):
        p = fake_root / "metabolon" / "organelles" / "nucleus.py"
        assert ns["module_path"](p, fake_root) == "metabolon.organelles.nucleus"

    def test_deeply_nested(self, ns, fake_root):
        p = fake_root / "metabolon" / "a" / "b" / "c.py"
        assert ns["module_path"](p, fake_root) == "metabolon.a.b.c"


# ── collect_metabolon_modules() ────────────────────────────────────────────


class TestCollectMetabolonModules:
    def test_finds_py_files(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        _write(fake_root / "metabolon" / "beta.py")
        modules = ns["collect_metabolon_modules"](fake_root / "metabolon")
        assert "metabolon.alpha" in modules
        assert "metabolon.beta" in modules

    def test_excludes_init(self, ns, fake_root):
        _write(fake_root / "metabolon" / "__init__.py", "# init")
        _write(fake_root / "metabolon" / "real.py")
        modules = ns["collect_metabolon_modules"](fake_root / "metabolon")
        assert "metabolon" not in modules  # __init__.py excluded
        assert "metabolon.real" in modules

    def test_excludes_test_files(self, ns, fake_root):
        _write(fake_root / "metabolon" / "alpha.py")
        _write(fake_root / "metabolon" / "test_alpha.py")
        _write(fake_root / "metabolon" / "conftest.py")
        modules = ns["collect_metabolon_modules"](fake_root / "metabolon")
        assert "metabolon.alpha" in modules
        assert "metabolon.test_alpha" not in modules
        assert "metabolon.conftest" not in modules

    def test_nested_subdirs(self, ns, fake_root):
        _write(fake_root / "metabolon" / "organelles" / "nucleus.py")
        _write(fake_root / "metabolon" / "organelles" / "__init__.py")
        modules = ns["collect_metabolon_modules"](fake_root / "metabolon")
        assert "metabolon.organelles.nucleus" in modules
        assert "metabolon.organelles" not in modules  # __init__.py excluded

    def test_empty_dir(self, ns, fake_root):
        modules = ns["collect_metabolon_modules"](fake_root / "metabolon")
        assert modules == set()


# ── extract_imports_from_file() ────────────────────────────────────────────


class TestExtractImports:
    def test_captures_from_import(self, ns, fake_root):
        p = _write(fake_root / "consumer.py", "from metabolon.alpha import something\n")
        imports = ns["extract_imports_from_file"](p)
        assert "metabolon.alpha" in imports

    def test_captures_plain_import(self, ns, fake_root):
        p = _write(fake_root / "consumer.py", "import metabolon.organelles.nucleus\n")
        imports = ns["extract_imports_from_file"](p)
        assert "metabolon.organelles.nucleus" in imports

    def test_captures_parent_packages(self, ns, fake_root):
        p = _write(
            fake_root / "consumer.py",
            "from metabolon.organelles import crispr\n",
        )
        imports = ns["extract_imports_from_file"](p)
        assert "metabolon.organelles" in imports
        assert "metabolon" in imports

    def test_ignores_comments(self, ns, fake_root):
        p = _write(fake_root / "consumer.py", "# from metabolon.alpha import something\n")
        imports = ns["extract_imports_from_file"](p)
        assert "metabolon.alpha" not in imports

    def test_handles_syntax_error(self, ns, fake_root):
        p = _write(fake_root / "bad.py", "def foo(:\n")
        imports = ns["extract_imports_from_file"](p)
        assert imports == set()

    def test_handles_missing_file(self, ns, tmp_path):
        p = tmp_path / "nonexistent.py"
        imports = ns["extract_imports_from_file"](p)
        assert imports == set()

    def test_multiple_imports(self, ns, fake_root):
        p = _write(
            fake_root / "consumer.py",
            "from metabolon.alpha import foo\nimport os\nfrom metabolon.beta import bar\n",
        )
        imports = ns["extract_imports_from_file"](p)
        assert "metabolon.alpha" in imports
        assert "metabolon.beta" in imports
        assert "os" in imports


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
        assert "is_entry_point" in o

    def test_entry_point_flag(self, ns, fake_root):
        _write(fake_root / "metabolon" / "sortase" / "__main__.py")
        orphans = ns["find_orphans"](fake_root)
        eps = [o for o in orphans if o["is_entry_point"]]
        non_eps = [o for o in orphans if not o["is_entry_point"]]
        assert len(eps) == 1
        assert "metabolon.sortase.__main__" in [o["module"] for o in eps]


# ── format_report() ────────────────────────────────────────────────────────


class TestFormatReport:
    def test_human_no_orphans(self, ns):
        report = ns["format_report"]([], use_json=False)
        assert "No orphan modules found" in report

    def test_human_with_orphans(self, ns):
        orphans = [{"module": "metabolon.alpha", "path": "metabolon/alpha.py", "is_entry_point": False}]
        report = ns["format_report"](orphans, use_json=False)
        assert "metabolon/alpha.py" in report
        assert "1 orphans" in report

    def test_human_entry_points(self, ns):
        orphans = [
            {"module": "metabolon.lonely", "path": "metabolon/lonely.py", "is_entry_point": False},
            {"module": "metabolon.sortase.__main__", "path": "metabolon/sortase/__main__.py", "is_entry_point": True},
        ]
        report = ns["format_report"](orphans, use_json=False)
        assert "Entry points" in report
        assert "metabolon/sortase/__main__.py" in report

    def test_json_output(self, ns):
        orphans = [{"module": "metabolon.alpha", "path": "metabolon/alpha.py", "is_entry_point": False}]
        out = ns["format_report"](orphans, use_json=True)
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["module"] == "metabolon.alpha"

    def test_json_empty(self, ns):
        out = ns["format_report"]([], use_json=True)
        data = json.loads(out)
        assert data == []


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
        assert isinstance(data, list)

    def test_no_args_uses_default_root(self, ns, capsys, monkeypatch):
        monkeypatch.setattr(ns, "DEFAULT_ROOT", Path("/tmp"))
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
        assert isinstance(data, list)

    def test_json_entries_have_required_fields(self):
        r = subprocess.run(
            [sys.executable, str(ORPHAN_SCAN_PATH), "--json"],
            capture_output=True, text=True, timeout=60,
        )
        data = json.loads(r.stdout)
        for entry in data:
            assert "path" in entry
            assert "module" in entry
            assert "is_entry_point" in entry
