#!/usr/bin/env python3
"""Tests for effectors/orphan-scan — find unimported .py files in metabolon/.

orphan-scan is a script (effectors/orphan-scan), not an importable module.
It is loaded via exec() into isolated namespaces.
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ORPHAN_SCAN_PATH = Path(__file__).resolve().parents[1] / "effectors" / "orphan-scan"
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def ns():
    """Load orphan-scan via exec into an isolated namespace dict."""
    ns_dict: dict = {"__name__": "test_orphan_scan", "__file__": str(ORPHAN_SCAN_PATH)}
    source = ORPHAN_SCAN_PATH.read_text(encoding="utf-8")
    exec(source, ns_dict)
    return ns_dict


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

    def test_docstring_mentions_orphan(self):
        content = ORPHAN_SCAN_PATH.read_text()
        assert "orphan" in content.lower() or "import" in content.lower()


# ── py_files_under() ───────────────────────────────────────────────────────


class TestPyFilesUnder:
    def test_finds_py_files(self, ns, tmp_path):
        """Should find .py files in a directory tree."""
        (tmp_path / "alpha.py").write_text("pass")
        (tmp_path / "beta.py").write_text("pass")
        (tmp_path / "__init__.py").write_text("pass")
        result = ns["py_files_under"](tmp_path)
        names = [p.name for p in result]
        assert "alpha.py" in names
        assert "beta.py" in names

    def test_excludes_init(self, ns, tmp_path):
        """Should exclude __init__.py."""
        (tmp_path / "__init__.py").write_text("pass")
        (tmp_path / "real.py").write_text("pass")
        result = ns["py_files_under"](tmp_path)
        assert all(p.name != "__init__.py" for p in result)

    def test_nested_dirs(self, ns, tmp_path):
        """Should find files in nested directories."""
        sub = tmp_path / "enzymes"
        sub.mkdir()
        (sub / "catalyst.py").write_text("pass")
        result = ns["py_files_under"](tmp_path)
        assert any(p.name == "catalyst.py" for p in result)

    def test_returns_sorted(self, ns, tmp_path):
        """Should return sorted list."""
        (tmp_path / "zeta.py").write_text("pass")
        (tmp_path / "alpha.py").write_text("pass")
        result = ns["py_files_under"](tmp_path)
        names = [p.name for p in result]
        assert names == sorted(names)


# ── module_path() ──────────────────────────────────────────────────────────


class TestModulePath:
    def test_simple_module(self, ns):
        """metabolon/foo.py → metabolon.foo"""
        p = ns["ROOT"] / "metabolon" / "foo.py"
        assert ns["module_path"](p) == "metabolon.foo"

    def test_nested_module(self, ns):
        """metabolon/enzymes/assay.py → metabolon.enzymes.assay"""
        p = ns["ROOT"] / "metabolon" / "enzymes" / "assay.py"
        assert ns["module_path"](p) == "metabolon.enzymes.assay"

    def test_deeply_nested(self, ns):
        """metabolon/organelles/endocytosis_rss/fetcher.py → metabolon.organelles.endocytosis_rss.fetcher"""
        p = ns["ROOT"] / "metabolon" / "organelles" / "endocytosis_rss" / "fetcher.py"
        assert ns["module_path"](p) == "metabolon.organelles.endocytosis_rss.fetcher"


# ── import_count() ─────────────────────────────────────────────────────────


class TestImportCount:
    def test_finds_import(self, ns, tmp_path):
        """Should count files that import the module."""
        importer = tmp_path / "consumer.py"
        importer.write_text("from metabolon.enzymes.assay import something\n")
        with patch.object(subprocess, "run", return_value=MagicMock(
            stdout=str(importer) + "\n", returncode=0,
        )):
            count = ns["import_count"]("metabolon.enzymes.assay", tmp_path)
        assert count == 1

    def test_zero_when_no_imports(self, ns, tmp_path):
        """Should return 0 when no files import the module."""
        with patch.object(subprocess, "run", return_value=MagicMock(
            stdout="", returncode=1,
        )):
            count = ns["import_count"]("metabolon.orphan_module", tmp_path)
        assert count == 0

    def test_timeout_returns_zero(self, ns, tmp_path):
        """Should return 0 on grep timeout."""
        with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("grep", 30)):
            count = ns["import_count"]("metabolon.anything", tmp_path)
        assert count == 0

    def test_skips_self_file(self, ns, tmp_path):
        """Should not count the file's own definition as an import."""
        # The module file itself lives at metabolon/enzymes/assay.py
        mod_file = ns["ROOT"] / "metabolon" / "enzymes" / "assay.py"
        mod_file.parent.mkdir(parents=True, exist_ok=True)
        mod_file.write_text("# module definition\n")
        with patch.object(subprocess, "run", return_value=MagicMock(
            stdout=str(mod_file) + "\n", returncode=0,
        )):
            count = ns["import_count"]("metabolon.enzymes.assay", tmp_path)
        assert count == 0

    def test_handles_file_not_found(self, ns, tmp_path):
        """Should return 0 when grep binary is missing."""
        with patch.object(subprocess, "run", side_effect=FileNotFoundError):
            count = ns["import_count"]("metabolon.anything", tmp_path)
        assert count == 0


# ── find_orphans() ─────────────────────────────────────────────────────────


class TestFindOrphans:
    def test_all_imported_returns_empty(self, ns, tmp_path):
        """Should return [] when everything is imported."""
        with patch.object(ns, "py_files_under", return_value=[
            tmp_path / "metabolon" / "active.py",
        ]), patch.object(ns, "import_count", return_value=3):
            result = ns["find_orphans"](tmp_path, tmp_path)
        assert result == []

    def test_reports_orphans(self, ns, tmp_path):
        """Should list files with zero imports."""
        orphan = tmp_path / "metabolon" / "lonely.py"
        orphan.parent.mkdir(parents=True, exist_ok=True)
        orphan.write_text("# lonely module\n")
        with patch.object(ns, "py_files_under", return_value=[orphan]), \
             patch.object(ns, "import_count", return_value=0):
            result = ns["find_orphans"](tmp_path, tmp_path)
        assert len(result) == 1
        assert result[0]["module"] == "metabolon.lonely"

    def test_orphan_has_lines_field(self, ns, tmp_path):
        """Orphan dict should include line count."""
        orphan = tmp_path / "metabolon" / "solo.py"
        orphan.parent.mkdir(parents=True, exist_ok=True)
        orphan.write_text("line1\nline2\nline3\n")
        with patch.object(ns, "py_files_under", return_value=[orphan]), \
             patch.object(ns, "import_count", return_value=0):
            result = ns["find_orphans"](tmp_path, tmp_path)
        assert result[0]["lines"] == 4  # 3 newlines + 1

    def test_mixed_imported_and_orphan(self, ns, tmp_path):
        """Should only include unimported files."""
        active = tmp_path / "metabolon" / "active.py"
        lonely = tmp_path / "metabolon" / "lonely.py"
        active.parent.mkdir(parents=True, exist_ok=True)
        active.write_text("pass")
        lonely.write_text("pass")
        files = [active, lonely]

        def side_effect(mod, root):
            return 5 if "active" in mod else 0

        with patch.object(ns, "py_files_under", return_value=files), \
             patch.object(ns, "import_count", side_effect=side_effect):
            result = ns["find_orphans"](tmp_path, tmp_path)
        assert len(result) == 1
        assert "lonely" in result[0]["module"]


# ── main() ─────────────────────────────────────────────────────────────────


class TestMain:
    def test_no_orphans_message(self, ns, capsys, monkeypatch):
        """Should print 'No orphans found' when empty."""
        monkeypatch.setattr(sys, "argv", ["orphan-scan"])
        monkeypatch.setattr(ns, "find_orphans", return_value=[])
        ns["main"]()
        out = capsys.readouterr().out
        assert "No orphans found" in out

    def test_reports_orphan_count(self, ns, capsys, monkeypatch):
        """Should print orphan count and file paths."""
        monkeypatch.setattr(sys, "argv", ["orphan-scan"])
        monkeypatch.setattr(ns, "find_orphans", return_value=[
            {"path": "metabolon/lonely.py", "module": "metabolon.lonely", "lines": 10},
        ])
        ns["main"]()
        out = capsys.readouterr().out
        assert "1 found" in out
        assert "metabolon/lonely.py" in out
        assert "Total: 1 orphan" in out

    def test_json_output(self, ns, capsys, monkeypatch):
        """--json should emit valid JSON array."""
        monkeypatch.setattr(sys, "argv", ["orphan-scan", "--json"])
        monkeypatch.setattr(ns, "find_orphans", return_value=[
            {"path": "metabolon/ghost.py", "module": "metabolon.ghost", "lines": 5},
        ])
        ns["main"]()
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["module"] == "metabolon.ghost"

    def test_json_flag_removed_from_argv(self, ns, capsys, monkeypatch):
        """--json should be stripped from sys.argv before further processing."""
        monkeypatch.setattr(sys, "argv", ["orphan-scan", "--json"])
        monkeypatch.setattr(ns, "find_orphans", return_value=[])
        ns["main"]()
        # Should not crash — --json was removed

    def test_multiple_orphans(self, ns, capsys, monkeypatch):
        """Should list all orphans with total count."""
        monkeypatch.setattr(sys, "argv", ["orphan-scan"])
        monkeypatch.setattr(ns, "find_orphans", return_value=[
            {"path": "metabolon/a.py", "module": "metabolon.a", "lines": 1},
            {"path": "metabolon/b.py", "module": "metabolon.b", "lines": 2},
            {"path": "metabolon/c.py", "module": "metabolon.c", "lines": 3},
        ])
        ns["main"]()
        out = capsys.readouterr().out
        assert "3 found" in out
        assert "Total: 3 orphan" in out


# ── CLI subprocess ─────────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_runs_without_error(self):
        """Running orphan-scan with no args should exit 0."""
        r = subprocess.run(
            [sys.executable, str(ORPHAN_SCAN_PATH)],
            capture_output=True, text=True, timeout=60,
        )
        assert r.returncode == 0
        assert r.stdout.strip()  # should produce output

    def test_json_flag_produces_valid_json(self):
        """--json flag should produce parseable JSON."""
        r = subprocess.run(
            [sys.executable, str(ORPHAN_SCAN_PATH), "--json"],
            capture_output=True, text=True, timeout=60,
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert isinstance(data, list)

    def test_json_entries_have_required_fields(self):
        """Each JSON entry should have path, module, lines."""
        r = subprocess.run(
            [sys.executable, str(ORPHAN_SCAN_PATH), "--json"],
            capture_output=True, text=True, timeout=60,
        )
        data = json.loads(r.stdout)
        for entry in data:
            assert "path" in entry
            assert "module" in entry
            assert "lines" in entry
            assert entry["path"].startswith("metabolon/")
            assert entry["lines"] > 0
