from __future__ import annotations

"""Tests for angiogenesis — hypoxia detection, vessel proposals, and registry."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

import metabolon.organelles.angiogenesis as angiogenesis


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(tool: str, ts: str, healed: bool = False) -> dict:
    return {"tool": tool, "ts": ts, "healed": healed}


def _iso(seconds_ago: float) -> str:
    """Return an ISO timestamp `seconds_ago` in the past."""
    return (datetime.now(UTC) - timedelta(seconds=seconds_ago)).isoformat()


# ---------------------------------------------------------------------------
# TestDetectHypoxia
# ---------------------------------------------------------------------------


class TestDetectHypoxia:
    """detect_hypoxia() reads the infection log and finds co-failing pairs."""

    def test_no_log_file_returns_empty(self, tmp_path):
        with patch.object(angiogenesis, "INFECTION_LOG", tmp_path / "nope.jsonl"):
            result = angiogenesis.detect_hypoxia()
        assert result == []

    def test_empty_log_returns_empty(self, tmp_path):
        log = tmp_path / "infections.jsonl"
        log.write_text("")
        with patch.object(angiogenesis, "INFECTION_LOG", log):
            result = angiogenesis.detect_hypoxia()
        assert result == []

    def test_healed_events_ignored(self, tmp_path):
        log = tmp_path / "infections.jsonl"
        log.write_text(json.dumps(_make_event("tool_a", _iso(100), healed=True)) + "\n")
        with patch.object(angiogenesis, "INFECTION_LOG", log):
            result = angiogenesis.detect_hypoxia()
        assert result == []

    def test_single_event_no_pair(self, tmp_path):
        log = tmp_path / "infections.jsonl"
        log.write_text(json.dumps(_make_event("tool_a", _iso(100))) + "\n")
        with patch.object(angiogenesis, "INFECTION_LOG", log):
            result = angiogenesis.detect_hypoxia()
        assert result == []

    def test_below_threshold_no_hypoxia(self, tmp_path):
        """Two co-failures of the same pair (below threshold of 3) -> no hypoxia."""
        log = tmp_path / "infections.jsonl"
        events = [
            _make_event("tool_a", _iso(200)),
            _make_event("tool_b", _iso(190)),
            _make_event("tool_a", _iso(100)),
            _make_event("tool_b", _iso(90)),
        ]
        log.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        with patch.object(angiogenesis, "INFECTION_LOG", log):
            result = angiogenesis.detect_hypoxia()
        # Only 2 co-failures, threshold is 3
        assert result == []

    def test_meets_threshold_returns_pair(self, tmp_path):
        """3+ co-failures within the window -> hypoxic pair detected."""
        log = tmp_path / "infections.jsonl"
        events = []
        # 3 pairs of (tool_a, tool_b) failing close together
        for offset in (600, 400, 200):
            events.append(_make_event("tool_a", _iso(offset)))
            events.append(_make_event("tool_b", _iso(offset - 5)))
        log.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        with patch.object(angiogenesis, "INFECTION_LOG", log):
            result = angiogenesis.detect_hypoxia()
        assert len(result) >= 1
        pair = result[0]
        assert pair["source"] == "tool_a"
        assert pair["target"] == "tool_b"
        assert pair["co_failures"] >= 3
        assert "last_seen" in pair

    def test_same_tool_pairs_excluded(self, tmp_path):
        """Consecutive failures of the same tool should not produce a pair."""
        log = tmp_path / "infections.jsonl"
        events = []
        for i in range(5):
            events.append(_make_event("tool_a", _iso(100 - i * 10)))
        log.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        with patch.object(angiogenesis, "INFECTION_LOG", log):
            result = angiogenesis.detect_hypoxia()
        assert result == []

    def test_events_beyond_window_not_paired(self, tmp_path):
        """tool_b failing >300s after tool_a should not be counted as a pair."""
        log = tmp_path / "infections.jsonl"
        events = [
            _make_event("tool_a", _iso(600)),
            _make_event("tool_b", _iso(200)),  # 400s later -> beyond window
        ]
        log.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        with patch.object(angiogenesis, "INFECTION_LOG", log):
            result = angiogenesis.detect_hypoxia()
        assert result == []

    def test_malformed_lines_skipped(self, tmp_path):
        """Bad JSON lines should be silently skipped."""
        log = tmp_path / "infections.jsonl"
        log.write_text("not json\n{bad\n")
        with patch.object(angiogenesis, "INFECTION_LOG", log):
            result = angiogenesis.detect_hypoxia()
        assert result == []

    def test_result_structure(self, tmp_path):
        """Each result dict has source, target, co_failures, last_seen."""
        log = tmp_path / "infections.jsonl"
        events = []
        for offset in (500, 300, 100):
            events.append(_make_event("alpha", _iso(offset)))
            events.append(_make_event("beta", _iso(offset - 3)))
        log.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        with patch.object(angiogenesis, "INFECTION_LOG", log):
            result = angiogenesis.detect_hypoxia()
        assert len(result) >= 1
        item = result[0]
        assert set(item.keys()) == {"source", "target", "co_failures", "last_seen"}


# ---------------------------------------------------------------------------
# TestProposeVessel
# ---------------------------------------------------------------------------


class TestProposeVessel:
    """propose_vessel() builds a proposal dict and appends it to the log."""

    def test_returns_proposal_dict(self, tmp_path):
        proposal_log = tmp_path / "proposals.jsonl"
        with patch.object(angiogenesis, "PROPOSAL_LOG", proposal_log):
            result = angiogenesis.propose_vessel("svc_a", "svc_b")
        assert isinstance(result, dict)
        assert result["source"] == "svc_a"
        assert result["target"] == "svc_b"
        assert result["status"] == "proposed"
        assert result["vessel_type"] == "pipeline"
        assert "description" in result
        assert "svc_a" in result["description"]
        assert "svc_b" in result["description"]

    def test_timestamp_is_iso_format(self, tmp_path):
        proposal_log = tmp_path / "proposals.jsonl"
        with patch.object(angiogenesis, "PROPOSAL_LOG", proposal_log):
            result = angiogenesis.propose_vessel("x", "y")
        # Should parse as ISO datetime
        datetime.fromisoformat(result["ts"])

    def test_appends_to_log(self, tmp_path):
        proposal_log = tmp_path / "proposals.jsonl"
        with patch.object(angiogenesis, "PROPOSAL_LOG", proposal_log):
            angiogenesis.propose_vessel("a", "b")
            angiogenesis.propose_vessel("c", "d")
        lines = proposal_log.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["source"] == "a"
        assert json.loads(lines[1])["source"] == "c"

    def test_creates_parent_directory(self, tmp_path):
        proposal_log = tmp_path / "deep" / "nested" / "proposals.jsonl"
        with patch.object(angiogenesis, "PROPOSAL_LOG", proposal_log):
            result = angiogenesis.propose_vessel("x", "y")
        assert proposal_log.exists()
        assert json.loads(proposal_log.read_text().strip())["source"] == "x"


# ---------------------------------------------------------------------------
# TestVesselRegistry
# ---------------------------------------------------------------------------


class TestVesselRegistry:
    """vessel_registry() reads the JSON registry file."""

    def test_no_registry_returns_empty(self, tmp_path):
        reg = tmp_path / "vessels.json"
        with patch.object(angiogenesis, "VESSEL_REGISTRY", reg):
            result = angiogenesis.vessel_registry()
        assert result == []

    def test_reads_existing_registry(self, tmp_path):
        reg = tmp_path / "vessels.json"
        data = [{"source": "a", "target": "b"}, {"source": "c", "target": "d"}]
        reg.write_text(json.dumps(data))
        with patch.object(angiogenesis, "VESSEL_REGISTRY", reg):
            result = angiogenesis.vessel_registry()
        assert len(result) == 2
        assert result[0]["source"] == "a"
        assert result[1]["target"] == "d"

    def test_malformed_json_returns_empty(self, tmp_path):
        reg = tmp_path / "vessels.json"
        reg.write_text("not valid json{{{")
        with patch.object(angiogenesis, "VESSEL_REGISTRY", reg):
            result = angiogenesis.vessel_registry()
        assert result == []

    def test_empty_array_returns_empty(self, tmp_path):
        reg = tmp_path / "vessels.json"
        reg.write_text("[]")
        with patch.object(angiogenesis, "VESSEL_REGISTRY", reg):
            result = angiogenesis.vessel_registry()
        assert result == []
