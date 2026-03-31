"""Tests for metabolon.enzymes.cytokinesis — gather pre-checks."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.cytokinesis import GatherResult, cytokinesis_gather


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_completed(returncode: int = 0, stdout: str = "", stderr: str = ""):
    """Build a fake CompletedProcess."""
    return MagicMock(
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _ok_payload(**overrides) -> dict:
    """Minimal successful cytokinesis gather JSON."""
    base = {
        "repos": {},
        "skills": {},
        "memory": {"lines": 10, "limit": 150},
        "now": {"age_label": "fresh"},
        "rfts": [],
        "deps": [],
        "reflect": [],
        "methylation": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestGatherHappyPath:
    """When cytokinesis CLI returns valid data."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_clean_session(self, mock_run):
        payload = _ok_payload()
        mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

        result = cytokinesis_gather()

        assert isinstance(result, GatherResult)
        assert result.status == "ok"
        assert result.message == "clean"
        assert result.repos == {}
        assert result.memory == {"lines": 10, "limit": 150}
        assert result.rfts == []
        assert result.deps == []
        assert result.peira is None

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_subprocess_args(self, mock_run):
        mock_run.return_value = _mock_completed(stdout=json.dumps(_ok_payload()))

        cytokinesis_gather()

        mock_run.assert_called_once_with(
            ["cytokinesis", "gather", "--syntactic"],
            capture_output=True,
            text=True,
            timeout=90,
        )

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_peira_forwarded(self, mock_run):
        mock_run.return_value = _mock_completed(
            stdout=json.dumps(_ok_payload(peira="some-branch"))
        )

        result = cytokinesis_gather()
        assert result.peira == "some-branch"

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_skills_forwarded(self, mock_run):
        skills = {"plan": True, "code": True}
        mock_run.return_value = _mock_completed(
            stdout=json.dumps(_ok_payload(skills=skills))
        )

        result = cytokinesis_gather()
        assert result.skills == skills


# ---------------------------------------------------------------------------
# Warning derivation
# ---------------------------------------------------------------------------

class TestGatherWarnings:
    """Warning status when deterministic checks find issues."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_memory_over_limit(self, mock_run):
        payload = _ok_payload(memory={"lines": 200, "limit": 150})
        mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

        result = cytokinesis_gather()

        assert result.status == "warning"
        assert "MEMORY.md 200/150" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_memory_at_limit_ok(self, mock_run):
        payload = _ok_payload(memory={"lines": 150, "limit": 150})
        mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

        result = cytokinesis_gather()
        assert result.status == "ok"

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_tonus_stale(self, mock_run):
        for label in ("stale", "very stale"):
            payload = _ok_payload(now={"age_label": label})
            mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

            result = cytokinesis_gather()
            assert result.status == "warning"
            assert "tonus stale" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_tonus_fresh_ok(self, mock_run):
        payload = _ok_payload(now={"age_label": "fresh"})
        mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

        result = cytokinesis_gather()
        assert result.status == "ok"

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_stale_rfts(self, mock_run):
        rfts = [{"path": "a.md"}, {"path": "b.md"}]
        payload = _ok_payload(rfts=rfts)
        mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

        result = cytokinesis_gather()

        assert result.status == "warning"
        assert "2 stale marks" in result.message
        assert result.rfts == rfts

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_dirty_repos(self, mock_run):
        repos = {
            "germline": {"clean": False},
            "other": {"clean": True},
        }
        payload = _ok_payload(repos=repos)
        mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

        result = cytokinesis_gather()

        assert result.status == "warning"
        assert "dirty: germline" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_multiple_dirty_repos(self, mock_run):
        repos = {
            "germline": {"clean": False},
            "soma": {"clean": False},
            "clean": {"clean": True},
        }
        payload = _ok_payload(repos=repos)
        mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

        result = cytokinesis_gather()

        assert result.status == "warning"
        # Both dirty repos mentioned
        assert "germline" in result.message
        assert "soma" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_combined_warnings(self, mock_run):
        payload = _ok_payload(
            memory={"lines": 300, "limit": 150},
            now={"age_label": "stale"},
            rfts=[{"path": "x"}],
            repos={"r1": {"clean": False}},
        )
        mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

        result = cytokinesis_gather()

        assert result.status == "warning"
        assert "MEMORY.md 300/150" in result.message
        assert "tonus stale" in result.message
        assert "1 stale marks" in result.message
        assert "dirty: r1" in result.message
        # All joined by semicolons
        assert ";" in result.message


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

class TestGatherErrors:
    """Error status when cytokinesis CLI fails."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_nonzero_exit(self, mock_run):
        mock_run.return_value = _mock_completed(returncode=1, stderr="oops")

        result = cytokinesis_gather()

        assert result.status == "error"
        assert "exit 1" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="cytokinesis", timeout=90)

        result = cytokinesis_gather()

        assert result.status == "error"
        assert "timed out" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_bad_json(self, mock_run):
        mock_run.return_value = _mock_completed(stdout="not json {{{")

        result = cytokinesis_gather()

        assert result.status == "error"
        assert "Expecting value" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_cytokinesis_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("cytokinesis not found")

        result = cytokinesis_gather()

        assert result.status == "error"
        assert "not found" in result.message


# ---------------------------------------------------------------------------
# GatherResult model
# ---------------------------------------------------------------------------

class TestGatherResultModel:
    """Verify GatherResult defaults and field types."""

    def test_defaults(self):
        r = GatherResult(status="ok", message="clean")
        assert r.repos == {}
        assert r.skills == {}
        assert r.memory == {}
        assert r.tonus == {}
        assert r.rfts == []
        assert r.deps == []
        assert r.peira is None
        assert r.reflect == []
        assert r.methylation == []

    def test_extra_fields_allowed(self):
        """Secretion base allows extra fields."""
        r = GatherResult(status="ok", message="clean", custom="val")
        assert r.custom == "val"  # type: ignore[attr-defined]
