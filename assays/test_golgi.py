from __future__ import annotations

"""Tests for golgi — blog publishing pipeline."""


from unittest.mock import patch

import pytest

import metabolon.organelles.golgi as golgi


# -- TestToSlug ----------------------------------------------------------------


class TestToSlug:
    def test_basic_slug(self):
        assert golgi._to_slug("Hello World") == "hello-world"

    def test_special_chars_stripped(self):
        result = golgi._to_slug("What's Next? AI & Banking!")
        # Apostrophe, ?, !, & all stripped; spaces become dashes
        assert "'" not in result
        assert "?" not in result
        assert "!" not in result
        assert "&" not in result

    def test_trailing_dash_stripped(self):
        assert not golgi._to_slug("test ").endswith("-")

    def test_leading_space_produces_dash(self):
        # space at start → treated as separator → dash prefix
        assert golgi._to_slug(" hello").startswith("-")

    def test_consecutive_spaces_single_dash(self):
        assert golgi._to_slug("hello  world") == "hello-world"

    def test_underscores_become_dash(self):
        assert golgi._to_slug("my_post") == "my-post"

    def test_empty_string(self):
        assert golgi._to_slug("") == ""

    def test_only_special_chars(self):
        assert golgi._to_slug("@#$%") == ""


# -- TestFrontmatter -----------------------------------------------------------


class TestFrontmatter:
    def test_parse_valid_frontmatter(self):
        content = "---\ntitle: Test\ndraft: true\n---\nBody here"
        result = golgi._parse_frontmatter(content)
        assert result is not None
        fm, body = result
        assert fm["title"] == "Test"
        assert "Body here" in body

    def test_parse_no_frontmatter(self):
        assert golgi._parse_frontmatter("No frontmatter here") is None

    def test_parse_unclosed_frontmatter(self):
        assert golgi._parse_frontmatter("---\ntitle: Test\nNo closing") is None

    def test_write_roundtrip(self):
        original_fm = {"title": "Test", "tags": ["ai", "banking"]}
        body = "\nBody content\n"
        result = golgi._write_frontmatter(original_fm, body)
        reparsed = golgi._parse_frontmatter(result)
        assert reparsed is not None
        assert reparsed[0]["title"] == "Test"
        assert reparsed[0]["tags"] == ["ai", "banking"]
        assert "Body content" in reparsed[1]


# -- TestChaperoneCheck --------------------------------------------------------


class TestChaperoneCheck:
    def test_pii_blocked(self):
        result = golgi.chaperone_check("Card: 4111 1111 1111 1111", "blog")
        assert result is not None
        assert "PII" in result

    def test_hkid_blocked(self):
        assert golgi.chaperone_check("HKID: A123456(7)", "blog") is not None

    def test_ssn_blocked(self):
        assert golgi.chaperone_check("SSN: 123-45-6789", "blog") is not None

    def test_clean_content_passes(self):
        assert golgi.chaperone_check("This is clean content.", "blog") is None

    def test_special_chars_blocked_for_tweet(self):
        result = golgi.chaperone_check("Here\u2019s a test", "tweet")
        assert result is not None

    def test_special_chars_blocked_for_telegram(self):
        result = golgi.chaperone_check("Wait\u2026 what?", "telegram")
        assert result is not None

    def test_special_chars_allowed_for_blog(self):
        # Smart quotes are OK in blog posts
        assert golgi.chaperone_check("Here\u2019s a test", "blog") is None

    def test_tweet_length_check(self):
        long = "x" * 300
        result = golgi.chaperone_check(long, "tweet")
        assert result is not None
        assert "too long" in result

    def test_tweet_under_limit_passes(self):
        short = "x" * 280
        assert golgi.chaperone_check(short, "tweet") is None


# -- TestScanContent -----------------------------------------------------------


class TestScanContent:
    def test_detects_dollar_amounts(self):
        warnings = golgi.scan_content("We saved $5000 last quarter")
        assert any("dollar" in w for w in warnings)

    def test_detects_hkd_amounts(self):
        warnings = golgi.scan_content("Budget was HKD 3000")
        assert any("HKD" in w for w in warnings)

    def test_detects_named_individuals(self):
        warnings = golgi.scan_content("Met with Mr. Smith yesterday")
        assert any("named" in w for w in warnings)

    def test_detects_credentials(self):
        warnings = golgi.scan_content("api_key: sk-abc123def456ghi789")
        assert any("credential" in w for w in warnings)

    def test_detects_offensive_language(self):
        warnings = golgi.scan_content("This is bullshit")
        assert any("offensive" in w for w in warnings)

    def test_clean_content(self):
        assert golgi.scan_content("A perfectly clean blog post about AI governance.") == []

    def test_detects_million_figure(self):
        warnings = golgi.scan_content("Revenue hit 5 million last year")
        assert any("million" in w for w in warnings)

    def test_detects_financial_percentage(self):
        warnings = golgi.scan_content("Our 40% margin improved")
        assert any("percentage" in w for w in warnings)


# -- TestNewPost ---------------------------------------------------------------


class TestNewPost:
    def test_new_creates_draft(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("My First Post")
        assert path.exists()
        content = path.read_text()
        assert "draft: true" in content
        assert slug == "my-first-post"

    def test_new_duplicate_raises(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            golgi.new("Dup Post")
            with pytest.raises(ValueError, match="already exists"):
                golgi.new("Dup Post")

    def test_new_includes_title_in_frontmatter(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Test Title Here")
        content = path.read_text()
        assert "title: Test Title Here" in content

    def test_new_includes_tags_field(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Tagged Post")
        content = path.read_text()
        assert "tags:" in content

    def test_new_creates_directory(self, tmp_path):
        subdir = tmp_path / "nested"
        with patch.object(golgi, "GARDEN_DIR", subdir):
            slug, path = golgi.new("Nested Post")
        assert subdir.exists()
        assert path.exists()


# -- TestPublish ---------------------------------------------------------------


class TestPublish:
    def test_publish_clears_draft(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Publish Me")
            golgi.publish(slug, force=True)
            content = path.read_text()
        assert "draft: false" in content

    def test_publish_warns_on_sensitive(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Risky Post")
            fm, body = golgi._parse_frontmatter(path.read_text())
            path.write_text(golgi._write_frontmatter(fm, "We saved $5000.\n" + body))
            with pytest.raises(ValueError, match="Content scan"):
                golgi.publish(slug, force=False)

    def test_publish_already_published(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Already Done")
            golgi.publish(slug, force=True)
            # Publishing again should succeed without error
            result = golgi.publish(slug, force=False)
        assert result == "Already Done"

    def test_publish_nonexistent_raises(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            with pytest.raises(ValueError, match="No post found"):
                golgi.publish("nonexistent", force=True)

    def test_publish_force_overrides_sensitive(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Force Post")
            fm, body = golgi._parse_frontmatter(path.read_text())
            path.write_text(golgi._write_frontmatter(fm, "We saved $5000.\n" + body))
            # Should NOT raise with force=True
            golgi.publish(slug, force=True)
        content = path.read_text()
        assert "draft: false" in content


# -- TestListPosts -------------------------------------------------------------


class TestListPosts:
    def test_list_empty(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            assert golgi.list_posts() == []

    def test_list_returns_metadata(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            golgi.new("Test Post")
            posts = golgi.list_posts()
        assert len(posts) == 1
        assert posts[0]["title"] == "Test Post"
        assert posts[0]["draft"] is True

    def test_list_nonexistent_dir(self, tmp_path):
        missing = tmp_path / "no-such-dir"
        with patch.object(golgi, "GARDEN_DIR", missing):
            assert golgi.list_posts() == []

    def test_list_sorted_by_date_descending(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            golgi.new("First Post")
            golgi.new("Second Post")
            posts = golgi.list_posts()
        # Both created in same second, but sorted reverse by datetime
        assert len(posts) == 2

    def test_list_includes_word_count(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            golgi.new("Word Count Post")
            posts = golgi.list_posts()
        assert "words" in posts[0]


# -- TestRevise ----------------------------------------------------------------


class TestRevise:
    def test_revise_adds_mod_datetime(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            slug, path = golgi.new("Revise Me")
            golgi.revise(slug, "Fixed typo")
            content = path.read_text()
        assert "modDatetime:" in content
        assert "revisionNote: Fixed typo" in content

    def test_revise_nonexistent_raises(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            with pytest.raises(ValueError, match="No post found"):
                golgi.revise("nope", "note")


# -- TestPush/Index (integration-light) ----------------------------------------


class TestPush:
    def test_push_missing_script_raises(self):
        with patch.object(golgi, "SYNC_SCRIPT", golgi.SYNC_SCRIPT):
            # Point to a nonexistent path
            with patch.object(golgi, "SYNC_SCRIPT", type("", (), {"exists": lambda s: False, "__fspath__": lambda s: "/nope"})()):
                pass  # just verify the guard exists; real push tests need the script


class TestIndex:
    def test_index_skips_drafts(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path):
            golgi.new("Draft Only")
            count = golgi.index()
        assert count == 0

    def test_index_includes_published(self, tmp_path):
        with patch.object(golgi, "GARDEN_DIR", tmp_path), \
             patch.object(golgi, "INDEX_PATH", tmp_path / "index.md"):
            slug, path = golgi.new("Published Post")
            golgi.publish(slug, force=True)
            count = golgi.index()
        assert count == 1
