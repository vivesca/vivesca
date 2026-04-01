from __future__ import annotations

import tempfile
from pathlib import Path
from typing import NamedTuple
from unittest import mock

import pytest

from metabolon.organelles import rename


class TestScan:
    def test_scan_finds_matching_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create test files
            (tmp_path / "file1.py").write_text("contains old_name here")
            (tmp_path / "file2.md").write_text("no matches here")
            (tmp_path / "file3.json").write_text("old_name twice here old_name")
            (tmp_path / "ignored.txt").write_text("old_name here but wrong extension")

            # Create subdirectory
            subdir = tmp_path / "sub"
            subdir.mkdir()
            (subdir / "file4.py").write_text("old_name here")

            result = rename.scan("old_name", [tmp_path])

        assert len(result.files) == 3
        assert result.total_matches == 4
        assert any(p.name == "file1.py" for p in result.files)
        assert any(p.name == "file3.json" for p in result.files)
        assert any(p.name == "file4.py" for p in result.files)

    def test_scan_skips_nonexistent_roots(self) -> None:
        result = rename.scan("old_name", [Path("/this/path/does/not/exist")])
        assert result.files == []
        assert result.total_matches == 0

    def test_scan_handles_permission_error(self, monkeypatch) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("old_name")

            # Mock read_text to raise PermissionError
            original_read = Path.read_text
            def mock_read(self, **kwargs):
                if self == test_file:
                    raise PermissionError
                return original_read(self, **kwargs)

            monkeypatch.setattr(Path, "read_text", mock_read)

            result = rename.scan("old_name", [tmp_path])
            assert result.files == []


class TestRenameDirs:
    def test_rename_dirs_deepest_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create nested directories: parent/child/old_name
            parent = tmp_path / "old_name"
            parent.mkdir()
            child = parent / "old_name"
            child.mkdir()

            result = rename.rename_dirs("old_name", "new_name", [tmp_path], dry_run=True)

        # Should find both directories
        assert len(result) == 2
        # Child should be renamed first (deepest first)
        # The paths returned are before renaming
        assert any(p[0].parent.parent == tmp_path for p in result)  # parent
        assert any(p[0].parent.name == "old_name" for p in result)   # child

    def test_rename_dirs_dry_run_no_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            old_dir = tmp_path / "old_name"
            old_dir.mkdir()

            result = rename.rename_dirs("old_name", "new_name", [tmp_path], dry_run=True)

            assert len(result) == 1
            assert old_dir.exists()
            assert not (tmp_path / "new_name").exists()

    def test_rename_dirs_actual_rename(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            old_dir = tmp_path / "old_name"
            old_dir.mkdir()

            result = rename.rename_dirs("old_name", "new_name", [tmp_path], dry_run=False)

            assert len(result) == 1
            assert not old_dir.exists()
            assert (tmp_path / "new_name").exists()

    def test_rename_dirs_skips_nonexistent_roots(self) -> None:
        result = rename.rename_dirs("old", "new", [Path("/does/not/exist")], dry_run=True)
        assert result == []


class TestRenameFiles:
    def test_rename_files_finds_matches_in_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "old_name_test.py").write_text("content")
            (tmp_path / "test_old_name.py").write_text("content")
            (tmp_path / "test.py").write_text("content contains old_name but name doesn't have it")

            result = rename.rename_files("old_name", "new_name", [tmp_path], dry_run=True)

            assert len(result) == 2
            assert any(p[0].name == "old_name_test.py" for p in result)
            assert any(p[0].name == "test_old_name.py" for p in result)

    def test_rename_files_actual_rename(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            old_file = tmp_path / "old_name.py"
            old_file.write_text("content")

            result = rename.rename_files("old_name", "new_name", [tmp_path], dry_run=False)

            assert len(result) == 1
            assert not old_file.exists()
            assert (tmp_path / "new_name.py").exists()
            assert (tmp_path / "new_name.py").read_text() == "content"


class TestUpdateContents:
    def test_update_contents_replaces_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("hello old_name world\nold_name again")

            result = rename.update_contents("old_name", "new_name", [test_file], dry_run=False)

            assert len(result) == 1
            assert test_file.read_text() == "hello new_name world\nnew_name again"

    def test_update_contents_dry_run_no_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            original = "hello old_name world"
            test_file.write_text(original)

            result = rename.update_contents("old_name", "new_name", [test_file], dry_run=True)

            assert len(result) == 1
            assert test_file.read_text() == original

    def test_update_contents_skips_nonexistent_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            existing = tmp_path / "existing.py"
            existing.write_text("old_name")
            nonexistent = tmp_path / "nonexistent.py"

            result = rename.update_contents("old_name", "new_name", [existing, nonexistent], dry_run=False)

            assert len(result) == 1

    def test_update_contents_skips_files_without_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("no matches here")

            result = rename.update_contents("old_name", "new_name", [test_file], dry_run=False)

            assert len(result) == 0


class TestUpdateLocus:
    def test_update_locus_updates_if_found(self, monkeypatch) -> None:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            f.write("contains old_name here")
            temp_path = Path(f.name)

        monkeypatch.setattr(rename, "_LOCUS_PATH", temp_path)

        result = rename.update_locus("old_name", "new_name", dry_run=False)
        assert result is True
        assert temp_path.read_text() == "contains new_name here"

        temp_path.unlink()

    def test_update_locus_dry_run_no_change(self, monkeypatch) -> None:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            f.write("contains old_name here")
            temp_path = Path(f.name)

        monkeypatch.setattr(rename, "_LOCUS_PATH", temp_path)

        result = rename.update_locus("old_name", "new_name", dry_run=True)
        assert result is True
        assert temp_path.read_text() == "contains old_name here"

        temp_path.unlink()

    def test_update_locus_returns_false_if_not_found(self, monkeypatch) -> None:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            f.write("no match here")
            temp_path = Path(f.name)

        monkeypatch.setattr(rename, "_LOCUS_PATH", temp_path)

        result = rename.update_locus("old_name", "new_name", dry_run=False)
        assert result is False

        temp_path.unlink()

    def test_update_locus_returns_false_if_nonexistent(self, monkeypatch) -> None:
        monkeypatch.setattr(rename, "_LOCUS_PATH", Path("/does/not/exist"))
        result = rename.update_locus("old", "new", dry_run=False)
        assert result is False


class TestFixSymlinks:
    def test_fix_symlinks_updates_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            target_dir = tmp_path / "old_name"
            target_dir.mkdir()
            link_path = tmp_path / "link_to_old"
            link_path.symlink_to(target_dir)

            result = rename.fix_symlinks("old_name", "new_name", [tmp_path], dry_run=False)

            assert len(result) == 1
            # After rename of target, symlink should point to new name
            assert link_path.is_symlink()
            new_target = str(tmp_path / "new_name")
            assert str(link_path.readlink()) == new_target

    def test_fix_symlinks_dry_run_no_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            target_dir = tmp_path / "old_name"
            target_dir.mkdir()
            link_path = tmp_path / "link_to_old"
            link_path.symlink_to(target_dir)

            result = rename.fix_symlinks("old_name", "new_name", [tmp_path], dry_run=True)

            assert len(result) == 1
            assert str(link_path.readlink()) == str(target_dir)


class TestFindGitRepo:
    def test_finds_git_repo_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / ".git").mkdir()
            subdir = tmp_path / "sub" / "subsub"
            subdir.mkdir(parents=True)
            test_file = subdir / "test.py"
            test_file.touch()

            result = rename._find_git_repo(test_file)
            assert result == tmp_path

    def test_returns_none_if_no_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.touch()

            result = rename._find_git_repo(test_file)
            assert result is None


class TestCommitChanges:
    def test_commit_changes_groups_by_repo(self, monkeypatch) -> None:
        mock_run = mock.Mock()
        mock_run.return_value.returncode = 0
        monkeypatch.setattr(rename.subprocess, "run", mock_run)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / ".git").mkdir()
            file1 = tmp_path / "file1.py"
            file2 = tmp_path / "file2.py"
            file1.touch()
            file2.touch()

            result = rename.commit_changes("old", "new", [file1, file2])

            assert len(result) == 1
            # Two adds, add -u, and commit = 4 calls
            assert mock_run.call_count == 4

    def test_commit_changes_returns_empty_list_no_changes(self, monkeypatch) -> None:
        mock_run = mock.Mock()
        monkeypatch.setattr(rename.subprocess, "run", mock_run)

        result = rename.commit_changes("old", "new", [])
        assert result == []
        mock_run.assert_not_called()


class TestRemapPaths:
    def test_remap_renamed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            old_file = tmp_path / "old.py"
            new_file = tmp_path / "new.py"

            renamed_files = [(old_file, new_file)]
            renamed_dirs = []

            result = rename._remap_paths([old_file], renamed_dirs, renamed_files)
            assert result == [new_file]

    def test_remap_under_renamed_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            old_dir = tmp_path / "old_dir"
            old_dir.mkdir()
            file_in_dir = old_dir / "file.py"

            new_dir = tmp_path / "new_dir"

            renamed_dirs = [(old_dir, new_dir)]
            renamed_files = []

            result = rename._remap_paths([file_in_dir], renamed_dirs, renamed_files)
            assert result[0] == new_dir / "file.py"

    def test_remap_unchanged_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            unchanged = tmp_path / "unchanged.py"
            unchanged.touch()

            renamed_dirs = []
            renamed_files = []

            result = rename._remap_paths([unchanged], renamed_dirs, renamed_files)
            assert result == [unchanged]


class TestBuildReport:
    def test_build_report_empty(self) -> None:
        scan_result = rename.ScanResult(files=[], total_matches=0)
        report = rename.build_report(
            scan_result,
            [],
            [],
            [],
            False,
            [],
        )
        assert "nothing to change" in report

    def test_build_report_shows_all_changes(self) -> None:
        scan_result = rename.ScanResult(files=[Path("f1.py"), Path("f2.py")], total_matches=5)
        renamed_dirs = [(Path("old_dir"), Path("new_dir"))]
        renamed_files = [(Path("old.py"), Path("new.py"))]
        updated_contents = [Path("f1.py")]
        updated_locus = True
        fixed_symlinks = [(Path("link"), "old_target", "new_target")]

        summary = rename.build_report(
            scan_result,
            renamed_dirs,
            renamed_files,
            updated_contents,
            updated_locus,
            fixed_symlinks,
        )

        assert "scan: 5 occurrences in 2 files" in summary
        assert "renamed dirs (1):" in summary
        assert "renamed files (1):" in summary
        assert "updated contents (1):" in summary
        assert "updated locus.py" in summary
        assert "fixed symlinks (1):" in summary


class TestRunRename:
    def test_run_rename_dry_run_completes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "old_name.py").write_text("old_name content")
            (tmp_path / "old_name").mkdir()

            report, summary = rename.run_rename("old_name", "new_name", [tmp_path], dry_run=True)

            assert isinstance(report, rename.RenameReport)
            assert len(report.renamed_dirs) == 1
            assert len(report.renamed_files) == 1
            assert len(report.updated_contents) >= 1
            assert "scan:" in summary

    def test_run_rename_nothing_to_do(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "test.py").write_text("no matches here")

            report, summary = rename.run_rename("old_name", "new_name", [tmp_path], dry_run=True)

            assert len(report.renamed_dirs) == 0
            assert len(report.renamed_files) == 0
            assert "nothing to change" in summary
