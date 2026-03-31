from __future__ import annotations

"""Tests for angiogenesis — subsystem integration detector."""

import json
from datetime import datetime, UTC, timedelta
from unittest.mock import patch

import pytest


class TestDetectHypoxia:
    def test_no_log_file(self, tmp_path):
        from metabolon.organelles.angiogenesis import detect_hypoxia
        import metabolon.organelles.angiogenesis as angio
        with patch.object(angio, "INFECTION_LOG", tmp_path / "nope.jsonl"):
            assert detect_hypoxia() == []

    def test_empty_log(self, tmp_path):
        from metabolon.organelles.angiogenesis import detect_hypoxia
        import metabolon.organelles.angiogenesis as angio
        log = tmp_path / "infections.jsonl"
        log.write_text("")
        with patch.object(angio, "INFECTION_LOG", log):
            assert detect_hypoxia() == []

    def test_detects_cofailure_pair(self, tmp_path):
        from metabolon.organelles.angiogenesis import detect_hypoxia
        import metabolon.organelles.angiogenesis as angio
        log = tmp_path / "infections.jsonl"
        base = datetime(2026, 3, 30, 10, 0, 0, tzinfo=UTC)
        # Create 4 sequential A→B failures (within 300s window)
        entries = []
        for i in range(4):
            ts_a = (base + timedelta(minutes=i * 10)).isoformat()
            ts_b = (base + timedelta(minutes=i * 10, seconds=30)).isoformat()
            entries.append(json.dumps({"tool": "toolA", "ts": ts_a, "healed": False}))
            entries.append(json.dumps({"tool": "toolB", "ts": ts_b, "healed": False}))
        log.write_text("\n".join(entries) + "\n")
        with patch.object(angio, "INFECTION_LOG", log):
            pairs = detect_hypoxia()
        # Should find toolA→toolB pair with co_failures >= 3
        ab_pair = [p for p in pairs if p["source"] == "toolA" and p["target"] == "toolB"]
        assert len(ab_pair) >= 1
        assert ab_pair[0]["co_failures"] >= 3

    def test_ignores_healed(self, tmp_path):
        from metabolon.organelles.angiogenesis import detect_hypoxia
        import metabolon.organelles.angiogenesis as angio
        log = tmp_path / "infections.jsonl"
        entries = [json.dumps({"tool": "x", "ts": "2026-03-30T10:00:00+00:00", "healed": True})]
        log.write_text("\n".join(entries) + "\n")
        with patch.object(angio, "INFECTION_LOG", log):
            assert detect_hypoxia() == []


class TestProposeVessel:
    def test_creates_proposal(self, tmp_path):
        from metabolon.organelles.angiogenesis import propose_vessel
        import metabolon.organelles.angiogenesis as angio
        proposal_log = tmp_path / "proposals.jsonl"
        with patch.object(angio, "PROPOSAL_LOG", proposal_log):
            result = propose_vessel("toolA", "toolB")
        assert result["source"] == "toolA"
        assert result["target"] == "toolB"
        assert result["status"] == "proposed"
        assert proposal_log.exists()


class TestVesselRegistry:
    def test_no_registry(self, tmp_path):
        from metabolon.organelles.angiogenesis import vessel_registry
        import metabolon.organelles.angiogenesis as angio
        with patch.object(angio, "VESSEL_REGISTRY", tmp_path / "nope.json"):
            assert vessel_registry() == []

    def test_reads_registry(self, tmp_path):
        from metabolon.organelles.angiogenesis import vessel_registry
        import metabolon.organelles.angiogenesis as angio
        reg = tmp_path / "vessels.json"
        reg.write_text(json.dumps([{"source": "a", "target": "b"}]))
        with patch.object(angio, "VESSEL_REGISTRY", reg):
            result = vessel_registry()
        assert len(result) == 1
        assert result[0]["source"] == "a"
