from pathlib import Path

from mtor.reflection import capture_reflection, capture_stall_report


def test_capture_reflection(tmp_path: Path):
    refl = tmp_path / "reflection.md"
    refl.write_text("harder than expected: config parsing edge cases")
    result = capture_reflection(refl)
    assert result == "harder than expected: config parsing edge cases"
    assert not refl.exists()


def test_capture_reflection_missing(tmp_path: Path):
    assert capture_reflection(tmp_path / "nonexistent.md") is None


def test_capture_stall_report(tmp_path: Path):
    stall = tmp_path / "stall.txt"
    stall.write_text("STALL: repeated import failure")
    result = capture_stall_report(stall)
    assert "import failure" in result
    assert not stall.exists()
