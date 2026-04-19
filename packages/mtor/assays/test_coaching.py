from pathlib import Path

from mtor.coaching import inject_coaching


def test_inject_coaching(tmp_path: Path):
    coaching = tmp_path / "coaching.md"
    coaching.write_text("## Rules\n- Do not hallucinate imports")
    result = inject_coaching("fix the bug", coaching)
    assert result.startswith("<coaching-notes>")
    assert "Do not hallucinate imports" in result
    assert result.endswith("fix the bug")


def test_inject_coaching_no_file():
    assert inject_coaching("fix the bug", None) == "fix the bug"


def test_inject_coaching_missing_file(tmp_path: Path):
    assert inject_coaching("fix the bug", tmp_path / "nonexistent.md") == "fix the bug"


def test_inject_coaching_empty_file(tmp_path: Path):
    coaching = tmp_path / "coaching.md"
    coaching.write_text("")
    assert inject_coaching("fix the bug", coaching) == "fix the bug"
