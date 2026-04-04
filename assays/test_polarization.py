"""Tests for metabolon.enzymes.polarization."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from metabolon.enzymes.polarization import (
    PolarizationPreflightResult,
    _find_cli,
    _guard,
    _preflight,
    polarization,
)
from metabolon.morphology import EffectorResult

# ---------------------------------------------------------------------------
# _find_cli
# ---------------------------------------------------------------------------


class TestFindCli:
    def test_returns_path_when_found(self):
        with patch(
            "metabolon.enzymes.polarization.shutil.which",
            return_value="/usr/local/bin/polarization-gather",
        ):
            assert _find_cli() == "/usr/local/bin/polarization-gather"

    def test_returns_none_when_missing(self):
        with patch("metabolon.enzymes.polarization.shutil.which", return_value=None):
            assert _find_cli() is None


# ---------------------------------------------------------------------------
# _preflight
# ---------------------------------------------------------------------------


class TestPreflight:
    def test_cli_not_found(self):
        with patch("metabolon.enzymes.polarization._find_cli", return_value=None):
            result = _preflight()
        assert isinstance(result, PolarizationPreflightResult)
        assert "not found" in result.summary

    def test_successful_json_output(self):
        payload = {"budget": 42, "guard": "off", "north_stars": 3}
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps(payload)
        mock_proc.stderr = ""
        with (
            patch(
                "metabolon.enzymes.polarization._find_cli", return_value="/bin/polarization-gather"
            ),
            patch("metabolon.enzymes.polarization.subprocess.run", return_value=mock_proc),
        ):
            result = _preflight()
        assert isinstance(result, PolarizationPreflightResult)
        assert result.data["budget"] == 42
        assert "budget" in result.summary

    def test_nonzero_exit_code(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "something broke"
        with (
            patch(
                "metabolon.enzymes.polarization._find_cli", return_value="/bin/polarization-gather"
            ),
            patch("metabolon.enzymes.polarization.subprocess.run", return_value=mock_proc),
        ):
            result = _preflight()
        assert "failed" in result.summary
        assert result.data.get("error") == "something broke"

    def test_timeout(self):
        import subprocess

        with (
            patch(
                "metabolon.enzymes.polarization._find_cli", return_value="/bin/polarization-gather"
            ),
            patch(
                "metabolon.enzymes.polarization.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="x", timeout=30),
            ),
        ):
            result = _preflight()
        assert "timed out" in result.summary


# ---------------------------------------------------------------------------
# _guard
# ---------------------------------------------------------------------------


class TestGuard:
    def test_invalid_action(self):
        result = _guard("explode")
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Invalid" in result.message

    def test_cli_not_found(self):
        with patch("metabolon.enzymes.polarization._find_cli", return_value=None):
            result = _guard("on")
        assert result.success is False
        assert "not found" in result.message

    def test_guard_on_success(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        with (
            patch(
                "metabolon.enzymes.polarization._find_cli", return_value="/bin/polarization-gather"
            ),
            patch("metabolon.enzymes.polarization.subprocess.run", return_value=mock_proc),
        ):
            result = _guard("on")
        assert result.success is True
        assert "activated" in result.message

    def test_guard_off_success(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        with (
            patch(
                "metabolon.enzymes.polarization._find_cli", return_value="/bin/polarization-gather"
            ),
            patch("metabolon.enzymes.polarization.subprocess.run", return_value=mock_proc),
        ):
            result = _guard("off")
        assert result.success is True
        assert "deactivated" in result.message

    def test_guard_failure_exit_code(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "denied"
        with (
            patch(
                "metabolon.enzymes.polarization._find_cli", return_value="/bin/polarization-gather"
            ),
            patch("metabolon.enzymes.polarization.subprocess.run", return_value=mock_proc),
        ):
            result = _guard("on")
        assert result.success is False
        assert "failed" in result.message

    def test_guard_timeout(self):
        import subprocess

        with (
            patch(
                "metabolon.enzymes.polarization._find_cli", return_value="/bin/polarization-gather"
            ),
            patch(
                "metabolon.enzymes.polarization.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="x", timeout=10),
            ),
        ):
            result = _guard("on")
        assert result.success is False
        assert "timed out" in result.message


# ---------------------------------------------------------------------------
# polarization (dispatch)
# ---------------------------------------------------------------------------


class TestPolarizationDispatch:
    def test_unknown_action(self):
        result = polarization("fly")
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Unknown" in result.message

    def test_dispatches_preflight(self):
        with patch(
            "metabolon.enzymes.polarization._preflight",
            return_value=PolarizationPreflightResult(
                raw="",
                data={},
                summary="ok",
            ),
        ) as mock_pf:
            result = polarization("preflight")
        mock_pf.assert_called_once()
        assert isinstance(result, PolarizationPreflightResult)

    def test_dispatches_guard(self):
        with patch(
            "metabolon.enzymes.polarization._guard",
            return_value=EffectorResult(
                success=True,
                message="guard activated.",
            ),
        ) as mock_g:
            result = polarization("guard", guard_action="on")
        mock_g.assert_called_once_with("on")
        assert isinstance(result, EffectorResult)
