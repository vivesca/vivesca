"""Tests for mismatch_repair — biological naming precision audit."""

from metabolon.metabolism.mismatch_repair import (
    SRC_DIR,
    VOCABULARY_GAPS,
    OrphanGap,
    VocabularyGap,
    _detect_orphan_gaps,
)


def test_vocabulary_gap_dataclass():
    g = VocabularyGap(
        old_term="OldName",
        new_term="NewName",
        layer="cortical",
        reason="better precision",
        grep_pattern=r"\bOldName\b",
    )
    assert g.old_term == "OldName"
    assert g.exclude_file == ""


def test_vocabulary_gaps_populated():
    assert len(VOCABULARY_GAPS) >= 1
    for gap in VOCABULARY_GAPS:
        assert isinstance(gap, VocabularyGap)
        assert gap.old_term
        assert gap.new_term


def test_orphan_gap_dataclass():
    g = OrphanGap(uri="vivesca://test", source_file="test.py")
    assert g.uri == "vivesca://test"


def test_src_dir_exists():
    assert SRC_DIR.exists()
    assert SRC_DIR.name == "metabolon"


def test_detect_orphan_gaps_empty(tmp_path):
    # Empty source dir should return empty list
    src = tmp_path / "metabolon"
    src.mkdir()
    result = _detect_orphan_gaps(src=src, consumer_files=[])
    assert isinstance(result, list)


def test_detect_orphan_gaps_with_resource(tmp_path):
    src = tmp_path / "metabolon"
    src.mkdir()
    res = src / "resources"
    res.mkdir()
    # Create a file that registers a resource
    (res / "test.py").write_text("""
from fastmcp.resources import resource
@resource(uri="vivesca://test")
def test_resource(): return "data"
""")
    # No consumer references
    consumer = tmp_path / "empty_consumer.md"
    consumer.write_text("nothing here")
    result = _detect_orphan_gaps(src=src, consumer_files=[consumer])
    assert isinstance(result, list)
