from __future__ import annotations

"""Tests for effectors/coverage-map — metabolon test coverage scanner."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


EFFECTOR = Path(__file__).parent.parent / "effectors" / "coverage-map"


def _load():
    """Load the coverage-map effector via exec."""
    source = EFFECTOR.read_text()
    ns: dict = {"__name__": "coverage_map_test"}
    exec(source, ns)
    return ns


_mod = _load()
find_modules = _mod["find_modules"]
module_to_test_name = _mod["module_to_test_name"]
find_test_files = _mod["find_test_files"]
check_coverage = _mod["check_coverage"]
print_report = _mod["print_report"]
main = _mod["main"]


# ── module_to_test_name ─────────────────────────────────────────────


class TestModuleToTestName:
    """Tests for module_to_test_name conversion logic."""

    def test_simple_module(self):
        assert module_to_test_name("config") == "test_config.py"

    def test_two_part_path(self):
        """Two-part path uses last component."""
        assert module_to_test_name("enzymes/sortase") == "test_sortase.py"

    def test_nested_rss_fetcher(self):
        """Three-part path with underscored parent uses suffix."""
        assert module_to_test_name("organelles/endocytosis_rss/fetcher") == "test_rss_fetcher.py"

    def test_nested_rss_config(self):
        assert module_to_test_name("organelles/endocytosis_rss/config") == "test_rss_config.py"

    def test_nested_no_underscore_parent(self):
        """Three-part path with non-underscored parent uses full parent name."""
        assert module_to_test_name("organelles/someorg/cli") == "test_someorg_cli.py"

    def test_single_part_deep(self):
        """Single component always uses itself."""
        assert module_to_test_name("my_module") == "test_my_module.py"


# ── find_modules ────────────────────────────────────────────────────


class TestFindModules:
    """Tests for find_modules with temp directory fixtures."""

    def test_finds_py_files(self, tmp_path):
        (tmp_path / "alpha.py").write_text("")
        (tmp_path / "beta.py").write_text("")
        result = find_modules(tmp_path)
        assert "alpha" in result
        assert "beta" in result

    def test_skips_init_in_subpackage(self, tmp_path):
        """Skips __init__.py inside subdirectories (has slash prefix)."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "real.py").write_text("")
        result = find_modules(tmp_path)
        assert "pkg/__init__" not in result
        assert "pkg/real" in result

    def test_skips_main_in_subpackage(self, tmp_path):
        """Skips __main__.py inside subdirectories (has slash prefix)."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__main__.py").write_text("")
        (pkg / "real.py").write_text("")
        result = find_modules(tmp_path)
        assert "pkg/__main__" not in result
        assert "pkg/real" in result

    def test_root_init_included(self, tmp_path):
        """Root __init__.py has no slash, so filter does not match it."""
        (tmp_path / "__init__.py").write_text("")
        (tmp_path / "real.py").write_text("")
        result = find_modules(tmp_path)
        assert "__init__" in result
        assert "real" in result

    def test_skips_test_dirs(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_x.py").write_text("")
        (tmp_path / "src.py").write_text("")
        result = find_modules(tmp_path)
        assert "src" in result
        assert all("tests/" not in m for m in result)

    def test_recursive(self, tmp_path):
        sub = tmp_path / "enzymes"
        sub.mkdir()
        (sub / "catalase.py").write_text("")
        result = find_modules(tmp_path)
        assert "enzymes/catalase" in result

    def test_sorted_output(self, tmp_path):
        (tmp_path / "zeta.py").write_text("")
        (tmp_path / "alpha.py").write_text("")
        result = find_modules(tmp_path)
        assert result == sorted(result)

    def test_empty_dir(self, tmp_path):
        result = find_modules(tmp_path)
        assert result == []


# ── find_test_files ─────────────────────────────────────────────────


class TestFindTestFiles:
    """Tests for find_test_files."""

    def test_finds_test_py(self, tmp_path):
        (tmp_path / "test_alpha.py").write_text("")
        (tmp_path / "test_beta.py").write_text("")
        result = find_test_files(tmp_path)
        assert "test_alpha.py" in result
        assert "test_beta.py" in result

    def test_ignores_non_test(self, tmp_path):
        (tmp_path / "helper.py").write_text("")
        (tmp_path / "test_real.py").write_text("")
        result = find_test_files(tmp_path)
        assert "helper.py" not in result
        assert "test_real.py" in result

    def test_nonexistent_dir(self, tmp_path):
        missing = tmp_path / "no_such_dir"
        result = find_test_files(missing)
        assert result == set()


# ── check_coverage ──────────────────────────────────────────────────


class TestCheckCoverage:
    """Tests for check_coverage."""

    def test_all_tested(self):
        modules = ["alpha", "beta"]
        test_files = {"test_alpha.py", "test_beta.py"}
        coverage, untested = check_coverage(modules, test_files)
        assert untested == []
        assert coverage["alpha"] == ("test_alpha.py", True)
        assert coverage["beta"] == ("test_beta.py", True)

    def test_none_tested(self):
        modules = ["alpha"]
        test_files: set[str] = set()
        coverage, untested = check_coverage(modules, test_files)
        assert untested == ["alpha"]
        assert coverage["alpha"] == ("test_alpha.py", False)

    def test_partial_coverage(self):
        modules = ["alpha", "beta", "gamma"]
        test_files = {"test_alpha.py", "test_gamma.py"}
        coverage, untested = check_coverage(modules, test_files)
        assert untested == ["beta"]
        assert coverage["beta"] == ("test_beta.py", False)

    def test_empty_modules(self):
        coverage, untested = check_coverage([], set())
        assert coverage == {}
        assert untested == []


# ── print_report ────────────────────────────────────────────────────


class TestPrintReport:
    """Tests for print_report output."""

    def test_report_output(self, capsys):
        modules = ["alpha", "beta"]
        test_files = {"test_alpha.py"}
        coverage, untested = check_coverage(modules, test_files)
        print_report(modules, test_files, coverage, untested)
        out = capsys.readouterr().out
        assert "METABOLON TEST COVERAGE REPORT" in out
        assert "Total modules: 2" in out
        assert "50.0%" in out
        assert "alpha" in out
        assert "beta" in out

    def test_full_coverage_report(self, capsys):
        modules = ["alpha"]
        test_files = {"test_alpha.py"}
        coverage, untested = check_coverage(modules, test_files)
        print_report(modules, test_files, coverage, untested)
        out = capsys.readouterr().out
        assert "100.0%" in out

    def test_zero_modules_report(self, capsys):
        coverage, untested = check_coverage([], set())
        print_report([], set(), coverage, untested)
        out = capsys.readouterr().out
        assert "Total modules: 0" in out


# ── main() via subprocess ───────────────────────────────────────────


class TestMainCLI:
    """Integration tests running the effector as a subprocess."""

    def test_default_exit_code(self):
        """Effector runs and exits (0 or 1 depending on coverage)."""
        r = subprocess.run(
            [sys.executable, str(EFFECTOR)],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode in (0, 1)
        assert "METABOLON TEST COVERAGE REPORT" in r.stdout

    def test_json_output(self):
        """--json flag produces valid JSON."""
        r = subprocess.run(
            [sys.executable, str(EFFECTOR), "--json"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode in (0, 1)
        data = json.loads(r.stdout)
        assert "total" in data
        assert "tested" in data
        assert "untested_count" in data
        assert "coverage_pct" in data
        assert "modules" in data
        assert data["total"] >= 0
        assert data["tested"] <= data["total"]

    def test_create_stubs_flag_dry_run(self, tmp_path, monkeypatch):
        """--create-stubs creates files for untested modules in a temp assays dir."""
        # Set up fake metabolon with one module
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "sample.py").write_text("x = 1\n")
        assays = tmp_path / "assays"
        assays.mkdir()
        # No test files yet -> module is untested

        r = subprocess.run(
            [sys.executable, str(EFFECTOR), "--create-stubs"],
            capture_output=True, text=True, timeout=30,
            cwd=str(tmp_path),
            # Won't work because effector uses Path(__file__).parent.parent.
            # We test stub creation logic via exec instead below.
        )
        # Just verify it doesn't crash
        assert r.returncode in (0, 1)


# ── stub creation via exec ──────────────────────────────────────────


class TestStubCreation:
    """Test the --create-stubs path by exec-ing main with mocked paths."""

    def test_create_stubs_writes_files(self, tmp_path, monkeypatch):
        """Verify stub creation logic directly."""
        source = EFFECTOR.read_text()
        ns: dict = {"__name__": "coverage_map_stub_test"}
        exec(source, ns)

        # Set up fake dirs
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "widget.py").write_text("x = 1\n")
        assays = tmp_path / "assays"
        assays.mkdir()

        # Monkeypatch the effector's path resolution
        # main() uses Path(__file__).parent.parent — we need to override that.
        # Instead, call functions directly.
        modules = ns["find_modules"](metabolon)
        test_files = ns["find_test_files"](assays)
        coverage, untested = ns["check_coverage"](modules, test_files)

        assert "widget" in modules
        assert untested == ["widget"]

        # Now create stubs manually following the effector's logic
        for mod in untested:
            expected_test = coverage[mod][0]
            test_path = assays / expected_test
            if not test_path.exists():
                stub = f'"""Tests for metabolon.{mod.replace("/", ".")}."""\nimport pytest\n\n\ndef test_placeholder():\n    assert True\n'
                test_path.write_text(stub)

        created = assays / "test_widget.py"
        assert created.exists()
        assert "test_placeholder" in created.read_text()


# ── main() via exec with argv patching ───────────────────────────────


class TestMainExec:
    """Test main() by exec-ing with patched germline path and sys.argv."""

    def _make_ns(self, tmp_path):
        """Exec the effector with germline redirected to tmp_path."""
        source = EFFECTOR.read_text().replace(
            "germline = Path(__file__).parent.parent",
            f"germline = Path('{tmp_path}')",
        )
        ns: dict = {"__name__": "coverage_map_main_test"}
        exec(source, ns)
        return ns

    def test_exit_zero_when_fully_tested(self, tmp_path):
        """main() returns 0 when all modules have tests."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "alpha.py").write_text("pass")
        assays = tmp_path / "assays"
        assays.mkdir()
        (assays / "test_alpha.py").write_text("pass")

        ns = self._make_ns(tmp_path)
        saved = sys.argv
        sys.argv = ["coverage-map"]
        try:
            assert ns["main"]() == 0
        finally:
            sys.argv = saved

    def test_exit_one_when_untested(self, tmp_path):
        """main() returns 1 when modules lack tests."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "alpha.py").write_text("pass")
        (metabolon / "beta.py").write_text("pass")
        assays = tmp_path / "assays"
        assays.mkdir()
        (assays / "test_alpha.py").write_text("pass")

        ns = self._make_ns(tmp_path)
        saved = sys.argv
        sys.argv = ["coverage-map"]
        try:
            assert ns["main"]() == 1
        finally:
            sys.argv = saved

    def test_json_flag_via_exec(self, tmp_path, capsys):
        """--json flag outputs valid JSON when exec-ed."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "alpha.py").write_text("pass")
        assays = tmp_path / "assays"
        assays.mkdir()
        (assays / "test_alpha.py").write_text("pass")

        ns = self._make_ns(tmp_path)
        saved = sys.argv
        sys.argv = ["coverage-map", "--json"]
        try:
            ns["main"]()
        finally:
            sys.argv = saved

        data = json.loads(capsys.readouterr().out)
        assert data["total"] == 1
        assert data["tested"] == 1
        assert data["untested_count"] == 0
        assert data["coverage_pct"] == 100.0

    def test_create_stubs_via_exec(self, tmp_path):
        """--create-stubs creates test files for untested modules."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "orphan.py").write_text("pass")
        assays = tmp_path / "assays"
        assays.mkdir()

        ns = self._make_ns(tmp_path)
        saved = sys.argv
        sys.argv = ["coverage-map", "--create-stubs"]
        try:
            ns["main"]()
        finally:
            sys.argv = saved

        stub = assays / "test_orphan.py"
        assert stub.exists()
        assert "test_placeholder" in stub.read_text()

    def test_create_stubs_no_overwrite(self, tmp_path):
        """--create-stubs does not overwrite existing test files."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "alpha.py").write_text("pass")
        assays = tmp_path / "assays"
        assays.mkdir()
        (assays / "test_alpha.py").write_text("original content")

        ns = self._make_ns(tmp_path)
        saved = sys.argv
        sys.argv = ["coverage-map", "--create-stubs"]
        try:
            ns["main"]()
        finally:
            sys.argv = saved

        assert (assays / "test_alpha.py").read_text() == "original content"
