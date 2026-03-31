#!/usr/bin/env python3
"""Tests for effectors/vesicle — garden CLI for terryli.hm.

vesicle is identical to publish (same script). Tests cover the same logic
loaded via the vesicle path. Uses exec() — never imports.
"""

import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Load the vesicle effector via exec
# ---------------------------------------------------------------------------
VESICLE_PATH = Path(__file__).resolve().parents[1] / "effectors" / "vesicle"
_vesicle_code = VESICLE_PATH.read_text()
ves = {}
exec(_vesicle_code, ves)


# ---------------------------------------------------------------------------
# Verify it's the same as publish
# ---------------------------------------------------------------------------

class TestVesicleIsPublish:
    def test_vesicle_file_exists(self):
        assert VESICLE_PATH.is_file()

    def test_vesicle_has_same_functions(self):
        """Vesicle should expose the same functions as publish."""
        publish_path = VESICLE_PATH.parent / "publish"
        pub2 = {}
        exec(publish_path.read_text(), pub2)
        expected_fns = ["cmd_new", "cmd_list", "cmd_publish", "cmd_revise",
                        "cmd_open", "cmd_index", "cmd_push", "main",
                        "to_slug", "parse_frontmatter", "scan_content", "now_iso"]
        for fn in expected_fns:
            assert fn in ves, f"{fn} missing from vesicle"
            assert fn in pub2, f"{fn} missing from publish"


# ---------------------------------------------------------------------------
# Pure function tests
# ---------------------------------------------------------------------------

class TestNowIso:
    def test_format(self):
        result = ves["now_iso"]()
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.000Z$", result)

    def test_is_valid_datetime(self):
        result = ves["now_iso"]()
        # Should not raise
        datetime.strptime(result, "%Y-%m-%dT%H:%M:%S.000Z")


class TestToSlug:
    @pytest.mark.parametrize("title,expected", [
        ("Hello World", "hello-world"),
        ("A & B * C", "a-b-c"),
        ("  spaces  ", "spaces"),
        ("UPPER CASE", "upper-case"),
        ("a-b_c d", "a-b-c-d"),
        ("post #42!", "post-42"),
        ("", ""),
        ("Under_Score", "under-score"),
    ])
    def test_slug_conversion(self, title, expected):
        assert ves["to_slug"](title) == expected


class TestParseFrontmatter:
    def test_standard_frontmatter(self):
        content = '---\ntitle: "Hello"\ndraft: false\npubDatetime: 2025-01-01T00:00:00.000Z\ntags: [a]\n---\nBody'
        fm = ves["parse_frontmatter"](content)
        assert fm["title"] == "Hello"
        assert fm["draft"] is False
        assert fm["tags"] == ["a"]

    def test_no_frontmatter_returns_none(self):
        assert ves["parse_frontmatter"]("no fm") is None

    def test_empty_tags(self):
        fm = ves["parse_frontmatter"]("---\ntags: []\n---\n")
        assert fm["tags"] == []

    def test_single_tag(self):
        fm = ves["parse_frontmatter"]("---\ntags: [solo]\n---\n")
        assert fm["tags"] == ["solo"]

    def test_body_offset_points_past_frontmatter(self):
        content = "---\ntitle: T\n---\n\nActual body."
        fm = ves["parse_frontmatter"](content)
        assert content[fm["_body_offset"]:] == "\nActual body."


class TestScanContent:
    def test_clean(self):
        assert ves["scan_content"]("Clean content here.") == []

    def test_dollar(self):
        assert any("dollar" in w for w in ves["scan_content"]("Got $100"))

    def test_hkd(self):
        assert any("HKD" in w for w in ves["scan_content"]("Cost HKD 5000"))

    def test_millions(self):
        assert any("million" in w for w in ves["scan_content"]("50 million"))

    def test_named_person(self):
        assert len(ves["scan_content"]("Said Prof. Andrews")) >= 1

    def test_secret(self):
        assert len(ves["scan_content"]('password: "abcdefgh"')) >= 1

    def test_no_false_positive(self):
        """Words like 'million' without a number should not trigger."""
        # The regex is [0-9]+\s*million — needs a number before "million"
        result = ves["scan_content"]("Millions of people attended.")
        # "Millions" won't match the regex since it lacks a number prefix
        assert not any("million" in w for w in result)


# ---------------------------------------------------------------------------
# cmd_new
# ---------------------------------------------------------------------------

class TestCmdNew:
    def test_creates_draft_file(self, tmp_path, capsys):
        vault = tmp_path / "pub"
        args = SimpleNamespace(title="New Post")
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            rc = ves["cmd_new"](args)
            assert rc == 0
            slug = ves["to_slug"]("New Post")
            fpath = vault / f"{slug}.md"
            assert fpath.exists()
            txt = fpath.read_text()
            assert "draft: true" in txt
            assert 'title: "New Post"' in txt
            captured = capsys.readouterr()
            assert "Created" in captured.out
        finally:
            ves["VAULT_DIR"] = orig

    def test_rejects_duplicate(self, tmp_path, capsys):
        vault = tmp_path / "pub"
        vault.mkdir()
        (vault / "dup.md").write_text("old")
        args = SimpleNamespace(title="dup")
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            rc = ves["cmd_new"](args)
            assert rc == 1
            captured = capsys.readouterr()
            assert "already exists" in captured.err
        finally:
            ves["VAULT_DIR"] = orig


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

class TestCmdList:
    def test_no_vault(self, capsys):
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = Path("/no/such/vesicle/vault")
        try:
            rc = ves["cmd_list"](SimpleNamespace())
            assert rc == 1
            captured = capsys.readouterr()
            assert "No vault" in captured.err
        finally:
            ves["VAULT_DIR"] = orig

    def test_lists_with_word_count(self, tmp_path, capsys):
        vault = tmp_path / "pub"
        vault.mkdir()
        (vault / "wcount.md").write_text(
            '---\ntitle: "WC"\ndescription: ""\n'
            "pubDatetime: 2025-06-01T00:00:00.000Z\ndraft: false\ntags: []\n---\n\n"
            "one two three four five"
        )
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            rc = ves["cmd_list"](SimpleNamespace())
            assert rc == 0
            captured = capsys.readouterr()
            assert "wcount" in captured.out
        finally:
            ves["VAULT_DIR"] = orig


# ---------------------------------------------------------------------------
# cmd_publish
# ---------------------------------------------------------------------------

class TestCmdPublish:
    def test_flips_draft_flag(self, tmp_path, capsys):
        vault = tmp_path / "pub"
        vault.mkdir()
        (vault / "flip.md").write_text(
            '---\ntitle: "Flip"\ndescription: ""\n'
            "pubDatetime: 2025-01-01T00:00:00.000Z\ndraft: true\ntags: []\n---\n\n"
        )
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            rc = ves["cmd_publish"](SimpleNamespace(slug="flip", push=False))
            assert rc == 0
            assert "draft: false" in (vault / "flip.md").read_text()
            captured = capsys.readouterr()
            assert "Published" in captured.out
        finally:
            ves["VAULT_DIR"] = orig

    def test_already_published_is_noop(self, tmp_path, capsys):
        vault = tmp_path / "pub"
        vault.mkdir()
        (vault / "done.md").write_text(
            '---\ntitle: "Done"\ndescription: ""\n'
            "pubDatetime: 2025-01-01T00:00:00.000Z\ndraft: false\ntags: []\n---\n\n"
        )
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            rc = ves["cmd_publish"](SimpleNamespace(slug="done", push=False))
            assert rc == 0
            captured = capsys.readouterr()
            assert "Already published" in captured.out
            # File unchanged
            assert "draft: false" in (vault / "done.md").read_text()
        finally:
            ves["VAULT_DIR"] = orig

    def test_missing_post(self, tmp_path, capsys):
        vault = tmp_path / "pub"
        vault.mkdir()
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            rc = ves["cmd_publish"](SimpleNamespace(slug="ghost", push=False))
            assert rc == 1
            captured = capsys.readouterr()
            assert "No post found" in captured.err
        finally:
            ves["VAULT_DIR"] = orig


# ---------------------------------------------------------------------------
# cmd_revise
# ---------------------------------------------------------------------------

class TestCmdRevise:
    def test_adds_note_and_modtime(self, tmp_path):
        vault = tmp_path / "pub"
        vault.mkdir()
        (vault / "rev.md").write_text(
            '---\ntitle: "Rev"\ndescription: ""\n'
            "pubDatetime: 2025-01-01T00:00:00.000Z\ndraft: false\ntags: []\n---\n\n"
        )
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            rc = ves["cmd_revise"](SimpleNamespace(slug="rev", note="typo fix"))
            assert rc == 0
            content = (vault / "rev.md").read_text()
            assert 'revisionNote: "typo fix"' in content
            assert "modDatetime:" in content
        finally:
            ves["VAULT_DIR"] = orig

    def test_not_found(self, tmp_path, capsys):
        vault = tmp_path / "pub"
        vault.mkdir()
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            rc = ves["cmd_revise"](SimpleNamespace(slug="missing", note="x"))
            assert rc == 1
        finally:
            ves["VAULT_DIR"] = orig


# ---------------------------------------------------------------------------
# cmd_open
# ---------------------------------------------------------------------------

class TestCmdOpen:
    def test_missing_file(self, tmp_path, capsys):
        vault = tmp_path / "pub"
        vault.mkdir()
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            rc = ves["cmd_open"](SimpleNamespace(slug="none"))
            assert rc == 1
        finally:
            ves["VAULT_DIR"] = orig

    def test_launches_editor(self, tmp_path):
        vault = tmp_path / "pub"
        vault.mkdir()
        (vault / "ed.md").write_text("---\ntitle: ed\n---\n")
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                with patch.dict("os.environ", {"EDITOR": "vim"}):
                    rc = ves["cmd_open"](SimpleNamespace(slug="ed"))
                assert rc == 0
                args_passed = mock_run.call_args[0][0]
                assert args_passed[0] == "vim"
        finally:
            ves["VAULT_DIR"] = orig


# ---------------------------------------------------------------------------
# cmd_index
# ---------------------------------------------------------------------------

class TestCmdIndex:
    def test_generates_markdown_index(self, tmp_path, capsys):
        vault = tmp_path / "pub"
        vault.mkdir()
        idx = tmp_path / "garden.md"
        (vault / "apost.md").write_text(
            '---\ntitle: "Alpha"\ndescription: "first"\n'
            "pubDatetime: 2025-02-01T00:00:00.000Z\ndraft: false\ntags: [dev]\n---\n\n"
        )
        orig_v = ves["VAULT_DIR"]
        orig_i = ves["INDEX_PATH"]
        ves["VAULT_DIR"] = vault
        ves["INDEX_PATH"] = idx
        try:
            rc = ves["cmd_index"](SimpleNamespace())
            assert rc == 0
            content = idx.read_text()
            assert "Alpha" in content
            assert "### dev" in content
            assert "By topic" in content
        finally:
            ves["VAULT_DIR"] = orig_v
            ves["INDEX_PATH"] = orig_i

    def test_excludes_drafts(self, tmp_path):
        vault = tmp_path / "pub"
        vault.mkdir()
        idx = tmp_path / "garden.md"
        (vault / "d.md").write_text(
            '---\ntitle: "Draft"\ndescription: ""\n'
            "pubDatetime: 2025-02-01T00:00:00.000Z\ndraft: true\ntags: []\n---\n\n"
        )
        orig_v = ves["VAULT_DIR"]
        orig_i = ves["INDEX_PATH"]
        ves["VAULT_DIR"] = vault
        ves["INDEX_PATH"] = idx
        try:
            rc = ves["cmd_index"](SimpleNamespace())
            assert rc == 0
            content = idx.read_text()
            assert "Draft" not in content
        finally:
            ves["VAULT_DIR"] = orig_v
            ves["INDEX_PATH"] = orig_i


# ---------------------------------------------------------------------------
# cmd_push
# ---------------------------------------------------------------------------

class TestCmdPush:
    def test_no_sync_script(self, tmp_path, capsys):
        orig = ves["SYNC_SCRIPT"]
        ves["SYNC_SCRIPT"] = tmp_path / "no" / "sync.sh"
        try:
            rc = ves["cmd_push"](SimpleNamespace())
            assert rc == 1
            captured = capsys.readouterr()
            assert "not found" in captured.err
        finally:
            ves["SYNC_SCRIPT"] = orig

    def test_successful_sync(self, tmp_path, capsys):
        s = tmp_path / "sync.sh"
        s.write_text("#!/bin/bash\nexit 0")
        s.chmod(0o755)
        orig = ves["SYNC_SCRIPT"]
        ves["SYNC_SCRIPT"] = s
        try:
            rc = ves["cmd_push"](SimpleNamespace())
            assert rc == 0
            captured = capsys.readouterr()
            assert "Live at" in captured.out
        finally:
            ves["SYNC_SCRIPT"] = orig

    def test_failed_sync(self, tmp_path, capsys):
        s = tmp_path / "fail.sh"
        s.write_text("#!/bin/bash\nexit 42")
        s.chmod(0o755)
        orig = ves["SYNC_SCRIPT"]
        ves["SYNC_SCRIPT"] = s
        try:
            rc = ves["cmd_push"](SimpleNamespace())
            assert rc == 1
            captured = capsys.readouterr()
            assert "Sync failed" in captured.err
        finally:
            ves["SYNC_SCRIPT"] = orig


# ---------------------------------------------------------------------------
# Integration: main() via CLI
# ---------------------------------------------------------------------------

class TestMain:
    def test_missing_command_exits(self):
        with patch("sys.argv", ["vesicle"]):
            with pytest.raises(SystemExit) as exc_info:
                ves["main"]()
            assert exc_info.value.code == 2

    def test_new_command(self, tmp_path, capsys):
        vault = tmp_path / "pub"
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            with patch("sys.argv", ["vesicle", "new", "Main Test"]):
                with pytest.raises(SystemExit) as exc_info:
                    ves["main"]()
                assert exc_info.value.code == 0
            slug = ves["to_slug"]("Main Test")
            assert (vault / f"{slug}.md").exists()
        finally:
            ves["VAULT_DIR"] = orig

    def test_publish_command(self, tmp_path):
        vault = tmp_path / "pub"
        vault.mkdir()
        (vault / "mp.md").write_text(
            '---\ntitle: "MP"\ndescription: ""\n'
            "pubDatetime: 2025-01-01T00:00:00.000Z\ndraft: true\ntags: []\n---\n\n"
        )
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            with patch("sys.argv", ["vesicle", "publish", "mp"]):
                with pytest.raises(SystemExit) as exc_info:
                    ves["main"]()
                assert exc_info.value.code == 0
            assert "draft: false" in (vault / "mp.md").read_text()
        finally:
            ves["VAULT_DIR"] = orig

    def test_revise_command(self, tmp_path):
        vault = tmp_path / "pub"
        vault.mkdir()
        (vault / "mr.md").write_text(
            '---\ntitle: "MR"\ndescription: ""\n'
            "pubDatetime: 2025-01-01T00:00:00.000Z\ndraft: false\ntags: []\n---\n\n"
        )
        orig = ves["VAULT_DIR"]
        ves["VAULT_DIR"] = vault
        try:
            with patch("sys.argv", ["vesicle", "revise", "mr", "--note", "fix"]):
                with pytest.raises(SystemExit) as exc_info:
                    ves["main"]()
                assert exc_info.value.code == 0
            assert 'revisionNote: "fix"' in (vault / "mr.md").read_text()
        finally:
            ves["VAULT_DIR"] = orig

    def test_index_command(self, tmp_path):
        vault = tmp_path / "pub"
        vault.mkdir()
        idx = tmp_path / "i.md"
        (vault / "ix.md").write_text(
            '---\ntitle: "IX"\ndescription: "d"\n'
            "pubDatetime: 2025-01-01T00:00:00.000Z\ndraft: false\ntags: []\n---\n\n"
        )
        orig_v = ves["VAULT_DIR"]
        orig_i = ves["INDEX_PATH"]
        ves["VAULT_DIR"] = vault
        ves["INDEX_PATH"] = idx
        try:
            with patch("sys.argv", ["vesicle", "index"]):
                with pytest.raises(SystemExit) as exc_info:
                    ves["main"]()
                assert exc_info.value.code == 0
            assert idx.exists()
        finally:
            ves["VAULT_DIR"] = orig_v
            ves["INDEX_PATH"] = orig_i

    def test_push_command_no_script(self, tmp_path):
        orig = ves["SYNC_SCRIPT"]
        ves["SYNC_SCRIPT"] = tmp_path / "no" / "sync.sh"
        try:
            with patch("sys.argv", ["vesicle", "push"]):
                with pytest.raises(SystemExit) as exc_info:
                    ves["main"]()
                assert exc_info.value.code == 1
        finally:
            ves["SYNC_SCRIPT"] = orig
