from __future__ import annotations

"""Tests for metabolon.organelles.angiogenesis — hypoxia detection and vessel proposals."""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.angiogenesis import (
    INFECTION_LOG,
    PROPOSAL_LOG,
    VESSEL_REGISTRY,
    _HYPOXIA_THRESHOLD,
    _SEQUENCE_WINDOW_S,
    detect_hypoxia,
    propose_vessel,
    vessel_registry,
)


# ---------------------------------------------------------------------------
# detect_hypoxia
# ---------------------------------------------------------------------------

class TestDetectHypoxia:
    """Tests for the detect_hypoxia() function."""

    def test_no_infection_log_returns_empty(self):
        """When the infection log file doesn't exist, return []."""
        fake_log = Path("/tmp/angiogenesis_test_missing_2781.jsonl")
        with patch("metabolon.organelles.angiogenesis.INFECTION_LOG", fake_log):
            assert detect_hypoxia() == []

    def test_empty_log_returns_empty(self, tmp_path: Path):
        """An empty infection log yields no pairs."""
        fake_log = tmp_path / "infections.jsonl"
        fake_log.write_text("")
        with patch("metabolon.organelles.angiogenesis.INFECTION_LOG", fake_log):
            assert detect_hypoxia() == []

    def test_only_healed_events_returns_empty(self, tmp_path: Path):
        """Healed events (healed=True) are ignored."""
        fake_log = tmp_path / "infections.jsonl"
        fake_log.write_text(
            json.dumps({"ts": "2025-01-01T00:00:00+00:00", "tool": "a", "healed": True})
            + "\n"
        )
        with patch("metabolon.organelles.angiogenesis.INFECTION_LOG", fake_log):
            assert detect_hypoxia() == []

    def test_below_threshold_returns_empty(self, tmp_path: Path):
        """Fewer than _HYPOXIA_THRESHOLD co-failures produces no results."""
        fake_log = tmp_path / "infections.jsonl"
        # Two a→b pairs spaced >300s apart so the O(n²) logic only
        # counts direct neighbours, yielding 2 co-failures (< threshold 3).
        events = [
            {"ts": "2025-01-01T00:00:00+00:00", "tool": "a", "healed": False},
            {"ts": "2025-01-01T00:00:10+00:00", "tool": "b", "healed": False},
            {"ts": "2025-01-01T00:10:00+00:00", "tool": "a", "healed": False},
            {"ts": "2025-01-01T00:10:10+00:00", "tool": "b", "healed": False},
        ]
        fake_log.write_text("\n".join(json.dumps(e) for e in events))
        with patch("metabolon.organelles.angiogenesis.INFECTION_LOG", fake_log):
            assert detect_hypoxia() == []

    def test_hypoxic_pair_detected(self, tmp_path: Path):
        """A pair with >= _HYPOXIA_THRESHOLD co-failures is detected."""
        fake_log = tmp_path / "infections.jsonl"
        base_ts = "2025-01-01T00:00:"
        events = []
        for i in range(_HYPOXIA_THRESHOLD):
            sec = i * 20  # 20s apart, well within 300s window
            events.append({"ts": f"{base_ts}{sec:02d}+00:00", "tool": "alpha", "healed": False})
            events.append({"ts": f"{base_ts}{sec + 5:02d}+00:00", "tool": "beta", "healed": False})

        fake_log.write_text("\n".join(json.dumps(e) for e in events))
        with patch("metabolon.organelles.angiogenesis.INFECTION_LOG", fake_log):
            result = detect_hypoxia()

        assert len(result) >= 1
        pair = result[0]
        assert pair["source"] == "alpha"
        assert pair["target"] == "beta"
        assert pair["co_failures"] >= _HYPOXIA_THRESHOLD
        assert "last_seen" in pair

    def test_same_tool_pair_not_counted(self, tmp_path: Path):
        """Pairs where both tools are the same are excluded."""
        fake_log = tmp_path / "infections.jsonl"
        events = []
        for i in range(5):
            ts = f"2025-01-01T00:{i:02d}:00+00:00"
            events.append({"ts": ts, "tool": "solo", "healed": False})
        fake_log.write_text("\n".join(json.dumps(e) for e in events))
        with patch("metabolon.organelles.angiogenesis.INFECTION_LOG", fake_log):
            assert detect_hypoxia() == []

    def test_events_beyond_window_not_paired(self, tmp_path: Path):
        """Events separated by more than _SEQUENCE_WINDOW_S are not co-failures."""
        fake_log = tmp_path / "infections.jsonl"
        t0 = "2025-01-01T00:00:00+00:00"
        # 600s later = beyond the 300s window
        t1 = "2025-01-01T00:10:00+00:00"
        events = [
            {"ts": t0, "tool": "x", "healed": False},
            {"ts": t1, "tool": "y", "healed": False},
        ] * 4  # repeat enough times
        fake_log.write_text("\n".join(json.dumps(e) for e in events))
        with patch("metabolon.organelles.angiogenesis.INFECTION_LOG", fake_log):
            assert detect_hypoxia() == []

    def test_malformed_json_lines_skipped(self, tmp_path: Path):
        """Malformed lines in the log are silently ignored."""
        fake_log = tmp_path / "infections.jsonl"
        events = [
            "BAD LINE",
            json.dumps({"ts": "2025-01-01T00:00:00+00:00", "tool": "a", "healed": False}),
            "",
            json.dumps({"ts": "2025-01-01T00:00:10+00:00", "tool": "b", "healed": False}),
        ]
        fake_log.write_text("\n".join(events))
        with patch("metabolon.organelles.angiogenesis.INFECTION_LOG", fake_log):
            result = detect_hypoxia()
            # Only 1 co-failure of (a,b) — below threshold
            assert result == []

    def test_bad_timestamp_skipped(self, tmp_path: Path):
        """Events with unparseable timestamps are skipped."""
        fake_log = tmp_path / "infections.jsonl"
        events = [
            json.dumps({"ts": "not-a-timestamp", "tool": "a", "healed": False}),
            json.dumps({"ts": "2025-01-01T00:00:10+00:00", "tool": "b", "healed": False}),
        ]
        fake_log.write_text("\n".join(events))
        with patch("metabolon.organelles.angiogenesis.INFECTION_LOG", fake_log):
            result = detect_hypoxia()
            assert result == []

    def test_multiple_hypoxic_pairs(self, tmp_path: Path):
        """Multiple distinct hypoxic pairs are all returned."""
        fake_log = tmp_path / "infections.jsonl"
        events = []
        for i in range(_HYPOXIA_THRESHOLD):
            sec = i * 10
            # Pair (a, b)
            events.append({"ts": f"2025-01-01T00:{sec:02d}:00+00:00", "tool": "a", "healed": False})
            events.append({"ts": f"2025-01-01T00:{sec:02d}:05+00:00", "tool": "b", "healed": False})
            # Pair (c, d)
            events.append({"ts": f"2025-01-01T00:{sec:02d}:01+00:00", "tool": "c", "healed": False})
            events.append({"ts": f"2025-01-01T00:{sec:02d}:06+00:00", "tool": "d", "healed": False})

        fake_log.write_text("\n".join(json.dumps(e) for e in events))
        with patch("metabolon.organelles.angiogenesis.INFECTION_LOG", fake_log):
            result = detect_hypoxia()
        sources = {r["source"] for r in result}
        assert "a" in sources and "c" in sources


# ---------------------------------------------------------------------------
# propose_vessel
# ---------------------------------------------------------------------------

class TestProposeVessel:
    """Tests for the propose_vessel() function."""

    @patch("metabolon.organelles.angiogenesis.datetime")
    def test_returns_proposal_dict(self, mock_dt, tmp_path: Path):
        """propose_vessel returns a well-formed proposal dict."""
        fixed_now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
        mock_dt.now.return_value = fixed_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        fake_log = tmp_path / "proposals.jsonl"
        with patch("metabolon.organelles.angiogenesis.PROPOSAL_LOG", fake_log):
            result = propose_vessel("src_tool", "dst_tool")

        assert result["ts"] == fixed_now.isoformat()
        assert result["source"] == "src_tool"
        assert result["target"] == "dst_tool"
        assert result["vessel_type"] == "pipeline"
        assert result["status"] == "proposed"
        assert "src_tool" in result["description"]
        assert "dst_tool" in result["description"]

    @patch("metabolon.organelles.angiogenesis.datetime")
    def test_appends_to_proposal_log(self, mock_dt, tmp_path: Path):
        """The proposal is appended as a JSON line to PROPOSAL_LOG."""
        fixed_now = datetime(2025, 7, 1, 0, 0, 0, tzinfo=UTC)
        mock_dt.now.return_value = fixed_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        fake_log = tmp_path / "proposals.jsonl"
        with patch("metabolon.organelles.angiogenesis.PROPOSAL_LOG", fake_log):
            propose_vessel("x", "y")
            propose_vessel("p", "q")

        lines = fake_log.read_text().strip().splitlines()
        assert len(lines) == 2
        first = json.loads(lines[0])
        assert first["source"] == "x"
        assert first["target"] == "y"
        second = json.loads(lines[1])
        assert second["source"] == "p"

    @patch("metabolon.organelles.angiogenesis.datetime")
    def test_creates_parent_directory(self, mock_dt, tmp_path: Path):
        """Parent directories for the proposal log are created if missing."""
        fixed_now = datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC)
        mock_dt.now.return_value = fixed_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        nested = tmp_path / "deep" / "nested" / "proposals.jsonl"
        with patch("metabolon.organelles.angiogenesis.PROPOSAL_LOG", nested):
            propose_vessel("a", "b")

        assert nested.exists()
        data = json.loads(nested.read_text().strip())
        assert data["source"] == "a"


# ---------------------------------------------------------------------------
# vessel_registry
# ---------------------------------------------------------------------------

class TestVesselRegistry:
    """Tests for the vessel_registry() function."""

    def test_missing_registry_returns_empty(self, tmp_path: Path):
        """When the registry file doesn't exist, return []."""
        fake_reg = tmp_path / "vessels.json"
        with patch("metabolon.organelles.angiogenesis.VESSEL_REGISTRY", fake_reg):
            assert vessel_registry() == []

    def test_valid_registry(self, tmp_path: Path):
        """A well-formed JSON array is returned as-is."""
        fake_reg = tmp_path / "vessels.json"
        vessels = [
            {"source": "a", "target": "b", "type": "pipeline"},
            {"source": "c", "target": "d", "type": "bridge"},
        ]
        fake_reg.write_text(json.dumps(vessels))
        with patch("metabolon.organelles.angiogenesis.VESSEL_REGISTRY", fake_reg):
            result = vessel_registry()
        assert result == vessels

    def test_corrupt_json_returns_empty(self, tmp_path: Path):
        """Malformed JSON in the registry returns [] instead of raising."""
        fake_reg = tmp_path / "vessels.json"
        fake_reg.write_text("NOT JSON")
        with patch("metabolon.organelles.angiogenesis.VESSEL_REGISTRY", fake_reg):
            assert vessel_registry() == []

    def test_empty_registry_file(self, tmp_path: Path):
        """An empty file (0 bytes) returns []."""
        fake_reg = tmp_path / "vessels.json"
        fake_reg.write_text("")
        with patch("metabolon.organelles.angiogenesis.VESSEL_REGISTRY", fake_reg):
            assert vessel_registry() == []


# ---------------------------------------------------------------------------
# Constants / smoke
# ---------------------------------------------------------------------------

class TestConstants:
    """Quick sanity checks on module-level constants."""

    def test_paths_are_under_home(self):
        assert str(INFECTION_LOG).startswith(str(Path.home()))
        assert str(VESSEL_REGISTRY).startswith(str(Path.home()))
        assert str(PROPOSAL_LOG).startswith(str(Path.home()))

    def test_thresholds_are_positive(self):
        assert _SEQUENCE_WINDOW_S > 0
        assert _HYPOXIA_THRESHOLD > 0
