#!/usr/bin/env python3
"""Tests for effectors/immunosurveillance.py — cargo audit sweep & LaunchAgent health.

All filesystem and subprocess calls are mocked.  The module is loaded via exec
so tests can patch names directly in the exec namespace (which the exec'd
functions close over).
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "effectors" / "immunosurveillance.py"


@pytest.fixture()
def ns():
    """Load immunosurveillance via exec, return the live namespace dict."""
    d: dict = {"__name__": "im_module"}
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    exec(source, d)
    return d


# Helpers to read constants from the namespace

def _code_dir(ns):
    return ns["CODE_DIR"]

def _cargo_audit(ns):
    return ns["CARGO_AUDIT"]

def _plist_path(ns):
    return ns["PLIST_PATH"]


# ── Module basics ────────────────────────────────────────────────────────────


class TestImmunosurveillanceBasics:
    def test_script_exists(self):
        assert SCRIPT_PATH.exists()
        assert SCRIPT_PATH.is_file()

    def test_has_main_function(self, ns):
        assert callable(ns["main"])

    def test_constants(self, ns):
        assert ns["CODE_DIR"] == Path.home() / "code"
        assert ns["CARGO_AUDIT"] == Path.home() / ".cargo/bin/cargo-audit"
        assert ns["LAUNCH_AGENT_NAME"] == "com.terry.immunosurveillance"


# ── CLI / argparse ──────────────────────────────────────────────────────────


class TestCLIArgparse:
    def test_help_exits_0(self, ns, capsys):
        with pytest.raises(SystemExit) as exc:
            ns["main"](["--help"])
        assert exc.value.code == 0
        assert "cargo audit sweep" in capsys.readouterr().out.lower()

    def test_no_args_runs_sweep(self, ns, capsys):
        """Default (no flags) should invoke run_sweep via main()."""
        mock_sweep = MagicMock()
        original = ns["run_sweep"]
        ns["run_sweep"] = mock_sweep
        try:
            ns["main"]([])
        finally:
            ns["run_sweep"] = original
        mock_sweep.assert_called_once_with(dry_run=False)

    def test_dry_run_flag(self, ns, capsys):
        mock_sweep = MagicMock()
        original = ns["run_sweep"]
        ns["run_sweep"] = mock_sweep
        try:
            ns["main"](["--dry-run"])
        finally:
            ns["run_sweep"] = original
        mock_sweep.assert_called_once_with(dry_run=True)

    def test_health_flag_calls_check_health(self, ns, capsys):
        mock_health = MagicMock(return_value=True)
        original = ns["check_health"]
        ns["check_health"] = mock_health
        try:
            ns["main"](["--health"])
        finally:
            ns["check_health"] = original
        mock_health.assert_called_once()

    def test_health_failure_exits_1(self, ns, capsys):
        mock_health = MagicMock(return_value=False)
        original = ns["check_health"]
        ns["check_health"] = mock_health
        try:
            with pytest.raises(SystemExit) as exc:
                ns["main"](["--health"])
            assert exc.value.code == 1
        finally:
            ns["check_health"] = original

    def test_unknown_flag_exits_2(self, ns, capsys):
        with pytest.raises(SystemExit) as exc:
            ns["main"](["--nonexistent"])
        assert exc.value.code == 2


# ── has_rustsec ─────────────────────────────────────────────────────────────


class TestHasRustsec:
    def test_detects_rustsec(self, ns):
        assert ns["has_rustsec"]("error: RUSTSEC-2024-0001 found") is True

    def test_no_rustsec(self, ns):
        assert ns["has_rustsec"]("all good, no issues") is False

    def test_empty_string(self, ns):
        assert ns["has_rustsec"]("") is False

    def test_rustsec_in_stderr(self, ns):
        output = "Crate: serde\nRUSTSEC-2023-0014\n"
        assert ns["has_rustsec"](output) is True


# ── find_rust_projects ──────────────────────────────────────────────────────


class TestFindRustProjects:
    def test_returns_empty_when_no_code_dir(self, ns):
        """If CODE_DIR doesn't exist, should return []."""
        orig = ns["CODE_DIR"]
        ns["CODE_DIR"] = Path("/nonexistent/path/that/does/not/exist")
        try:
            result = ns["find_rust_projects"]()
        finally:
            ns["CODE_DIR"] = orig
        assert result == []

    def test_finds_projects_with_lock(self, ns, tmp_path):
        proj_a = tmp_path / "proj-a"
        proj_a.mkdir()
        (proj_a / "Cargo.toml").write_text("[package]\nname='a'")
        (proj_a / "Cargo.lock").write_text("# lock")
        proj_b = tmp_path / "proj-b"
        proj_b.mkdir()
        (proj_b / "Cargo.toml").write_text("[package]\nname='b'")
        # proj_b has no Cargo.lock — excluded

        orig = ns["CODE_DIR"]
        ns["CODE_DIR"] = tmp_path
        try:
            result = ns["find_rust_projects"]()
        finally:
            ns["CODE_DIR"] = orig
        assert len(result) == 1
        assert result[0].name == "proj-a"

    def test_sorted_output(self, ns, tmp_path):
        for name in ("zebra", "alpha", "mid"):
            p = tmp_path / name
            p.mkdir()
            (p / "Cargo.toml").write_text("")
            (p / "Cargo.lock").write_text("")

        orig = ns["CODE_DIR"]
        ns["CODE_DIR"] = tmp_path
        try:
            result = ns["find_rust_projects"]()
        finally:
            ns["CODE_DIR"] = orig
        names = [p.name for p in result]
        assert names == sorted(names)


# ── run_audit ───────────────────────────────────────────────────────────────


class TestRunAudit:
    def test_success(self, ns):
        mock_result = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch("subprocess.run", return_value=mock_result):
            ok, output = ns["run_audit"](Path("/some/project"))
        assert ok is True
        assert output == "ok"

    def test_failure_captures_stdout_stderr(self, ns):
        mock_result = MagicMock(returncode=1, stdout="RUSTSEC-2024-0001", stderr="error found")
        with patch("subprocess.run", return_value=mock_result):
            ok, output = ns["run_audit"](Path("/some/project"))
        assert ok is False
        assert "RUSTSEC-2024-0001" in output
        assert "error found" in output

    def test_passes_correct_args(self, ns):
        cwd = Path("/some/project")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            ns["run_audit"](cwd)
        args = mock_run.call_args
        assert str(ns["CARGO_AUDIT"]) in args[0][0]
        assert "audit" in args[0][0]
        assert args[1]["cwd"] == cwd


# ── check_health ────────────────────────────────────────────────────────────


class TestCheckHealth:
    """Mock Path.exists via the class method to avoid read-only PosixPath attrs."""

    def _path_exists_side_effect(self, ns, mapping: dict):
        """Return a side_effect function that returns True/False by path string."""
        cargo_audit = str(ns["CARGO_AUDIT"])
        plist_path = str(ns["PLIST_PATH"])
        plist_parent = str(ns["PLIST_PATH"].parent)
        code_dir = str(ns["CODE_DIR"])

        def _exists(self_path):
            s = str(self_path)
            if s in mapping:
                return mapping[s]
            # Default: cargo-audit and code dir exist, plist parent doesn't
            if s == cargo_audit:
                return mapping.get("__cargo_audit__", True)
            if s == plist_path:
                return mapping.get("__plist__", False)
            if s == plist_parent:
                return mapping.get("__plist_parent__", False)
            if s == code_dir:
                return mapping.get("__code_dir__", True)
            # Fall back to real filesystem
            return Path(self_path).exists()

        return _exists

    def test_all_healthy_on_macos(self, ns, capsys):
        """macOS with plist parent, plist, cargo-audit, code dir all present."""
        mapping = {
            "__cargo_audit__": True,
            "__plist_parent__": True,
            "__plist__": True,
            "__code_dir__": True,
        }
        side_effect = self._path_exists_side_effect(ns, mapping)
        with patch("pathlib.Path.exists", side_effect), \
             patch("subprocess.run", return_value=MagicMock(returncode=0)):
            assert ns["check_health"]() is True
        out = capsys.readouterr().out
        assert "cargo-audit found" in out
        assert "plist found" in out

    def test_missing_cargo_audit(self, ns, capsys):
        mapping = {"__cargo_audit__": False, "__plist_parent__": False, "__code_dir__": True}
        side_effect = self._path_exists_side_effect(ns, mapping)
        with patch("pathlib.Path.exists", side_effect):
            assert ns["check_health"]() is False
        err = capsys.readouterr().err
        assert "cargo-audit missing" in err

    def test_missing_plist(self, ns, capsys):
        mapping = {
            "__cargo_audit__": True,
            "__plist_parent__": True,
            "__plist__": False,
            "__code_dir__": True,
        }
        side_effect = self._path_exists_side_effect(ns, mapping)
        with patch("pathlib.Path.exists", side_effect):
            assert ns["check_health"]() is False
        err = capsys.readouterr().err
        assert "plist missing" in err

    def test_missing_code_dir(self, ns, capsys):
        mapping = {"__cargo_audit__": True, "__plist_parent__": False, "__code_dir__": False}
        side_effect = self._path_exists_side_effect(ns, mapping)
        with patch("pathlib.Path.exists", side_effect):
            assert ns["check_health"]() is False
        err = capsys.readouterr().err
        assert "code directory missing" in err

    def test_launchctl_not_loaded(self, ns, capsys):
        mapping = {
            "__cargo_audit__": True,
            "__plist_parent__": True,
            "__plist__": True,
            "__code_dir__": True,
        }
        side_effect = self._path_exists_side_effect(ns, mapping)
        with patch("pathlib.Path.exists", side_effect), \
             patch("subprocess.run", return_value=MagicMock(returncode=1)):
            assert ns["check_health"]() is False
        err = capsys.readouterr().err
        assert "not loaded" in err

    def test_non_macos_skips_plist_check(self, ns, capsys):
        mapping = {"__cargo_audit__": True, "__plist_parent__": False, "__code_dir__": True}
        side_effect = self._path_exists_side_effect(ns, mapping)
        with patch("pathlib.Path.exists", side_effect):
            assert ns["check_health"]() is True
        out = capsys.readouterr().out
        assert "plist check skipped" in out


# ── run_sweep ───────────────────────────────────────────────────────────────


class TestRunSweep:
    def test_dry_run_lists_targets(self, ns, capsys, tmp_path):
        proj = tmp_path / "myproject"
        proj.mkdir()
        (proj / "Cargo.toml").write_text("")
        (proj / "Cargo.lock").write_text("")

        orig_code = ns["CODE_DIR"]
        ns["CODE_DIR"] = tmp_path
        try:
            ns["run_sweep"](dry_run=True)
        finally:
            ns["CODE_DIR"] = orig_code

        out = capsys.readouterr().out
        assert "Targets (1):" in out
        assert "myproject" in out

    def test_dry_run_with_workspace_root(self, ns, capsys, tmp_path):
        """Workspace root Cargo.lock should appear as an extra target."""
        (tmp_path / "Cargo.lock").write_text("# root")
        proj = tmp_path / "subproj"
        proj.mkdir()
        (proj / "Cargo.toml").write_text("")
        (proj / "Cargo.lock").write_text("")

        orig_code = ns["CODE_DIR"]
        ns["CODE_DIR"] = tmp_path
        try:
            ns["run_sweep"](dry_run=True)
        finally:
            ns["CODE_DIR"] = orig_code

        out = capsys.readouterr().out
        assert "Targets (2):" in out
        assert "workspace-root" in out
        assert "subproj" in out

    def test_clean_sweep(self, ns, capsys, tmp_path):
        proj = tmp_path / "clean-proj"
        proj.mkdir()
        (proj / "Cargo.toml").write_text("[package]\nname='clean'")
        (proj / "Cargo.lock").write_text("# lock")

        mock_result = MagicMock(returncode=0, stdout="ok", stderr="")
        orig_code = ns["CODE_DIR"]
        ns["CODE_DIR"] = tmp_path
        try:
            with patch("subprocess.run", return_value=mock_result):
                ns["run_sweep"]()
        finally:
            ns["CODE_DIR"] = orig_code

        assert "all 1 targets clean" in capsys.readouterr().out

    def test_vulnerable_sweep_sends_alert(self, ns, capsys, tmp_path):
        proj = tmp_path / "vuln-proj"
        proj.mkdir()
        (proj / "Cargo.toml").write_text("[package]\nname='vuln'")
        (proj / "Cargo.lock").write_text("# lock")

        vuln_output = (
            "ID: RUSTSEC-2024-0001\nCrate: bad-crate\n"
            "Version: 1.0.0\nDate: 2024-01-01\n"
        )
        mock_result = MagicMock(returncode=1, stdout=vuln_output, stderr="")
        mock_secrete = MagicMock()

        orig_code = ns["CODE_DIR"]
        ns["CODE_DIR"] = tmp_path
        try:
            with patch("subprocess.run", return_value=mock_result), \
                 patch.dict("sys.modules", {
                     "metabolon": MagicMock(),
                     "metabolon.organelles": MagicMock(),
                     "metabolon.organelles.secretory_vesicle": MagicMock(
                         secrete_text=mock_secrete,
                     ),
                 }):
                ns["run_sweep"]()
        finally:
            ns["CODE_DIR"] = orig_code

        out = capsys.readouterr().out
        assert "1/1 targets have vulnerabilities" in out
        assert "RUSTSEC-2024-0001" in out
        mock_secrete.assert_called_once()

    def test_sweep_filters_non_rustsec_failures(self, ns, capsys, tmp_path):
        """Non-RUSTSEC failures (e.g. parse errors) should not trigger alerts."""
        proj = tmp_path / "fail-proj"
        proj.mkdir()
        (proj / "Cargo.toml").write_text("[package]\nname='fail'")
        (proj / "Cargo.lock").write_text("# lock")

        mock_result = MagicMock(returncode=1, stdout="parse error", stderr="")
        orig_code = ns["CODE_DIR"]
        ns["CODE_DIR"] = tmp_path
        try:
            with patch("subprocess.run", return_value=mock_result):
                ns["run_sweep"]()
        finally:
            ns["CODE_DIR"] = orig_code

        assert "all 1 targets clean" in capsys.readouterr().out

    def test_workspace_root_audit(self, ns, capsys, tmp_path):
        """When ~/code/Cargo.lock exists, the workspace-root is also audited."""
        (tmp_path / "Cargo.lock").write_text("# root lock")

        mock_result = MagicMock(returncode=0, stdout="ok", stderr="")
        orig_code = ns["CODE_DIR"]
        ns["CODE_DIR"] = tmp_path
        try:
            with patch("subprocess.run", return_value=mock_result):
                ns["run_sweep"]()
        finally:
            ns["CODE_DIR"] = orig_code

        assert "all 1 targets clean" in capsys.readouterr().out
