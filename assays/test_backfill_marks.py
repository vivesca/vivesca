#!/usr/bin/env python3
from __future__ import annotations

"""Tests for backfill-marks effector — tests frontmatter field addition for epigenome marks."""


import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Execute the backfill-marks script directly
backfill_marks_path = Path(str(Path.home() / "germline/effectors/backfill-marks"))
backfill_marks_code = backfill_marks_path.read_text()
namespace = {}
exec(backfill_marks_code, namespace)

# Extract all the functions/globals from the namespace
bm = type("backfill_marks_module", (), {})()
for key, value in namespace.items():
    if not key.startswith("__"):
        setattr(bm, key, value)


# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------


def test_marks_dir_defined():
    """Test MARKS_DIR is set correctly."""
    assert Path.home() / "epigenome" / "marks" == bm.MARKS_DIR


def test_skip_files_defined():
    """Test SKIP_FILES contains expected files."""
    assert "MEMORY.md" in bm.SKIP_FILES
    assert "methylome.md" in bm.SKIP_FILES


def test_protected_stems_defined():
    """Test PROTECTED_STEMS contains expected feedback files."""
    assert "feedback_keep_digging" in bm.PROTECTED_STEMS
    assert "feedback_hold_position" in bm.PROTECTED_STEMS
    assert "feedback_pull_the_thread" in bm.PROTECTED_STEMS


def test_email_to_source_mapping():
    """Test EMAIL_TO_SOURCE has expected mappings."""
    assert bm.EMAIL_TO_SOURCE["opencode@local"] == "opencode"
    assert bm.EMAIL_TO_SOURCE["codex@local"] == "codex"


# ---------------------------------------------------------------------------
# Test get_git_blame_source function
# ---------------------------------------------------------------------------


def test_get_git_blame_source_defaults_to_cc():
    """Test get_git_blame_source returns 'cc' when no matching email."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.md"
        test_file.write_text("---\nname: test\n---\nbody")

        with patch.object(bm, "MARKS_DIR", Path(tmpdir)):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="unknown@example.com\n", stderr="")
                result = bm.get_git_blame_source(test_file)
                assert result == "cc"


def test_get_git_blame_source_maps_known_email():
    """Test get_git_blame_source maps known emails correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.md"
        test_file.write_text("---\nname: test\n---\nbody")

        with patch.object(bm, "MARKS_DIR", Path(tmpdir)):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="opencode@local\n", stderr="")
                result = bm.get_git_blame_source(test_file)
                assert result == "opencode"


def test_get_git_blame_source_handles_error():
    """Test get_git_blame_source returns 'cc' on subprocess error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.md"
        test_file.write_text("---\nname: test\n---\nbody")

        with patch.object(bm, "MARKS_DIR", Path(tmpdir)):
            with patch("subprocess.run", side_effect=subprocess.SubprocessError):
                result = bm.get_git_blame_source(test_file)
                assert result == "cc"


# ---------------------------------------------------------------------------
# Test parse_frontmatter function
# ---------------------------------------------------------------------------


def test_backfill_marks_parse_frontmatter_valid():
    """Test parse_frontmatter extracts frontmatter correctly."""
    content = "---\nname: test\nvalue: 123\n---\nBody content here"
    fm_lines, body = bm.parse_frontmatter(content)
    assert fm_lines == ["name: test", "value: 123"]
    assert "Body content here" in body


def test_backfill_marks_parse_frontmatter_no_frontmatter():
    """Test parse_frontmatter returns None for content without frontmatter."""
    content = "No frontmatter here\nJust body"
    fm_lines, body = bm.parse_frontmatter(content)
    assert fm_lines is None
    assert body == content


def test_parse_frontmatter_unclosed():
    """Test parse_frontmatter handles unclosed frontmatter."""
    content = "---\nname: test\nvalue: 123\nNo closing delimiter"
    fm_lines, _body = bm.parse_frontmatter(content)
    assert fm_lines is None


def test_backfill_marks_parse_frontmatter_empty():
    """Test parse_frontmatter handles empty frontmatter."""
    content = "---\n---\nBody"
    fm_lines, body = bm.parse_frontmatter(content)
    assert fm_lines == []
    assert body.strip() == "Body"


def test_parse_frontmatter_multiline_body():
    """Test parse_frontmatter preserves multiline body."""
    content = "---\nname: test\n---\nLine 1\nLine 2\nLine 3"
    _fm_lines, body = bm.parse_frontmatter(content)
    assert "Line 1" in body
    assert "Line 2" in body
    assert "Line 3" in body


# ---------------------------------------------------------------------------
# Test has_field function
# ---------------------------------------------------------------------------


def test_has_field_present():
    """Test has_field returns True when field exists."""
    fm_lines = ["name: test", "source: cc", "durability: methyl"]
    assert bm.has_field(fm_lines, "source") is True
    assert bm.has_field(fm_lines, "name") is True


def test_has_field_absent():
    """Test has_field returns False when field doesn't exist."""
    fm_lines = ["name: test", "durability: methyl"]
    assert bm.has_field(fm_lines, "source") is False


def test_has_field_partial_match():
    """Test has_field requires exact field name match."""
    fm_lines = ["sourcename: test"]
    assert bm.has_field(fm_lines, "source") is False


# ---------------------------------------------------------------------------
# Test rebuild_file function
# ---------------------------------------------------------------------------


def test_rebuild_file_basic():
    """Test rebuild_file reconstructs file correctly."""
    fm_lines = ["name: test", "source: cc"]
    body = "\nBody content"
    result = bm.rebuild_file(fm_lines, body)
    assert result.startswith("---\n")
    assert "name: test" in result
    assert "source: cc" in result
    assert "Body content" in result


def test_rebuild_file_adds_newline_to_body():
    """Test rebuild_file adds leading newline to body if missing."""
    fm_lines = ["name: test"]
    body = "Body without leading newline"
    result = bm.rebuild_file(fm_lines, body)
    assert "\n---\nBody without leading newline" in result


def test_rebuild_file_empty_body():
    """Test rebuild_file handles empty body."""
    fm_lines = ["name: test"]
    body = ""
    result = bm.rebuild_file(fm_lines, body)
    assert result.endswith("---")


# ---------------------------------------------------------------------------
# Test process_file function
# ---------------------------------------------------------------------------


def test_process_file_no_frontmatter(capsys):
    """Test process_file skips files without frontmatter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "no_fm.md"
        test_file.write_text("No frontmatter here\n")

        result = bm.process_file(test_file, execute=False)
        assert result is False
        captured = capsys.readouterr()
        assert "SKIP" in captured.out


def test_process_file_already_complete():
    """Test process_file returns False when all fields present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "complete.md"
        test_file.write_text("---\nname: test\nsource: cc\ndurability: methyl\n---\nBody\n")

        result = bm.process_file(test_file, execute=False)
        assert result is False


def test_process_file_adds_source(capsys):
    """Test process_file adds missing source field."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "needs_source.md"
        test_file.write_text("---\nname: test\ndurability: methyl\n---\nBody\n")

        with patch.object(bm, "MARKS_DIR", Path(tmpdir)):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="test@example.com\n", stderr="")
                result = bm.process_file(test_file, execute=False)
                assert result is True
                captured = capsys.readouterr()
                assert "source=cc" in captured.out


def test_process_file_adds_durability_acetyl_for_checkpoint(capsys):
    """Test process_file sets durability=acetyl for checkpoint files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "checkpoint_test.md"
        test_file.write_text("---\nname: test\nsource: cc\n---\nBody\n")

        result = bm.process_file(test_file, execute=False)
        assert result is True
        captured = capsys.readouterr()
        assert "durability=acetyl" in captured.out


def test_process_file_adds_durability_methyl_default(capsys):
    """Test process_file sets durability=methyl for regular files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "regular_file.md"
        test_file.write_text("---\nname: test\nsource: cc\n---\nBody\n")

        result = bm.process_file(test_file, execute=False)
        assert result is True
        captured = capsys.readouterr()
        assert "durability=methyl" in captured.out


def test_process_file_adds_protected_for_stem(capsys):
    """Test process_file adds protected=true for PROTECTED_STEMS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "feedback_keep_digging.md"
        test_file.write_text("---\nname: test\nsource: cc\ndurability: methyl\n---\nBody\n")

        result = bm.process_file(test_file, execute=False)
        assert result is True
        captured = capsys.readouterr()
        assert "protected=true" in captured.out


def test_process_file_dry_run_vs_execute():
    """Test process_file dry-run doesn't modify file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.md"
        original = "---\nname: test\n---\nBody\n"
        test_file.write_text(original)

        with patch.object(bm, "MARKS_DIR", Path(tmpdir)):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="test@example.com\n", stderr="")

                # Dry run
                bm.process_file(test_file, execute=False)
                assert "source:" not in test_file.read_text()

                # Execute
                bm.process_file(test_file, execute=True)
                content = test_file.read_text()
                assert "source: cc" in content


def test_process_file_execute_writes_changes():
    """Test process_file writes changes when execute=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.md"
        test_file.write_text("---\nname: test\n---\nBody\n")

        with patch.object(bm, "MARKS_DIR", Path(tmpdir)):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="test@example.com\n", stderr="")
                bm.process_file(test_file, execute=True)

                content = test_file.read_text()
                assert "source: cc" in content
                assert "durability: methyl" in content


# ---------------------------------------------------------------------------
# Test main function CLI handling
# ---------------------------------------------------------------------------


def test_main_dry_run_default(capsys):
    """Test main defaults to dry-run mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        marks_dir = Path(tmpdir)

        with patch.object(bm, "MARKS_DIR", marks_dir):
            with patch("sys.argv", ["backfill-marks"]):
                bm.main()
                captured = capsys.readouterr()
                assert "DRY-RUN" in captured.out


def test_main_explicit_dry_run(capsys):
    """Test --dry-run flag explicitly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        marks_dir = Path(tmpdir)

        with patch.object(bm, "MARKS_DIR", marks_dir):
            with patch("sys.argv", ["backfill-marks", "--dry-run"]):
                bm.main()
                captured = capsys.readouterr()
                assert "DRY-RUN" in captured.out


def test_main_execute_mode(capsys):
    """Test --execute flag enables write mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        marks_dir = Path(tmpdir)

        with patch.object(bm, "MARKS_DIR", marks_dir):
            with patch("sys.argv", ["backfill-marks", "--execute"]):
                bm.main()
                captured = capsys.readouterr()
                assert "EXECUTE" in captured.out


def test_main_skips_symlinks():
    """Test main skips symlink files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        marks_dir = Path(tmpdir)
        target = marks_dir / "target.md"
        target.write_text("---\nname: target\n---\nBody\n")
        symlink = marks_dir / "MEMORY.md"
        symlink.symlink_to(target)

        with patch.object(bm, "MARKS_DIR", marks_dir):
            with patch("sys.argv", ["backfill-marks"]):
                bm.main()
                # Should not crash on symlink


def test_main_skips_index_files():
    """Test main skips files in SKIP_FILES."""
    with tempfile.TemporaryDirectory() as tmpdir:
        marks_dir = Path(tmpdir)
        skip_file = marks_dir / "methylome.md"
        skip_file.write_text("---\nname: index\n---\nBody\n")

        with patch.object(bm, "MARKS_DIR", marks_dir):
            with patch("sys.argv", ["backfill-marks"]):
                bm.main()
                # Should skip without error


def test_main_results_summary(capsys):
    """Test main prints results summary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        marks_dir = Path(tmpdir)

        with patch.object(bm, "MARKS_DIR", marks_dir):
            with patch("sys.argv", ["backfill-marks"]):
                bm.main()
                captured = capsys.readouterr()
                assert "Results:" in captured.out
                assert "Total scanned:" in captured.out
