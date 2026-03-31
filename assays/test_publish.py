#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/publish — garden CLI for terryli.hm.

Uses exec() to load the script (never imports). Mocks filesystem paths
and subprocess calls.
"""


import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Load the publish effector via exec
# ---------------------------------------------------------------------------
PUBLISH_PATH = Path(__file__).resolve().parents[1] / "effectors" / "publish"
_publish_code = PUBLISH_PATH.read_text()
pub = {}
exec(_publish_code, pub)


# ---------------------------------------------------------------------------
# Pure-function tests: now_iso
# ---------------------------------------------------------------------------

class TestNowIso:
    def test_returns_iso_format(self):
        """now_iso returns a string matching YYYY-MM-DDTHH:MM:SS.000Z."""
        result = pub["now_iso"]()
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.000Z$", result)

    def test_utc_timestamp(self):
        """now_iso should be close to current UTC time (within 2 seconds)."""
        from datetime import timedelta as td
        from datetime import datetime as dt_cls, timezone
        before = dt_cls.now(timezone.utc) - td(seconds=1)
        result = pub["now_iso"]()
        after = dt_cls.now(timezone.utc) + td(seconds=1)
        result_dt = dt_cls.strptime(result, "%Y-%m-%dT%H:%M:%S.000Z").replace(tzinfo=timezone.utc)
        assert before <= result_dt <= after


# ---------------------------------------------------------------------------
# Pure-function tests: to_slug
# ---------------------------------------------------------------------------

class TestToSlug:
    def test_simple_title(self):
        assert pub["to_slug"]("Hello World") == "hello-world"

    def test_special_characters_removed(self):
        assert pub["to_slug"]("Hello, World!") == "hello-world"

    def test_multiple_spaces_collapsed(self):
        assert pub["to_slug"]("foo   bar") == "foo-bar"

    def test_hyphens_collapsed(self):
        assert pub["to_slug"]("foo--bar") == "foo-bar"

    def test_leading_trailing_stripped(self):
        assert pub["to_slug"]("--hello-world--") == "hello-world"

    def test_uppercase_lowered(self):
        assert pub["to_slug"]("My GREAT Post") == "my-great-post"

    def test_underscores_converted(self):
        assert pub["to_slug"]("my_great_post") == "my-great-post"

    def test_empty_string(self):
        assert pub["to_slug"]("") == ""

    def test_numbers_preserved(self):
        assert pub["to_slug"]("Post 123") == "post-123"

    def test_mixed_separators(self):
        assert pub["to_slug"]("a _ b - c") == "a-b-c"


# ---------------------------------------------------------------------------
# Pure-function tests: parse_frontmatter
# ---------------------------------------------------------------------------

class TestParseFrontmatter:
    def test_basic_frontmatter(self):
        content = '---\ntitle: "Test"\ndraft: true\n---\nBody here'
        fm = pub["parse_frontmatter"](content)
        assert fm is not None
        assert fm["title"] == "Test"
        assert fm["draft"] is True

    def test_no_frontmatter(self):
        content = "Just some markdown\nNo frontmatter"
        assert pub["parse_frontmatter"](content) is None

    def test_empty_frontmatter(self):
        content = "---\n---\nBody"
        fm = pub["parse_frontmatter"](content)
        assert fm is not None
        assert fm.get("title") is None

    def test_tags_parsed_as_list(self):
        content = '---\ntags: [python, testing, ci]\n---\nBody'
        fm = pub["parse_frontmatter"](content)
        assert fm["tags"] == ["python", "testing", "ci"]

    def test_boolean_false(self):
        content = "---\ndraft: false\n---\nBody"
        fm = pub["parse_frontmatter"](content)
        assert fm["draft"] is False

    def test_boolean_true(self):
        content = "---\ndraft: true\n---\nBody"
        fm = pub["parse_frontmatter"](content)
        assert fm["draft"] is True

    def test_body_offset(self):
        content = "---\ntitle: Hello\n---\n\nBody paragraph"
        fm = pub["parse_frontmatter"](content)
        assert fm is not None
        assert "_body_offset" in fm
        body = content[fm["_body_offset"]:]
        assert body.startswith("\nBody paragraph")

    def test_single_quoted_values(self):
        content = "---\ntitle: 'My Post'\n---\n"
        fm = pub["parse_frontmatter"](content)
        assert fm["title"] == "My Post"

    def test_empty_tags(self):
        content = "---\ntags: []\n---\n"
        fm = pub["parse_frontmatter"](content)
        assert fm["tags"] == []

    def test_colon_in_value(self):
        """Values after first colon kept intact."""
        content = '---\ndescription: "A: B"\n---\n'
        fm = pub["parse_frontmatter"](content)
        assert "A: B" in fm["description"]


# ---------------------------------------------------------------------------
# Pure-function tests: scan_content
# ---------------------------------------------------------------------------

class TestScanContent:
    def test_clean_content_no_warnings(self):
        result = pub["scan_content"]("This is a perfectly fine blog post.")
        assert result == []

    def test_dollar_figure(self):
        result = pub["scan_content"]("I made $5000 last month.")
        assert len(result) == 1
        assert "dollar figure" in result[0]

    def test_hkd_figure(self):
        result = pub["scan_content"]("Cost was HKD 12000.")
        assert len(result) == 1
        assert "HKD figure" in result[0]

    def test_million_figure(self):
        result = pub["scan_content"]("Revenue hit 5 million units.")
        assert len(result) == 1
        assert "million" in result[0]

    def test_named_individual(self):
        result = pub["scan_content"]("According to Dr. Smith the results are in.")
        assert len(result) >= 1
        assert any("individual" in w for w in result)

    def test_credential(self):
        result = pub["scan_content"]('password = "abcdefghijk"')
        assert len(result) >= 1
        assert any("credential" in w for w in result)

    def test_api_key_detected(self):
        result = pub["scan_content"]('api_key = "ABCDEFGH12345678"')
        assert len(result) >= 1
        assert any("credential" in w for w in result)

    def test_multiple_warnings(self):
        content = "Made $100 and met Mr. Johnson."
        result = pub["scan_content"](content)
        assert len(result) >= 2


# ---------------------------------------------------------------------------
# cmd_new tests
# ---------------------------------------------------------------------------

class TestCmdNew:
    def test_creates_file(self, tmp_path):
        vault = tmp_path / "Published"
        args = SimpleNamespace(title="Test Post")
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_new"](args)
            assert rc == 0
            slug = pub["to_slug"]("Test Post")
            fpath = vault / f"{slug}.md"
            assert fpath.exists()
            content = fpath.read_text()
            assert 'title: "Test Post"' in content
            assert "draft: true" in content
        finally:
            pub["VAULT_DIR"] = orig

    def test_refuses_existing_file(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir(parents=True)
        slug = pub["to_slug"]("Existing Post")
        (vault / f"{slug}.md").write_text("old content")
        args = SimpleNamespace(title="Existing Post")
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_new"](args)
            assert rc == 1
            captured = capsys.readouterr()
            assert "already exists" in captured.err
        finally:
            pub["VAULT_DIR"] = orig

    def test_creates_parent_dirs(self, tmp_path):
        vault = tmp_path / "deep" / "nested" / "Published"
        args = SimpleNamespace(title="Nested Test")
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_new"](args)
            assert rc == 0
            assert vault.exists()
        finally:
            pub["VAULT_DIR"] = orig


# ---------------------------------------------------------------------------
# cmd_list tests
# ---------------------------------------------------------------------------

class TestCmdList:
    def test_no_vault_dir(self, capsys):
        fake_dir = Path("/nonexistent/path/no/vault")
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = fake_dir
        try:
            rc = pub["cmd_list"](SimpleNamespace())
            assert rc == 1
            captured = capsys.readouterr()
            assert "No vault directory" in captured.err
        finally:
            pub["VAULT_DIR"] = orig

    def test_lists_posts(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        # Create a test post
        post = vault / "test-post.md"
        post.write_text(
            '---\ntitle: "Test Post"\ndescription: "desc"\n'
            "pubDatetime: 2025-01-15T10:00:00.000Z\ndraft: false\ntags: []\n---\n\nHello world."
        )
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_list"](SimpleNamespace())
            assert rc == 0
            captured = capsys.readouterr()
            assert "test-post" in captured.out
            assert "Test Post" in captured.out
        finally:
            pub["VAULT_DIR"] = orig

    def test_skips_files_without_frontmatter(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "no-fm.md").write_text("Just some text without frontmatter")
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_list"](SimpleNamespace())
            assert rc == 0
            captured = capsys.readouterr()
            assert "no-fm" not in captured.out
        finally:
            pub["VAULT_DIR"] = orig

    def test_shows_draft_marker(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "draft-post.md").write_text(
            '---\ntitle: "Draft"\ndescription: ""\n'
            "pubDatetime: 2025-01-15T10:00:00.000Z\ndraft: true\ntags: []\n---\n\n"
        )
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_list"](SimpleNamespace())
            assert rc == 0
            captured = capsys.readouterr()
            assert "(draft)" in captured.out
        finally:
            pub["VAULT_DIR"] = orig


# ---------------------------------------------------------------------------
# cmd_publish tests
# ---------------------------------------------------------------------------

class TestCmdPublish:
    def test_publish_draft(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "my-post.md").write_text(
            '---\ntitle: "My Post"\ndescription: "desc"\n'
            "pubDatetime: 2025-01-15T10:00:00.000Z\ndraft: true\ntags: []\n---\n\nContent."
        )
        args = SimpleNamespace(slug="my-post", push=False)
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_publish"](args)
            assert rc == 0
            content = (vault / "my-post.md").read_text()
            assert "draft: false" in content
            captured = capsys.readouterr()
            assert "Published" in captured.out
        finally:
            pub["VAULT_DIR"] = orig

    def test_already_published(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "my-post.md").write_text(
            '---\ntitle: "My Post"\ndescription: "desc"\n'
            "pubDatetime: 2025-01-15T10:00:00.000Z\ndraft: false\ntags: []\n---\n\nContent."
        )
        args = SimpleNamespace(slug="my-post", push=False)
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_publish"](args)
            assert rc == 0
            captured = capsys.readouterr()
            assert "Already published" in captured.out
        finally:
            pub["VAULT_DIR"] = orig

    def test_post_not_found(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        args = SimpleNamespace(slug="nonexistent", push=False)
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_publish"](args)
            assert rc == 1
            captured = capsys.readouterr()
            assert "No post found" in captured.err
        finally:
            pub["VAULT_DIR"] = orig

    def test_bad_frontmatter(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "bad-post.md").write_text("No frontmatter here")
        args = SimpleNamespace(slug="bad-post", push=False)
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_publish"](args)
            assert rc == 1
            captured = capsys.readouterr()
            assert "Failed to parse frontmatter" in captured.err
        finally:
            pub["VAULT_DIR"] = orig

    def test_publish_with_content_warnings(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "sensitive.md").write_text(
            '---\ntitle: "Sensitive"\ndescription: ""\n'
            "pubDatetime: 2025-01-15T10:00:00.000Z\ndraft: true\ntags: []\n---\n\n"
            "I earned $50000 last year."
        )
        args = SimpleNamespace(slug="sensitive", push=False)
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_publish"](args)
            assert rc == 0
            captured = capsys.readouterr()
            assert "Content scan warnings" in captured.err
            # Still publishes despite warnings
            assert "draft: false" in (vault / "sensitive.md").read_text()
        finally:
            pub["VAULT_DIR"] = orig

    def test_publish_with_push_calls_cmd_push(self, tmp_path):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "push-me.md").write_text(
            '---\ntitle: "Push Me"\ndescription: "desc"\n'
            "pubDatetime: 2025-01-15T10:00:00.000Z\ndraft: true\ntags: []\n---\n\nContent."
        )
        args = SimpleNamespace(slug="push-me", push=True)
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            with patch.dict(pub, {"cmd_push": MagicMock(return_value=0)}):
                rc = pub["cmd_publish"](args)
                assert rc == 0
                pub["cmd_push"].assert_called_once_with(None)
        finally:
            pub["VAULT_DIR"] = orig


# ---------------------------------------------------------------------------
# cmd_revise tests
# ---------------------------------------------------------------------------

class TestCmdRevise:
    def test_revise_adds_revision_note(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "rev-post.md").write_text(
            '---\ntitle: "Rev Post"\ndescription: "desc"\n'
            "pubDatetime: 2025-01-15T10:00:00.000Z\ndraft: false\ntags: []\n---\n\nContent."
        )
        args = SimpleNamespace(slug="rev-post", note="Fixed typo")
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_revise"](args)
            assert rc == 0
            content = (vault / "rev-post.md").read_text()
            assert 'revisionNote: "Fixed typo"' in content
            assert "modDatetime:" in content
            captured = capsys.readouterr()
            assert "Revised" in captured.out
        finally:
            pub["VAULT_DIR"] = orig

    def test_revise_updates_existing_revision_note(self, tmp_path):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "rev2.md").write_text(
            '---\ntitle: "Rev2"\ndescription: "desc"\n'
            "pubDatetime: 2025-01-15T10:00:00.000Z\n"
            'revisionNote: "Old note"\n'
            "modDatetime: 2025-01-15T10:00:00.000Z\n"
            "draft: false\ntags: []\n---\n\nContent."
        )
        args = SimpleNamespace(slug="rev2", note="New note")
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_revise"](args)
            assert rc == 0
            content = (vault / "rev2.md").read_text()
            assert 'revisionNote: "New note"' in content
            assert 'revisionNote: "Old note"' not in content
        finally:
            pub["VAULT_DIR"] = orig

    def test_revise_post_not_found(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        args = SimpleNamespace(slug="nope", note="nothing")
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_revise"](args)
            assert rc == 1
            captured = capsys.readouterr()
            assert "No post found" in captured.err
        finally:
            pub["VAULT_DIR"] = orig

    def test_revise_bad_frontmatter(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "bad.md").write_text("No frontmatter")
        args = SimpleNamespace(slug="bad", note="fix")
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_revise"](args)
            assert rc == 1
            captured = capsys.readouterr()
            assert "Failed to parse frontmatter" in captured.err
        finally:
            pub["VAULT_DIR"] = orig


# ---------------------------------------------------------------------------
# cmd_open tests
# ---------------------------------------------------------------------------

class TestCmdOpen:
    def test_open_post_not_found(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        args = SimpleNamespace(slug="nonexistent")
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            rc = pub["cmd_open"](args)
            assert rc == 1
            captured = capsys.readouterr()
            assert "No post found" in captured.err
        finally:
            pub["VAULT_DIR"] = orig

    def test_open_calls_editor(self, tmp_path):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "edit-me.md").write_text("---\ntitle: test\n---\n")
        args = SimpleNamespace(slug="edit-me")
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                with patch.dict("os.environ", {"EDITOR": "nano"}):
                    rc = pub["cmd_open"](args)
                assert rc == 0
                mock_run.assert_called_once()
                cmd_args = mock_run.call_args[0][0]
                assert cmd_args[0] == "nano"
                assert "edit-me.md" in cmd_args[1]
        finally:
            pub["VAULT_DIR"] = orig


# ---------------------------------------------------------------------------
# cmd_index tests
# ---------------------------------------------------------------------------

class TestCmdIndex:
    def test_generates_index(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        index_path = tmp_path / "index.md"
        (vault / "post-a.md").write_text(
            '---\ntitle: "Post A"\ndescription: "First post"\n'
            "pubDatetime: 2025-03-01T10:00:00.000Z\ndraft: false\ntags: [python]\n---\n\n"
            "Content A."
        )
        (vault / "post-b.md").write_text(
            '---\ntitle: "Post B"\ndescription: "Second post"\n'
            "pubDatetime: 2025-03-15T10:00:00.000Z\ndraft: false\ntags: [python, rust]\n---\n\n"
            "Content B."
        )
        # A draft — should be excluded
        (vault / "post-c.md").write_text(
            '---\ntitle: "Draft C"\ndescription: ""\n'
            "pubDatetime: 2025-04-01T10:00:00.000Z\ndraft: true\ntags: []\n---\n\n"
        )
        orig_vault = pub["VAULT_DIR"]
        orig_index = pub["INDEX_PATH"]
        pub["VAULT_DIR"] = vault
        pub["INDEX_PATH"] = index_path
        try:
            rc = pub["cmd_index"](SimpleNamespace())
            assert rc == 0
            assert index_path.exists()
            content = index_path.read_text()
            assert "terryli.hm" in content
            assert "Post A" in content
            assert "Post B" in content
            assert "Draft C" not in content
            assert "python" in content
            captured = capsys.readouterr()
            assert "2 posts indexed" in captured.out
        finally:
            pub["VAULT_DIR"] = orig_vault
            pub["INDEX_PATH"] = orig_index

    def test_index_skips_posts_missing_fields(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        index_path = tmp_path / "index.md"
        (vault / "incomplete.md").write_text(
            '---\ntitle: "Incomplete"\ndraft: false\ntags: []\n---\n\n'
            # Missing pubDatetime and description
        )
        orig_vault = pub["VAULT_DIR"]
        orig_index = pub["INDEX_PATH"]
        pub["VAULT_DIR"] = vault
        pub["INDEX_PATH"] = index_path
        try:
            rc = pub["cmd_index"](SimpleNamespace())
            assert rc == 0
            content = index_path.read_text()
            assert "Incomplete" not in content
            captured = capsys.readouterr()
            assert "[ERROR]" in captured.err
            assert "0 posts indexed" in captured.out
        finally:
            pub["VAULT_DIR"] = orig_vault
            pub["INDEX_PATH"] = orig_index

    def test_index_empty_vault(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        vault.mkdir()
        index_path = tmp_path / "index.md"
        orig_vault = pub["VAULT_DIR"]
        orig_index = pub["INDEX_PATH"]
        pub["VAULT_DIR"] = vault
        pub["INDEX_PATH"] = index_path
        try:
            rc = pub["cmd_index"](SimpleNamespace())
            assert rc == 0
            content = index_path.read_text()
            assert "0 posts" in content
            assert "All posts" in content
        finally:
            pub["VAULT_DIR"] = orig_vault
            pub["INDEX_PATH"] = orig_index

    def test_index_vault_not_exists(self, tmp_path, capsys):
        """When vault dir doesn't exist, index still generates (0 posts)."""
        vault = tmp_path / "no_such_dir"
        index_path = tmp_path / "index.md"
        orig_vault = pub["VAULT_DIR"]
        orig_index = pub["INDEX_PATH"]
        pub["VAULT_DIR"] = vault
        pub["INDEX_PATH"] = index_path
        try:
            rc = pub["cmd_index"](SimpleNamespace())
            assert rc == 0
            content = index_path.read_text()
            assert "0 posts" in content
        finally:
            pub["VAULT_DIR"] = orig_vault
            pub["INDEX_PATH"] = orig_index

    def test_index_by_topic_section(self, tmp_path):
        vault = tmp_path / "Published"
        vault.mkdir()
        index_path = tmp_path / "index.md"
        (vault / "tagged.md").write_text(
            '---\ntitle: "Tagged Post"\ndescription: "desc"\n'
            "pubDatetime: 2025-01-01T00:00:00.000Z\ndraft: false\ntags: [rust, wasm]\n---\n\n"
            "Content."
        )
        orig_vault = pub["VAULT_DIR"]
        orig_index = pub["INDEX_PATH"]
        pub["VAULT_DIR"] = vault
        pub["INDEX_PATH"] = index_path
        try:
            rc = pub["cmd_index"](SimpleNamespace())
            assert rc == 0
            content = index_path.read_text()
            assert "### rust" in content
            assert "### wasm" in content
        finally:
            pub["VAULT_DIR"] = orig_vault
            pub["INDEX_PATH"] = orig_index


# ---------------------------------------------------------------------------
# cmd_push tests
# ---------------------------------------------------------------------------

class TestCmdPush:
    def test_sync_script_not_found(self, tmp_path, capsys):
        fake_script = tmp_path / "nonexistent" / "sync.sh"
        orig = pub["SYNC_SCRIPT"]
        pub["SYNC_SCRIPT"] = fake_script
        try:
            rc = pub["cmd_push"](SimpleNamespace())
            assert rc == 1
            captured = capsys.readouterr()
            assert "Sync script not found" in captured.err
        finally:
            pub["SYNC_SCRIPT"] = orig

    def test_sync_success(self, tmp_path, capsys):
        script = tmp_path / "sync.sh"
        script.write_text("#!/bin/bash\nexit 0")
        script.chmod(0o755)
        orig = pub["SYNC_SCRIPT"]
        pub["SYNC_SCRIPT"] = script
        try:
            rc = pub["cmd_push"](SimpleNamespace())
            assert rc == 0
            captured = capsys.readouterr()
            assert "Live at https://terryli.hm" in captured.out
        finally:
            pub["SYNC_SCRIPT"] = orig

    def test_sync_failure(self, tmp_path, capsys):
        script = tmp_path / "sync-fail.sh"
        script.write_text("#!/bin/bash\nexit 1")
        script.chmod(0o755)
        orig = pub["SYNC_SCRIPT"]
        pub["SYNC_SCRIPT"] = script
        try:
            rc = pub["cmd_push"](SimpleNamespace())
            assert rc == 1
            captured = capsys.readouterr()
            assert "Sync failed" in captured.err
        finally:
            pub["SYNC_SCRIPT"] = orig


# ---------------------------------------------------------------------------
# main / CLI integration tests
# ---------------------------------------------------------------------------

class TestMain:
    def test_no_command_exits_with_error(self):
        """main() with no args should error (argparse required=True)."""
        with patch("sys.argv", ["publish"]):
            with pytest.raises(SystemExit) as exc_info:
                pub["main"]()
            assert exc_info.value.code == 2  # argparse error

    def test_new_via_main(self, tmp_path, capsys):
        vault = tmp_path / "Published"
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            with patch("sys.argv", ["publish", "new", "CLI Test Post"]):
                with pytest.raises(SystemExit) as exc_info:
                    pub["main"]()
                assert exc_info.value.code == 0
            slug = pub["to_slug"]("CLI Test Post")
            assert (vault / f"{slug}.md").exists()
        finally:
            pub["VAULT_DIR"] = orig

    def test_list_via_main(self, tmp_path):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "listed.md").write_text(
            '---\ntitle: "Listed"\ndescription: ""\n'
            "pubDatetime: 2025-01-01T00:00:00.000Z\ndraft: false\ntags: []\n---\n\n"
        )
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            with patch("sys.argv", ["publish", "list"]):
                with pytest.raises(SystemExit) as exc_info:
                    pub["main"]()
                assert exc_info.value.code == 0
        finally:
            pub["VAULT_DIR"] = orig

    def test_publish_via_main(self, tmp_path):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "main-pub.md").write_text(
            '---\ntitle: "Main Publish"\ndescription: ""\n'
            "pubDatetime: 2025-01-01T00:00:00.000Z\ndraft: true\ntags: []\n---\n\n"
        )
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            with patch("sys.argv", ["publish", "publish", "main-pub"]):
                with pytest.raises(SystemExit) as exc_info:
                    pub["main"]()
                assert exc_info.value.code == 0
            content = (vault / "main-pub.md").read_text()
            assert "draft: false" in content
        finally:
            pub["VAULT_DIR"] = orig

    def test_revise_via_main(self, tmp_path):
        vault = tmp_path / "Published"
        vault.mkdir()
        (vault / "main-rev.md").write_text(
            '---\ntitle: "Main Revise"\ndescription: ""\n'
            "pubDatetime: 2025-01-01T00:00:00.000Z\ndraft: false\ntags: []\n---\n\n"
        )
        orig = pub["VAULT_DIR"]
        pub["VAULT_DIR"] = vault
        try:
            with patch("sys.argv", ["publish", "revise", "main-rev", "--note", "updated"]):
                with pytest.raises(SystemExit) as exc_info:
                    pub["main"]()
                assert exc_info.value.code == 0
            content = (vault / "main-rev.md").read_text()
            assert 'revisionNote: "updated"' in content
        finally:
            pub["VAULT_DIR"] = orig

    def test_index_via_main(self, tmp_path):
        vault = tmp_path / "Published"
        vault.mkdir()
        index_path = tmp_path / "idx.md"
        (vault / "ipost.md").write_text(
            '---\ntitle: "Index Post"\ndescription: "desc"\n'
            "pubDatetime: 2025-01-01T00:00:00.000Z\ndraft: false\ntags: []\n---\n\n"
        )
        orig_vault = pub["VAULT_DIR"]
        orig_index = pub["INDEX_PATH"]
        pub["VAULT_DIR"] = vault
        pub["INDEX_PATH"] = index_path
        try:
            with patch("sys.argv", ["publish", "index"]):
                with pytest.raises(SystemExit) as exc_info:
                    pub["main"]()
                assert exc_info.value.code == 0
            assert index_path.exists()
        finally:
            pub["VAULT_DIR"] = orig_vault
            pub["INDEX_PATH"] = orig_index

    def test_push_via_main_no_script(self, tmp_path):
        fake_script = tmp_path / "no" / "sync.sh"
        orig = pub["SYNC_SCRIPT"]
        pub["SYNC_SCRIPT"] = fake_script
        try:
            with patch("sys.argv", ["publish", "push"]):
                with pytest.raises(SystemExit) as exc_info:
                    pub["main"]()
                assert exc_info.value.code == 1
        finally:
            pub["SYNC_SCRIPT"] = orig
