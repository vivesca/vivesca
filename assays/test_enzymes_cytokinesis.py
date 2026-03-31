from __future__ import annotations

"""Additional edge-case tests for metabolon.enzymes.cytokinesis gather."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.cytokinesis import GatherResult, cytokinesis_gather


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(returncode: int = 0, stdout: str = "", stderr: str = ""):
    return MagicMock(returncode=returncode, stdout=stdout, stderr=stderr)


def _payload(**overrides) -> dict:
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
# Field forwarding
# ---------------------------------------------------------------------------

class TestFieldForwarding:
    """Ensure all JSON keys are forwarded to GatherResult."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_deps_forwarded(self, mock_run):
        deps = ["pkg-a==1.0", "pkg-b>=2.0"]
        mock_run.return_value = _run(stdout=json.dumps(_payload(deps=deps)))
        result = cytokinesis_gather()
        assert result.status == "ok"
        assert result.deps == deps

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_reflect_forwarded(self, mock_run):
        reflect = ["note-1", "note-2"]
        mock_run.return_value = _run(stdout=json.dumps(_payload(reflect=reflect)))
        result = cytokinesis_gather()
        assert result.reflect == reflect

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_methylation_forwarded(self, mock_run):
        meth = ["methyl-item"]
        mock_run.return_value = _run(stdout=json.dumps(_payload(methylation=meth)))
        result = cytokinesis_gather()
        assert result.methylation == meth

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_tonus_forwarded(self, mock_run):
        now = {"age_label": "fresh", "hours": 1.2}
        mock_run.return_value = _run(stdout=json.dumps(_payload(now=now)))
        result = cytokinesis_gather()
        assert result.tonus == now

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_repos_with_clean_true(self, mock_run):
        repos = {"germline": {"clean": True}, "other": {"clean": True}}
        mock_run.return_value = _run(stdout=json.dumps(_payload(repos=repos)))
        result = cytokinesis_gather()
        assert result.status == "ok"
        assert result.repos == repos


# ---------------------------------------------------------------------------
# Missing / partial JSON keys
# ---------------------------------------------------------------------------

class TestPartialJson:
    """Gracefully handle missing keys in CLI output."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_empty_json_object(self, mock_run):
        mock_run.return_value = _run(stdout=json.dumps({}))
        result = cytokinesis_gather()
        # No repos, no memory over limit, no stale tonus, no rfts → ok
        assert result.status == "ok"
        assert result.memory == {}
        assert result.rfts == []

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_missing_memory_key(self, mock_run):
        payload = _payload()
        del payload["memory"]
        mock_run.return_value = _run(stdout=json.dumps(payload))
        result = cytokinesis_gather()
        # mem.get("lines", 0) → 0, mem.get("limit", 150) → 150 → not over
        assert result.status == "ok"

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_missing_now_key(self, mock_run):
        payload = _payload()
        del payload["now"]
        mock_run.return_value = _run(stdout=json.dumps(payload))
        result = cytokinesis_gather()
        assert result.status == "ok"

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_missing_rfts_key(self, mock_run):
        payload = _payload()
        del payload["rfts"]
        mock_run.return_value = _run(stdout=json.dumps(payload))
        result = cytokinesis_gather()
        assert result.status == "ok"
        assert result.rfts == []


# ---------------------------------------------------------------------------
# Warning boundary conditions
# ---------------------------------------------------------------------------

class TestWarningBoundaries:
    """Fine-grained boundary checks for warning derivation."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_memory_one_below_limit(self, mock_run):
        mock_run.return_value = _run(
            stdout=json.dumps(_payload(memory={"lines": 149, "limit": 150}))
        )
        result = cytokinesis_gather()
        assert result.status == "ok"

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_memory_one_over_limit(self, mock_run):
        mock_run.return_value = _run(
            stdout=json.dumps(_payload(memory={"lines": 151, "limit": 150}))
        )
        result = cytokinesis_gather()
        assert result.status == "warning"
        assert "151/150" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_tonus_very_stale(self, mock_run):
        mock_run.return_value = _run(
            stdout=json.dumps(_payload(now={"age_label": "very stale"}))
        )
        result = cytokinesis_gather()
        assert result.status == "warning"
        assert "tonus stale" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_tonus_unknown_label_ok(self, mock_run):
        """Labels other than stale/very stale should not trigger warning."""
        mock_run.return_value = _run(
            stdout=json.dumps(_payload(now={"age_label": "moderate"}))
        )
        result = cytokinesis_gather()
        assert result.status == "ok"

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_single_rft_warning(self, mock_run):
        mock_run.return_value = _run(
            stdout=json.dumps(_payload(rfts=[{"path": "single.md"}]))
        )
        result = cytokinesis_gather()
        assert result.status == "warning"
        assert "1 stale marks" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_empty_rfts_ok(self, mock_run):
        mock_run.return_value = _run(
            stdout=json.dumps(_payload(rfts=[]))
        )
        result = cytokinesis_gather()
        assert result.status == "ok"


# ---------------------------------------------------------------------------
# Error result shape
# ---------------------------------------------------------------------------

class TestErrorResultShape:
    """Error results should still be GatherResult with sensible defaults."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_error_has_defaults(self, mock_run):
        mock_run.return_value = _run(returncode=2)
        result = cytokinesis_gather()
        assert isinstance(result, GatherResult)
        assert result.status == "error"
        assert result.repos == {}
        assert result.rfts == []
        assert result.peira is None

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_error_message_contains_exit_code(self, mock_run):
        mock_run.return_value = _run(returncode=42)
        result = cytokinesis_gather()
        assert "42" in result.message


# ---------------------------------------------------------------------------
# GatherResult model edge cases
# ---------------------------------------------------------------------------

class TestGatherResultModelEdgeCases:

    def test_status_required(self):
        with pytest.raises(Exception):
            GatherResult(message="clean")

    def test_message_required(self):
        with pytest.raises(Exception):
            GatherResult(status="ok")

    def test_full_construction(self):
        r = GatherResult(
            status="warning",
            message="test",
            repos={"r": {"clean": False}},
            skills={"s": True},
            memory={"lines": 1, "limit": 2},
            tonus={"age_label": "stale"},
            rfts=[{"path": "a"}],
            deps=["d"],
            peira="branch",
            reflect=["ref"],
            methylation=["meth"],
        )
        assert r.status == "warning"
        assert r.repos["r"]["clean"] is False
        assert r.peira == "branch"

    def test_is_secretion_subclass(self):
        from metabolon.morphology import Secretion

        assert issubclass(GatherResult, Secretion)


# ---------------------------------------------------------------------------
# Tool decorator attributes
# ---------------------------------------------------------------------------

class TestToolDecorator:
    """Verify the @tool decorator was applied correctly."""

    def test_tool_name(self):
        meta = cytokinesis_gather.__fastmcp__
        assert meta.name == "cytokinesis_gather"

    def test_tool_readonly(self):
        ann = cytokinesis_gather.__fastmcp__.annotations
        assert ann.readOnlyHint is True
        assert ann.destructiveHint is False
