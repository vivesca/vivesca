from __future__ import annotations

"""Tests for metabolon.organelles.angiogenesis."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import metabolon.organelles.angiogenesis as angiogenesis

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_infection_line(tool: str, ts: str, healed: bool = False) -> str:
    return json.dumps({"tool": tool, "ts": ts, "healed": healed})


def _write_infection_log(tmp_path: Path, lines: list[str]) -> None:
    """Write infection log lines to a temp file and patch the module constant."""
    p = tmp_path / "infections.jsonl"
    p.write_text("\n".join(lines))
    return p


# ---------------------------------------------------------------------------
# detect_hypoxia
# ---------------------------------------------------------------------------


class TestDetectHypoxia:
    """Tests for angiogenesis.detect_hypoxia()."""

    @patch.object(angiogenesis, "INFECTION_LOG", Path("/nonexistent"))
    def test_no_log_file_returns_empty(self):
        assert angiogenesis.detect_hypoxia() == []

    @patch.object(angiogenesis, "INFECTION_LOG")
    def test_empty_log_returns_empty(self, mock_path):
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = ""
        assert angiogenesis.detect_hypoxia() == []

    @patch.object(angiogenesis, "INFECTION_LOG")
    def test_healed_events_ignored(self, mock_path):
        mock_path.exists.return_value = True
        lines = [
            _make_infection_line("tool_a", "2025-01-01T00:00:00", healed=True),
            _make_infection_line("tool_b", "2025-01-01T00:00:01", healed=True),
        ]
        mock_path.read_text.return_value = "\n".join(lines)
        assert angiogenesis.detect_hypoxia() == []

    @patch.object(angiogenesis, "INFECTION_LOG")
    def test_single_failure_no_pair(self, mock_path):
        mock_path.exists.return_value = True
        lines = [_make_infection_line("tool_a", "2025-01-01T00:00:00")]
        mock_path.read_text.return_value = "\n".join(lines)
        assert angiogenesis.detect_hypoxia() == []

    @patch.object(angiogenesis, "INFECTION_LOG")
    def test_below_threshold_excluded(self, mock_path):
        """Events spaced >300s apart so no cross-tool pair fits the window."""
        mock_path.exists.return_value = True
        lines = [
            _make_infection_line("tool_a", "2025-01-01T00:00:00"),
            _make_infection_line("tool_b", "2025-01-01T00:06:00"),  # 360s later
            _make_infection_line("tool_a", "2025-01-01T00:12:00"),  # 720s from first
            _make_infection_line("tool_b", "2025-01-01T00:18:00"),  # 1080s from first
        ]
        mock_path.read_text.return_value = "\n".join(lines)
        result = angiogenesis.detect_hypoxia()
        assert result == []

    @patch.object(angiogenesis, "INFECTION_LOG")
    def test_meets_threshold_returns_pair(self, mock_path):
        """All a-events before b-events => only (a,b) direction is counted."""
        mock_path.exists.return_value = True
        lines = [
            _make_infection_line("tool_a", "2025-01-01T00:00:00"),
            _make_infection_line("tool_a", "2025-01-01T00:00:10"),
            _make_infection_line("tool_a", "2025-01-01T00:00:20"),
            _make_infection_line("tool_b", "2025-01-01T00:00:30"),
            _make_infection_line("tool_b", "2025-01-01T00:00:40"),
            _make_infection_line("tool_b", "2025-01-01T00:00:50"),
        ]
        mock_path.read_text.return_value = "\n".join(lines)
        result = angiogenesis.detect_hypoxia()
        # 3 a-events × 3 b-events = 9 (a,b) co-failures, well above threshold
        assert len(result) == 1
        pair = result[0]
        assert pair["source"] == "tool_a"
        assert pair["target"] == "tool_b"
        assert pair["co_failures"] >= 3

    @patch.object(angiogenesis, "INFECTION_LOG")
    def test_same_tool_not_counted(self, mock_path):
        """Pairs where both tools are the same should not be counted."""
        mock_path.exists.return_value = True
        lines = [
            _make_infection_line("tool_a", "2025-01-01T00:00:00"),
            _make_infection_line("tool_a", "2025-01-01T00:00:10"),
            _make_infection_line("tool_a", "2025-01-01T00:00:20"),
            _make_infection_line("tool_a", "2025-01-01T00:00:30"),
        ]
        mock_path.read_text.return_value = "\n".join(lines)
        assert angiogenesis.detect_hypoxia() == []

    @patch.object(angiogenesis, "INFECTION_LOG")
    def test_window_enforcement(self, mock_path):
        """All inter-tool gaps >300s so no pair qualifies."""
        mock_path.exists.return_value = True
        lines = [
            _make_infection_line("tool_a", "2025-01-01T00:00:00"),
            _make_infection_line("tool_b", "2025-01-01T00:06:00"),  # +360s
            _make_infection_line("tool_a", "2025-01-01T00:12:00"),  # +360s
            _make_infection_line("tool_b", "2025-01-01T00:18:00"),  # +360s
            _make_infection_line("tool_a", "2025-01-01T00:24:00"),  # +360s
            _make_infection_line("tool_b", "2025-01-01T00:30:00"),  # +360s
        ]
        mock_path.read_text.return_value = "\n".join(lines)
        assert angiogenesis.detect_hypoxia() == []

    @patch.object(angiogenesis, "INFECTION_LOG")
    def test_malformed_lines_skipped(self, mock_path):
        mock_path.exists.return_value = True
        lines = [
            "not json at all",
            "",
            _make_infection_line("tool_a", "2025-01-01T00:00:00"),
            _make_infection_line("tool_b", "2025-01-01T00:00:10"),
        ]
        mock_path.read_text.return_value = "\n".join(lines)
        # Only 1 co-failure pair (a,b) -> below threshold
        assert angiogenesis.detect_hypoxia() == []

    @patch.object(angiogenesis, "INFECTION_LOG")
    def test_result_contains_last_seen(self, mock_path):
        """All a-events before b-events to get a single direction pair."""
        mock_path.exists.return_value = True
        lines = [
            _make_infection_line("a", "2025-01-01T00:00:00"),
            _make_infection_line("a", "2025-01-01T00:00:10"),
            _make_infection_line("a", "2025-01-01T00:00:20"),
            _make_infection_line("b", "2025-01-01T00:00:30"),
            _make_infection_line("b", "2025-01-01T00:00:40"),
            _make_infection_line("b", "2025-01-01T00:00:50"),
        ]
        mock_path.read_text.return_value = "\n".join(lines)
        result = angiogenesis.detect_hypoxia()
        assert len(result) == 1
        assert "last_seen" in result[0]
        # last_seen should be the latest b-event timestamp
        assert result[0]["last_seen"].startswith("2025-01-01T00:00:50")


# ---------------------------------------------------------------------------
# propose_vessel
# ---------------------------------------------------------------------------


class TestProposeVessel:
    """Tests for angiogenesis.propose_vessel()."""

    @patch.object(angiogenesis, "PROPOSAL_LOG")
    def test_returns_proposal_dict(self, mock_path):
        mock_path.parent = MagicMock()
        mock_path.open.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_path.open.return_value.__exit__ = MagicMock(return_value=False)

        proposal = angiogenesis.propose_vessel("src_tool", "tgt_tool")

        assert proposal["source"] == "src_tool"
        assert proposal["target"] == "tgt_tool"
        assert proposal["vessel_type"] == "pipeline"
        assert proposal["status"] == "proposed"
        assert "ts" in proposal
        assert "src_tool" in proposal["description"]
        assert "tgt_tool" in proposal["description"]

    @patch.object(angiogenesis, "PROPOSAL_LOG")
    def test_writes_to_log(self, mock_path):
        mock_parent = MagicMock()
        mock_path.parent = mock_parent
        mock_file = MagicMock()
        mock_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_path.open.return_value.__exit__ = MagicMock(return_value=False)

        angiogenesis.propose_vessel("alpha", "beta")

        mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        assert mock_file.write.call_count == 1
        written = mock_file.write.call_args[0][0]
        parsed = json.loads(written.strip())
        assert parsed["source"] == "alpha"
        assert parsed["target"] == "beta"
        assert parsed["status"] == "proposed"

    @patch.object(angiogenesis, "PROPOSAL_LOG")
    def test_timestamp_is_iso_format(self, mock_path):
        mock_path.parent = MagicMock()
        mock_path.open.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_path.open.return_value.__exit__ = MagicMock(return_value=False)

        proposal = angiogenesis.propose_vessel("x", "y")
        # Should parse without error
        from datetime import datetime

        datetime.fromisoformat(proposal["ts"])


# ---------------------------------------------------------------------------
# vessel_registry
# ---------------------------------------------------------------------------


class TestVesselRegistry:
    """Tests for angiogenesis.vessel_registry()."""

    @patch.object(angiogenesis, "VESSEL_REGISTRY")
    def test_missing_registry_returns_empty(self, mock_path):
        mock_path.exists.return_value = False
        assert angiogenesis.vessel_registry() == []

    @patch.object(angiogenesis, "VESSEL_REGISTRY")
    def test_valid_json_returns_list(self, mock_path):
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(
            [
                {"source": "a", "target": "b"},
                {"source": "c", "target": "d"},
            ]
        )
        result = angiogenesis.vessel_registry()
        assert len(result) == 2
        assert result[0]["source"] == "a"

    @patch.object(angiogenesis, "VESSEL_REGISTRY")
    def test_corrupt_json_returns_empty(self, mock_path):
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "NOT VALID JSON{{{{"
        assert angiogenesis.vessel_registry() == []

    @patch.object(angiogenesis, "VESSEL_REGISTRY")
    def test_oserror_returns_empty(self, mock_path):
        mock_path.exists.return_value = True
        mock_path.read_text.side_effect = OSError("permission denied")
        assert angiogenesis.vessel_registry() == []
