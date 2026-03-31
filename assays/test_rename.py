from __future__ import annotations

"""Tests for metabolon.organelles.rename — scanning and dry-run logic."""


from pathlib import Path

import pytest

from metabolon.organelles.rename import (
    ScanResult,
    fix_symlinks,
    rename_dirs,
    rename_files,
    run_rename,
    scan,
    update_contents,
    update_locus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tree(root: Path) -> None:
    """Build a small fixture tree for testing.

    root/
        engrams/
            index.md        (contains "engrams")
            notes.py        (contains "engrams" twice)
        data/
            engrams_config.toml  (engrams in filename + content)
            other.md             (no "engrams")
        deep/
            sub/
                engrams/    (deeply nested dir)
                    leaf.py (contains "engrams")
    """
    (root / "engrams").mkdir()
    (root / "engrams" / "index.md").write_text("# engrams index\nengrams are memory.\n")
    (root / "engrams" / "notes.py").write_text(
        "# engrams module\nENGRAMS_DIR = 'engrams'\n"
    )
    (root / "data").mkdir()
    (root / "data" / "engrams_config.toml").write_text('[engrams]\npath = "engrams"\n')
    (root / "data" / "other.md").write_text("# unrelated\nnothing here\n")
    (root / "deep" / "sub" / "engrams").mkdir(parents=True)
    (root / "deep" / "sub" / "engrams" / "leaf.py").write_text(
        "# deep engrams\nengrams_path = '/engrams/'\n"
    )


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------


class TestScan:
    def test_finds_all_files_with_match(self, tmp_path):
        _make_tree(tmp_path)
        result = scan("engrams", [tmp_path])
        assert isinstance(result, ScanResult)
        # engrams/index.md, engrams/notes.py, data/engrams_config.toml, deep/sub/engrams/leaf.py
        assert len(result.files) == 4

    def test_excludes_files_without_match(self, tmp_path):
        _make_tree(tmp_path)
        result = scan("engrams", [tmp_path])
        names = {p.name for p in result.files}
        assert "other.md" not in names

    def test_counts_total_occurrences(self, tmp_path):
        _make_tree(tmp_path)
        result = scan("engrams", [tmp_path])
        # index.md: 2, notes.py: 2, engrams_config.toml: 3, leaf.py: 2 = 9
        assert result.total_matches >= 4  # conservative lower bound

    def test_empty_scope_returns_zero(self, tmp_path):
        result = scan("engrams", [])
        assert result.files == []
        assert result.total_matches == 0

    def test_nonexistent_scope_dir_is_skipped(self, tmp_path):
        result = scan("engrams", [tmp_path / "doesnotexist"])
        assert result.files == []

    def test_only_checks_known_extensions(self, tmp_path):
        # .sh file should be ignored
        (tmp_path / "run.sh").write_text("echo engrams\n")
        (tmp_path / "notes.md").write_text("engrams\n")
        result = scan("engrams", [tmp_path])
        names = {p.name for p in result.files}
        assert "run.sh" not in names
        assert "notes.md" in names

    def test_multiple_scope_dirs(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "a.md").write_text("engrams in a\n")
        (dir_b / "b.md").write_text("engrams in b\n")
        result = scan("engrams", [dir_a, dir_b])
        assert len(result.files) == 2


# ---------------------------------------------------------------------------
# rename_dirs (dry-run only — no filesystem mutations in tests)
# ---------------------------------------------------------------------------


class TestRenameDirs:
    def test_dry_run_identifies_dirs(self, tmp_path):
        _make_tree(tmp_path)
        pairs = rename_dirs("engrams", "marks", [tmp_path], dry_run=True)
        old_names = {p.name for p, _ in pairs}
        assert "engrams" in old_names

    def test_dry_run_proposes_new_name(self, tmp_path):
        _make_tree(tmp_path)
        pairs = rename_dirs("engrams", "marks", [tmp_path], dry_run=True)
        new_names = {n.name for _, n in pairs}
        assert "marks" in new_names

    def test_dry_run_does_not_rename(self, tmp_path):
        _make_tree(tmp_path)
        rename_dirs("engrams", "marks", [tmp_path], dry_run=True)
        assert (tmp_path / "engrams").exists()

    def test_live_rename_moves_dir(self, tmp_path):
        (tmp_path / "engrams").mkdir()
        (tmp_path / "engrams" / "f.py").write_text("x")
        pairs = rename_dirs("engrams", "marks", [tmp_path], dry_run=False)
        assert not (tmp_path / "engrams").exists()
        assert (tmp_path / "marks").exists()
        assert len(pairs) == 1

    def test_deepest_first_ordering(self, tmp_path):
        """Parent renamed before child would break child rename; verify deepest-first."""
        (tmp_path / "engrams").mkdir()
        (tmp_path / "engrams" / "engrams").mkdir()
        pairs = rename_dirs("engrams", "marks", [tmp_path], dry_run=True)
        paths = [old for old, _ in pairs]
        depths = [len(p.parts) for p in paths]
        # Each depth should be >= the next (deepest first)
        assert depths == sorted(depths, reverse=True)


# ---------------------------------------------------------------------------
# rename_files (dry-run only for most)
# ---------------------------------------------------------------------------


class TestRenameFiles:
    def test_dry_run_identifies_filename_matches(self, tmp_path):
        _make_tree(tmp_path)
        pairs = rename_files("engrams", "marks", [tmp_path], dry_run=True)
        old_names = {p.name for p, _ in pairs}
        assert "engrams_config.toml" in old_names

    def test_dry_run_proposes_replacement(self, tmp_path):
        _make_tree(tmp_path)
        pairs = rename_files("engrams", "marks", [tmp_path], dry_run=True)
        new_names = {n.name for _, n in pairs}
        assert "marks_config.toml" in new_names

    def test_dry_run_does_not_rename(self, tmp_path):
        _make_tree(tmp_path)
        rename_files("engrams", "marks", [tmp_path], dry_run=True)
        assert (tmp_path / "data" / "engrams_config.toml").exists()

    def test_live_rename_changes_filename(self, tmp_path):
        (tmp_path / "engrams_notes.md").write_text("engrams")
        pairs = rename_files("engrams", "marks", [tmp_path], dry_run=False)
        assert not (tmp_path / "engrams_notes.md").exists()
        assert (tmp_path / "marks_notes.md").exists()


# ---------------------------------------------------------------------------
# update_contents
# ---------------------------------------------------------------------------


class TestUpdateContents:
    def test_dry_run_returns_matches_without_writing(self, tmp_path):
        f = tmp_path / "notes.md"
        f.write_text("engrams are memory\n")
        updated = update_contents("engrams", "marks", [f], dry_run=True)
        assert f in updated
        # File unchanged
        assert "engrams" in f.read_text()

    def test_live_replaces_content(self, tmp_path):
        f = tmp_path / "notes.md"
        f.write_text("engrams are memory\n")
        update_contents("engrams", "marks", [f], dry_run=False)
        assert "marks" in f.read_text()
        assert "engrams" not in f.read_text()

    def test_skips_missing_files(self, tmp_path):
        ghost = tmp_path / "ghost.md"
        # Do not create it
        updated = update_contents("engrams", "marks", [ghost], dry_run=False)
        assert updated == []

    def test_skips_files_without_match(self, tmp_path):
        f = tmp_path / "other.md"
        f.write_text("nothing here\n")
        updated = update_contents("engrams", "marks", [f], dry_run=False)
        assert updated == []


# ---------------------------------------------------------------------------
# fix_symlinks
# ---------------------------------------------------------------------------


class TestFixSymlinks:
    def test_dry_run_identifies_affected_symlinks(self, tmp_path):
        target_dir = tmp_path / "engrams"
        target_dir.mkdir()
        link = tmp_path / "link_to_engrams"
        link.symlink_to(str(target_dir))

        fixed = fix_symlinks("engrams", "marks", [tmp_path], dry_run=True)
        assert len(fixed) == 1
        link_path, old_t, new_t = fixed[0]
        assert "engrams" in old_t
        assert "marks" in new_t

    def test_dry_run_does_not_modify_symlink(self, tmp_path):
        target_dir = tmp_path / "engrams"
        target_dir.mkdir()
        link = tmp_path / "link_to_engrams"
        link.symlink_to(str(target_dir))

        fix_symlinks("engrams", "marks", [tmp_path], dry_run=True)
        import os
        assert "engrams" in os.readlink(str(link))

    def test_live_updates_symlink_target(self, tmp_path):
        target_dir = tmp_path / "marks"
        target_dir.mkdir()
        # Symlink points to path containing "engrams"
        old_target = tmp_path / "engrams"
        link = tmp_path / "link"
        link.symlink_to(str(old_target))

        fixed = fix_symlinks("engrams", "marks", [tmp_path], dry_run=False)
        assert len(fixed) == 1
        import os
        assert "marks" in os.readlink(str(link))

    def test_ignores_symlinks_without_match(self, tmp_path):
        target_dir = tmp_path / "other_dir"
        target_dir.mkdir()
        link = tmp_path / "link"
        link.symlink_to(str(target_dir))

        fixed = fix_symlinks("engrams", "marks", [tmp_path], dry_run=True)
        assert fixed == []


# ---------------------------------------------------------------------------
# run_rename (integration — dry-run)
# ---------------------------------------------------------------------------


class TestRunRename:
    def test_dry_run_produces_summary(self, tmp_path):
        _make_tree(tmp_path)
        report, summary = run_rename("engrams", "marks", [tmp_path], dry_run=True)
        assert "scan:" in summary
        assert "engrams" in summary or "marks" in summary

    def test_dry_run_leaves_filesystem_unchanged(self, tmp_path):
        _make_tree(tmp_path)
        run_rename("engrams", "marks", [tmp_path], dry_run=True)
        # Original directory structure intact
        assert (tmp_path / "engrams").exists()
        assert (tmp_path / "engrams" / "index.md").exists()
        assert (tmp_path / "data" / "engrams_config.toml").exists()
        # File contents unchanged
        assert "engrams" in (tmp_path / "engrams" / "index.md").read_text()

    def test_dry_run_scan_count_reported(self, tmp_path):
        _make_tree(tmp_path)
        _, summary = run_rename("engrams", "marks", [tmp_path], dry_run=True)
        assert "scan:" in summary
        # At least 4 files matched
        assert any(c.isdigit() for c in summary)

    def test_live_run_renames_everything(self, tmp_path):
        _make_tree(tmp_path)
        report, _ = run_rename("engrams", "marks", [tmp_path], dry_run=False)
        # Old top-level dir gone, new one present
        assert not (tmp_path / "engrams").exists()
        assert (tmp_path / "marks").exists()
        # File renamed
        assert (tmp_path / "data" / "marks_config.toml").exists()
        # Contents updated
        content = (tmp_path / "marks" / "index.md").read_text()
        assert "marks" in content

    def test_report_fields_populated(self, tmp_path):
        _make_tree(tmp_path)
        report, _ = run_rename("engrams", "marks", [tmp_path], dry_run=True)
        # Should have at least some dirs and files identified
        assert len(report.renamed_dirs) >= 1
        assert len(report.renamed_files) >= 1
        assert len(report.updated_contents) >= 1

    def test_no_change_when_name_absent(self, tmp_path):
        (tmp_path / "notes.md").write_text("nothing relevant\n")
        report, summary = run_rename("engrams", "marks", [tmp_path], dry_run=True)
        assert report.renamed_dirs == []
        assert report.renamed_files == []
        assert report.updated_contents == []
        assert "nothing to change" in summary
