from __future__ import annotations

"""Tests for metabolon.metabolism.substrates.hygiene."""


import os
import subprocess
import textwrap
from unittest.mock import patch

from metabolon.metabolism.substrates.hygiene import HygieneSubstrate, _run

# ---------------------------------------------------------------------------
# _run helper
# ---------------------------------------------------------------------------


class TestRun:
    """Tests for the _run wrapper around subprocess.run."""

    @patch("metabolon.metabolism.substrates.hygiene.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo"], returncode=0, stdout="ok\n", stderr=""
        )
        result = _run(["echo", "hello"])
        assert result.returncode == 0
        assert result.stdout == "ok\n"
        mock_run.assert_called_once()

    @patch("metabolon.metabolism.substrates.hygiene.subprocess.run")
    def test_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["slow"], timeout=5)
        result = _run(["slow"], timeout=5)
        assert result.returncode == 1
        assert "timeout" in result.stderr

    @patch("metabolon.metabolism.substrates.hygiene.subprocess.run")
    def test_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("nope")
        result = _run(["nonexistent-binary"])
        assert result.returncode == 1
        assert "not found" in result.stderr


# ---------------------------------------------------------------------------
# _sense_deps
# ---------------------------------------------------------------------------


class TestSenseDeps:
    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_parses_updated_packages(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["uv"],
            returncode=0,
            stdout="Updated foo v1.0.0 -> v1.1.0\nUpdated bar v2.3.0 -> v2.3.1\n",
            stderr="",
        )
        sub = HygieneSubstrate()
        signals = sub._sense_deps()
        assert len(signals) == 2
        assert signals[0]["package"] == "foo"
        assert signals[0]["current"] == "1.0.0"
        assert signals[0]["available"] == "1.1.0"
        assert signals[0]["major"] is False
        assert signals[1]["package"] == "bar"
        assert signals[1]["major"] is False

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_detects_major_bump(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["uv"],
            returncode=0,
            stdout="Updated biglib v1.5.0 -> v2.0.0\n",
            stderr="",
        )
        sub = HygieneSubstrate()
        signals = sub._sense_deps()
        assert len(signals) == 1
        assert signals[0]["major"] is True

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_error_returns_error_signal(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["uv"], returncode=1, stdout="", stderr="lockfile conflict"
        )
        sub = HygieneSubstrate()
        signals = sub._sense_deps()
        assert len(signals) == 1
        assert signals[0]["kind"] == "deps"
        assert "error" in signals[0]

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_no_updates_returns_empty(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["uv"], returncode=0, stdout="", stderr="Resolved 42 packages"
        )
        sub = HygieneSubstrate()
        assert sub._sense_deps() == []

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_would_update_variant(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["uv"],
            returncode=0,
            stdout="Would update baz v0.4.1 -> v0.4.2\n",
            stderr="",
        )
        sub = HygieneSubstrate()
        signals = sub._sense_deps()
        assert len(signals) == 1
        assert signals[0]["package"] == "baz"


# ---------------------------------------------------------------------------
# _sense_hooks
# ---------------------------------------------------------------------------


class TestSenseHooks:
    def test_no_config_returns_empty(self, tmp_path):
        sub = HygieneSubstrate(project_root=tmp_path)
        assert sub._sense_hooks() == []

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_config_unchanged_returns_empty(self, mock_run, tmp_path):
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text("repos: []\n")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pre-commit"], returncode=0, stdout="", stderr=""
        )
        sub = HygieneSubstrate(project_root=tmp_path)
        assert sub._sense_hooks() == []
        # Config should be restored to original
        assert config.read_text() == "repos: []\n"

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_parses_hook_update(self, mock_run, tmp_path):
        config = tmp_path / ".pre-commit-config.yaml"
        original = (
            "repos:\n  - repo: https://github.com/pre-commit/pre-commit-hooks\n    rev: v4.0.0\n"
        )
        config.write_text(original)
        updated_text = (
            "repos:\n  - repo: https://github.com/pre-commit/pre-commit-hooks\n    rev: v4.5.0\n"
        )

        def side_effect(*a, **kw):
            # Simulate autoupdate modifying the config file on disk
            config.write_text(updated_text)
            return subprocess.CompletedProcess(
                args=["pre-commit"],
                returncode=0,
                stdout="updating https://github.com/pre-commit/pre-commit-hooks -> v4.5.0\n",
                stderr="",
            )

        mock_run.side_effect = side_effect
        sub = HygieneSubstrate(project_root=tmp_path)
        signals = sub._sense_hooks()
        # Output parsed a hook update
        assert len(signals) == 1
        assert signals[0]["kind"] == "hook"
        assert signals[0]["repo"] == "https://github.com/pre-commit/pre-commit-hooks"
        assert signals[0]["new_rev"] == "v4.5.0"
        # Config restored
        assert config.read_text() == original

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_autoupdate_error(self, mock_run, tmp_path):
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text("repos: []\n")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pre-commit"], returncode=1, stdout="", stderr="network error"
        )
        sub = HygieneSubstrate(project_root=tmp_path)
        signals = sub._sense_hooks()
        assert len(signals) == 1
        assert signals[0]["kind"] == "hooks"
        assert "error" in signals[0]

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_config_changed_but_no_parsed_output(self, mock_run, tmp_path):
        """Fallback: config changed but output didn't parse."""
        config = tmp_path / ".pre-commit-config.yaml"
        original = "repos:\n  - rev: v1.0\n"
        config.write_text(original)

        # Make the file change after autoupdate (simulate write during run)
        def side_effect(*a, **kw):
            # Simulate autoupdate modifying the config file
            config.write_text("repos:\n  - rev: v2.0\n")
            return subprocess.CompletedProcess(
                args=["pre-commit"], returncode=0, stdout="some opaque output", stderr=""
            )

        mock_run.side_effect = side_effect
        sub = HygieneSubstrate(project_root=tmp_path)
        signals = sub._sense_hooks()
        assert len(signals) == 1
        assert signals[0]["repo"] == "(unknown)"
        assert signals[0]["new_rev"] == "(changed)"
        # Config should be restored
        assert config.read_text() == original


# ---------------------------------------------------------------------------
# _sense_tests
# ---------------------------------------------------------------------------


class TestSenseTests:
    @patch.dict(os.environ, {"VIVESCA_HYGIENE_NO_TESTS": "1"})
    def test_skipped_when_env_set(self, tmp_path):
        sub = HygieneSubstrate(project_root=tmp_path)
        signals = sub._sense_tests()
        assert len(signals) == 1
        assert signals[0]["skipped"] is True
        assert signals[0]["healthy"] is True

    @patch("metabolon.metabolism.substrates.hygiene._run")
    @patch.dict(os.environ, {}, clear=True)
    def test_parses_passed_failed(self, mock_run, tmp_path):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pytest"],
            returncode=1,
            stdout="3 failed, 207 passed\n",
            stderr="",
        )
        sub = HygieneSubstrate(project_root=tmp_path)
        signals = sub._sense_tests()
        assert len(signals) == 1
        assert signals[0]["passed"] == 207
        assert signals[0]["failed"] == 3
        assert signals[0]["errors"] == 0
        assert signals[0]["healthy"] is False

    @patch("metabolon.metabolism.substrates.hygiene._run")
    @patch.dict(os.environ, {}, clear=True)
    def test_all_passed_healthy(self, mock_run, tmp_path):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pytest"],
            returncode=0,
            stdout="42 passed\n",
            stderr="",
        )
        sub = HygieneSubstrate(project_root=tmp_path)
        signals = sub._sense_tests()
        assert signals[0]["passed"] == 42
        assert signals[0]["healthy"] is True

    @patch("metabolon.metabolism.substrates.hygiene._run")
    @patch.dict(os.environ, {}, clear=True)
    def test_errors_detected(self, mock_run, tmp_path):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pytest"],
            returncode=1,
            stdout="2 failed, 40 passed, 1 error\n",
            stderr="",
        )
        sub = HygieneSubstrate(project_root=tmp_path)
        signals = sub._sense_tests()
        assert signals[0]["errors"] == 1
        assert signals[0]["healthy"] is False

    @patch("metabolon.metabolism.substrates.hygiene._run")
    @patch.dict(os.environ, {}, clear=True)
    def test_env_guard_set(self, mock_run, tmp_path):
        """Verify the recursion guard env var is set when calling pytest."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pytest"], returncode=0, stdout="5 passed\n", stderr=""
        )
        sub = HygieneSubstrate(project_root=tmp_path)
        sub._sense_tests()
        # Check that _run was called with env containing the guard
        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs.get("env", {}).get("VIVESCA_HYGIENE_NO_TESTS") == "1"


# ---------------------------------------------------------------------------
# _sense_python
# ---------------------------------------------------------------------------


class TestSensePython:
    def test_reads_pyproject(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            textwrap.dedent("""\
                [project]
                name = "test"
                requires-python = ">=3.11"
            """)
        )
        sub = HygieneSubstrate(project_root=tmp_path)
        signals = sub._sense_python()
        assert len(signals) == 1
        assert signals[0]["kind"] == "python"
        assert signals[0]["current"]  # non-empty
        assert signals[0]["requires"] == ">=3.11"

    def test_no_pyproject(self, tmp_path):
        sub = HygieneSubstrate(project_root=tmp_path)
        signals = sub._sense_python()
        assert signals[0]["requires"] == ""


# ---------------------------------------------------------------------------
# sense (integration of all _sense_* methods)
# ---------------------------------------------------------------------------


class TestSense:
    @patch.object(
        HygieneSubstrate,
        "_sense_python",
        return_value=[{"kind": "python", "current": "3.12.0", "requires": ">=3.11"}],
    )
    @patch.object(
        HygieneSubstrate,
        "_sense_tests",
        return_value=[{"kind": "tests", "passed": 10, "failed": 0, "errors": 0, "healthy": True}],
    )
    @patch.object(HygieneSubstrate, "_sense_hooks", return_value=[])
    @patch.object(HygieneSubstrate, "_sense_deps", return_value=[])
    def test_aggregates_all_signals(self, mock_deps, mock_hooks, mock_tests, mock_py):
        sub = HygieneSubstrate()
        signals = sub.sense()
        kinds = [s["kind"] for s in signals]
        assert "deps" not in kinds  # empty
        assert "tests" in kinds
        assert "python" in kinds


# ---------------------------------------------------------------------------
# candidates
# ---------------------------------------------------------------------------


class TestCandidates:
    def test_filters_actionable_deps(self):
        sub = HygieneSubstrate()
        sensed = [
            {
                "kind": "dep",
                "package": "foo",
                "current": "1.0",
                "available": "1.1",
                "major": False,
            },
            {"kind": "dep", "package": "bar", "current": "2.0", "available": "", "major": False},
        ]
        result = sub.candidates(sensed)
        assert len(result) == 1
        assert result[0]["package"] == "foo"

    def test_filters_actionable_hooks(self):
        sub = HygieneSubstrate()
        sensed = [
            {"kind": "hook", "repo": "r1", "new_rev": "v2"},
        ]
        result = sub.candidates(sensed)
        assert len(result) == 1

    def test_filters_unhealthy_tests(self):
        sub = HygieneSubstrate()
        sensed = [
            {"kind": "tests", "passed": 10, "failed": 1, "errors": 0, "healthy": False},
            {"kind": "tests", "passed": 10, "failed": 0, "errors": 0, "healthy": True},
        ]
        result = sub.candidates(sensed)
        assert len(result) == 1
        assert result[0]["healthy"] is False

    def test_includes_error_signals(self):
        sub = HygieneSubstrate()
        sensed = [
            {"kind": "deps", "error": "lockfile conflict"},
        ]
        result = sub.candidates(sensed)
        assert len(result) == 1

    def test_empty_input(self):
        sub = HygieneSubstrate()
        assert sub.candidates([]) == []

    def test_python_not_actionable(self):
        sub = HygieneSubstrate()
        sensed = [
            {"kind": "python", "current": "3.11.0", "requires": ">=3.10"},
        ]
        assert sub.candidates(sensed) == []


# ---------------------------------------------------------------------------
# act
# ---------------------------------------------------------------------------


class TestAct:
    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_minor_dep_upgraded(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["uv"], returncode=0, stdout="", stderr=""
        )
        sub = HygieneSubstrate()
        result = sub.act(
            {
                "kind": "dep",
                "package": "foo",
                "current": "1.0.0",
                "available": "1.1.0",
                "major": False,
            }
        )
        assert "upgraded" in result
        assert "foo" in result

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_major_dep_proposed(self, mock_run):
        sub = HygieneSubstrate()
        result = sub.act(
            {
                "kind": "dep",
                "package": "big",
                "current": "1.0.0",
                "available": "2.0.0",
                "major": True,
            }
        )
        assert "propose" in result
        mock_run.assert_not_called()

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_dep_upgrade_failure(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["uv"], returncode=1, stdout="", stderr="resolution failed badly"
        )
        sub = HygieneSubstrate()
        result = sub.act(
            {
                "kind": "dep",
                "package": "foo",
                "current": "1.0",
                "available": "1.1",
                "major": False,
            }
        )
        assert "failed" in result

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_hook_update_success(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pre-commit"], returncode=0, stdout="", stderr=""
        )
        sub = HygieneSubstrate()
        result = sub.act(
            {
                "kind": "hook",
                "repo": "https://github.com/example/hooks",
                "new_rev": "v3.0",
            }
        )
        assert "updated" in result

    @patch("metabolon.metabolism.substrates.hygiene._run")
    def test_hook_update_failure(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pre-commit"], returncode=1, stdout="", stderr="git error"
        )
        sub = HygieneSubstrate()
        result = sub.act(
            {
                "kind": "hook",
                "repo": "https://github.com/example/hooks",
                "new_rev": "v3.0",
            }
        )
        assert "failed" in result

    def test_tests_propose(self):
        sub = HygieneSubstrate()
        result = sub.act(
            {
                "kind": "tests",
                "failed": 3,
                "errors": 1,
            }
        )
        assert "propose" in result
        assert "3" in result
        assert "1" in result

    def test_error_signal(self):
        sub = HygieneSubstrate()
        result = sub.act(
            {
                "kind": "deps",
                "error": "lockfile conflict",
            }
        )
        assert "propose" in result
        assert "fix" in result

    def test_unknown_kind(self):
        sub = HygieneSubstrate()
        result = sub.act({"kind": "weird"})
        assert "unknown" in result


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


class TestReport:
    def test_full_report(self):
        sub = HygieneSubstrate()
        sensed = [
            {
                "kind": "dep",
                "package": "foo",
                "current": "1.0",
                "available": "1.1",
                "major": False,
            },
            {"kind": "dep", "package": "bar", "current": "2.0", "available": "3.0", "major": True},
            {"kind": "hook", "repo": "https://github.com/example", "new_rev": "v2"},
            {"kind": "tests", "passed": 100, "failed": 2, "errors": 0, "healthy": False},
            {"kind": "python", "current": "3.12.0", "requires": ">=3.11"},
        ]
        acted = ["upgraded: foo 1.0 -> 1.1"]
        report = sub.report(sensed, acted)
        assert "5 artifact" in report
        assert "Hygiene substrate" in report
        assert "foo" in report
        assert "MAJOR" in report
        assert "UNHEALTHY" in report
        assert "upgraded: foo" in report
        assert "Python" in report

    def test_empty_report(self):
        sub = HygieneSubstrate()
        report = sub.report([], [])
        assert "0 artifact" in report
        assert "all fresh" in report

    def test_healthy_tests(self):
        sub = HygieneSubstrate()
        sensed = [{"kind": "tests", "passed": 50, "failed": 0, "errors": 0, "healthy": True}]
        report = sub.report(sensed, [])
        assert "healthy" in report

    def test_error_section(self):
        sub = HygieneSubstrate()
        sensed = [
            {"kind": "deps", "error": "lockfile conflict"},
        ]
        report = sub.report(sensed, [])
        assert "Errors" in report
        assert "lockfile conflict" in report
