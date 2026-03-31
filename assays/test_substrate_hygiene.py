"""Tests for HygieneSubstrate — dependency and tooling health metabolism."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from metabolon.metabolism.substrates.hygiene import (
    _run,
    HygieneSubstrate,
)


class TestRun:
    def test_successful_command(self):
        result = _run(["echo", "hello"])
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_failed_command(self):
        result = _run(["ls", "/nonexistent_dir_xyz"])
        assert result.returncode != 0

    def test_timeout_command(self):
        # Use a command that will timeout
        result = _run(["sleep", "5"], timeout=1)
        assert result.returncode == 1
        assert "timeout" in result.stderr.lower()

    def test_command_not_found(self):
        result = _run(["nonexistent_command_xyz_123"])
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()


class TestHygieneSubstrateInit:
    def test_default_root(self):
        sub = HygieneSubstrate()
        assert sub.root.is_absolute()

    def test_custom_root(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        assert sub.root == tmp_path


class TestSenseDeps:
    def test_sense_deps_no_updates(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)

        with patch("metabolon.metabolism.substrates.hygiene._run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )
            result = sub._sense_deps()
            assert result == []

    def test_sense_deps_with_updates(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)

        with patch("metabolon.metabolism.substrates.hygiene._run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="Would update foo v1.0.0 -> v1.1.0\nWould update bar v2.0.0 -> v3.0.0",
            )
            result = sub._sense_deps()
            assert len(result) == 2
            assert result[0]["package"] == "foo"
            assert result[0]["current"] == "1.0.0"
            assert result[0]["available"] == "1.1.0"
            assert result[0]["major"] is False
            assert result[1]["major"] is True  # 2.x -> 3.x

    def test_sense_deps_with_error(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)

        with patch("metabolon.metabolism.substrates.hygiene._run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="uv not found",
            )
            result = sub._sense_deps()
            assert len(result) == 1
            assert result[0]["kind"] == "deps"
            assert "error" in result[0]


class TestSenseHooks:
    def test_no_precommit_config(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        result = sub._sense_hooks()
        assert result == []

    def test_hooks_up_to_date(self, tmp_path: Path):
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text("repos:\n  - repo: https://github.com/test\n    rev: v1.0\n")

        sub = HygieneSubstrate(project_root=tmp_path)

        with patch("metabolon.metabolism.substrates.hygiene._run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )
            result = sub._sense_hooks()
            # Config should be unchanged
            assert result == []

    def test_hooks_with_update(self, tmp_path: Path):
        config = tmp_path / ".pre-commit-config.yaml"
        original = "repos:\n  - repo: https://github.com/test\n    rev: v1.0\n"
        config.write_text(original)

        sub = HygieneSubstrate(project_root=tmp_path)

        with patch("metabolon.metabolism.substrates.hygiene._run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="updating https://github.com/test -> v1.1",
                stderr="",
            )
            # Patch Path.read_text to simulate the config change then restore
            original_read = Path.read_text
            call_count = [0]
            def side_effect_read_text(self, *args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    return original  # First read (original)
                elif call_count[0] == 2:
                    return "repos:\n  - repo: https://github.com/test\n    rev: v1.1\n"  # After autoupdate
                else:
                    return original  # After restore
            with patch.object(Path, "read_text", side_effect_read_text):
                result = sub._sense_hooks()
                assert len(result) == 1
                assert result[0]["kind"] == "hook"


class TestSenseTests:
    def test_skips_with_env_var(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        os.environ["VIVESCA_HYGIENE_NO_TESTS"] = "1"
        try:
            result = sub._sense_tests()
            assert len(result) == 1
            assert result[0]["skipped"] is True
        finally:
            del os.environ["VIVESCA_HYGIENE_NO_TESTS"]

    def test_parses_test_output(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)

        with patch("metabolon.metabolism.substrates.hygiene._run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="10 passed\n",
                stderr="",
            )
            with patch.dict(os.environ, {"VIVESCA_HYGIENE_NO_TESTS": ""}, clear=False):
                os.environ.pop("VIVESCA_HYGIENE_NO_TESTS", None)
                result = sub._sense_tests()
                assert len(result) == 1
                assert result[0]["passed"] == 10
                assert result[0]["failed"] == 0
                assert result[0]["healthy"] is True

    def test_parses_failed_tests(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)

        with patch("metabolon.metabolism.substrates.hygiene._run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="3 failed, 7 passed\n",
                stderr="",
            )
            with patch.dict(os.environ, {"VIVESCA_HYGIENE_NO_TESTS": ""}, clear=False):
                os.environ.pop("VIVESCA_HYGIENE_NO_TESTS", None)
                result = sub._sense_tests()
                assert result[0]["passed"] == 7
                assert result[0]["failed"] == 3
                assert result[0]["healthy"] is False

    def test_parses_errors(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)

        with patch("metabolon.metabolism.substrates.hygiene._run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="2 error, 5 passed\n",
                stderr="",
            )
            with patch.dict(os.environ, {"VIVESCA_HYGIENE_NO_TESTS": ""}, clear=False):
                os.environ.pop("VIVESCA_HYGIENE_NO_TESTS", None)
                result = sub._sense_tests()
                assert result[0]["errors"] == 2
                assert result[0]["healthy"] is False


class TestSensePython:
    def test_reports_current_version(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        result = sub._sense_python()
        assert len(result) == 1
        assert result[0]["kind"] == "python"
        assert "current" in result[0]
        import sys
        assert result[0]["current"].startswith(f"{sys.version_info.major}.{sys.version_info.minor}")

    def test_reads_requires_python(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.10"\n')

        sub = HygieneSubstrate(project_root=tmp_path)
        result = sub._sense_python()
        assert result[0]["requires"] == ">=3.10"

    def test_handles_missing_pyproject(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        result = sub._sense_python()
        assert result[0]["requires"] == ""


class TestSense:
    def test_aggregates_all_signals(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)

        with patch.object(sub, "_sense_deps", return_value=[{"kind": "dep", "package": "foo"}]):
            with patch.object(sub, "_sense_hooks", return_value=[]):
                with patch.object(sub, "_sense_tests", return_value=[{"kind": "tests", "healthy": True}]):
                    with patch.object(sub, "_sense_python", return_value=[{"kind": "python"}]):
                        result = sub.sense()
                        assert len(result) == 3  # deps + tests + python (hooks empty)
                        kinds = {r["kind"] for r in result}
                        assert "dep" in kinds
                        assert "tests" in kinds
                        assert "python" in kinds


class TestCandidates:
    def test_filters_actionable_deps(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        sensed = [
            {"kind": "dep", "package": "foo", "current": "1.0", "available": "1.1"},
            {"kind": "dep", "package": "bar", "current": "2.0"},  # no available
        ]
        result = sub.candidates(sensed)
        assert len(result) == 1
        assert result[0]["package"] == "foo"

    def test_filters_actionable_hooks(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        sensed = [
            {"kind": "hook", "repo": "test", "new_rev": "v2.0"},
        ]
        result = sub.candidates(sensed)
        assert len(result) == 1

    def test_filters_unhealthy_tests(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        sensed = [
            {"kind": "tests", "passed": 10, "failed": 0, "healthy": True},
            {"kind": "tests", "passed": 5, "failed": 5, "healthy": False},
        ]
        result = sub.candidates(sensed)
        assert len(result) == 1
        assert result[0]["healthy"] is False

    def test_filters_errors(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        sensed = [
            {"kind": "deps", "error": "uv not found"},
        ]
        result = sub.candidates(sensed)
        assert len(result) == 1


class TestAct:
    def test_act_minor_dep_upgrade(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)

        with patch("metabolon.metabolism.substrates.hygiene._run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            candidate = {
                "kind": "dep",
                "package": "foo",
                "current": "1.0.0",
                "available": "1.1.0",
                "major": False,
            }
            result = sub.act(candidate)
            assert "upgraded" in result

    def test_act_major_dep_proposes(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        candidate = {
            "kind": "dep",
            "package": "foo",
            "current": "1.0.0",
            "available": "2.0.0",
            "major": True,
        }
        result = sub.act(candidate)
        assert "propose" in result.lower()
        assert "MAJOR" in result

    def test_act_hook_update(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)

        with patch("metabolon.metabolism.substrates.hygiene._run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            candidate = {"kind": "hook", "repo": "test", "new_rev": "v2.0"}
            result = sub.act(candidate)
            assert "updated" in result

    def test_act_failed_tests(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        candidate = {"kind": "tests", "passed": 5, "failed": 3, "errors": 1}
        result = sub.act(candidate)
        assert "propose" in result.lower()
        assert "3 test failure" in result

    def test_act_with_error(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        candidate = {"kind": "deps", "error": "uv not found"}
        result = sub.act(candidate)
        assert "propose" in result.lower()
        assert "fix" in result.lower()


class TestReport:
    def test_empty_report(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        report = sub.report([], [])
        assert "0 artifact(s) sensed" in report

    def test_report_with_deps(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        sensed = [
            {"kind": "dep", "package": "foo", "current": "1.0", "available": "1.1", "major": False},
        ]
        report = sub.report(sensed, [])
        assert "Dependencies" in report
        assert "foo" in report

    def test_report_with_major_flag(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        sensed = [
            {"kind": "dep", "package": "bar", "current": "1.0", "available": "2.0", "major": True},
        ]
        report = sub.report(sensed, [])
        assert "MAJOR" in report

    def test_report_with_tests(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        sensed = [
            {"kind": "tests", "passed": 10, "failed": 0, "errors": 0, "healthy": True},
        ]
        report = sub.report(sensed, [])
        assert "Tests: healthy" in report

    def test_report_with_unhealthy_tests(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        sensed = [
            {"kind": "tests", "passed": 5, "failed": 3, "errors": 1, "healthy": False},
        ]
        report = sub.report(sensed, [])
        assert "UNHEALTHY" in report

    def test_report_with_python(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        sensed = [
            {"kind": "python", "current": "3.11.0", "requires": ">=3.10"},
        ]
        report = sub.report(sensed, [])
        assert "Python: 3.11.0" in report
        assert ">=3.10" in report

    def test_report_with_actions(self, tmp_path: Path):
        sub = HygieneSubstrate(project_root=tmp_path)
        report = sub.report([], ["upgraded: foo 1.0 -> 1.1"])
        assert "Actions" in report
        assert "foo" in report
