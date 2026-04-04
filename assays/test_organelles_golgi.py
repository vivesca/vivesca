from __future__ import annotations

"""Tests for metabolon.organelles.golgi — blog publishing pipeline.

Covers: _now_iso, _to_slug, _parse_frontmatter, _write_frontmatter,
chaperone_check, scan_content, new, publish, revise, list_posts,
push, index, _cli.  All filesystem I/O is mocked via tmp_path.
"""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest
import yaml

import metabolon.organelles.golgi as golgi


# ============================================================================
# _now_iso
# ============================================================================


class TestNowIso:
    def test_format_matches_iso8601(self):
        result = golgi._now_iso()
        assert result.endswith("Z")
        assert "T" in result
        # pattern: YYYY-MM-DDTHH:MM:SS.000Z
        assert len(result) == 24

    def test_returns_string(self):
        assert isinstance(golgi._now_iso(), str)


# ============================================================================
# _to_slug
# ============================================================================


class TestToSlug:
    @pytest.mark.parametrize(
        "title, expected",
        [
            ("Hello World", "hello-world"),
            ("my_post", "my-post"),
            ("", ""),
            ("@#$%", ""),
            ("hello  world", "hello-world"),
        ],
    )
    def test_slug_cases(self, title, expected):
        assert golgi._to_slug(title) == expected

    def test_trailing_dash_removed(self):
        assert not golgi._to_slug("test ").endswith("-")

    def test_apostrophe_stripped(self):
        slug = golgi._to_slug("What's Next?")
        assert "'" not in slug
        assert "?" not in slug

    def test_leading_space(self):
        assert golgi._to_slug(" hello").startswith("-")

    def test_unicode_chars_stripped(self):
        slug = golgi._to_slug("café résumé")
        assert slug == "caf-rsum"


# ============================================================================
# _parse_frontmatter / _write_frontmatter
# ============================================================================


class TestParseFrontmatter:
    def test_valid_frontmatter(self):
        content = "---\ntitle: Test\ndraft: true\n---\nBody here"
        result = golgi._parse_frontmatter(content)
        assert result is not None
        fm, body = result
        assert fm["title"] == "Test"
        assert fm["draft"] is True
        assert body.strip() == "Body here"

    def test_no_frontmatter(self):
        assert golgi._parse_frontmatter("Just text") is None

    def test_unclosed_frontmatter(self):
        assert golgi._parse_frontmatter("---\ntitle: X\nNo close") is None

    def test_empty_body(self):
        content = "---\ntitle: X\n---\n"
        result = golgi._parse_frontmatter(content)
        assert result is not None
        fm, body = result
        assert fm["title"] == "X"
        assert body.strip() == ""


class TestWriteFrontmatter:
    def test_roundtrip(self):
        fm = {"title": "Test", "tags": ["ai", "rust"], "draft": True}
        body = "\nSome body\n"
        text = golgi._write_frontmatter(fm, body)
        assert text.startswith("---\n")
        parsed = golgi._parse_frontmatter(text)
        assert parsed is not None
        assert parsed[0]["title"] == "Test"
        assert parsed[0]["tags"] == ["ai", "rust"]

    def test_unicode_preserved(self):
        fm = {"title": "日本語テスト"}
        text = golgi._write_frontmatter(fm, "\n")
        assert "日本語テスト" in text


# ============================================================================
# chaperone_check
# ============================================================================


class TestChaperoneCheck:
    def test_pii_card_number(self):
        r = golgi.chaperone_check("Card: 4111 1111 1111 1111", "blog")
        assert r is not None and "PII" in r

    def test_pii_hkid(self):
        assert golgi.chaperone_check("ID: A123456(7)", "blog") is not None

    def test_pii_ssn(self):
        assert golgi.chaperone_check("SSN: 123-45-6789", "blog") is not None

    def test_clean_passes(self):
        assert golgi.chaperone_check("Normal text.", "blog") is None

    @pytest.mark.parametrize("channel", ["tweet", "telegram"])
    def test_special_chars_blocked_tweet_telegram(self, channel):
        r = golgi.chaperone_check("Here\u2019s a test", channel)
        assert r is not None and "special characters" in r

    def test_special_chars_ok_blog(self):
        assert golgi.chaperone_check("Here\u2019s a test", "blog") is None

    def test_tweet_too_long(self):
        r = golgi.chaperone_check("x" * 300, "tweet")
        assert r is not None and "too long" in r

    def test_tweet_at_exactly_280(self):
        assert golgi.chaperone_check("x" * 280, "tweet") is None

    def test_tweet_281_chars(self):
        r = golgi.chaperone_check("x" * 281, "tweet")
        assert r is not None


# ============================================================================
# scan_content
# ============================================================================


class TestScanContent:
    def test_clean_content(self):
        assert golgi.scan_content("A perfectly clean post about governance.") == []

    def test_dollar_amount(self):
        w = golgi.scan_content("We saved $5000 last quarter")
        assert any("dollar" in x for x in w)

    def test_hkd_amount(self):
        w = golgi.scan_content("Budget was HKD 3000")
        assert any("HKD" in x for x in w)

    def test_million_figure(self):
        w = golgi.scan_content("Revenue hit 5 million units")
        assert any("million" in x for x in w)

    def test_billion_figure(self):
        w = golgi.scan_content("Market cap 2 billion dollars")
        assert any("billion" in x for x in w)

    def test_financial_percentage(self):
        w = golgi.scan_content("Our 40% margin improved")
        assert any("percentage" in x for x in w)

    def test_named_individual(self):
        w = golgi.scan_content("Met with Mr. Smith yesterday")
        assert any("named" in x for x in w)

    def test_credential_leak(self):
        w = golgi.scan_content('api_key: sk-abc123def456ghi789')
        assert any("credential" in x for x in w)

    def test_offensive_word(self):
        w = golgi.scan_content("This is bullshit")
        assert any("offensive" in x for x in w)

    def test_multiple_warnings(self):
        w = golgi.scan_content("Mr. Rich saved $5000 and said fuck")
        assert len(w) >= 3

    def test_non_financial_percentage_ok(self):
        assert golgi.scan_content("Growth was 50% overall") == []


# ============================================================================
# new
# ============================================================================


class TestNew:
    def test_creates_draft_file(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("My First Post")
        assert path.exists()
        assert slug == "my-first-post"
        content = path.read_text()
        assert "title: My First Post" in content
        assert "draft: true" in content

    def test_duplicate_raises(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            golgi.new("Dup Post")
            with pytest.raises(ValueError, match="already exists"):
                golgi.new("Dup Post")

    def test_creates_directory(self, tmp_path):
        subdir = tmp_path / "nested"
        with patch.object(golgi, "GARDEN_DIR", subdir):
            slug, path = golgi.new("Nested Post")
        assert subdir.exists()
        assert path.exists()

    def test_includes_pub_datetime(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            _, path = golgi.new("Dated Post")
        content = path.read_text()
        assert "pubDatetime:" in content

    def test_empty_tags_list(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            _, path = golgi.new("Tag Post")
        content = path.read_text()
        assert "tags: []" in content


# ============================================================================
# publish
# ============================================================================


class TestPublish:
    def test_publish_clears_draft(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Pub Me")
            title = golgi.publish(slug, force=True)
        assert title == "Pub Me"
        assert "draft: false" in path.read_text()

    def test_publish_already_published(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, _ = golgi.new("Done Already")
            golgi.publish(slug, force=True)
            title = golgi.publish(slug, force=False)
        assert title == "Done Already"

    def test_publish_nonexistent_raises(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            with pytest.raises(ValueError, match="No post found"):
                golgi.publish("nonexistent")

    def test_publish_blocks_on_sensitive_content(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Risky")
            fm, body = golgi._parse_frontmatter(path.read_text())
            path.write_text(golgi._write_frontmatter(fm, "Saved $5000.\n" + body))
            with pytest.raises(ValueError, match="Content scan"):
                golgi.publish(slug, force=False)

    def test_publish_force_overrides_sensitive(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Force It")
            fm, body = golgi._parse_frontmatter(path.read_text())
            path.write_text(golgi._write_frontmatter(fm, "Saved $5000.\n" + body))
            golgi.publish(slug, force=True)
        assert "draft: false" in path.read_text()

    def test_publish_bad_frontmatter_raises(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Bad FM")
            # overwrite with no frontmatter
            path.write_text("No frontmatter here")
            with pytest.raises(ValueError, match="Failed to parse"):
                golgi.publish(slug)


# ============================================================================
# revise
# ============================================================================


class TestRevise:
    def test_revise_adds_fields(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Revise Me")
            title = golgi.revise(slug, "Fixed typo")
        assert title == "Revise Me"
        content = path.read_text()
        assert "modDatetime:" in content
        assert "revisionNote: Fixed typo" in content

    def test_revise_nonexistent_raises(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            with pytest.raises(ValueError, match="No post found"):
                golgi.revise("nope", "note")

    def test_revise_bad_frontmatter_raises(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Bad Rev")
            path.write_text("No frontmatter here")
            with pytest.raises(ValueError, match="Failed to parse"):
                golgi.revise(slug, "note")


# ============================================================================
# list_posts
# ============================================================================


class TestListPosts:
    def test_empty_dir(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            assert golgi.list_posts() == []

    def test_nonexistent_dir(self, tmp_path):
        missing = tmp_path / "no-such-dir"
        with patch.object(golgi, "GARDEN_DIR", missing):
            assert golgi.list_posts() == []

    def test_returns_metadata(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            golgi.new("Test Post")
            posts = golgi.list_posts()
        assert len(posts) == 1
        p = posts[0]
        assert p["title"] == "Test Post"
        assert p["draft"] is True
        assert "words" in p
        assert "pubDatetime" in p
        assert "slug" in p
        assert "tags" in p

    def test_skips_bad_frontmatter(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            (tmp_path / "bad.md").write_text("No frontmatter")
            golgi.new("Good Post")
            posts = golgi.list_posts()
        assert len(posts) == 1
        assert posts[0]["title"] == "Good Post"

    def test_sorted_by_date_descending(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            golgi.new("Alpha")
            golgi.new("Beta")
            posts = golgi.list_posts()
        assert len(posts) == 2


# ============================================================================
# push
# ============================================================================


class TestPush:
    def test_missing_script_raises(self):
        fake = MagicMock()
        fake.exists.return_value = False
        with patch.object(golgi, "SYNC_SCRIPT", fake):
            with pytest.raises(ValueError, match="Sync script not found"):
                golgi.push()

    def test_successful_push(self):
        fake_script = MagicMock()
        fake_script.exists.return_value = True
        fake_script.__str__ = lambda s: "/fake/sync.sh"
        fake_result = MagicMock()
        fake_result.returncode = 0
        fake_result.stdout = "ok"
        with patch.object(golgi, "SYNC_SCRIPT", fake_script), \
             patch("metabolon.organelles.golgi.subprocess.run", return_value=fake_result) as mock_run:
            result = golgi.push()
        assert result == "Live at https://terryli.hm"
        mock_run.assert_called_once_with(
            ["bash", "/fake/sync.sh"],
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_failed_push_raises(self):
        fake_script = MagicMock()
        fake_script.exists.return_value = True
        fake_script.__str__ = lambda s: "/fake/sync.sh"
        fake_result = MagicMock()
        fake_result.returncode = 1
        fake_result.stderr = "permission denied"
        with patch.object(golgi, "SYNC_SCRIPT", fake_script), \
             patch("metabolon.organelles.golgi.subprocess.run", return_value=fake_result):
            with pytest.raises(ValueError, match="Sync failed"):
                golgi.push()


# ============================================================================
# index
# ============================================================================


class TestIndex:
    def test_skips_drafts(self, tmp_path):
        idx = tmp_path / "index.md"
        with patch.object(golgi, "GARDEN_DIR", tmp_path), \
             patch.object(golgi, "INDEX_PATH", idx):
            golgi.new("Draft Only")
            count = golgi.index()
        assert count == 0

    def test_includes_published(self, tmp_path):
        idx = tmp_path / "index.md"
        with patch.object(golgi, "GARDEN_DIR", tmp_path), \
             patch.object(golgi, "INDEX_PATH", idx):
            slug, _ = golgi.new("Published Post")
            golgi.publish(slug, force=True)
            count = golgi.index()
        assert count == 1
        text = idx.read_text()
        assert "terryli.hm" in text
        assert "Published Post" in text

    def test_groups_by_tag(self, tmp_path):
        idx = tmp_path / "index.md"
        with patch.object(golgi, "GARDEN_DIR", tmp_path), \
             patch.object(golgi, "INDEX_PATH", idx):
            # Create two posts with tags
            slug1, path1 = golgi.new("Tagged One")
            fm1, body1 = golgi._parse_frontmatter(path1.read_text())
            fm1["tags"] = ["ai"]
            path1.write_text(golgi._write_frontmatter(fm1, body1))
            golgi.publish(slug1, force=True)

            slug2, path2 = golgi.new("Tagged Two")
            fm2, body2 = golgi._parse_frontmatter(path2.read_text())
            fm2["tags"] = ["ai"]
            path2.write_text(golgi._write_frontmatter(fm2, body2))
            golgi.publish(slug2, force=True)

            count = golgi.index()
        assert count == 2
        text = idx.read_text()
        assert "## ai" in text.lower() or "### ai" in text

    def test_empty_garden_dir(self, tmp_path):
        idx = tmp_path / "index.md"
        garden = tmp_path / "garden"
        garden.mkdir()
        with patch.object(golgi, "GARDEN_DIR", garden), \
             patch.object(golgi, "INDEX_PATH", idx):
            count = golgi.index()
        assert count == 0

    def test_wikilink_format(self, tmp_path):
        idx = tmp_path / "index.md"
        with patch.object(golgi, "GARDEN_DIR", tmp_path), \
             patch.object(golgi, "INDEX_PATH", idx):
            slug, path = golgi.new("Link Test")
            golgi.publish(slug, force=True)
            golgi.index()
        text = idx.read_text()
        assert "[[Writing/Blog/Published/link-test|Link Test]]" in text


# ============================================================================
# _cli
# ============================================================================


class TestCli:
    def _run_cli(self, args):
        """Run _cli with patched sys.argv, return captured output."""
        with patch("sys.argv", ["publish"] + args):
            with patch("builtins.print") as mock_print:
                golgi._cli()
        return mock_print

    def test_new(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            mock_print = self._run_cli(["new", "CLI Post"])
        mock_print.assert_called_once()
        assert "Created" in mock_print.call_args[0][0]
        assert "(draft)" in mock_print.call_args[0][0]

    def test_list(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            golgi.new("Listed Post")
            mock_print = self._run_cli(["list"])
        assert mock_print.call_count == 1
        output = mock_print.call_args[0][0]
        assert "listed-post" in output

    def test_publish(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            golgi.new("Pub CLI")
            mock_print = self._run_cli(["publish", "pub-cli"])
        assert mock_print.call_count == 1
        assert "Published" in mock_print.call_args[0][0]

    def test_publish_with_push(self, tmp_path):
        fake_script = MagicMock()
        fake_script.exists.return_value = True
        fake_script.__str__ = lambda s: "/fake/sync.sh"
        fake_result = MagicMock()
        fake_result.returncode = 0
        with patch.object(golgi, "GARDEN_DIR", tmp_path), \
             patch.object(golgi, "SYNC_SCRIPT", fake_script), \
             patch("metabolon.organelles.golgi.subprocess.run", return_value=fake_result):
            golgi.new("Push CLI")
            mock_print = self._run_cli(["publish", "push-cli", "--push"])
        assert mock_print.call_count == 2

    def test_revise(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            golgi.new("Rev CLI")
            mock_print = self._run_cli(["revise", "rev-cli", "--note", "typo fix"])
        assert mock_print.call_count == 1
        assert "Revised" in mock_print.call_args[0][0]

    def test_index(self, tmp_path):
        idx = tmp_path / "index.md"
        with patch.object(golgi, "GARDEN_DIR", tmp_path), \
             patch.object(golgi, "INDEX_PATH", idx):
            mock_print = self._run_cli(["index"])
        assert mock_print.call_count == 1
        assert "Index updated" in mock_print.call_args[0][0]

    def test_push(self):
        fake_script = MagicMock()
        fake_script.exists.return_value = True
        fake_script.__str__ = lambda s: "/fake/sync.sh"
        fake_result = MagicMock()
        fake_result.returncode = 0
        with patch.object(golgi, "SYNC_SCRIPT", fake_script), \
             patch("metabolon.organelles.golgi.subprocess.run", return_value=fake_result):
            mock_print = self._run_cli(["push"])
        assert mock_print.call_count == 1
        assert "Live at" in mock_print.call_args[0][0]

    def test_no_command_shows_help(self):
        with patch("sys.argv", ["publish"]), \
             patch.object(golgi, "GARDEN_DIR", MagicMock()), \
             patch("argparse.ArgumentParser.print_help") as mock_help:
            golgi._cli()
        mock_help.assert_called_once()
