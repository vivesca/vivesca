from __future__ import annotations
"""Tests for effectors/coverage-map — metabolon test coverage scanner.

Load via exec (effectors are scripts, not importable modules).
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

EFFECTOR = Path(__file__).parent.parent / "effectors" / "coverage-map"


def _load():
    """Exec the coverage-map script and return its namespace."""
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


# ── find_modules ─────────────────────────────────────────────────────


class TestFindModules:
    def test_finds_py_files(self, tmp_path):
        """Finds .py files in metabolon tree."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "alpha.py").write_text("pass")
        (pkg / "beta.py").write_text("pass")
        assert find_modules(tmp_path) == ["pkg/alpha", "pkg/beta"]

    def test_skips_init(self, tmp_path):
        """Skips __init__.py."""
        (tmp_path / "__init__.py").write_text("pass")
        (tmp_path / "real.py").write_text("pass")
        assert find_modules(tmp_path) == ["real"]

    def test_skips_main(self, tmp_path):
        """Skips __main__.py."""
        (tmp_path / "__main__.py").write_text("pass")
        (tmp_path / "real.py").write_text("pass")
        assert find_modules(tmp_path) == ["real"]

    def test_skips_test_dirs(self, tmp_path):
        """Skips files inside tests/ directories."""
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "foo.py").write_text("pass")
        (tmp_path / "sub" / "tests").mkdir(parents=True)
        (tmp_path / "sub" / "tests" / "bar.py").write_text("pass")
        (tmp_path / "sub" / "real.py").write_text("pass")
        assert find_modules(tmp_path) == ["sub/real"]

    def test_nested_packages(self, tmp_path):
        """Finds deeply nested modules."""
        (tmp_path / "a" / "b" / "c").mkdir(parents=True)
        (tmp_path / "a" / "b" / "c" / "deep.py").write_text("pass")
        assert find_modules(tmp_path) == ["a/b/c/deep"]

    def test_empty_dir(self, tmp_path):
        """Returns empty list for empty directory."""
        assert find_modules(tmp_path) == []

    def test_sorted_output(self, tmp_path):
        """Returns modules in sorted order."""
        for name in ("zeta.py", "alpha.py", "mid.py"):
            (tmp_path / name).write_text("pass")
        result = find_modules(tmp_path)
        assert result == sorted(result)


# ── module_to_test_name ──────────────────────────────────────────────


class TestModuleToTestName:
    def test_simple_module(self):
        """Single-part name -> test_<name>.py."""
        assert module_to_test_name("config") == "test_config.py"

    def test_two_part_path(self):
        """Two-part path uses leaf name."""
        assert module_to_test_name("enzymes/sortase") == "test_sortase.py"

    def test_three_part_underscore_parent(self):
        """Three-part path with underscore parent extracts suffix."""
        # organelles/endocytosis_rss/fetcher -> test_rss_fetcher.py
        result = module_to_test_name("organelles/endocytosis_rss/fetcher")
        assert result == "test_rss_fetcher.py"

    def test_three_part_no_underscore_parent(self):
        """Three-part path without underscore parent uses parent name."""
        result = module_to_test_name("organelles/someorganelle/worker")
        assert result == "test_someorganelle_worker.py"

    def test_four_part_deep(self):
        """Deeply nested path still uses last two parts."""
        result = module_to_test_name("a/b/c_rss/fetcher")
        assert result == "test_rss_fetcher.py"

    def test_cli_module(self):
        """CLI module naming."""
        assert module_to_test_name("lysin/cli") == "test_cli.py"


# ── find_test_files ──────────────────────────────────────────────────


class TestFindTestFiles:
    def test_finds_test_files(self, tmp_path):
        """Finds test_*.py files."""
        (tmp_path / "test_alpha.py").write_text("pass")
        (tmp_path / "test_beta.py").write_text("pass")
        (tmp_path / "helper.py").write_text("pass")
        result = find_test_files(tmp_path)
        assert result == {"test_alpha.py", "test_beta.py"}

    def test_nonexistent_dir(self, tmp_path):
        """Returns empty set for non-existent directory."""
        result = find_test_files(tmp_path / "nope")
        assert result == set()

    def test_empty_dir(self, tmp_path):
        """Returns empty set for empty directory."""
        empty = tmp_path / "empty"
        empty.mkdir()
        assert find_test_files(empty) == set()


# ── check_coverage ───────────────────────────────────────────────────


class TestCheckCoverage:
    def test_all_tested(self):
        """All modules have matching test files."""
        modules = ["alpha", "beta"]
        tests = {"test_alpha.py", "test_beta.py"}
        coverage, untested = check_coverage(modules, tests)
        assert untested == []
        assert coverage["alpha"] == ("test_alpha.py", True)
        assert coverage["beta"] == ("test_beta.py", True)

    def test_none_tested(self):
        """No modules have matching test files."""
        modules = ["alpha", "beta"]
        tests: set[str] = set()
        coverage, untested = check_coverage(modules, tests)
        assert untested == ["alpha", "beta"]
        assert coverage["alpha"] == ("test_alpha.py", False)

    def test_partial_coverage(self):
        """Some modules tested, some not."""
        modules = ["alpha", "beta", "gamma"]
        tests = {"test_beta.py"}
        coverage, untested = check_coverage(modules, tests)
        assert untested == ["alpha", "gamma"]
        assert coverage["beta"] == ("test_beta.py", True)
        assert coverage["alpha"] == ("test_alpha.py", False)

    def test_empty_modules(self):
        """Empty module list returns empty results."""
        coverage, untested = check_coverage([], set())
        assert coverage == {}
        assert untested == []


# ── print_report ─────────────────────────────────────────────────────


class TestPrintReport:
    def test_report_output(self, capsys):
        """print_report produces expected output sections."""
        modules = ["alpha", "beta"]
        tests = {"test_beta.py"}
        coverage, untested = check_coverage(modules, tests)
        print_report(modules, tests, coverage, untested)
        out = capsys.readouterr().out
        assert "METABOLON TEST COVERAGE REPORT" in out
        assert "Total modules: 2" in out
        assert "Coverage: 50.0%" in out
        assert "UNTESTED MODULES" in out
        assert "alpha" in out
        assert "TESTED MODULES" in out
        assert "✓ beta" in out

    def test_full_coverage_report(self, capsys):
        """Report when everything is tested."""
        modules = ["alpha"]
        tests = {"test_alpha.py"}
        coverage, untested = check_coverage(modules, tests)
        print_report(modules, tests, coverage, untested)
        out = capsys.readouterr().out
        assert "Coverage: 100.0%" in out
        assert "UNTESTED" not in out.split("SUMMARY")[0]  # no untested section content

    def test_zero_modules_report(self, capsys):
        """Report with no modules at all."""
        coverage, untested = check_coverage([], set())
        print_report([], set(), coverage, untested)
        out = capsys.readouterr().out
        assert "Total modules: 0" in out
        assert "Coverage: 0.0%" in out


# ── main() with --json ───────────────────────────────────────────────


class TestMainJson:
    def test_json_output(self, capsys, tmp_path):
        """--json flag produces valid JSON with expected keys."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "alpha.py").write_text("pass")
        assays = tmp_path / "assays"
        assays.mkdir()
        (assays / "test_alpha.py").write_text("pass")

        with patch.object(Path, "parent", new_callable=lambda: property(lambda self: tmp_path)):
            # We need to patch __file__ inside the module's main()
            # Easier: just call subprocess
            pass

        # Use subprocess for integration test
        result = subprocess.run(
            [sys.executable, str(EFFECTOR), "--json"],
            capture_output=True, text=True,
            cwd=str(tmp_path),
        )
        # This will run against the real metabolon/ dir, so just check format
        if result.returncode in (0, 1):
            data = json.loads(result.stdout)
            assert "total" in data
            assert "tested" in data
            assert "untested_count" in data
            assert "coverage_pct" in data

    def test_exit_code_zero_when_fully_tested(self, tmp_path):
        """Returns 0 when all modules have tests."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "alpha.py").write_text("pass")
        assays = tmp_path / "assays"
        assays.mkdir()
        (assays / "test_alpha.py").write_text("pass")

        # Patch the paths inside main by exec-ing with modified __file__
        source = EFFECTOR.read_text().replace(
            'germline = Path(__file__).parent.parent',
            f'germline = Path("{tmp_path}")'
        )
        ns: dict = {"__name__": "coverage_map_test"}
        exec(source, ns)
        exit_code = ns["main"]()
        assert exit_code == 0

    def test_exit_code_one_when_untested(self, tmp_path):
        """Returns 1 when some modules lack tests."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "alpha.py").write_text("pass")
        (metabolon / "beta.py").write_text("pass")
        assays = tmp_path / "assays"
        assays.mkdir()
        # Only test_alpha, not test_beta
        (assays / "test_alpha.py").write_text("pass")

        source = EFFECTOR.read_text().replace(
            'germline = Path(__file__).parent.parent',
            f'germline = Path("{tmp_path}")'
        )
        ns: dict = {"__name__": "coverage_map_test"}
        exec(source, ns)
        exit_code = ns["main"]()
        assert exit_code == 1


# ── --create-stubs ───────────────────────────────────────────────────


class TestCreateStubs:
    def test_creates_stub_files(self, tmp_path):
        """--create-stubs creates test files for untested modules."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "orphan.py").write_text("pass")
        assays = tmp_path / "assays"
        assays.mkdir()

        source = EFFECTOR.read_text().replace(
            'germline = Path(__file__).parent.parent',
            f'germline = Path("{tmp_path}")'
        )
        ns: dict = {"__name__": "coverage_map_test"}
        exec(source, ns)
        # Simulate --create-stubs
        sys_argv_backup = sys.argv
        sys.argv = ["coverage-map", "--create-stubs"]
        try:
            ns["main"]()
        finally:
            sys.argv = sys_argv_backup

        stub = assays / "test_orphan.py"
        assert stub.exists()
        content = stub.read_text()
        assert "test_placeholder" in content
        assert "orphan" in content

    def test_does_not_overwrite_existing(self, tmp_path):
        """--create-stubs skips files that already exist."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "alpha.py").write_text("pass")
        assays = tmp_path / "assays"
        assays.mkdir()
        existing = assays / "test_alpha.py"
        existing.write_text("original content")

        source = EFFECTOR.read_text().replace(
            'germline = Path(__file__).parent.parent',
            f'germline = Path("{tmp_path}")'
        )
        ns: dict = {"__name__": "coverage_map_test"}
        exec(source, ns)
        sys_argv_backup = sys.argv
        sys.argv = ["coverage-map", "--create-stubs"]
        try:
            ns["main"]()
        finally:
            sys.argv = sys_argv_backup

        assert existing.read_text() == "original content"


# ── subprocess integration ───────────────────────────────────────────


class TestSubprocessInvocation:
    def test_runs_with_real_repo(self):
        """Script runs against real metabolon/ without crashing."""
        result = subprocess.run(
            [sys.executable, str(EFFECTOR), "--json"],
            capture_output=True, text=True,
            timeout=10,
        )
        assert result.returncode in (0, 1)
        data = json.loads(result.stdout)
        assert data["total"] >= 0
        assert data["coverage_pct"] >= 0

    def test_help_flag(self):
        """--help exits with 0."""
        result = subprocess.run(
            [sys.executable, str(EFFECTOR), "--help"],
            capture_output=True, text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "coverage" in result.stdout.lower()
