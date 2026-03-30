"""Tests for complement — convergent detection organelle."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestAssembleMac:
    def test_no_hits_when_clean(self, tmp_path):
        from metabolon.organelles.complement import assemble_mac
        with patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"), \
             patch("metabolon.organelles.complement.recall_infections", return_value=[]):
            hits = assemble_mac()
        assert hits == []

    def test_infection_only(self, tmp_path):
        from metabolon.organelles.complement import assemble_mac
        infections = [{"tool": "broken_tool", "healed": False, "ts": "2026-03-30T10:00:00"}]
        with patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"), \
             patch("metabolon.organelles.complement.recall_infections", return_value=infections):
            hits = assemble_mac()
        assert len(hits) == 1
        assert hits[0]["convergent"] is False
        assert hits[0]["infection_count"] == 1

    def test_convergent_detection(self, tmp_path):
        from metabolon.organelles.complement import assemble_mac
        priming = {"broken_tool": 3}
        priming_path = tmp_path / "priming.json"
        priming_path.write_text(json.dumps(priming))
        infections = [{"tool": "broken_tool", "healed": False, "ts": "2026-03-30T10:00:00"}]
        with patch("metabolon.organelles.complement._PRIMING_PATH", priming_path), \
             patch("metabolon.organelles.complement.recall_infections", return_value=infections):
            hits = assemble_mac()
        convergent_hits = [h for h in hits if h["key"] == "broken_tool"]
        assert len(convergent_hits) == 1
        assert convergent_hits[0]["convergent"] is True
        assert convergent_hits[0]["probe_consecutive_fails"] == 3

    def test_suppressed_keys(self, tmp_path):
        from metabolon.organelles.complement import assemble_mac
        infections = [{"tool": "chromatin", "healed": False, "ts": "2026-03-30T10:00:00"}]
        with patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"), \
             patch("metabolon.organelles.complement.recall_infections", return_value=infections):
            hits = assemble_mac()
        chromatin_hits = [h for h in hits if h["key"] == "chromatin"]
        assert len(chromatin_hits) == 1
        assert chromatin_hits[0]["resolution"] == "suppress"

    def test_healed_infections_excluded(self, tmp_path):
        from metabolon.organelles.complement import assemble_mac
        infections = [{"tool": "healed_tool", "healed": True, "ts": "2026-03-30T10:00:00"}]
        with patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"), \
             patch("metabolon.organelles.complement.recall_infections", return_value=infections):
            hits = assemble_mac()
        assert all(h["key"] != "healed_tool" for h in hits)


class TestResolve:
    def test_quiescent_when_clean(self, tmp_path):
        from metabolon.organelles.complement import resolve
        with patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"), \
             patch("metabolon.organelles.complement.recall_infections", return_value=[]), \
             patch("metabolon.organelles.complement.record_event"), \
             patch("metabolon.organelles.complement.log"):
            result = resolve()
        assert result["status"] == "quiescent"

    def test_active_with_hits(self, tmp_path):
        from metabolon.organelles.complement import resolve
        infections = [{"tool": "real_problem", "healed": False, "ts": "2026-03-30T10:00:00"}]
        with patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"), \
             patch("metabolon.organelles.complement.recall_infections", return_value=infections), \
             patch("metabolon.organelles.complement.record_event"), \
             patch("metabolon.organelles.complement.log"):
            result = resolve()
        assert result["status"] == "active"
        assert result["hits"] >= 1
