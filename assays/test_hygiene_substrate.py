from __future__ import annotations

"""Tests for HygieneSubstrate — tooling health metabolism."""


from unittest.mock import patch

from metabolon.metabolism.substrate import Substrate
from metabolon.metabolism.substrates.hygiene import HygieneSubstrate


def test_implements_substrate_protocol():
    s = HygieneSubstrate()
    assert isinstance(s, Substrate)
    assert s.name == "hygiene"


def _mock_run(stdout: str = "", stderr: str = "", returncode: int = 0):
    """Create a mock CompletedProcess."""
    from subprocess import CompletedProcess

    return CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


class TestSenseDeps:
    def test_parses_upgrade_output(self, tmp_path):
        s = HygieneSubstrate(project_root=tmp_path)
        mock_output = _mock_run(
            stderr="Updated click v8.1.0 -> v8.2.0\nUpdated pydantic v2.0.0 -> v3.0.0\n"
        )
        with patch("metabolon.metabolism.substrates.hygiene._run", return_value=mock_output):
            result = s._sense_deps()

        assert len(result) == 2
        assert result[0]["package"] == "click"
        assert result[0]["current"] == "8.1.0"
        assert result[0]["available"] == "8.2.0"
        assert result[0]["major"] is False

        assert result[1]["package"] == "pydantic"
        assert result[1]["major"] is True

    def test_handles_no_upgrades(self, tmp_path):
        s = HygieneSubstrate(project_root=tmp_path)
        mock_output = _mock_run(stderr="Resolved 80 packages in 1.2s\n")
        with patch("metabolon.metabolism.substrates.hygiene._run", return_value=mock_output):
            result = s._sense_deps()
        assert result == []

    def test_handles_uv_failure(self, tmp_path):
        s = HygieneSubstrate(project_root=tmp_path)
        mock_output = _mock_run(stderr="error: no pyproject.toml found", returncode=1)
        with patch("metabolon.metabolism.substrates.hygiene._run", return_value=mock_output):
            result = s._sense_deps()
        assert len(result) == 1
        assert result[0]["kind"] == "deps"
        assert "error" in result[0]


class TestSenseHooks:
    def test_no_config_returns_empty(self, tmp_path):
        s = HygieneSubstrate(project_root=tmp_path)
        assert s._sense_hooks() == []

    def test_parses_update_output(self, tmp_path):
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text("repos: []")
        s = HygieneSubstrate(project_root=tmp_path)
        mock_output = _mock_run(
            stdout="updating https://github.com/astral-sh/ruff-pre-commit -> v0.16.0\n"
        )

        def fake_run(*args, **kwargs):
            # Simulate autoupdate modifying the config
            config.write_text("repos: [updated]")
            return mock_output

        with patch("metabolon.metabolism.substrates.hygiene._run", side_effect=fake_run):
            result = s._sense_hooks()
        assert len(result) == 1
        assert result[0]["kind"] == "hook"
        assert "ruff" in result[0]["repo"]
        assert result[0]["new_rev"] == "v0.16.0"
        # Config should be restored
        assert config.read_text() == "repos: []"


class TestSenseTests:
    def test_parses_passing_suite(self, tmp_path):
        s = HygieneSubstrate(project_root=tmp_path)
        mock_output = _mock_run(stdout="210 passed in 5.0s\n")
        with patch("metabolon.metabolism.substrates.hygiene._run", return_value=mock_output):
            result = s._sense_tests()
        assert result[0]["passed"] == 210
        assert result[0]["failed"] == 0
        assert result[0]["healthy"] is True

    def test_parses_failing_suite(self, tmp_path):
        s = HygieneSubstrate(project_root=tmp_path)
        mock_output = _mock_run(stdout="3 failed, 207 passed in 5.0s\n", returncode=1)
        with patch("metabolon.metabolism.substrates.hygiene._run", return_value=mock_output):
            result = s._sense_tests()
        assert result[0]["failed"] == 3
        assert result[0]["passed"] == 207
        assert result[0]["healthy"] is False


class TestSensePython:
    def test_reads_version(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')
        s = HygieneSubstrate(project_root=tmp_path)
        result = s._sense_python()
        assert result[0]["kind"] == "python"
        assert result[0]["requires"] == ">=3.11"
        assert "." in result[0]["current"]  # has a version string


class TestCandidates:
    def test_filters_actionable(self):
        s = HygieneSubstrate()
        sensed = [
            {
                "kind": "dep",
                "package": "click",
                "current": "8.1",
                "available": "8.2",
                "major": False,
            },
            {"kind": "tests", "passed": 210, "failed": 0, "errors": 0, "healthy": True},
            {"kind": "python", "current": "3.13.12", "requires": ">=3.11"},
        ]
        candidates = s.candidates(sensed)
        assert len(candidates) == 1
        assert candidates[0]["package"] == "click"

    def test_includes_unhealthy_tests(self):
        s = HygieneSubstrate()
        sensed = [
            {"kind": "tests", "passed": 207, "failed": 3, "errors": 0, "healthy": False},
        ]
        candidates = s.candidates(sensed)
        assert len(candidates) == 1


class TestAct:
    def test_major_dep_proposes_only(self):
        s = HygieneSubstrate()
        result = s.act(
            {
                "kind": "dep",
                "package": "pydantic",
                "current": "2.0",
                "available": "3.0",
                "major": True,
            }
        )
        assert result.startswith("propose:")
        assert "MAJOR" in result

    def test_minor_dep_executes(self, tmp_path):
        s = HygieneSubstrate(project_root=tmp_path)
        mock_output = _mock_run()
        with patch("metabolon.metabolism.substrates.hygiene._run", return_value=mock_output):
            result = s.act(
                {
                    "kind": "dep",
                    "package": "click",
                    "current": "8.1",
                    "available": "8.2",
                    "major": False,
                }
            )
        assert result.startswith("upgraded:")

    def test_test_failure_proposes(self):
        s = HygieneSubstrate()
        result = s.act({"kind": "tests", "failed": 3, "errors": 0})
        assert result.startswith("propose:")


class TestReport:
    def test_full_report(self):
        s = HygieneSubstrate()
        sensed = [
            {
                "kind": "dep",
                "package": "click",
                "current": "8.1",
                "available": "8.2",
                "major": False,
            },
            {"kind": "tests", "passed": 210, "failed": 0, "errors": 0, "healthy": True},
            {"kind": "python", "current": "3.13.12", "requires": ">=3.11"},
        ]
        acted = ["upgraded: click 8.1 -> 8.2"]
        report = s.report(sensed, acted)
        assert "Hygiene substrate" in report
        assert "click" in report
        assert "upgraded" in report
        assert "healthy" in report
        assert "3.13.12" in report

    def test_empty_report(self):
        s = HygieneSubstrate()
        report = s.report([], [])
        assert "0 artifact(s)" in report
