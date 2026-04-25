"""Tests for rhodopsin content-based rotation detection.

Stub created at spec time. Ribosome will populate during build.
See spec: ~/epigenome/chromatin/loci/plans/rhodopsin-content-based-rotation.md
"""

import pytest


@pytest.mark.skip(reason="not yet implemented — see spec")
def test_correct_orientation_unchanged() -> None:
    """Photo where content is already upright. Detection should apply 0° rotation."""
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented — see spec")
def test_sideways_doc_rotated_90() -> None:
    """Photo of sideways-displayed doc. Detection should rotate ±90° to upright."""
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented — see spec")
def test_upside_down_rotated_180() -> None:
    """Photo of upside-down doc. Detection should rotate 180°."""
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented — see spec")
def test_low_confidence_no_rotation() -> None:
    """Non-document photo. Detection should leave EXIF rotation unchanged."""
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented — see spec")
def test_ambiguous_no_rotation() -> None:
    """Ambiguous orientation. Detection should leave at 0° when winner not clear."""
    raise NotImplementedError
