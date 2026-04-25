"""Tests for rhodopsin content-based rotation detection.

Uses mocked _measure_text_confidence and subprocess.run to test the rotation
decision algorithm without requiring macOS Vision framework or real images.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_MOD_PATH = Path(__file__).resolve().parent.parent / "effectors" / "rhodopsin.py"
_spec = importlib.util.spec_from_file_location("rhodopsin", _MOD_PATH)
_rhodopsin = importlib.util.module_from_spec(_spec)
sys.modules["rhodopsin"] = _rhodopsin
_spec.loader.exec_module(_rhodopsin)

_detect_content_orientation = _rhodopsin._detect_content_orientation


@pytest.fixture
def dummy_jpeg(tmp_path: Path) -> Path:
    """Create a minimal dummy JPEG file for testing."""
    jpeg = tmp_path / "test_photo.jpeg"
    jpeg.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    return jpeg


def _mock_sips_factory(tmp_path: Path):
    """Return a subprocess.run mock that creates dummy output files for sips."""
    def mock_run(cmd, **kwargs):
        if cmd[0] == "sips" and "--out" in cmd:
            out_idx = cmd.index("--out")
            Path(cmd[out_idx + 1]).write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        return MagicMock(returncode=0)
    return mock_run


def test_correct_orientation_unchanged(dummy_jpeg: Path) -> None:
    """Photo where content is already upright. Detection should apply 0° rotation."""
    with (
        patch("rhodopsin._measure_text_confidence") as mock_conf,
        patch("rhodopsin.subprocess.run") as mock_run,
    ):
        mock_run.side_effect = _mock_sips_factory(dummy_jpeg.parent)
        # 0° is the clear winner
        mock_conf.side_effect = [0.92, 0.21, 0.18, 0.20]

        result = _detect_content_orientation(dummy_jpeg)

    assert result == 0
    # No final rotation sips call — only 4 temp-file-creation calls
    for call in mock_run.call_args_list:
        assert "--out" in call[0][0]


def test_sideways_doc_rotated_90(dummy_jpeg: Path) -> None:
    """Photo of sideways-displayed doc. Detection should rotate 90° to upright."""
    with (
        patch("rhodopsin._measure_text_confidence") as mock_conf,
        patch("rhodopsin.subprocess.run") as mock_run,
    ):
        mock_run.side_effect = _mock_sips_factory(dummy_jpeg.parent)
        # 90° is the clear winner (sideways document)
        mock_conf.side_effect = [0.21, 0.94, 0.17, 0.22]

        result = _detect_content_orientation(dummy_jpeg)

    assert result == 90
    # Should have 5 sips calls: 4 temp creation + 1 final rotation
    assert mock_run.call_count == 5
    final_call = mock_run.call_args_list[-1]
    assert final_call[0][0] == ["sips", "-r", "90", str(dummy_jpeg)]


def test_upside_down_rotated_180(dummy_jpeg: Path) -> None:
    """Photo of upside-down doc. Detection should rotate 180°."""
    with (
        patch("rhodopsin._measure_text_confidence") as mock_conf,
        patch("rhodopsin.subprocess.run") as mock_run,
    ):
        mock_run.side_effect = _mock_sips_factory(dummy_jpeg.parent)
        # 180° is the clear winner (upside-down document)
        mock_conf.side_effect = [0.15, 0.19, 0.91, 0.16]

        result = _detect_content_orientation(dummy_jpeg)

    assert result == 180
    final_call = mock_run.call_args_list[-1]
    assert final_call[0][0] == ["sips", "-r", "180", str(dummy_jpeg)]


def test_low_confidence_no_rotation(dummy_jpeg: Path) -> None:
    """Non-document photo. Detection should leave rotation unchanged."""
    with (
        patch("rhodopsin._measure_text_confidence") as mock_conf,
        patch("rhodopsin.subprocess.run") as mock_run,
    ):
        mock_run.side_effect = _mock_sips_factory(dummy_jpeg.parent)
        # All angles have very low confidence — not a document
        mock_conf.side_effect = [0.08, 0.06, 0.07, 0.05]

        result = _detect_content_orientation(dummy_jpeg)

    assert result == 0
    # No final rotation — only 4 temp creation calls
    assert mock_run.call_count == 4


def test_ambiguous_no_rotation(dummy_jpeg: Path) -> None:
    """Ambiguous orientation. Detection should leave at 0° when winner not clear."""
    with (
        patch("rhodopsin._measure_text_confidence") as mock_conf,
        patch("rhodopsin.subprocess.run") as mock_run,
    ):
        mock_run.side_effect = _mock_sips_factory(dummy_jpeg.parent)
        # 0° barely wins over 90° — not 1.5× clearer
        mock_conf.side_effect = [0.50, 0.45, 0.10, 0.08]

        result = _detect_content_orientation(dummy_jpeg)

    assert result == 0
    # No final rotation — ambiguous
    assert mock_run.call_count == 4
